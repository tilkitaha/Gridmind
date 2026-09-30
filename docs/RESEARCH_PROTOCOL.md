> This document describes the original experiment. For the 22 September 2026 follow-up results and current scope, read ABLATION_REPRODUCTION.md and POLISH_MARKET_STUDY.md.

# GridMind research protocol

The primary beneficiary is the prosumer community. Its coordinator allocates bill savings; households do not directly become wholesale-market participants.

## Primary research question

Can a learning-based controller improve the distribution of household savings while retaining at least 95 percent of a strong optimizer's savings, and how does this change with forecast uncertainty and battery flexibility?

The 95 percent level is a proposed experimental tolerance. The completed pilot compares allocation baselines and a separate learned forecasting model; it does not answer the full control question.

## Accounting

For seller i and buyer j, let x be matched kWh, b_j the import tariff, s_i the export tariff and f the external fee per kWh. Midpoint pricing and equal fee splitting give each party (b_j-s_i-f)x/2. Nonpositive-gain edges are excluded. Internal payments cancel from community costs.

With common b, s and f, community savings equal (b-s-f) times matched volume. Redistributing identical volume cannot create more savings. A real trade-off needs heterogeneous outside options, changed volume, flexibility, losses or other binding constraints.

The Nash method maximizes the mean log of epsilon plus cumulative daily savings divided by a household scale fixed using January-May load. It retains a configured share of the interval welfare-LP bound. This is a myopic numerical baseline, not a full-horizon optimum or trained RL policy. SLSQP status and feasibility are checked; any failure uses an explicitly labelled LP fallback.

## Domain and evaluation rules

Jain and Gini are undefined for the all-zero benefit vector and are not interpreted on signed losses. Material negative values are never clipped. Report losses separately. Regularized Nash uses epsilon=0.01 on dimensionless benefits and is distinct from exact Nash welfare. Raw and normalized fairness answer different normative questions.

The pilot uses measured consumption and PV without historical battery dispatch, assumed tariffs, single-bus allocation and source-clock timestamps. It cannot establish actual Irish bill savings, legal settlement feasibility, feeder feasibility or a causal treatment effect. Missing intervals are dropped jointly across all policies, without interpolation.

Paired moving-block intervals are exploratory: only 14 days and six houses were tested. A 95 percent daily-cost CVaR with 14 days contains 0.7 tail-day equivalents and reduces to the observed maximum; do not present it as robust tail-risk evidence.

## Confirmatory extension

1. Verify source time zone, Ireland case scope, tariff/settlement rules and a matching historical data period.
2. Use all eligible original households; select on coverage before outcomes. Replicating households into 50/100 agents is a synthetic scaling test.
3. Freeze chronological and household splits, normalization, main metric, comparator, exclusions, stopping rule and training budget before a new final test.
4. Implement physically constrained battery control, terminal state handling and deterministic/scenario MPC.
5. Compare IPPO and MAPPO under equal information, constraints, training steps and five training seeds. A heuristic is not a trained AI baseline.
6. Separate forecasting ablations from controller ablations; the current one-step forecast is not a day-ahead forecast.
7. Evaluate paired daily outcomes and seed variation separately. Target at least 180 test days for an initial tail-cost analysis; nine tail-day equivalents at 95 percent remain limited.
8. Compare a signed database audit record with a permissioned ledger under the same workload. Measure latency, fees, faults and governance; do not infer physical delivery from hashes.

## Pilot interpretation

The guarded Nash optimizer improves average daily normalized Jain versus the welfare LP under heterogeneous tariffs with a small loss in savings. Proportional allocation remains more equal on several metrics. Keep it as a strong comparator. Daily log utility and pooled Jain are different objectives and can rank methods differently. No metric should be selected after inspecting which one makes the proposed method look best.
