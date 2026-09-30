"""Run: PYTHONPATH=src python -m gridmind_research.run --data data/storenet_h1_h6_15min.csv"""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .clearing import clear
from .forecast import benchmark
from .metrics import benefit_metrics, cvar, paired_block_ci


def run(data, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(data, index_col=0, parse_dates=True)
    if d.index.duplicated().any() or not d.index.is_monotonic_increasing:
        raise ValueError("Ordered unique timestamps required")
    if not d.index.to_series().diff().dropna().eq(pd.Timedelta(minutes=15)).all():
        raise ValueError("Keep missing intervals as rows with NaNs, not missing timestamp rows")
    load = d.filter(like="_load_kwh")
    pv = d.filter(like="_pv_kwh")
    if load.shape[1] != 6 or pv.shape[1] != 6:
        raise ValueError("This pilot requires the fixed H1-H6 cohort")
    scale = (load.loc[:"2020-05-31"].mean().to_numpy() * 96 * 0.3).clip(0.1)
    test = d.loc["2020-06-01":"2020-06-14 23:45"]
    kept = test.dropna()
    if len(kept) < 100:
        raise ValueError("Insufficient pilot data")
    scenarios = {
        "homogeneous": {"buy": [0.30] * 6, "sell": [0.08] * 6, "fee": 0.02},
        "heterogeneous": {
            "buy": [0.22, 0.26, 0.30, 0.34, 0.38, 0.42],
            "sell": [0.08, 0.08, 0.08, 0.08, 0.08, 0.08],
            "fee": 0.02,
        },
    }
    specs = [
        ("proportional", 0.0),
        ("welfare_lp", 0.0),
        ("nash_guarded", 0.0),
        ("nash_guarded", 0.05),
        ("nash_guarded", 0.10),
    ]
    all_daily = []
    all_trades = []
    summaries = []
    all_households = []
    for scenario, tariff in scenarios.items():
        for policy, tolerance in specs:
            label = policy if policy != "nash_guarded" else f"nash_guarded_{tolerance:.2f}"
            total = np.zeros(6)
            daily = []
            fallback = 0
            statuses = {}
            started = time.perf_counter()
            for day, frame in kept.groupby(kept.index.date):
                cum = np.zeros(6)
                outside = 0.0
                fees = 0.0
                energy = 0.0
                bounds = 0.0
                max_residual = 0.0
                for stamp, row in frame.iterrows():
                    net = (
                        row.filter(like="_load_kwh").to_numpy()
                        - row.filter(like="_pv_kwh").to_numpy()
                    )
                    r = clear(
                        net,
                        tariff["buy"],
                        tariff["sell"],
                        policy=policy,
                        fee=tariff["fee"],
                        cumulative=cum,
                        scale=scale,
                        welfare_tolerance=tolerance,
                    )
                    cum += r.benefit_eur
                    outside += float(
                        np.array(tariff["buy"]) @ np.maximum(net, 0)
                        - np.array(tariff["sell"]) @ np.maximum(-net, 0)
                    )
                    fees += r.fee_eur
                    bounds += r.welfare_bound_eur
                    residual = abs(r.grid_import_kwh.sum() - r.grid_export_kwh.sum() - net.sum())
                    max_residual = max(max_residual, residual)
                    energy += sum(t["kwh"] for t in r.trades)
                    statuses[r.solver_status] = statuses.get(r.solver_status, 0) + 1
                    fallback += int("fallback" in r.solver_status)
                    for trade in r.trades:
                        all_trades.append(
                            {
                                "scenario": scenario,
                                "policy": label,
                                "timestamp": str(stamp),
                                **trade,
                            }
                        )
                normalized = benefit_metrics(cum / scale)
                record = {
                    "scenario": scenario,
                    "policy": label,
                    "day": str(day),
                    "intervals": len(frame),
                    "benefit_eur": float(cum.sum()),
                    "outside_cost_eur": outside,
                    "community_cost_eur": outside - float(cum.sum()),
                    "fee_eur": fees,
                    "matched_kwh": energy,
                    "welfare_bound_eur": bounds,
                    "normalized_jain": normalized["jain"],
                    "normalized_gini": normalized["gini"],
                    "max_balance_residual_kwh": max_residual,
                }
                daily.append(record)
                total += cum
                for i, v in enumerate(cum):
                    all_households.append(
                        {
                            "scenario": scenario,
                            "policy": label,
                            "day": str(day),
                            "household": f"H{i + 1}",
                            "benefit_eur": float(v),
                            "normalized_benefit": float(v / scale[i]),
                        }
                    )
            all_daily += daily
            sums = benefit_metrics(total)
            norm = benefit_metrics(total / scale)
            summaries.append(
                {
                    "scenario": scenario,
                    "policy": label,
                    "benefits": sums,
                    "normalized_benefits": norm,
                    "per_household_eur": total.tolist(),
                    "mean_daily_normalized_jain": float(
                        np.mean(
                            [
                                r["normalized_jain"]
                                for r in daily
                                if r["normalized_jain"] is not None
                            ]
                        )
                    ),
                    "daily_cost_cvar95_eur": cvar([r["community_cost_eur"] for r in daily]),
                    "cvar_tail_days": len(daily) * 0.05,
                    "nash_fallback_intervals": fallback,
                    "solver_status_counts": statuses,
                    "runtime_seconds": time.perf_counter() - started,
                }
            )
            print(scenario, label, round(total.sum(), 4), "EUR benefit", flush=True)
    daily = pd.DataFrame(all_daily)
    daily.to_csv(out / "daily_metrics.csv", index=False)
    pd.DataFrame(all_trades).to_csv(out / "trades.csv", index=False)
    pd.DataFrame(all_households).to_csv(out / "household_daily_benefits.csv", index=False)
    intervals = {}
    for scenario in scenarios:
        part = daily[daily.scenario.eq(scenario)]
        lp = part[part.policy.eq("welfare_lp")].set_index("day")
        fair = part[part.policy.eq("nash_guarded_0.05")].set_index("day")
        intervals[scenario] = {
            metric: paired_block_ci(fair[metric], lp[metric])
            for metric in ["benefit_eur", "normalized_jain"]
        }
    forecasts, preds = benchmark(d)
    preds.to_csv(out / "forecast_predictions.csv")
    result = {
        "evidence": "measured_load_and_pv_with_assumed_tariffs_counterfactual_allocation",
        "not_live_trading": True,
        "not_marl_evaluation": True,
        "cohort": "H1-H6",
        "period": "2020-06-01 through 2020-06-14 in source clock",
        "expected_intervals": 14 * 96,
        "retained_intervals": len(kept),
        "household_scale_eur_per_day": scale.tolist(),
        "scenarios": scenarios,
        "savings_relative_to": "grid-only without battery, same measured load and PV",
        "fairness_objective": "regularized log cumulative daily savings / fixed training scale",
        "epsilon": 0.01,
        "summaries": summaries,
        "exploratory_paired_intervals": intervals,
        "forecasts": forecasts,
        "data_sha256": hashlib.sha256(Path(data).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "packages": {
            p: importlib.metadata.version(p) for p in ["numpy", "scipy", "pandas", "scikit-learn"]
        },
    }
    (out / "pilot_results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/storenet_h1_h6_15min.csv")
    p.add_argument("--out", default="results")
    a = p.parse_args()
    run(a.data, a.out)
