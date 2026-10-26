# Risk-averse scheduling (exploratory, October 2026)

The deterministic MILP of the Polish study maximizes the profit expected from one forecast, so it is risk-neutral; downside risk (CVaR 5%) was so far only measured afterwards. This extension adds a scheduling model that puts the risk into the optimization itself.

**Status: exploratory.** It was added on 26 October 2026, after the confirmatory test and the second untouched period had been scored, and it is not part of the frozen protocol. Its results on July–August and on 1 September–24 October 2026 are therefore not confirmatory. The design and the weight-selection rule below were fixed and committed before any result of the model existed.

## Model

For each delivery day one schedule is fixed for all price scenarios; it maximizes

(1 − w) · mean profit over the scenarios + w · CVaR<sub>α</sub> of the scenario profits,

where CVaR<sub>α</sub> is the mean profit of the worst α share of scenarios, linearized as in Rockafellar and Uryasev (2000). Battery limits, efficiency and the 10 EUR/MWh wear cost are those of the deterministic MILP (`polish_market.BESS`). Code: `src/gridmind_research/polish_risk.py`, tests: `research_tests/test_polish_risk.py`.

**Scenarios.** The day's LEAR forecast plus the forecast error (realized minus forecast prices) of each of the 28 most recent full days before the delivery day. The prices of D−1 are published before the D−1 gate, so every scenario is available when the schedule is fixed. The forecasts come from the same `lear()` function as every other Polish result.

## Fixed in advance

| Item | Value |
|---|---|
| Past error days (scenarios) | 28 |
| α inside the day | 0.2 (about 6 of 28 scenarios) |
| Weights w | 0, 0.25, 0.5, 0.75, 1 |
| Weight selection | On the 180 development days only: the highest CVaR 5% (over days) among the weights whose mean profit is at least 95% of MILP on LEAR; ties go to the smaller weight |
| Comparison | The picked weight against MILP on LEAR and against MILP on D−1 prices, same days, circular block bootstrap (blocks of 7 days, 10,000 draws, seed 15102026), mean and CVaR 5% |
| Periods | Development January–June 2026 (180 days); July–August 2026 (62); 1 September–24 October 2026 (54); both later periods pooled (116) |

The recomputed deterministic MILP on LEAR must reproduce the recorded daily profits of `results/polish_profile` and `results/polish_test*` exactly, otherwise the script stops. w = 0 is not identical to MILP on LEAR: it plans on the forecast plus the mean of the recent errors, a bias correction.

## Reproduction

```bash
python scripts/polish_cvar_eval.py forecasts --days data/polish/prices/days
python scripts/polish_cvar_eval.py development --days data/polish/prices/days
python scripts/polish_cvar_eval.py test --days data/polish/prices/days
```

The forecasts stage writes a git-ignored cache (`data/polish/lear/`), because forecasts derived from ENTSO-E prices are not redistributed. Results: `results/polish_cvar/`.

## Results

Not yet run.
