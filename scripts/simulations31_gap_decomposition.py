"""SIMULATIONS31: exact forecast-price opportunity-gap decomposition.

This audit describes why two *recorded feasible schedules* yield different profits on
the same forecast. It is an accounting identity, not a causal explanation, new policy,
live-trading result, or unseen test. Never accesses withheld observed prices.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DT_HOURS = 0.25
WEAR_EUR_MWH = 10.0
EXPECTED_MODELS = tuple(f"forecast_2000_seed{s}" for s in (11, 22, 33, 44, 55))


def compare(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return per-slot exact cash-flow difference and deterministic diagnostics."""
    required = {"local_time", "forecast_eur_per_mwh", "milp_power_mw_positive_charge"}
    required.update(f"{m}_power_mw" for m in EXPECTED_MODELS)
    required.update(f"{m}_requested_mw" for m in EXPECTED_MODELS)
    required.update(f"{m}_soc_mwh" for m in EXPECTED_MODELS)
    required.add("milp_soc_mwh")
    missing = sorted(required.difference(frame))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if len(frame) != 96 or frame["local_time"].isna().any():
        raise ValueError("Exactly 96 dated slots required")
    if frame["local_time"].duplicated().any():
        raise ValueError("Duplicate time labels")
    numeric = frame[[c for c in required if c != "local_time"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Non-finite input")
    f = frame["forecast_eur_per_mwh"].to_numpy(float)
    milp = frame["milp_power_mw_positive_charge"].to_numpy(float)
    powers = np.stack([frame[f"{m}_power_mw"].to_numpy(float) for m in EXPECTED_MODELS])
    requests = np.stack([frame[f"{m}_requested_mw"].to_numpy(float) for m in EXPECTED_MODELS])
    if np.max(np.abs(powers)) > 1.000001 or np.max(np.abs(milp)) > 1.000001:
        raise ValueError("Power limit exceeded")
    # Reward is negative for buying, positive for selling, minus linear degradation.
    def pnl(power):
        return DT_HOURS * (-f * power - WEAR_EUR_MWH * np.abs(power))
    m_pnl = pnl(milp)
    p_pnl = np.stack([pnl(power) for power in powers])
    diff = m_pnl - p_pnl.mean(axis=0)
    # Arithmetic decomposition isolates price cashflow and wear (no interactions).
    price_component = DT_HOURS * f * (powers.mean(axis=0) - milp)
    wear_component = DT_HOURS * WEAR_EUR_MWH * (
        np.abs(powers).mean(axis=0) - np.abs(milp)
    )
    if not np.allclose(diff, price_component + wear_component, atol=1e-9):
        raise AssertionError("Interval accounting decomposition failed")
    out = pd.DataFrame({
        "local_time": frame["local_time"],
        "forecast_eur_per_mwh": f,
        "milp_power_mw": milp,
        "ppo_mean_executed_power_mw": powers.mean(axis=0),
        "milp_forecast_pnl_eur": m_pnl,
        "ppo_mean_forecast_pnl_eur": p_pnl.mean(axis=0),
        "milp_minus_ppo_mean_eur": diff,
        "price_cashflow_component_eur": price_component,
        "wear_component_eur": wear_component,
        "signed_cumulative_gap_eur": np.cumsum(diff),
        "ppo_clipped_model_count": np.sum(np.abs(powers - requests) > 1e-8, axis=0),
        "opposing_dispatch_model_count": np.sum(powers * milp < -1e-9, axis=0),
    })
    by_slot = np.argsort(-np.abs(diff), kind="stable")[:10]
    result = {
        "method": "exact accounting identity on common saved LEAR forecast",
        "status": "exploratory development diagnostics; not realized profit or causality",
        "slots": 96,
        "ppo_models": len(EXPECTED_MODELS),
        "forecast_milp_pnl_eur": float(m_pnl.sum()),
        "forecast_ppo_mean_pnl_eur": float(p_pnl.sum(axis=1).mean()),
        "forecast_milp_minus_ppo_eur": float(diff.sum()),
        "price_cashflow_component_eur": float(price_component.sum()),
        "wear_component_eur": float(wear_component.sum()),
        "clipped_model_intervals": int(out["ppo_clipped_model_count"].sum()),
        "opposing_model_intervals": int(out["opposing_dispatch_model_count"].sum()),
        "top_absolute_contribution_slots": out.iloc[by_slot][[
            "local_time", "milp_minus_ppo_mean_eur", "forecast_eur_per_mwh"
        ]].to_dict(orient="records"),
        "note": "Individual signed slot gaps can cancel. The ten largest absolute gaps "
                "are descriptive, not the fraction of profit gain causally recoverable.",
    }
    if not np.isclose(result["forecast_milp_minus_ppo_eur"],
                      result["forecast_milp_pnl_eur"] - result["forecast_ppo_mean_pnl_eur"],
                      atol=1e-8):
        raise AssertionError("Daily accounting identity failed")
    return out, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actions", required=True, type=Path,
                        help="Existing verified 96_interval_actions.csv generated externally")
    parser.add_argument("--out", required=True, type=Path,
                        help="New output directory, outside repository")
    args = parser.parse_args()
    actions = args.actions.resolve()
    out = args.out.resolve()
    repo = Path(__file__).resolve().parents[1]
    if out.is_relative_to(repo):
        raise ValueError("Output inside repository is forbidden")
    if out.exists() or not out.parent.is_dir():
        raise ValueError("Output must be a new directory under an existing parent")
    if not actions.is_file() or actions.name != "96_interval_actions.csv":
        raise ValueError("Expected a verified actions file named 96_interval_actions.csv")
    # Independent accounting audit; input provenance must be ensured by upstream audit.
    detail, result = compare(pd.read_csv(actions))
    out.mkdir()
    detail.to_csv(out / "forecast_gap_by_slot.csv", index=False)
    (out / "forecast_gap_summary.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": result["status"],
                      "forecast_gap_eur": result["forecast_milp_minus_ppo_eur"]}))


if __name__ == "__main__":
    main()
