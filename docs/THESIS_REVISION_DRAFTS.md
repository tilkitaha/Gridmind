# Draft text for the FEM review items

14 October 2026. Proposed wording for the gaps in `docs/THESIS_FORMAT_REVIEW.md`. Nothing has been inserted into the manuscript. The team chooses, edits and takes responsibility for any text it adopts, and records the assistance in the GenAI declaration. Numbers below are copied from the retained evidence; recheck them against the final manuscript before use.

## 1. Front matter order (review item 1)

Move **Contents** so that the order reads: Title page → Streszczenie → Abstract → Contents → Abbreviations and notation → Chapter 1. No text change is needed.

## 2. Title options (review item 2, team and supervisor decision)

The title must match the USOS APD entry. If a change is still possible, these use the recommended forms and match the completed evidence:

- *Comparison of Learning-Based and Model-Predictive Battery Control with Verifiable Settlement for a Prosumer Energy Community*
- *Design of an Auditable Battery Control and Settlement Pipeline for a Prosumer Energy Community*
- *Application of Multi-Agent Reinforcement Learning and Model Predictive Control to Community Battery Scheduling*

If the APD title cannot change, add one sentence to 1.1 stating that autonomous Polish trading and enforced risk optimisation are the intended application and remain unfinished, as Sections 8.10–8.12 already explain.

## 3. Object, subject and objective (review item 3, new paragraph in 1.1)

> **Object of research.** Battery control methods for a prosumer energy community: multi-agent reinforcement learning (IPPO and MAPPO), model predictive control with persistence and Ridge forecasts, and the settlement record that accounts for the resulting energy sharing.
>
> **Subject of research.** A community of six Irish households with measured consumption and photovoltaic generation (StoreNet, 2020), simulated batteries and assumed time-of-use tariffs, with a Polish price-taking battery trader as the intended application.
>
> **Objective.** To compare learned and optimisation-based controllers on community electricity cost and household outcomes under identical information and physical constraints, and to verify that settlement records remain consistent with the simulated energy flows.

## 4. SMART goal (review item 4)

> The goal is to determine whether any retained learned policy lowers aggregate community electricity cost below the persistence-forecast MPC baseline (*specific*), measured as paired cost in EUR over identical episodes with every household's outcome reported (*measurable*), using measured StoreNet data for H1–H6 with the battery and tariff assumptions of Chapter 3 (*achievable*), because a community coordinator needs a controller that saves money without making any household worse off (*relevant*), evaluated on June 2020 and on the frozen-model July–December 2020 extension within the thesis period (*time-bound*).

## 5. Introduction: motivation and structure (review item 5)

Motivation, placed before 1.1.1:

> Households with photovoltaic panels and batteries can lower their bills by sharing energy and timing storage, but the coordinator of such a community needs evidence that a controller saves money, treats households acceptably and produces settlement records that can be checked. Learned controllers are often reported to outperform simpler optimisation, yet results are sensitive to data selection, tariffs and evaluation practice. This thesis was chosen to test that claim under explicit assumptions and reproducible evidence rather than to assume it.

Structure, at the end of Chapter 1:

> Chapter 2 reviews research on forecasting, control, multi-agent learning, fairness, risk and trust, and defines the market and data boundary. Chapter 3 formulates the physical, economic and fairness model. Chapter 4 describes the research design, the implemented system and the evaluation protocol. Chapter 5 reports the allocation and forecasting pilot, Chapter 6 the battery control and learning results, and Chapter 7 the settlement experiment. Chapter 8 assesses innovation and implementation potential, including the Polish application, and Chapter 9 states the achievement of each objective and the conclusions.

## 6. Justification of methods and tools (review item 6, new table in Chapter 4)

**Table 4.x Methods, alternatives and reasons for the choice**

| Method or tool | Alternatives considered | Reason for the choice |
| --- | --- | --- |
| IPPO and MAPPO (PPO) | Value-based multi-agent learning; single centralised agent | PPO is a widely used, stable baseline for cooperative multi-agent control (Schulman et al. 2017; Yu et al. 2022); the IPPO/MAPPO pair isolates the effect of a centralised critic under identical actors |
| Model predictive control as a linear programme | Rule-based control; heuristic scheduling | Exact optimum for the forecast horizon under linear battery and settlement constraints; a strong economic baseline that learned policies must beat |
| Persistence and Ridge forecasts | Gradient boosting; neural forecasters | Transparent, causal and fast; enough to show how forecast choice propagates to control cost before adding complex models |
| Non-causal oracle | None | A diagnostic upper bound that separates forecast error from controller limits |
| Five training seeds and checkpoint replay | Single run | Learned-policy results vary by seed (Henderson et al. 2018; Agarwal et al. 2021) |
| Circular moving-block bootstrap | Independent bootstrap; t-intervals | Daily costs are serially dependent; block resampling preserves that dependence |
| Ed25519-signed SQLite alongside a local Solidity contract | Public blockchain only | Tests whether a shared ledger adds anything over a simpler signed database for the same transactions (Wüst and Gervais 2018) |
| SciPy (HiGHS) and PyTorch | Commercial solvers; other frameworks | Open source, reproducible from pinned versions without licences |

## 7. Intellectual property and implementation possibility (review item 7, new subsection in Chapter 8)

> **8.x Intellectual property.** The software developed for this thesis is released under the MIT licence, and its authorship is recorded in Appendix B and the repository history. The StoreNet input data are published under CC0 by their authors and are used here as a derived subset with full attribution; the Polish market data, when acquired, remain subject to the ENTSO-E terms of use. The contribution is a reproducible evaluation pipeline and its findings rather than a patentable invention: the controllers, forecasts and ledger techniques used are established methods. The diploma thesis itself is subject to copyright, and Poznan University of Technology has priority in its publication. Any implementation partner would therefore license the open-source code freely, while results and text remain subject to the University's publication priority.

Implementation possibility is already covered in Sections 8.2–8.9; refer to them from this subsection rather than repeating them.

## 8. Achievement of each objective (review item 8, new table in 9.1)

**Table 9.x Level of achievement of the research objectives**

| Objective (Table 1.1) | Level | Evidence |
| --- | --- | --- |
| Community cost: compare learned and MPC control | Achieved | 10 original and 60 follow-up policies; on July–December, Ridge MPC 1939.34 EUR versus persistence MPC 1946.68 EUR and idle 1947.50 EUR; all ten 300-update discrete policies reproduce idle |
| Distribution: household outcomes and fairness | Partly achieved | Household outcomes reported for every arm; the signed-benefit penalty gave no consistent improvement; no fairness or retention guarantee |
| Risk: tail-cost control | Partly achieved | CVaR computed as a diagnostic only; no enforced daily risk constraint |
| Settlement: verifiable accounting | Achieved within scope | 64 transactions with balance parity and tamper rejection in both the contract and the signed database; meter truth and multi-party governance not tested |
| Polish market application | Not achieved | Scheduling model and data contract implemented and tested analytically; no market data acquired and no trading result |
| Untouched independent test | Not achieved | All evaluation dates were inspected before analysis |

## 9. Literature: books and standards (review item 9)

Add only works the team has actually read and uses in the text. Candidates that match methods already in the thesis:

- Sutton RS, Barto AG. 2018. *Reinforcement Learning: An Introduction*. 2nd edn. Cambridge MA: MIT Press. (Chapter 2, learning)
- Rawlings JB, Mayne DQ, Diehl MM. 2017. *Model Predictive Control: Theory, Computation, and Design*. 2nd edn. Madison: Nob Hill Publishing. (Chapters 3–4, MPC)
- Boyd S, Vandenberghe L. 2004. *Convex Optimization*. Cambridge: Cambridge University Press. (LP formulation)
- Hyndman RJ, Athanasopoulos G. 2021. *Forecasting: Principles and Practice*. 3rd edn. Melbourne: OTexts. (persistence and regression forecasts)
- Hoerl AE, Kennard RW. 1970. Ridge Regression: Biased Estimation for Nonorthogonal Problems. *Technometrics* 12(1), 55–67. (Ridge forecast)
- Künsch HR. 1989. The Jackknife and the Bootstrap for General Stationary Observations. *The Annals of Statistics* 17(3), 1217–1241. (block bootstrap)
- Standards: the ENTSO-E Transparency Platform documents follow the IEC 62325 series (framework for energy market communications), and battery energy storage systems are covered by the IEC 62933 series. Check the exact part, title and edition in the IEC catalogue before citing.

## 10. Figure 6.2 source line (review item 10)

> Figure 6.2 Coverage by start hour and monthly Ridge minus persistence cost
> Source: own study based on Trivedi et al. 2024 (StoreNet data); research experiment outputs.
