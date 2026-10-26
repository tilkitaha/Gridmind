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

## Results (26 October 2026)

The recomputed MILP on LEAR reproduced every recorded daily profit (largest difference 6e-14 EUR). The rule picked **w = 0.25** on the development days, before the test stage was run.

Mean profit and CVaR 5% (EUR/day; CVaR over 9, 4, 3 and 6 worst days):

| Policy | Jan–Jun mean | Jan–Jun CVaR | Jul–Aug mean | Jul–Aug CVaR | Sep–Oct mean | Sep–Oct CVaR | Pooled mean | Pooled CVaR |
|---|---|---|---|---|---|---|---|---|
| MILP on D−1 prices | 155.13 | −42.96 | 174.83 | −74.79 | 202.63 | −113.72 | 187.77 | −109.06 |
| MILP on LEAR | 175.63 | −18.55 | 213.87 | 10.15 | 264.16 | −72.62 | 237.28 | −39.29 |
| Mean-CVaR, w = 0 | 176.13 | −25.30 | 212.16 | 7.38 | 272.52 | −61.24 | 240.26 | −32.73 |
| **Mean-CVaR, w = 0.25 (picked)** | 172.05 | −22.36 | 210.84 | 7.66 | 267.39 | −58.10 | 237.17 | −30.35 |
| Mean-CVaR, w = 0.5 | 164.16 | −19.99 | 207.54 | 4.98 | 255.86 | −56.08 | 230.03 | −31.46 |
| Mean-CVaR, w = 0.75 | 154.95 | −16.27 | 200.97 | 7.18 | 245.00 | −41.55 | 221.47 | −23.68 |
| Mean-CVaR, w = 1 | 141.17 | −17.76 | 194.51 | 7.80 | 225.66 | −46.31 | 209.01 | −25.14 |

Picked weight minus MILP on LEAR, same days (95% intervals):

| Period | Mean profit | CVaR 5% | Worst day, EUR |
|---|---|---|---|
| January–June (180) | −3.58 (−7.81 to +0.22) | −3.81 (−8.99 to +3.35) | −37.05 vs −38.86 |
| July–August (62) | −3.03 (−6.70 to +0.72) | −2.49 (−10.61 to +13.95) | −9.38 vs −26.38 |
| September–October (54) | +3.23 (−1.41 to +7.94) | +14.52 (−10.04 to +51.26) | −71.47 vs −122.73 |
| Both later periods (116) | −0.12 (−3.41 to +3.30) | +8.95 (−6.70 to +32.34) | −71.47 vs −122.73 |

Against MILP on D−1 prices, the picked weight earns 49.40 EUR/day more on the pooled later periods (37.79 to 61.94) with a CVaR 5% 78.71 EUR/day higher (20.86 to 127.71), much like MILP on LEAR.

**Reading.** With the weight fixed in advance, putting CVaR into the optimization did not change mean profit or CVaR 5% detectably compared with the risk-neutral MILP on the same forecast; every interval includes zero. The worst single day was milder in every later period. Larger weights trade mean profit for a better tail (w = 0.75: −15.81 EUR/day and +15.62 EUR CVaR 5% on the pooled later periods), but they were not picked on the development data and are reported as a description, not a result. Most of the reduction in downside risk in this study comes from the forecast itself (H1), not from the risk term. Throughput falls with the weight (5.47 to 4.35 MWh/day in development), so the risk-averse schedules also cycle the battery less.
