"""SIM31 self-improvement research loop (manual or scheduled execution).

Trains a *candidate*, compares on a separate chronological development validation
block and records accept/reject recommendation. Never replaces serving checkpoints.
Does not access July-August 2026 holdout. Output outside the repo only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


def split_dates(days, train_end="2026-04-30", validation_end="2026-05-31"):
    dates = pd.to_datetime(days)
    if dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError("Dates must be unique and chronologically sorted")
    if len(dates) == 0 or dates.min() < pd.Timestamp("2026-01-01"):
        raise ValueError("Only 2026 development dates supported")
    if dates.max() > pd.Timestamp(validation_end):
        raise ValueError("Candidate training/evaluation cannot include June or test months")
    mask = dates <= pd.Timestamp(train_end)
    valid = (dates > pd.Timestamp(train_end)) & (dates <= pd.Timestamp(validation_end))
    if mask.sum() == 0 or valid.sum() == 0:
        raise ValueError("Require nonempty chronological training and validation")
    return np.asarray(mask), np.asarray(valid)


def daily_metrics(values):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not len(x) or not np.isfinite(x).all():
        raise ValueError("Expected nonempty finite one-dimensional profits")
    losses = -x
    tail_n = max(1, int(np.ceil(len(x) * 0.2)))
    return {
        "mean_profit": float(x.mean()),
        "worst20_mean_profit": float(np.sort(x)[:tail_n].mean()),
        "losing_days": int(np.sum(x < 0)),
        "days": int(len(x)),
    }


def gate(candidate, baseline, min_mean_margin=0.0, min_tail_margin=0.0):
    """Conservative development-only paired gate. Not a statistical guarantee."""
    c, b = np.asarray(candidate, float), np.asarray(baseline, float)
    if c.shape != b.shape:
        raise ValueError("Candidate and baseline must be paired on identical days")
    cm, bm = daily_metrics(c), daily_metrics(b)
    advantage = c - b
    # Day-level tail of candidate performance, separately from paired advantage.
    accepted = (
        cm["mean_profit"] >= bm["mean_profit"] + min_mean_margin
        and cm["worst20_mean_profit"] >= bm["worst20_mean_profit"] + min_tail_margin
        and cm["losing_days"] <= bm["losing_days"]
    )
    return {
        "recommendation": "eligible_for_human_review" if accepted else "reject",
        "automatic_promotion": False,
        "candidate": cm,
        "baseline": bm,
        "paired_mean_advantage": float(advantage.mean()),
        "limitations": "Development-only selection gate, no test significance or production guarantee.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--updates", type=int, default=10,
                    help="Small research pilot by default; larger runs require explicit choice")
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if out.is_relative_to(repo) or out.exists() or not out.parent.is_dir():
        raise ValueError("Output must be a new directory outside the repository")
    if not 1 <= args.updates <= 2000:
        raise ValueError("Updates outside approved range")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "src"))
    from gridmind_research.polish_forecast import price_matrix
    from gridmind_research.polish_rl import PPO, train, run_days, Policy
    import torch

    fpath = repo / "results/polish_rl/lear_forecasts.csv"
    frame = pd.read_csv(fpath, index_col=0, parse_dates=True)
    frame = frame.loc["2026-01-01":"2026-05-31"]
    train_mask, val_mask = split_dates(frame.index)
    if frame.shape[1] != 96 or not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError("Expected 96 finite forecast prices per day")
    price_dir = repo / "data/polish/prices/days"
    if not price_dir.is_dir():
        raise FileNotFoundError("Audited Polish raw development prices are not available locally")
    _, _, prices, _ = price_matrix(price_dir, "2025-10-01", "2026-05-31")
    keys = [str(t.date()) for t in frame.index]
    if any(key not in prices for key in keys):
        raise ValueError("Missing observed development prices; refusing mismatched evaluation")
    f = frame.to_numpy(float)
    p = np.stack([prices[k] for k in keys])
    torch.set_num_threads(1)
    cfg = dict(PPO, updates=args.updates)
    candidate, training = train(args.seed, f[train_mask], p[train_mask],
                                f[val_mask], p[val_mask], cfg=cfg)
    candidate_profit = run_days(candidate, f[val_mask], p[val_mask])[0]
    # Re-evaluate the existing frozen PPO-2000 model on exactly the same May dates.
    rel = f"results/polish_rl_ablation/models/forecast_2000_seed{args.seed}.pt"
    spec = json.loads((repo / "configs/polish_test_protocol.json").read_text())
    ref_path = repo / rel
    if hashlib.sha256(ref_path.read_bytes()).hexdigest() != spec["treatment_checkpoints"][rel]:
        raise ValueError("Frozen reference checkpoint hash mismatch")
    saved = torch.load(ref_path, weights_only=True, map_location="cpu")
    if saved.get("seed") != args.seed or saved.get("arm") != "forecast_2000":
        raise ValueError("Frozen reference checkpoint metadata mismatch")
    reference = Policy(PPO["hidden"])
    reference.load_state_dict(saved["state_dict"], strict=True)
    reference_profit = run_days(reference, f[val_mask], p[val_mask])[0]
    decision = gate(candidate_profit, reference_profit)
    decision["training"] = training
    decision["input_period"] = {"train": "2026-01-01 to 2026-04-30",
                                "validation": "2026-05-01 to 2026-05-31"}
    decision["data_policy"] = "No June checkpoint-selection period or July-August holdout was accessed"
    decision["new_model_is_serving"] = False
    out.mkdir()
    torch.save({"seed": args.seed, "config": cfg,
                "state_dict": candidate.state_dict()}, out / "candidate.pt")
    (out / "report.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    pd.DataFrame({"day": np.asarray(frame.index[val_mask], dtype=str),
                  "candidate": candidate_profit, "baseline": reference_profit}).to_csv(
        out / "validation.csv", index=False
    )
    print(json.dumps({k: decision[k] for k in
                      ("recommendation", "automatic_promotion", "paired_mean_advantage")}))


if __name__ == "__main__":
    main()
