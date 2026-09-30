# Scientific release / 30 September 2026

## 01 / Contribution and claim discipline

### Research contribution
An auditable decision pipeline connects measured household energy, forecast-conditioned battery control, distributional outcomes and settlement verification. Its contribution is reproducibility and an explicit evaluation of failure modes; the retained evidence does not establish DRL superiority.

### Two scopes, two objectives
Completed empirical scope: six Irish households, simulated tariffs and batteries, minimizing aggregate electricity cost while reporting individual outcomes. Intended application: a price-taking Polish BESS trader maximizing net trading profit. These are separate estimands; the Irish experiment cannot establish Polish trading profitability.

### Evidence hierarchy
Measured: consumption and PV inputs. Assumed: tariffs, battery parameters and single-bus physics. Computed: policy costs, physical residuals and settlement consistency. Proposed: Polish trading validation, independent test, risk-constrained operation and production governance. Each layer must retain its label in the abstract and defense.

### Claim that survives scrutiny
Within the retained complete-case simulations, forecast choice changes MPC economics; longer training and continuous actions do not establish an RL advantage. Local settlement agreement supports accounting consistency, not meter truth or the necessity of blockchain.

### Reading map
The following 80-page manuscript, 20-slide defense and 19-page guide retain their existing scientific record. This five-page release addendum provides new descriptive calculations, explicit decision gates and a navigable evidence map. It does not retroactively preregister any experiment.

## 02 / What the retained results actually show

### Forecast quality is decision-dependent
Ridge MPC costs EUR 1939.3432, versus EUR 1946.6754 for persistence MPC: EUR 7.3322 lower (0.377%). Horizon MAE decreases by 13.67%, while first-step MAE increases by 2.23%. A single one-step accuracy score is therefore insufficient to rank these controllers.

### Careful interpretation
This comparison uses identical retained episodes and the same controller family, but it is descriptive evidence on inspected data. It does not show that every decrease in forecast error causes a predictable increase in savings. Forecast fallbacks remain part of the deployed Ridge pipeline and must be reported.

### Ablation summary
The table reports means across five training seeds for each family on the same later-period data. These seeds are repeated algorithm realizations, not independent households or new market observations.

### Mechanism remains partly unresolved
All ten 300-update discrete policies reproduce idle cost and zero throughput. Every 300-update continuous policy is more expensive than persistence MPC. Longer training improves family mean cost here, but inactivity can arise from multiple causes. Reward gradients, exploration and state coverage were not independently isolated; a single root cause is not established.

## 03 / A falsifiable next study

### Freeze before access
Create a prospective registration with exact source identifiers, prior-access declaration, train/validation/test boundaries, raw hashes, exclusion rules, decision-time feature availability, code commit, physical assumptions and compute budget. A candidate date range becomes confirmatory only after its independence is verified; chronology alone is insufficient.

### One primary endpoint
For the Polish study, use paired daily net profit: selected PPO minus the deterministic MILP under the same forecast, battery constraints and cost assumptions. Select the policy and all hyperparameters on development data. Evaluate once on complete held-out delivery days; report failures and excluded days as well as retained observations.

### Precision before sample size
Choose a financially meaningful minimum effect and target confidence-interval width. Estimate day-to-day dependence on development data, then use a development-only block-bootstrap precision simulation to select the required duration. A target of 180 days is a coverage objective, not evidence of adequate statistical power.

### Separate uncertainty sources
Preserve temporal dependence in paired comparisons. Report seed variation separately, with the primary aggregation rule fixed before testing. Lock the block-length selection rule on development data. Treat alternative controllers, fairness metrics and subgroup contrasts as secondary unless separately registered.

### Explicit decision gate
A superiority claim requires the prespecified interval for incremental profit to clear the prespecified economic threshold while meeting physical and risk constraints. Otherwise retain the benchmark and report a negative or inconclusive result. A wide interval that includes zero does not demonstrate equivalence.

### Unfinished risk component
A reward penalty is not a hard CVaR constraint. Risk-constrained optimization and correct fractional-tail estimation must be implemented and checked before claiming bounded downside. Extreme-tail estimates from a short window must retain their uncertainty.

## 04 / System boundaries and independent evaluation

### Forecast to controller
Historical data and only decision-time-available features produce the forecast. The forecast, current battery state and physical limits produce a schedule. Metered realizations determine simulated cash flows. The existing coupled empirical evidence is forecast-to-MPC; a Polish forecast-conditioned PPO remains future work.

### Evaluate propagation
Hold the controller fixed and substitute persistence, a trained forecast and a non-causal oracle. The oracle is a diagnostic bound, not a deployable competitor. Add forecast perturbations only under a frozen protocol, and report horizon error, incremental cost, throughput and individual gains on the same episodes.

### Physics is a feasibility boundary
The aggregate BESS model checks energy conservation, charge/discharge limits, efficiencies and terminal state. Four-hour episode resets and the absence of feeder power flow limit interpretation. Real deployment also requires network, metering, market-access and operational validation; aggregate feasibility does not imply network feasibility.

### Ledger to trust claim
Replay identical settlement records against the signed database and local smart contract. Compare accepted transactions, rejected tampering, accounting balances and resource costs. A signature authenticates the signing key, not the physical accuracy of a meter. A contract cannot repair a compromised measurement oracle.

### When blockchain is justified
Use a shared ledger only when independent parties require shared ordering and settlement without trusting one database operator, with explicit validator governance and key recovery. If one accountable operator is acceptable, the signed database is a valid simpler baseline. Escrow and independent governance are not implemented evidence in this release.

### Failure isolation
Log forecast versions, policy identity, decision timestamps, input hashes, constraint residuals and settlement identifiers. This permits a wrong bill to be traced to a forecast, controller, physical assumption or ledger step instead of presenting adjacent modules as one validated system.

## 05 / Evidence map and submission gates

### Audit trail
results/later_period/summary.csv contains the controller outcomes. results/release_analysis.json records the new calculations and the source hash. configs/ablation_protocol.json and configs/forecast_control_protocol.json describe the completed exploratory comparisons. docs/FOLLOW_UP_PROTOCOL.md records the independence and uncertainty limits.

### Reproduce without retraining
Run the four read-only verify scripts listed in README.md. The release manifest checks file identities; the retained evidence audits check economic accounting, model/data identity and temporal coverage. Unit tests cover implementation invariants, not profitability. Training is a separate, explicitly documented operation.

### Scientific completion gate
Still required for a stronger market thesis: acquire and audit the Polish dataset; implement the intended forecast-conditioned policy and risk constraint; execute a genuinely untouched test; assess missingness and realistic market execution. No formatting or repository publication substitutes for these results.

### Academic completion gate
The team must confirm official identifiers, real author contributions, the approved scope and institutional submission requirements. Review AI-assisted prose and calculations with the supervisor. This release does not certify student authorship, originality review or institutional approval.

### Release note / 30 September 2026
This release adds a descriptive ablation synthesis, forecast-to-cost interpretation, explicit confirmation gates, a trust-boundary analysis and navigable PDF packaging. All prior empirical data and checkpoints are retained. No additional training, market acquisition or independent confirmation was performed for this release.

### Scientific standard
The defensible outcome is an inspectable research artifact with calibrated conclusions. The final thesis should be judged by valid questions, traceable evidence and honest limits, not by a guarantee of perfection or an unsupported claim that AI wins.
