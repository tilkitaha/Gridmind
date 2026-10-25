# Draft protocol: the Polish test, PPO against MILP on unseen months

**Status: DRAFT, not frozen.** Drafted 15 October 2026. The machine-readable version is `configs/polish_test_protocol.json`; where the two differ, the JSON is what the code runs. Nothing is confirmatory until the open decisions in section 8 are settled, the file's status is set to `FROZEN_<date>` in one commit, and `scripts/polish_test_run.py lock` has recorded the hashes before any test score exists.

`configs/polish_market_protocol.json` (22 September 2026) is kept unchanged as the record of what was proposed to the supervisor. This draft fills in what that proposal left open, using the development results in `docs/POLISH_MARKET_STUDY.md`.

## 1. Question

For a price-taking 1 MW / 2 MWh battery trader in the Polish day-ahead market, does a learned policy (PPO) earn more per day than a mixed-integer optimiser (MILP) when both plan from the same price forecast, on months that informed none of the choices?

- **Primary contrast:** daily profit of PPO minus daily profit of MILP, both with the LEAR forecast, at realized prices.
- **What the development data lead us to expect:** PPO below MILP. On June 2026 (validation) the chosen PPO arm earns 214.37 EUR/day against 236.08 for MILP, interval −33.7 to −10.6. The test is still worth running: a pre-registered negative result is a valid finding, and the test months could differ.

## 2. Data

| Item | Fixed choice |
| --- | --- |
| Source | ENTSO-E 12.1.D day-ahead prices (A44), zone `10YPL-AREA-----S`, EUR/MWh, PT15M, value published at retrieval |
| History | From 1 October 2025; every forecast uses only days before the delivery day |
| Test window | 1 July–31 August 2026, 62 days |
| Fallback window | 1 September–24 October 2026, only if a signer has looked at July–August prices (section 8). Shortened on 25 October 2026 (was to 31 October) so the live paper test could start with delivery day 26 October; prices from 25 October on are read by the live test, 1 September–24 October stay unread |
| Eligible days | 96 market time units and `validate_day` passes; all methods on the same days; exclusions listed |
| Download | `scripts/fetch_entsoe_prices.py` after the freeze; it refuses the test window before. The provenance is appended to `data/polish/prices/provenance.json` |

## 3. Forecast

LEAR-style LASSO (`polish_forecast.lear`), prices only: 96 per-slot models on asinh-normalised prices, refitted for each day on all earlier days, at least 56 days of history. No exogenous inputs: they added +1.16 EUR/day (interval −3.74 to 5.67) in development, and earlier publication versions of the load forecast cannot be audited, which the September proposal requires.

## 4. Controllers

| Role | Controller |
| --- | --- |
| Treatment | PPO, the five checkpoints listed with SHA-256 in the JSON (2,000-update arm, seeds 11–55), deterministic action, observing only the LEAR forecast, battery level and time |
| Comparator | MILP (`polish_market.optimize_schedule`) on the same LEAR forecast |
| Secondary | MILP on the 7-day mean profile; MILP on D−1 prices; threshold rule, 10 slots per side, on LEAR; do nothing |
| Bound, not a competitor | MILP on the realized prices |

The policies are not retrained after the freeze; the checkpoint files are the treatment. The 2,000-update arm was chosen because it had the highest June validation mean (214.37 against 210.01 for 1,000 and 194.83 for 300 updates). That choice used June, which is what the validation month is for, so June results are not reported as evidence.

## 5. Endpoints

**Primary:** mean over eligible test days of (PPO daily profit averaged over the five checkpoints) minus (MILP daily profit), EUR/day. Averaging the seeds measures the method, not a lucky seed.

**Inference:** circular moving-block bootstrap over test days, block 7 days, 10,000 draws, seed 15102026, 95% percentile interval. Block length was fixed in development and not tuned.

**Decision rule** (margin M set before the freeze):

| Outcome | Condition |
| --- | --- |
| PPO better | lower bound > M |
| PPO worse | upper bound < 0 |
| No demonstrated gain | otherwise |

**Secondary, exploratory:** each checkpoint minus MILP; each secondary controller minus MILP; PPO (seed mean) minus each secondary controller; share of the realized-price bound; losing days; throughput; results by month. With 62 days, a CVaR95 rests on about three tail days, so tail risk is described, not tested.

## 6. Execution

1. Team settles section 8, sets the status to `FROZEN_<date>` and commits.
2. Download July–August prices; run `scripts/verify_polish_data.py`.
3. `python scripts/polish_test_run.py lock --days data/polish/prices/days`: refuses unless the protocol is frozen, the margin is set, the declaration is answered "no" by all three, every tracked change is committed, and the test-day files match their provenance. Writes `results/polish_test/execution_lock.json` with the hashes of this protocol, the commit, the checkpoints and every test day. Commit the lock.
4. `python scripts/polish_test_run.py run --days data/polish/prices/days`: refuses if the lock is missing, if code or configuration changed since the locked commit, if any test file changed, or if a result already exists. Runs once and writes `results/polish_test/results.json` and `daily.csv`.
5. Report the outcome whatever it is. A bug found after the run is fixed in a new, labelled rerun; the first result stays in the record.

**Rehearsal (done 15 October 2026):** `polish_test_run.py rehearse` runs the same pipeline on June 2026 and reproduces every development value (MILP 236.08, PPO mean 214.37, 7-day profile 237.22, D−1 210.31, rule 167.75), with the LEAR forecasts recomputed from scratch. In a throwaway copy of the repository with a mock-frozen protocol, lock refused a second lock, run refused without a lock, refused a second run and refused after a code change.

## 7. Threats and how they are handled

| Threat | Handling |
| --- | --- |
| Someone has seen July–August 2026 prices | Signed access declaration; fallback window |
| Prices republished after download | Hashes in the lock; `verify_polish_data.py` |
| Forecast or policy chosen on test data | Everything fixed before the lock; policies are hashed files |
| PPO advantage from a single seed | Primary endpoint averages five seeds |
| Profit depends on full acceptance at the zonal price | Stated limit: price taker, no imbalance, no fees beyond 10 EUR/MWh wear |
| Summer months only | Stated limit: the result is for July–August, not a year |

## 8. Open decisions before the freeze

| Decision | Who | Note |
| --- | --- | --- |
| Margin M (EUR/day) | Team with the supervisor | Asked on slide 14 of the supervisor deck; a day's profit is about 200–270 EUR, so 5 EUR/day is about 2% |
| Access declaration | Serhat, Cem, Taha, each in writing | Has anyone looked at July–August 2026 Polish prices, from any source? |
| Treatment arm | Team | Proposed: 2,000-update checkpoints; alternative: the original 300-update run, whose settings were fixed before any June result (its checkpoints were still selected on June) |
| Fallback window | Team | Usable only after 24 October 2026 is published (end moved from 31 October on 25 October 2026) |
