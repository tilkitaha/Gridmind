# SIMULATIONS31 — read-only PPO versus MILP decision audit

Status: an **additive exploratory analysis**, not a thesis result, model improvement, or independent test.

## Scope and scientific boundary

This branch-only tool audits one Polish development day at a time, January–June 2026. It reads the existing 96-point LEAR day-ahead forecast, the original BESS/MILP code, and the five PPO-2000 saved checkpoints listed in `configs/polish_test_protocol.json`. It checks checkpoint SHA-256 values, repeats the original deterministic PPO rollout, and rejects a discrepancy between calculated profits/throughput and the original replay functions. It computes every model's 96 actions, clipped actions, stored battery energy and its **forecast-price** objective. It never retrains a model or downloads prices.

A forecast-price objective **cannot be compared directly** with recorded realized daily EUR profit; there are no original realized quarter-hour Polish price CSVs in the GitHub repo. The tool therefore does not claim to identify which intervals caused the observed June profit gap. It never uses the protected July–August 2026 candidate test dates. Model selection on June already happened, so these diagrams are exploratory and not unbiased test findings.

## Run (Python 3.12, existing project research dependencies)

From the repository root, after installing the existing pinned dependencies:

```bash
python scripts/simulations31_ppo_audit.py --repo . --day 2026-06-30 --out /tmp/gridmind-sim31-2026-06-30
```

Use any **non-existing folder outside the repository** for `--out`. Output contains `96_interval_actions.csv`, `summary.json`, `dispatch_comparison.png`, `battery_soc.png`, and `LIMITATIONS.md`. The tool refuses existing output paths and verifies every model before creating output. Positive AC power means charging; negative means discharging. Source repository and checkpoint files are never written to.

## Verification

```bash
python -m pytest -q research_tests/test_simulations31_ppo_audit.py
python -m unittest discover -s research_tests -v
ruff check .
```

Branch workflow `.github/workflows/simulations31.yml` additionally runs the full existing tests and attempts a real-checkpoint replay on 30 June 2026. A successful mock fixture test does not replace this real-checkpoint validation. Inspect the specific workflow run before quoting actual decision-trace outputs in your thesis. Outputs remain **external** to the repo and are available as workflow artifacts when that job succeeds.

## Strict compatibility policy

Only four **new files** belong to this change: this documentation, the audit script, its isolated tests and a branch-specific CI workflow. Existing code, data, manifests, checkpoints, thesis files and all `main` files are untouched. `SIMULATIONS31` must not be merged into `main` without the team's review, reproducibility audit and supervisor scope decision.
