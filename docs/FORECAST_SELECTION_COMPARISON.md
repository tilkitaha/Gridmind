# Comparing profit and error objectives

20 October 2026. Local exploratory extension; not a new independent test.

## Why this comparison

The first profit selector compared five forecasts with retained trading outcomes.
It did not compare selecting for profit against selecting for accuracy. This experiment
holds the candidate set, available history, physical controller and scoring dates fixed,
changing only the selector's objective.

`results/polish_forecast/daily.csv` contains daily MAE and MILP profit for LEAR,
gradient boosting, yesterday's prices and last week's prices. These four models form
the matched panel. The 7/14/28-day profiles are excluded from both selectors because
their daily MAE records were not retained. Consequently these results must not be
compared directly with the first selector as if the candidate set were unchanged.

## Fixed choices

- Rolling profit: maximize average past MILP profit over the preceding 28 calendar days.
- Rolling error: minimize average past daily MAE over the same window.
- Both require 14 observed dates. Missing dates are not filled or counted as zero.
- Exact ties use LEAR, gradient boosting, yesterday, then last week.
- Frozen June comparators choose once using January-May and keep that choice for June.
- Rolling June comparators may use earlier June outcomes, as day-ahead settlement
  prices for D-1 are already available at the D-1 scheduling gate in this experiment.
- Only January-June 2026 input dates are accepted. Candidate test data are not opened.

The selector settings were chosen before the first run of this extension, with no
parameter sweep. These development dates and the candidate models were already
inspected, so neither the full-period result nor the frozen June comparison is confirmatory.

## Results

| Same 166 scored days | EUR/day | Realized daily MAE | Losing days |
| --- | ---: | ---: | ---: |
| Rolling profit selection | 179.66 | 23.68 | 11 |
| Rolling error selection | 181.70 | 23.49 | 12 |
| Always LEAR | 181.83 | 23.02 | 12 |

Profit selection minus error selection is -2.04 EUR/day, with an exploratory 95%
interval of [-6.10, 1.30]. It does not demonstrate an advantage. In June, both frozen
objectives select LEAR and earn 236.08 EUR/day; the rolling profit selector earns
232.42 EUR/day. These outcomes are retained rather than used to choose another window.

Intervals resample paired daily profit differences with circular blocks of seven
observed rows, 10,000 draws and seed 20102026. They bridge missing calendar dates,
condition on the recorded choices, do not refit the selector inside each draw, and
are not adjusted for multiple comparisons. They summarize this exploratory record,
not uncertainty about a newly trained policy's future performance.

## Reproduce and review

```powershell
$env:PYTHONPATH = 'src'
python scripts/compare_forecast_selection.py --out results/my_selection_comparison
python -m unittest discover -s research_tests -p test_forecast_selection.py -v
```

The evaluator requires NumPy, already included in the research environment. The output
directory must not exist. It reads saved scores only, with no network or raw-price access.

`results/forecast_selection_comparison/` contains:

- `REPORT.md`: readable comparison, paired intervals and limits.
- `daily.csv`: selected model and realized profit/error for each arm on each scored date.
  Frozen columns are blank before June, rather than filled with zero.
- `decisions.json`: each choice, all candidate scores, and the first/last dates and count
  of observations used for the decision.
- `results.json`: aggregates, exclusions, fixed settings and input/code SHA-256 hashes.

Tests cover future-data leakage, frozen June decisions, profit/error disagreement,
ties, missing dates, matched panels, invalid inputs and bootstrap behavior.

## Implication for the next model

Past profit is noisy. Simply replacing MAE with trailing realized profit does not
guarantee a better choice. Training with a scheduling-regret objective remains a
distinct research step; this experiment has not implemented or tested that training.
Any later trial should keep strong fixed forecasts and recent-mean profiles as
comparators, with a separately frozen evaluation plan.
