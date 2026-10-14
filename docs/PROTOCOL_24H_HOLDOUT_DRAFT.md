# Draft protocol: 24-hour MPC on held-out StoreNet households

**Status: DRAFT, not frozen.** Drafted 14 October 2026. Nothing in this file is confirmatory until the open decisions below are settled, the team signs the access declaration, and the protocol hash is written to an execution lock before any held-out meter value is read.

## 1. Motivation

`docs/EPISODE_LENGTH_EXPLORATION.md` found, on previously inspected July–December 2020 data for H1–H6, that four-hour episodes cap the perfect-foresight saving near 3% of idle cost, and that 24-hour episodes let causal Ridge MPC save 3.47% with no household worse off. Those dates were inspected, the comparison was designed after seeing the four-hour results, and the households were the ones every earlier choice was made on. This protocol tests the finding once on households that informed none of those choices.

## 2. Question and hypothesis

Does receding-horizon Ridge MPC with 24-hour episodes lower community electricity cost relative to no battery use, on StoreNet households not used in development, by an economically meaningful margin?

- **H1 (primary):** the pooled saving of Ridge MPC 24 h versus idle exceeds 1% of idle cost.
- The claim is generalization to other households of the same community, year, tariff and battery. It is not temporal, tariff or market generalization.

## 3. Data

| Item | Fixed choice |
| --- | --- |
| Source | StoreNet Figshare collection 6829134 (Trivedi et al. 2024, CC0), `H*_W.csv` one-minute power files |
| Held-out households | H7–H20. The collection lists 20 households; only H1–H6 appear in this repository |
| Forecast training | 1 January–30 April 2020, raw values only |
| Test period | 1 July–31 December 2020 |
| Unused | May–June 2020, never read for the held-out households |
| Processing | Unchanged `gridmind_research.data.prepare`: 15 complete one-minute samples summed / 60000 = kWh; source clock retained |

On download, record each file's URL, size, SHA-256 and retrieval time in `data/holdout/source_retrieval.json` before processing.

## 4. Two-stage execution

**Stage 1: eligibility, quality only.** Compute from presence or absence of values, never from consumption, PV or cost:

1. A household is eligible if at least 85% of its July–December 15-minute slots and at least 70% of its January–April slots are complete.
2. Communities: eligible households in ascending ID order, in consecutive groups of six. A remainder of fewer than six is excluded and reported.
3. A day enters a community's test set if all six homes have complete values in at least 80 of 96 slots.
4. A community with fewer than 60 eligible days is excluded. If no community remains, the study stops and reports that outcome.

Stage 1 writes `results/holdout_24h/eligibility.json` and an execution lock containing the SHA-256 of this protocol (once frozen), the code commit, the raw and processed data hashes and the eligibility file. **Stage 2 refuses to run without the lock and refuses to overwrite an existing result.**

**Stage 2: outcomes.** Executed once.

## 5. Fixed scenario and controllers

- Battery, tariff, community settlement and degradation: unchanged `battery.py` constants (2 kWh nominal, 0.2–1.8 kWh, 0.5 kWh per 15 min, 0.95 efficiencies, 0.01 EUR/kWh throughput, tariff 0.20/0.30/0.42 import, 0.08 export, 0.02 sharing fee).
- 24-hour episodes run midnight to midnight with 1 kWh at both ends; four-hour comparators use the six standard blocks of the same days.
- Realized load for settlement: time-linear fill of missing slots (primary); same month and slot median (sensitivity).
- Forecasts read only raw rows strictly before the decision time. A missing previous interval uses the latest complete row and is counted.
- Ridge: refit per community with the `forecast_control.fit_model` recipe (previous interval, same slot one day earlier, time-of-day sine/cosine; standardization; alpha 1) on January–April only. No tuning, feature or horizon change.
- MPC: the `battery.mpc_action` LP generalized to the remaining horizon, re-solved every 15 minutes, as in `scripts/explore_mpc_24h.py`.

| Role | Arm |
| --- | --- |
| Treatment | Ridge MPC, 24 h |
| Primary comparator | Idle |
| Secondary comparators | Ridge MPC 4 h; persistence MPC 24 h and 4 h |
| Bounds, not competitors | Perfect foresight 4 h and 24 h |

## 6. Endpoints

**Primary:** pooled relative saving `R = Σ(idle − Ridge24) / Σ idle` over all community-days.

**Secondary**, each reported regardless of direction:

1. Ridge 24 h minus Ridge 4 h, and minus persistence 24 h, in EUR per community-day.
2. Ridge 24 h saving as a share of the 24 h perfect-foresight bound.
3. Number of households with negative total saving under Ridge 24 h (individual rationality).
4. Each community separately.
5. Fill sensitivity: slot-median fill.
6. Stale-input and daily-fallback counts.

## 7. Statistical analysis

- Unit: community-day. Days are resampled jointly across communities by calendar date, preserving cross-community dependence.
- Interval: circular moving-block bootstrap, block 7 eligible days, 10,000 draws, seed 14102026, ratio of sums recomputed per draw. Sensitivity: blocks 1, 3 and 14.
- Two-sided 95% percentile interval for `R`.
- No interim look, no early stopping, no subgroup-based claim.

**Precision rationale (development data, H1–H6, linear fill).** Daily community saving 0.692 EUR (SD 0.304, lag-1 autocorrelation 0.37), 1% of mean daily idle cost is 0.199 EUR, and 163 of 164 days were positive. An autocorrelation-adjusted normal approximation gives a 95% half-width of about 0.11 EUR per community-day at 60 days and 0.07 at 164. Sixty days per community is therefore enough to separate a development-sized effect from the threshold. This is not a power guarantee: held-out households may consume differently.

## 8. Decision rule

| Result for `R` | Conclusion |
| --- | --- |
| Lower 95% bound > 1% | H1 supported on held-out households |
| Lower bound > 0 but ≤ 1% | Positive saving; economic margin not established |
| Interval includes 0 | Inconclusive; does not show equivalence |
| Upper bound < 0 | Ridge MPC 24 h raises cost on held-out households |

Losing households are reported in every case. A positive pooled result with losing households must say so in the abstract.

## 9. Integrity

- All code, including Stage 1 and Stage 2, is complete and tested before freezing. Dry runs use H1–H6 only.
- Freezing: commit the final protocol and code, record the commit hash in this file, and change the status line to FROZEN.
- Any deviation after freezing, including a bug fix, is logged with date, reason and the result both before and after. The original run is kept.
- Negative, null and excluded results are published in the same place and format as positive ones.

## 10. Out of scope

24-hour reinforcement learning, other tariffs or batteries, network constraints, the Polish market study, and the ledger. Each needs its own protocol.

## 11. Open decisions before freezing

These belong to the team and supervisor, not to the analysis code:

1. **Access declaration.** Each coauthor states whether they have opened any H7–H20 meter file. If anyone has, name the files and dates; those households cannot be treated as untouched without that disclosure. So far, on 14 October 2026, only the collection's article titles were listed (Figshare API), and no H7–H20 values were downloaded.
2. **Threshold.** Is 1% of idle cost the right economically meaningful margin, or should it be stated in EUR per household-year?
3. **Community formation.** Consecutive groups of six in ID order (proposed), one community of all eligible homes (requires generalizing the fixed `N = 6`), or another prespecified rule.
4. **Coverage thresholds.** 85% / 70% household and 80-of-96 day rules, set before seeing held-out coverage.
5. **Scope.** Whether this study belongs in the thesis, an addendum or later work, given the submission timeline.

## 12. Implementation checklist

- [ ] Download and hash step writing `data/holdout/source_retrieval.json`
- [ ] Stage 1 eligibility script with lock writer
- [ ] Generalize `explore_mpc_24h.py` to arbitrary household groups and per-community Ridge refits
- [ ] Bootstrap module for the ratio-of-sums endpoint, with a unit test on synthetic data
- [ ] Dry run end to end on H1–H6, confirming the development numbers above
- [ ] Freeze: protocol hash, code commit, team signatures
