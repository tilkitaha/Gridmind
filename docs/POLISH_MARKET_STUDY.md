# Polish market study boundary and reproducible interface

22 September 2026. Intended application: a price-taking BESS trader in the PL bidding zone. No Polish empirical market performance has been computed.

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
- Better forecasts turn into money: the ranking by error matches the ranking by profit. This is the first measurement of the forecast-to-trading coupling (E1 and E3 of the design) on Polish data.
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

## Data and sources

ENTSO-E zone `10YPL-AREA-----S`, energy prices 12.1.D, is the proposed source. Candidate training: 2025-10-01 to 2026-05-31; validation: June 2026; candidate test: July-August 2026. No raw data, published-version audit or independent-test access audit has been completed. The proposed protocol is therefore not data-frozen. API access requires registration and a security token; do not put tokens in source files or the archive.

- [ENTSO-E market design](https://www.entsoe.eu/network_codes/cacm/implementation/sdac/)
- [PSE 15-minute launch announcement](https://www.pse.pl/-/pomyslne-uruchomienie-projektu-15-mtu-na-rynku-dnia-nastepnego)
- [ENTSO-E API access](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token)
- [SciPy MILP documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

## Remaining research

LEAR/boosting/Transformer forecasts, forecast-conditioned Polish PPO, risk-constrained optimization, partial order acceptance, imbalance charges and ten-owner physical disaggregation are unimplemented. Synthetic analytical tests of the scheduling module are not backtests. A future daily policy must not consume realized intraday prices when scoring a schedule that was supposedly fixed on D-1.

The original Irish data evaluate a different community and tariff model. Do not join their unverified source clock to Polish prices or rescale their savings to the 1 MW system.
