# SIMULATIONS31 Research Program: from projection diagnosis to risk-aware AI

**Status:** pre-experiment research design. These are hypotheses, not published results, model improvements, or claims of superiority. The existing protocol's independent Polish July-August 2026 test and H7-H20 households remain unopened.

## Scientific problem and scope

In the 30-day June 2026 **validation** data, LEAR-driven MILP records EUR 236.08/day versus five-seed 2,000-update PPO EUR 214.37/day. June served checkpoint selection and is not an independent test. The June 30 read-only audit replays five SHA-256-checked checkpoints and decomposes the *forecast-price* schedule gap; it does not estimate realized half-hourly regret or causal importance of intervals.

## Three falsifiable hypotheses

**H1 — constrained-action saturation:** At states close to the energy limits or the terminal return-to-target constraint, a material share of sampled policy requests are clipped. This may reduce the alignment between PPO action-density updates and executed rewards. **Measure** the clipped share by model, 15-minute position, forecast-price quantile and SoC; compare with feasible action-set parameterization. **Reject** if well-controlled ablations do not reduce clipping or improve held-out *development-only* validation.

**H2 — forecast-aware imitation initialization:** A policy pre-trained to imitate a forecast-driven optimal MILP schedule, then fine-tuned by PPO, may learn profitable arbitrage sooner than PPO trained from scratch. This is a *training intervention* distinct from a trivial controller that simply executes MILP. **Baselines:** original 2,000-update PPO; imitation-only actor; imitation+PPO; MILP itself; do-nothing; simple threshold and mean-profile MILP.

**H3 — tail-risk tradeoff:** A day-level risk-sensitive objective may reduce lower-tail forecast/realized-price losses, perhaps at the expense of mean return. Use CVaR of simulated *daily realized profit* only in a properly separated development train/validation environment. Do not claim CVaR improvement until its loss distribution and intervals are measured. Report risk aversion coefficients predeclared and treat any parameter sweep as exploratory.

## Evaluation safeguards

1. Keep the original five frozen policy checkpoints and original baseline results unchanged.
2. Train new candidate checkpoints only with Jan–May 2026 development data, separating internal train and validation periods chronologically. Do not tune to the existing June leaderboard and subsequently call June unseen.
3. Any synthetic scenario generator must be fit only on historical inputs available before the decision; disclose its assumptions and stress ranges. Using actual same-day delivery prices to choose a D-1 schedule is prohibited.
4. Apply exactly the same feasible BESS state and terminal SoC constraints to every policy and comparator; reconcile the two accounting conventions.
5. Run at least five deterministic random seeds per stochastic policy; report all seeds and negative results.
6. Report paired daily mean profit, lower-tail quantile, CVaR, losing-day count, throughput, clipping frequency, forecast-baseline comparisons and block-bootstrap uncertainty. Distinguish forecast-price objective from observed-price simulated profit.
7. No claims about actual accepted bids, grid fees, imbalance settlement, live financial performance or ten physical participant settlement until separately modeled and evidenced.
8. **Do not** open the independent July–August 2026 dataset or alter the frozen-test protocol based on these exploratory diagnostics.
9. Store candidate experiments only in additional SIMULATIONS31 files; require tests, recorded dependency/environment versions, hashes, reviewer read-through and no data overwrites before promotion.
10. Source and contribution declaration: generated suggestions/code are AI-assisted and must be reviewed, run, interpreted and independently explained by the student team.

## Decision gates

- **Gate A (completed when CI succeeds):** verified 96-slot schedule replay and exact price/wear contribution identity.
- **Gate B (not yet done):** causal controlled ablations separating projection from other differences in architecture and optimization budget.
- **Gate C (not yet done):** risk-aware PPO and imitation-seeded PPO experiments with documented development splits.
- **Gate D (not yet done):** supervisor/team approval of scope, successful provenance lock and independent test on a precommitted treatment, with all negative findings preserved.

**Interpretation discipline:** A high clipping fraction is a diagnosis, not proof of an algorithmic bug. Exact forecast-price cashflow decomposition is arithmetic, not attribution of realized daily losses or a claim that replacing isolated actions would preserve final energy feasibility.
