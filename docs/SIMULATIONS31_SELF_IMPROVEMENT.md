# SIMULATIONS31 — Controlled Self-Improvement Research Loop

This is **not** an autonomous trading bot. It is a research candidate trainer and a conservative gate: it may recommend a candidate for *human review*, but it will **never automatically replace** original PPO models, trigger trading, merge into `main`, or claim unseen-test success.

## Status

- Candidate-training script and gate tests have been committed separately on `SIMULATIONS31`.
- **The full retraining experiment is not run**: licensed/audited Polish development raw prices are not included in the public GitHub repository. The script fails closed when those files are missing.
- The default 10 PPO updates are only a smoke/pilot budget, **not** evidence that the candidate is superior.
- Five frozen PPO-2000 checkpoints remain unchanged. This run contrasts against the same-seed frozen reference on **May 2026**. **Caution: the reference checkpoint was originally trained on Jan–May, so May is in-sample for that reference, but out-of-sample for the new Jan–Apr candidate.** The comparison is deliberately conservative and cannot support an apples-to-apples efficacy claim. A later controlled experiment must retrain both strategies on identical pre-May data and run multiple seeds and paired uncertainty analyses.

## Invocation

Run only on a research machine that already holds audited `data/polish/prices/days` for development dates:

```sh
python scripts/simulations31_self_improvement.py --repo . --out /tmp/sim31_candidate_seed11 --updates 10 --seed 11
```

Use a **new external output directory** for every experiment. The script refuses outputs inside the repository, overwrites and missing prices. It only loads 2026-01-01 through 2026-05-31 forecasts and observed prices, with April 30 train cutoff and May as validation. No June test-selection window and no July–August candidate test data are loaded.

Outputs: an isolated candidate checkpoint, full decision report and daily paired results. **Eligible for human review** is not deployment approval; the student team must inspect the experiment design, sample sizes, multiple-seed stability, scientific limitations and independent test protocol before interpreting improvements.

## Safe future automation

To make this loop recurring, trigger it from a private runner containing licensed historical data, not a public action that downloads or exposes restricted measurements. Each iteration should (1) lock eligible historical dates, (2) train new candidate models on past-only data, (3) compute several independent validation metrics and safety constraints, (4) log artifacts immutably, and (5) require an explicitly approved model promotion. Retraining schedules and new data windows must have a pre-registered policy to prevent silent test leakage. A new inference API must expose read-only simulation endpoints, not market or wallet commands.