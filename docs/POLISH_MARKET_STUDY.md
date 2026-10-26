# Polish market study boundary and reproducible interface

22 September 2026. Intended application: a price-taking BESS trader in the PL bidding zone. Updated 15 October 2026: the sections below report development-period results (October 2025 to June 2026). No confirmatory test result exists; the test plan is `configs/polish_test_protocol.json` and `docs/PROTOCOL_POLISH_TEST_DRAFT.md`. Updated 25 October 2026: every experiment re-run and matched, and an exploratory live paper test started (sections at the end).

## Implemented

`polish_market.py` supplies delivery-day indexing, strict CSV validation, a deterministic BESS MILP, physical checks and realized-price scoring. Nameplate energy is 2 MWh; the 10-90 percent range provides 1.6 MWh of usable swing. Power and grid exchange are 1 MW. Both efficiencies are 0.95 and start/end inventory is 1 MWh. A binary variable rules out simultaneous charging and discharging under negative prices. Throughput cost defaults to 10 EUR/MWh for each AC direction.

Local dates use Europe/Warsaw, while unique interval keys are UTC. Clock-change days contain 92 or 100 quarter-hours rather than 96. The model accepts only an exact complete 15-minute day, including its clock-change length. It does not silently turn hourly prices into four observations.

## Canonical CSV contract

Forecast CSV columns: `timestamp_utc,value_eur_mwh,issued_at`. Realized-price CSV columns: `timestamp_utc,value_eur_mwh`. Timestamps require explicit offsets, records must be strictly ordered and complete, and values must be finite EUR/MWh. Forecast issue time must be strictly before noon Europe/Warsaw on D-1. This checks metadata consistency, not its authenticity. Preserve original downloads, query parameters, units, publication revisions, source URL and retrieval time in a separate provenance manifest.

```bash
PYTHONPATH=src python scripts/evaluate_polish_day.py --day YYYY-MM-DD --forecast forecast.csv --realized realized.csv --output results/new_day.json
```

The command fixes the forecast-based schedule before reading realized prices. It refuses to overwrite an existing output. Inputs are required; no invented market data are bundled. Evaluated profit assumes full order acceptance, no imbalance settlement and no network/exchange charges. The default zero ledger monetary charge is an explicit assumption; local gas has not been converted to a market fee.

## Price download (added 14 October 2026)

`src/gridmind_research/entsoe.py` parses ENTSO-E A44 day-ahead responses into the realized-price contract above: A01 and A03 curves (A03 omits repeated prices), 15/30/60-minute resolutions, EUR/MWh only, conflicting duplicates rejected, and hourly periods never split into quarter-hours, so pre-15-minute days fail `validate_day` instead of being silently converted. `scripts/fetch_entsoe_prices.py` reads the token only from `ENTSOE_TOKEN`, stores every raw response with its SHA-256, retrieval time and token-free query in `provenance.json`, and writes per-day CSVs only for complete delivery days. Synthetic XML tests are in `research_tests/test_entsoe.py`. The parser has not yet seen a live response; check the first download by hand. It records the version published at retrieval time and does not audit earlier publication versions.

Prices published in another currency are kept unconverted as `value_<currency>_mwh` in a separate folder, because a conversion needs a recorded FX source; EUR prices outside the harmonised SDAC limits (−600 to 4,000 EUR/MWh) are rejected. Both the download and the pilot refuse any range that touches the candidate test window (July–August 2026) until this protocol's status is frozen, so the window stays usable as an untouched test.

`scripts/polish_pilot.py` (logic in `src/gridmind_research/polish_pilot.py`) is a descriptive development-period pilot: daily spreads, negative-price intervals, the perfect-foresight MILP profit, and the realized profit of MILP schedules built from two naive forecasts that are published before the D-1 gate (same quarter-hours on D-1 and D-7). It compares no controller and claims no trading result.

## Development-period pilot (15 October 2026)

ENTSO-E prices for 1 October 2025 to 30 June 2026 were downloaded with `scripts/fetch_entsoe_prices.py`: nine monthly A44 responses, EUR/MWh, PT15M, A03 curves, all 273 delivery days complete, including the 100-interval day (26 October 2025) and the 92-interval day (29 March 2026). An independent re-parse of the raw XML matched every day exactly. July and August 2026 were not requested.

| Measure (`results/polish_pilot/results.json`) | Value |
| --- | --- |
| Mean daily price spread | 172.3 EUR/MWh |
| Perfect-foresight MILP profit | 199.26 EUR/day (≈ 72,700 EUR per MW-year) |
| MILP on D−1 prices: share of the bound, comparable days | 62.9% (123.63 EUR/day; loses money on 52 of 260 days) |
| MILP on D−7 prices: share of the bound | 61.6% |
| Negative-price quarter-hours | 900, on 59 days; minimum −490 EUR/MWh |

The perfect-foresight profit is at least the naive-forecast profit on every comparable day. Thirteen days lack a comparable D−1 or D−7 day (the first week and the days around clock changes). This is a description of the development period, not a test of any controller.

## Walk-forward forecast comparison (15 October 2026)

`scripts/polish_forecast_eval.py` (models in `src/gridmind_research/polish_forecast.py`) forecasts every delivery day from 1 January to 30 June 2026 using only earlier days, refitting as the window grows, and scores both the forecast and the realized profit of the MILP schedule built from it. History starts on 1 October 2025; one clock-change day is not scored; the candidate test window is not read. Model settings were fixed before the run and were not tuned on these results.

| 180 days, Jan–Jun 2026 | MAE (EUR/MWh) | MAE relative to D−1 | MILP profit (EUR/day) | Share of perfect foresight | Losing days |
| --- | --- | --- | --- | --- | --- |
| Naive D−1 | 31.17 | 1.000 | 155.13 | 68.4% | 23 |
| Naive D−7 | 38.25 | 1.227 | 148.20 | 65.3% | 27 |
| LEAR-style LASSO | **25.20** | **0.809** | **175.63** | **77.4%** | 17 |
| Gradient boosting | 28.74 | 0.922 | 168.33 | 74.2% | 14 |
| Perfect foresight | – | – | 226.88 | 100% | – |

- LEAR has lower error than naive D−1 (Diebold–Mariano p < 0.001) and earns 20.50 EUR/day more (7-day block bootstrap 95% interval 12.32 to 28.92). Gradient boosting earns 13.20 EUR/day more (5.68 to 20.84); LEAR also beats it on error (p < 0.001).
- LEAR earns more than naive D−1 in every one of the six months. In the June validation month alone, LEAR reaches 86.1% of perfect foresight.
- Among these four models, the ranking by error matches the ranking by profit. This is the first measurement of the forecast-to-trading coupling (E1 and E3 of the design) on Polish data. **Correction (same day):** a rolling 7-day mean profile, added later, has higher error than naive D−1 but earns as much as LEAR, so the error ranking does not carry over to profit in general; see “Mean-profile forecasts” below.
- Limits: development period, price and calendar inputs only (no load or generation forecasts yet), one battery configuration, full acceptance at the zonal price.

## Exogenous inputs (15 October 2026)

`scripts/fetch_entsoe_features.py` downloaded the day-ahead total load forecast (6.1.B), actual total load (6.1.A) and actual generation per production type (16.1.B&C) for 20 September 2025 to 30 June 2026: PT15M, 284 complete days, consumption series (pumped storage) dropped. Load is 18.9 GW on average (peak 27.7 GW); the published load forecast misses actual load by 2.27% on average. Inputs available at the D-1 12:00 gate: the load forecast for D, D-1 and D-7, and D-2 daily means of solar, wind and actual load; scaling statistics also stop at D-2 (a unit test caught an earlier version that used D-1).

| 180 days, Jan–Jun 2026 (`results/polish_forecast_exog`) | MAE (EUR/MWh) | MILP profit (EUR/day) | Losing days |
| --- | --- | --- | --- |
| LEAR-style LASSO, prices only | 25.20 | 175.63 | 17 |
| LEAR-X, with exogenous inputs | **23.71** | **176.79** | 14 |
| Gradient boosting, prices only | 28.74 | 168.33 | 14 |
| Gradient boosting with exogenous inputs | 29.40 | 171.73 | 14 |

- The exogenous inputs lower LEAR's error by 6% (Diebold–Mariano p = 0.01) but add only 1.16 EUR/day (95% interval −3.74 to 5.67), which is not distinguishable from zero.
- A schedule depends on when prices are low and high, not on their level; better level forecasts do not necessarily change the schedule. Forecast accuracy alone is therefore not the right criterion for choosing a forecaster, which matches the horizon-versus-one-step finding of the Irish study.

## PPO against MILP on the same forecast (15 October 2026)

`scripts/polish_rl_eval.py` (environment and PPO in `src/gridmind_research/polish_rl.py`) trains a single-battery PPO policy on whole delivery days. The policy observes only the LEAR walk-forward forecast for the day (scaled per day), the battery level and the time left; the reward is the realized profit of each step and is used only for training. Physics follow `BESS`; a unit test shows that the environment reproduces the MILP schedule’s profit exactly. Settings fixed before the run, carrying the Irish lessons: one day per episode, GAE λ = 1.0, five seeds, 300 updates of 16 days. PPO trains on 150 January–May days and selects its checkpoint on June, so June is a validation month, not a test.

| June 2026, 30 days (`results/polish_rl`) | EUR/day | Share of perfect foresight | PPO minus MILP, 95% interval |
| --- | --- | --- | --- |
| Perfect foresight | 274.32 | 100% | – |
| MILP on LEAR forecast | **236.08** | 86.1% | – |
| MILP on yesterday’s prices | 210.31 | 76.7% | – |
| PPO on LEAR forecast, mean of 5 seeds | 194.83 | 71.0% | – |
| PPO seeds 11, 22, 33, 44, 55 | 198.55, 204.10, 208.52, 160.56, 202.41 | 58.5–76.0% | −27.6 to −75.5 EUR/day; every interval below zero |

- PPO learns real arbitrage: validation profit rises from about 40 to about 200 EUR/day, and it cycles about as much as MILP (3.9–4.9 versus 4.87 MWh/day). It does not idle as in the Irish study.
- It does not reach MILP with the same forecast: all five seeds are lower, with intervals that exclude zero, and the seed mean is below MILP planned on yesterday’s prices. The best seed beats MILP on 5 of 30 days.
- Selected checkpoints come late (updates 210–300), so the training budget may be binding. A longer budget is a candidate for the protocol; it would have to be fixed before the test, not tuned on June.

## Simple controllers and forecast-error sensitivity (15 October 2026)

`scripts/polish_controls_eval.py` adds the two simplest controllers on the same LEAR forecast: doing nothing, and a threshold rule (`polish_rl.rule_profit`) that charges at full power in the k cheapest forecast quarter-hours and discharges in the k dearest, clipped to the battery limits. k = 10 was chosen on January–May from {2, …, 32}; June is reported separately (`results/polish_controls`).

| June 2026, 30 days | EUR/day | Share of perfect foresight |
| --- | --- | --- |
| Perfect foresight | 274.32 | 100% |
| MILP on LEAR | 236.08 | 86.1% |
| PPO on LEAR, 300 updates, mean of 5 seeds | 194.83 | 71.0% |
| Threshold rule on LEAR, k = 10 | 167.75 | 61.2% |
| Do nothing | 0 | 0% |

The rule trails MILP by 68.33 EUR/day (95% interval −94.17 to −46.31). PPO (300 updates, seed mean) beats the rule by 27.08 EUR/day (19.53 to 34.14); four of five seeds beat it.

The same script measures how forecast error turns into lost profit, over all 180 days: MILP plans on the real prices plus a scaled copy of the actual LEAR error, or plus independent normal noise.

| Forecast given to MILP | MAE (EUR/MWh) | EUR/day |
| --- | --- | --- |
| Real prices | 0 | 226.88 |
| Real + 0.5 × LEAR error | 12.60 | 215.04 |
| Real + 0.75 × LEAR error | 18.90 | 200.85 |
| LEAR (real + 1 × error) | 25.20 | 175.63 |
| Real + independent noise, σ = 10 | 7.97 | 200.75 |
| Real + independent noise, σ = 20 | 15.93 | 123.11 |
| Real + independent noise, σ = 30 | 23.90 | 56.07 |

- Halving LEAR's error would be worth about 39 EUR/day; about half of the loss comes in the last quarter of the error.
- At nearly the same MAE, LEAR's errors cost 51 EUR/day and independent noise costs 171 EUR/day. LEAR's errors keep the daily shape, while independent noise moves the cheap and dear quarter-hours. Error size alone does not predict lost profit. Scaling the LEAR error beyond 1 is an extrapolation and is left in the results file only.

## PPO follow-ups: training budget and no forecast (15 October 2026)

`scripts/polish_rl_ablation.py` reruns PPO with the same forecasts, split, seeds and settings, changing one thing at a time (`results/polish_rl_ablation`). Checkpoints are again selected on June, so June remains validation.

| June 2026 | PPO mean of 5 seeds (EUR/day) | Each seed minus MILP on LEAR | Selected updates |
| --- | --- | --- | --- |
| 300 updates (original run) | 194.83 | −27.6 to −75.5, every interval below zero | 210–300 |
| 1,000 updates | 210.01 | −22.6 to −30.3, every interval below zero | 550–990 |
| 2,000 updates | **214.37** | −17.4 to −29.7, every interval below zero | 710–1,750 |
| 300 updates, no forecast | −12.09 | −228 to −262 | 10–20 |

- A longer budget helps, with diminishing returns: +15.2 EUR/day from 300 to 1,000 updates, +4.4 from 1,000 to 2,000. The weakest seed of the original run (seed 44, 160.56) reaches 214.84. No seed reaches MILP with the same forecast. The 2,000-update seed mean beats the threshold rule by 46.62 EUR/day (33.57 to 61.73; `results/polish_test_rehearsal`).
- Without the forecast, PPO sees only the battery level and the time of day and loses money; its best checkpoints are the first ones. The information was not the problem: one fixed schedule, planned once on the January–May mean price per quarter-hour and repeated every June day, earns 156.96 EUR/day, and one planned on the May mean earns 243.34 (`results/polish_profile`). With this reward and budget PPO did not find a profitable fixed pattern; this is a learning failure, so the arm does not measure the value of the forecast.

## Mean-profile forecasts (15 October 2026, exploratory)

Added after the no-forecast result: `scripts/polish_profile_eval.py` forecasts day D by the mean price per quarter-hour over the last 7, 14 or 28 days (`polish_forecast.profile`, D−1 included, published before the gate). Same 180 days and scoring; designed after seeing the June results, so exploratory (`results/polish_profile`).

| 180 days, Jan–Jun 2026 | MAE (EUR/MWh) | MILP profit (EUR/day) | Minus LEAR, 95% interval | Months above LEAR | June (EUR/day) |
| --- | --- | --- | --- | --- | --- |
| LEAR-style LASSO | **25.20** | 175.63 | – | – | 236.08 |
| Mean of last 7 days | 31.29 | **177.16** | +1.54 (−3.27 to 6.19) | 4 of 6 | 237.22 |
| Mean of last 14 days | 31.70 | 175.95 | +0.32 (−6.00 to 6.40) | 4 of 6 | 239.20 |
| Mean of last 28 days | 32.42 | 172.07 | −3.55 (−10.89 to 3.45) | 2 of 6 | 242.71 |
| Naive D−1 | 31.17 | 155.13 | −20.50 (−28.92 to −12.32) | 0 of 6 | 210.31 |

- The 7-day mean profile has 24% more error than LEAR (Diebold–Mariano p < 0.001) and slightly more than naive D−1, yet earns as much as LEAR. What LEAR adds over yesterday's prices, an average of recent days adds too: both remove day-specific noise and keep the timing.
- This corrects the earlier reading that better forecasts earn more. Forecasters should be compared by the profit of the schedule they produce, and any forecaster must beat a recent-mean profile, not only naive D−1.
- The test protocol keeps LEAR as the forecast (fixed before these results) and adds the 7-day profile as a secondary comparator.

## Downside risk (exploratory, 26 October 2026)

`scripts/polish_risk_eval.py` adds risk measures to the recorded daily profits, without new data: CVaR 5% (mean profit on the worst ceil(0.05 n) days; Rockafellar and Uryasev, 2000), the 5th percentile, the standard deviation, losing days and the worst day, with the paired circular block bootstrap of the other Polish evaluations (blocks of 7 days, 10,000 draws, seed 15102026). Results in `results/polish_risk/`.

| January–June 2026, 180 days | Mean (EUR/day) | CVaR 5% (EUR/day) | Losing days |
| --- | --- | --- | --- |
| MILP, LEAR | 175.63 | −18.55 | 17 |
| MILP, 7-day mean | 177.16 | −50.62 | 18 |
| MILP, naive D−1 | 155.13 | −42.96 | 23 |
| Threshold rule, LEAR | 121.19 | −21.63 | 17 |

- LEAR minus naive D−1: mean +20.50 (12.32 to 28.92), CVaR 5% +24.42 (6.74 to 47.00). LEAR raises the profit and lowers the downside risk.
- LEAR minus the 7-day mean: mean −1.54 (−6.19 to 3.27), CVaR 5% +32.08 (8.29 to 57.43). The 7-day mean earns as much on average, but its worst days are much worse: the more accurate forecast pays off through lower risk.
- June 2026, PPO (mean of the five checkpoints) minus MILP with LEAR: mean −21.71 (−33.69 to −10.61), CVaR 5% +1.92 (−20.02 to 15.51).

The analysis was chosen after the mean-profit results were known, and the 5% tail holds only nine of 180 days (two of 30 in June), so it is exploratory.

## Re-run of every experiment (25 October 2026)

All unlocked experiments above were re-run from the repository code: 4,506 of 4,506 recorded numbers were identical, and the five protocol PPO checkpoints, retrained from scratch, have the registered SHA-256 and bit-identical weights. Details: [GridMind Lab](GRIDMIND_LAB.md#re-run-of-every-experiment-25-october-2026).

## Live paper test (from 26 October 2026)

A paper-trading test runs the same agents on live prices for 15 delivery days, 26 October–9 November 2026. Each morning every agent fixes its schedule before the 12:00 gate; after publication the schedule is scored. Schedules and scores are kept in the hash-chained `results/live_paper_trading/ledger.jsonl`, without prices. To start the test on 25 October, the fallback window of the test protocol now ends on 24 October 2026 instead of 31 October; 1 September–24 October stays unread. The test uses fresh prices only, so the yesterday's-prices MILP trades from 26 October and the agents that need a week of history (7-day mean, LEAR, PPO, threshold rule) from 1 November. This is exploratory evidence; the confirmatory test is still the locked July–August window. Standings: [results/live_paper_trading](../results/live_paper_trading/README.md); method: [GridMind Lab](GRIDMIND_LAB.md#the-live-paper-test).

## Data and sources

ENTSO-E zone `10YPL-AREA-----S`: day-ahead prices 12.1.D, load forecast 6.1.B, actual load 6.1.A, generation per type 16.1.B&C. Downloaded for 2025-09-20 to 2026-06-30; July–August 2026 not requested. API access requires registration and a security token; the token is read only from `ENTSOE_TOKEN` and never stored.

Redistribution: ENTSO-E's “List of data available for free re-use” (version 18 October 2023) puts the listed items under CC-BY 4.0. The day-ahead load forecast (6.1.b) is on the list; day-ahead prices (12.1.d), actual load (6.1.a) and generation per type (16.1.b&c) are not, so re-using them needs the primary owner's agreement. The repository therefore keeps only `data/polish/*/provenance.json` (queries, retrieval times and SHA-256 of every raw response and day file). After a fresh download with the fetch scripts, `scripts/verify_polish_data.py` shows whether the files match those the results were computed from; a mismatch means a value was republished. Later downloads are appended to the provenance, never replace it.

- [ENTSO-E Transparency Platform legal terms and open-data list](https://transparencyplatform.zendesk.com/hc/en-us/articles/40921911218961-Legal-Terms-and-Conditions)
- [ENTSO-E market design](https://www.entsoe.eu/network_codes/cacm/implementation/sdac/)
- [PSE 15-minute launch announcement](https://www.pse.pl/-/pomyslne-uruchomienie-projektu-15-mtu-na-rynku-dnia-nastepnego)
- [ENTSO-E API access](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token)
- [SciPy MILP documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

## Remaining research

Done on development data: price download, pilot, naive/LEAR/boosting forecasts with and without exogenous inputs, mean-profile forecasts, threshold rule, forecast-conditioned PPO with budget and no-forecast arms, and the test pipeline (`scripts/polish_test_run.py`, rehearsed on June). Running: the 15-day live paper test (from 26 October 2026). Not done: the test itself (needs the freeze), audit of earlier publication versions of the load forecast, Transformer forecast, risk-constrained optimization, partial order acceptance and imbalance charges, ten-owner physical disaggregation and settlement, escrow and validator governance. Synthetic analytical tests of the scheduling module are not backtests. A daily policy must not consume realized intraday prices when scoring a schedule that was fixed on D-1.

The original Irish data evaluate a different community and tariff model. Do not join their unverified source clock to Polish prices or rescale their savings to the 1 MW system.
