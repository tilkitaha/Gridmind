# Follow-up evidence and remaining protocol

Updated 22 September 2026. This file distinguishes completed exploratory work from the next independent study.

## Executed

`configs/ablation_protocol.json` preceded sixty runs. Forty cross discrete/continuous actions with 60/300 updates, using both IPPO and MAPPO and seeds 11, 22, 33, 44, 55. Twenty compare economic-only versus a signed-benefit variance penalty at fixed weight 0.1, with fourteen actor inputs in both arms. The latter uses the same May economic checkpoint rule. No penalty grid was searched. The normalization is a fixed 1 EUR reference.

`configs/forecast_control_protocol.json` precedes four forecast substitutions in the same MPC. Ridge uses 9,442 January-April rows, alpha 1 and recursive predictions. Every arm uses the same 44 June episodes. The oracle reads future measurements and is not deployable.

June was inspected before these studies. Neither protocol is a confirmatory registration. Sixty trained models and thousands of repeated rows do not create new independent households or dates. See `ABLATION_REPRODUCTION.md` for actual commands and results.

## Independent data

Audit previous access, then freeze exact dates, source hashes, quality rules, households or bidding zone, price versions, physical model, decision timing, features, algorithms, seeds, tuning budget, metrics and stopping rule. A later period is not automatically untouched. If candidate dates have informed choices, reserve another period.

The Polish application has its own `configs/polish_market_protocol.json`. Proposed dates are not yet data-frozen. Its primary actor and profit outcome differ from the Irish community's bill-saving objective.

## Statistical interpretation

Use one primary paired comparison and declare secondary comparisons exploratory. Preserve chronological dependence when estimating uncertainty. Select block length from development data before looking at test scores. Separate seed variability from variability across days and households. Report absolute monetary effects and losing participants alongside relative measures.

CVaR95 over 44 short episodes has 2.2 tail-episode equivalents; a 62-day study has only 3.1 tail-day equivalents. Neither warrants a precise general tail-risk guarantee. A 180-day target is coverage, not a power calculation. Specify an effect and precision target.

Equal signed savings can include equal losses, so dispersion alone is not welfare. A weighted penalty does not enforce individual rationality or 95 percent savings retention. Keep negative outcomes visible and define zero/negative outside-option handling before evaluating any ratio.
