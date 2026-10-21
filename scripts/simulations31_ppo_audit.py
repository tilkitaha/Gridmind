"""Read-only forecast-conditioned PPO/MILP decision audit for development dates.

Example: python scripts/simulations31_ppo_audit.py --repo . --day 2026-06-30 \
    --out /tmp/gridmind-sim31-june30

Does not train, download prices, edit repository files, or evaluate reserved test months.
No observed prices are used: profits are hypothetical *forecast-price* objectives.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
START = date(2026, 1, 1)
END = date(2026, 6, 30)
SEEDS = (11, 22, 33, 44, 55)


def inside(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def validate_paths(repo: Path, out: Path, day: date) -> tuple[Path, Path]:
    repo, out = repo.resolve(), out.resolve()
    if not START <= day <= END:
        raise ValueError("Only 2026-01-01 through 2026-06-30 development dates are permitted")
    if not (repo / "src/gridmind_research/polish_rl.py").is_file():
        raise ValueError("Not a Gridmind repository")
    if inside(out, repo):
        raise ValueError("Output must be outside the repository")
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite output: {out}")
    if not out.parent.is_dir():
        raise ValueError("Output parent directory must already exist")
    return repo, out


def forecast_for_day(repo: Path, day: date) -> np.ndarray:
    data = pd.read_csv(repo / "results/polish_rl/lear_forecasts.csv", index_col=0)
    if data.index.has_duplicates or str(day) not in data.index:
        raise ValueError("Forecast date missing or duplicated")
    forecast = data.loc[str(day)].to_numpy(dtype=float)
    if forecast.shape != (96,) or not np.isfinite(forecast).all():
        raise ValueError("Forecast must contain exactly 96 finite values")
    return forecast


def verified_models(repo: Path, rl):
    """Load exactly the five protocol-registered, hash-matched PPO-2000 checkpoints."""
    import torch

    spec = json.loads((repo / "configs/polish_test_protocol.json").read_text())
    expected = spec["treatment_checkpoints"]
    names = {
        f"results/polish_rl_ablation/models/forecast_2000_seed{seed}.pt"
        for seed in SEEDS
    }
    if set(expected) != names:
        raise ValueError("Protocol does not register the expected five PPO checkpoints")
    models = {}
    for seed in SEEDS:
        name = f"forecast_2000_seed{seed}"
        rel = f"results/polish_rl_ablation/models/{name}.pt"
        path = (repo / rel).resolve()
        if not inside(path, repo) or not path.is_file():
            raise ValueError(f"Missing or unsafe checkpoint: {rel}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected[rel]:
            raise ValueError(f"Checkpoint SHA-256 mismatch: {rel}")
        saved = torch.load(path, map_location="cpu", weights_only=True)
        if saved.get("seed") != seed or saved.get("arm") != "forecast_2000":
            raise ValueError(f"Checkpoint metadata mismatch: {rel}")
        policy = rl.Policy(saved["config"]["hidden"])
        policy.load_state_dict(saved["state_dict"], strict=True)
        policy.eval()
        models[name] = policy
    return models


def trace_policy(policy, forecast: np.ndarray, rl):
    """Replicate deterministic run_days and separately retain requested/actual power."""
    import torch

    energy = np.array([rl.E0], dtype=float)
    requested, executed, stored = [], [], []
    for t in range(96):
        obs = torch.as_tensor(rl.observe(forecast[None, :], energy, t))
        with torch.no_grad():
            request = float(policy.power(policy.distribution(obs).mean).numpy()[0])
        energy, power = rl.project(energy, np.array([request]), 96 - t)
        requested.append(request)
        executed.append(float(power[0]))
        stored.append(float(energy[0]))
    if not np.isclose(energy[0], rl.E0, rtol=0, atol=1e-9):
        raise AssertionError("PPO terminal state of charge is inconsistent")
    return np.asarray(requested), np.asarray(executed), np.asarray(stored)


def analyze(repo: Path, out: Path, day: date):
    repo, out = validate_paths(repo, out, day)
    sys.path.insert(0, str(repo / "src"))
    from gridmind_research import polish_market as market
    from gridmind_research import polish_rl as rl

    if rl.T != 96 or len(market.delivery_index(str(day))) != 96:
        raise ValueError("Audit requires a 96-quarter-hour local delivery day")
    forecast = forecast_for_day(repo, day)
    models = verified_models(repo, rl)
    baseline = market.optimize_schedule(forecast)
    market.check_schedule(baseline)
    baseline_power = np.asarray(baseline["charge_mw"]) - np.asarray(baseline["discharge_mw"])
    baseline_soc = np.asarray(baseline["energy_mwh"])
    baseline_objective = market.realized_profit(baseline, forecast)
    times = market.delivery_index(str(day)).tz_convert("Europe/Warsaw")
    rows = pd.DataFrame({
        "local_time": times.astype(str),
        "forecast_eur_per_mwh": forecast,
        "milp_power_mw_positive_charge": baseline_power,
        "milp_soc_mwh": baseline_soc,
    })
    summaries = {}
    powers = []
    for name, model in models.items():
        requested, power, soc = trace_policy(model, forecast, rl)
        replay_profit, replay_throughput = rl.run_days(
            model, forecast[None, :], forecast[None, :], deterministic=True
        )
        audit_profit = float(np.sum(rl.step_profit(power, forecast)))
        throughput = float(np.sum(np.abs(power)) * rl.DT)
        if not np.isclose(audit_profit, replay_profit[0], rtol=0, atol=1e-5):
            raise AssertionError(f"Policy replay profit mismatch: {name}")
        if not np.isclose(throughput, replay_throughput[0], rtol=0, atol=1e-7):
            raise AssertionError(f"Policy replay throughput mismatch: {name}")
        if audit_profit > baseline_objective + 1e-4:
            raise AssertionError(f"PPO unexpectedly exceeds forecast-price MILP optimum: {name}")
        rows[name + "_requested_mw"] = requested
        rows[name + "_power_mw"] = power
        rows[name + "_soc_mwh"] = soc
        powers.append(power)
        summaries[name] = {
            "forecast_price_objective_eur": audit_profit,
            "forecast_price_gap_to_milp_eur": audit_profit - baseline_objective,
            "throughput_mwh": throughput,
            "mean_absolute_dispatch_difference_mw": float(np.mean(np.abs(power - baseline_power))),
            "opposite_charge_discharge_intervals": int(np.sum(power * baseline_power < -1e-9)),
            "physically_clipped_intervals": int(np.sum(np.abs(requested - power) > 1e-8)),
            "checkpoint_verified": True,
            "original_run_days_reconciled": True,
        }
    rows["ppo_mean_power_mw"] = np.mean(np.stack(powers), axis=0)
    rows["ppo_minus_milp_power_mw"] = rows["ppo_mean_power_mw"] - baseline_power
    leaders = rows.reindex(rows["ppo_minus_milp_power_mw"].abs().nlargest(10).index)
    summary = {
        "development_day": str(day),
        "source_commit_not_modified": True,
        "price_type": "LEAR FORECAST ONLY: not observed prices or realized trading profit",
        "observed_price_data_used": False,
        "checkpoint_count": len(models),
        "interval_count": len(rows),
        "milp_forecast_price_objective_eur": baseline_objective,
        "ppo_mean_forecast_price_objective_eur": float(np.mean([
            item["forecast_price_objective_eur"] for item in summaries.values()
        ])),
        "models": summaries,
        "top_dispatch_disagreements": leaders[[
            "local_time", "forecast_eur_per_mwh", "milp_power_mw_positive_charge",
            "ppo_mean_power_mw", "ppo_minus_milp_power_mw",
        ]].to_dict(orient="records"),
    }
    # Nothing is written until every checkpoint, replay, invariant and input is verified.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with tempfile.TemporaryDirectory(prefix="sim31-check-", dir=out.parent) as temp:
        folder = Path(temp)
        rows.to_csv(folder / "96_interval_actions.csv", index=False)
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.step(times, baseline_power, label="MILP (+ charge / - discharge)", where="mid")
        ax.plot(times, rows["ppo_mean_power_mw"], label="PPO average (5 models)")
        ax.set_ylabel("AC power, MW")
        ax.legend()
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(folder / "dispatch_comparison.png", dpi=160)
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.plot(times, baseline_soc, label="MILP")
        for name in models:
            ax.plot(times, rows[name + "_soc_mwh"], alpha=0.7, label=name[-6:])
        ax.set_ylabel("Stored energy, MWh")
        ax.legend(ncol=3)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(folder / "battery_soc.png", dpi=160)
        plt.close(fig)
        (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (folder / "LIMITATIONS.md").write_text(
            "# Read-only research audit\n\n"
            "Actions use saved LEAR **forecast prices** and five unchanged hashed PPO checkpoints.\n"
            "The MILP uses the same forecast and physical model. This is a development-only "
            "decision diagnostic, not a new training run or untouched test.\n\n"
            "No observed prices were downloaded or used. Hence the report cannot attribute "
            "the **realized** daily profit gap to particular intervals, nor establish a bug.\n"
            "Candidate July-August 2026 test days are never read.\n",
            encoding="utf-8",
        )
        os.replace(folder, out)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--day", type=date.fromisoformat, default=date(2026, 6, 30))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.repo, args.out, args.day)
    print(json.dumps({
        "development_day": result["development_day"],
        "verified_models": result["checkpoint_count"],
        "intervals": result["interval_count"],
        "output_dir": str(args.out.resolve()),
    }))


if __name__ == "__main__":
    main()
