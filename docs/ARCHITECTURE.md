# Research architecture

28 September 2026. Two evidence levels are kept explicit.

| Component | Implemented role | Evidence boundary |
| --- | --- | --- |
| data.py and clearing.py | Measured-profile aggregation and energy allocation | Six Irish homes; partial coverage |
| forecast.py | Original aggregate one-step forecast | Separate allocation-pilot target |
| battery.py and learned_control.py | Physical battery simulation and original control comparison | Assumed tariffs and four-hour resets |
| ablations.py | Action/budget and matched reward interventions | Sixty runs on reused June dates |
| forecast_control.py | Past observations to forecast to MPC to realized cost | Four executed arms; forecast not supplied to learned actors |
| ledger_experiment.py and contracts | One fixed control stream replayed on local EVM and signed SQLite | Meter authority trusted; no independent validators or escrow |
| polish_market.py | Delivery clock, forecast gate, constrained aggregate MILP | Analytical verification only; no acquired Polish prices |
| evaluate_later_period.py and temporal analysis | Frozen policies, five baselines and paired daily uncertainty on 501 later episodes | Exploratory with documented prior access; incomplete source-day coverage |
| configs and results | Recorded protocols, checkpoints and outcomes | Config hash is not evidence of untouched data |

In the implemented coupling, causal meter history produces a remaining-horizon net-load forecast. MPC chooses an action, the physical layer enforces feasibility, and proportional accounting yields household cost. The original settlement stream is then independently replayed on two ledgers. Substituting the ledger does not change dispatch or improve the controller's economics.

The intended Polish application uses a complete day-ahead price forecast and a fixed daily market schedule. It is not the existing four-hour community environment. The baseline evaluator fixes its schedule before opening the realized-price file. It assumes full order acceptance and omits imbalance settlement. `POLISH_MARKET_STUDY.md` describes the remaining integration.

FastAPI, PostgreSQL, Next.js, authentication and billing are not current thesis capabilities. Historical product architecture is in `archive/ARCHITECTURE.md`.
