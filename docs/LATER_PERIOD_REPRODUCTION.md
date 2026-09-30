# Frozen model temporal extension

Executed again on 28 September 2026. This is an exploratory temporal extension,
not an untouched confirmatory test. A temporary 25 September evaluation had
already inspected eligibility and some outcomes; its complete artifacts were
lost during workspace maintenance. The protocol discloses that access. Only
the retained recomputation supports the reported values.

The same six CC0 StoreNet source files were downloaded and their SHA-256
digests match `data/source_manifest.json`. The full-year processed file is
included under `data/later_period/`. Its prefix through 14 June exactly matches
the original processed input. No external price series is joined to the
unverified source clock. Raw one-minute files are not duplicated in the archive.

## Evidence

- Period: 1 July–31 December 2020, 184 calendar days.
- 501 of 1,104 candidate four-hour blocks, across 168 retained source days.
- Every block requires 16 complete intervals plus a complete preceding interval.
- All 60 saved follow-up checkpoints, without retraining or reselection.
- Idle, self-consumption, persistence MPC, previous-day MPC and Ridge MPC.
- Ridge uses January–April only and matches the saved coefficients.
- Every arm has 3,006 household-episode rows; 195,390 rows in total.
- Maximum energy residual 1.34e-15 kWh; zero terminal residual.
- All ten discrete 300-update policies again execute zero throughput.

Aggregate cost is 1,947.4997 EUR for idle, 1,946.6754 for persistence MPC and
1,939.3432 for Ridge MPC. These totals cover retained episodes only. Ridge
saves 7.3322 EUR against persistence (about 0.38%), with positive aggregate
savings against idle in all six homes. Individual days and episodes can lose.

The primary five-seed discrete-IPPO mean minus persistence contrast is
+0.00491 EUR per retained day; its seven-eligible-day block interval is
[-0.00008, +0.01111]. Ridge minus persistence is -0.04364 EUR per retained day,
with interval [-0.06889, -0.02127]. These are unadjusted conditional exploratory
intervals. Model seeds do not multiply the number of temporal observations.
Only 1 midnight and 11 04:00 blocks are eligible. This strongly limits full-day
arbitrage interpretation. Seven eligible days need not be seven calendar days.

## Reproduce from retained outcomes

From the project root with Python 3.12 and extension dependencies installed:

```bash
export PYTHONPATH=src
python scripts/analyze_temporal_sensitivity.py
python scripts/verify_later_period.py
python -m unittest discover -s research_tests -v
```

The analysis writes aggregate summaries from retained household rows and
checks cost plus savings against the matching idle counterfactual. It uses
10,000 circular moving-block draws with seed 25092026 and block lengths
1, 2, 3, 7 and 14. June is analyzed separately.

## Repeat model evaluation

Preserve the delivered evidence. Use a separate copy of the project and an
empty `results/later_period/` directory. Never delete the delivered execution
lock to disguise a second run. Obtain the six files named in the source
manifest in a raw-data folder and verify their hashes first.

```bash
python scripts/evaluate_later_period.py --raw-dir /path/to/raw
python scripts/evaluate_later_period.py --raw-dir /path/to/raw --method idle
python scripts/evaluate_later_period.py --raw-dir /path/to/raw --method rule
python scripts/evaluate_later_period.py --raw-dir /path/to/raw --method persistence_mpc
python scripts/evaluate_later_period.py --raw-dir /path/to/raw --method daily_mpc
python scripts/evaluate_later_period.py --raw-dir /path/to/raw --method ridge_mpc
python scripts/analyze_temporal_sensitivity.py
```

The initialization refuses to replace an existing lock, compares the historical
input prefix and fitted Ridge parameters, and records data, code and checkpoint
hashes before evaluating policies. Baseline arms check that identity and refuse
to replace completed arm files. No optimization uses future measurements.
All costs use the existing positive-tariff battery model and terminal reset.

ChatGPT/Codex assisted implementation and analysis. Retained execution and
verification are evidence of computation, not certification of student
authorship, supervisor approval or real-world market validity.
