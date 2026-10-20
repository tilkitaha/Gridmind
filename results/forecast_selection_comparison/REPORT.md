# Profit versus error: exploratory forecast selection

Retained development outcomes; no independent test or new model training.

Both selectors use the same candidates and dates. Rolling choices use only
earlier days; frozen June choices use January-May only.

## All Scored Days (166 days)

| Method | EUR/day | MAE EUR/MWh | Losing days |
| --- | ---: | ---: | ---: |
| rolling_profit | 179.66 | 23.68 | 11 |
| rolling_mae | 181.70 | 23.49 | 12 |
| lear | 181.83 | 23.02 | 12 |
| gbm | 174.63 | 27.23 | 11 |
| naive_d1 | 161.91 | 28.76 | 16 |
| naive_d7 | 152.42 | 35.98 | 21 |

Paired differences in EUR/day (exploratory 95% intervals):

- rolling_profit_minus_rolling_mae: -2.04 [-6.10, 1.30]
- rolling_profit_minus_lear: -2.17 [-6.15, 1.08]
- rolling_mae_minus_lear: -0.12 [-0.71, 0.32]

## June Validation (30 days)

| Method | EUR/day | MAE EUR/MWh | Losing days |
| --- | ---: | ---: | ---: |
| rolling_profit | 232.42 | 27.42 | 0 |
| rolling_mae | 236.08 | 25.36 | 1 |
| lear | 236.08 | 25.36 | 1 |
| gbm | 220.66 | 28.54 | 0 |
| naive_d1 | 210.31 | 32.96 | 2 |
| naive_d7 | 205.20 | 34.94 | 1 |
| frozen_profit | 236.08 | 25.36 | 1 |
| frozen_mae | 236.08 | 25.36 | 1 |

Paired differences in EUR/day (exploratory 95% intervals):

- rolling_profit_minus_rolling_mae: -3.66 [-9.71, 1.98]
- rolling_profit_minus_lear: -3.66 [-9.71, 1.98]
- rolling_mae_minus_lear: 0.00 [0.00, 0.00]
- frozen_profit_minus_frozen_mae: 0.00 [0.00, 0.00]

## Limits

- Same candidate panel for both objectives; mean profiles lack retained daily MAE
- No new model training or dispatch execution; recorded counterfactual profits reused
- June is reused validation data, not an untouched test
- Bootstrap blocks count observations, bridging missing calendar dates
- Bootstrap conditions on recorded choices; no policy refitting or multiplicity adjustment
