# Profit-oriented forecast selection

20 October 2026. Exploratory addition, separate from the frozen-policy test proposal.

## Question and implementation

Can selecting a forecaster by its recent battery trading profit improve on always using
LEAR or a recent mean-price profile? The first implementation selects existing forecasts;
it does not train a neural forecaster with a profit loss.

For delivery day D, choose the candidate with the highest mean realized MILP profit in
the preceding 28 calendar days, requiring at least 14 observed days. The candidate order
is LEAR, yesterday's prices, and 7-, 14-, and 28-day mean profiles; ties use that order.
The window and minimum were chosen before this experiment's first run, without a sweep.
Candidate design used earlier development findings, so the whole exercise is exploratory.

The selector uses only rows strictly before D. D-1 day-ahead prices are known at the
D-1 scheduling gate under the existing experiment's timing assumptions. That reasoning
does not permit using future intraday outcomes. The perfect-foresight oracle is excluded.
Missing days are not filled. All baselines are compared on identical scored dates after
the selector's warm-up. Input dates outside January-June 2026 are rejected unconditionally.

## Reproduction

The retained `results/polish_profile/daily.csv` contains realized profit for each candidate
forecast followed by the same MILP. Selecting one column per day therefore evaluates
forecast selection without downloading restricted raw prices or recomputing schedules.
This assumes each retained candidate schedule could have been selected at the gate.

PowerShell, from the repository root:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s research_tests -p test_profit_forecast.py -v
python scripts/polish_profit_forecast_eval.py --out results/my_profit_forecast_run
```

Only Python's standard library is needed for this addition. The output directory must
not exist. Outputs include the daily choice, history count, selection score, realized
profit, all fixed baselines, and input/code SHA-256 hashes. Alternative windows are
supported for explicitly labelled exploration, not for tuning against the pending test.

## First retained run

`results/polish_profit_forecast/` contains 166 scored days, January 15-June 30, with the
original clock-change exclusion. January 1-14 supplies warm-up history.

| Method | EUR/day | Losing days |
| --- | ---: | ---: |
| Past-profit selector | 183.91 | 11 |
| Always LEAR | 181.83 | 12 |
| Always yesterday's prices | 161.91 | 16 |
| Always 7-day mean | 183.08 | 14 |
| Always 14-day mean | 181.52 | 16 |
| Always 28-day mean | 177.06 | 15 |

The selector gains 2.08 EUR/day over LEAR and 0.83 over the 7-day profile in this reused
sample. These small descriptive differences do not establish statistical superiority
or out-of-sample improvement. No confidence interval or independent test is claimed.
The selection counts are 48 LEAR, 46 seven-day, 38 fourteen-day, and 34 twenty-eight-day;
yesterday's prices is never selected. All profits inherit the original battery,
full-acceptance, cost, and market assumptions; they are not observed trading revenue.

## Next research step

A [matched profit-versus-error comparison](FORECAST_SELECTION_COMPARISON.md) now uses
the four candidates with retained daily MAE and profit. On 166 reused dates, rolling
profit selection earns 179.66 EUR/day versus 181.70 for error selection; the exploratory
interval for the difference includes zero. The candidate set differs from the first
run above. Both January-May objectives select LEAR for a fixed June strategy.

Keep the current Polish test protocol unchanged. A separate future protocol could
compare profit-based selection with error-based selection and a forecaster trained
with a scheduling-regret objective, fixing candidates and tuning budgets before new
evaluation data are opened. Fresh forecast/dispatch integration needs the original
price files and their provenance; this first addition uses retained outcomes only.
