# October 2026 exploratory addendum (draft for supervisor review)

**Status: draft.** Prepared 14 October 2026 for discussion with the supervisor. Nothing here has been added to the submitted manuscript, slides or PDF package. All analyses use previously inspected data and are exploratory. The analysis and drafting were AI-assisted; the team must review them and record that assistance in the GenAI declaration (Section 1.3 and Appendix B).

## 1. Why this addendum

The thesis concludes that the retained learners do not beat MPC and that the discrete learners settle on idle. A follow-up question is whether that reflects the methods or the experimental design. Every retained episode lasts four hours and must end at 1 kWh, while the assumed tariff charges 0.20 EUR before 07:00 and 0.42 EUR from 16:00 to 20:00. Those windows never share a four-hour block, so night-to-peak shifting is unavailable to every controller.

## 2. Findings

| # | Finding | Evidence |
| --- | --- | --- |
| 1 | On the 501 retained July–December episodes, perfect foresight saves only 60.20 EUR (3.09% of idle). Ridge MPC captures 13.6% of that bound, persistence MPC 1.4%, the 300-update discrete learners 0%. | `docs/EPISODE_LENGTH_EXPLORATION.md`, `results/exploratory_episode_length/` |
| 2 | On 164 days with at least 80 of 96 observed slots, 24-hour episodes raise the perfect-foresight saving from 95.15 to 283.51 EUR (2.98 times). | same |
| 3 | Causal Ridge MPC with 24-hour episodes saves 113.55 EUR (3.47% of idle, 40% of the bound) with no household worse off. Persistence MPC loses money at both lengths. | `results/exploratory_mpc_24h/` |
| 4 | The retained IPPO/MAPPO learners with 24-hour episodes and otherwise unchanged settings do not exploit the larger value: 8 of 10 discrete policies stay idle, and the other 2 and all 10 continuous policies lose 73 to 173 EUR. No validation checkpoint was positive. Two runs are bit-identical. | `results/exploratory_rl_24h/` |
| 5 | No 2020 day has all 96 quarter-hours for H1–H6; gaps concentrate between 00:00 and 05:00. Two gap fills agree within 0.6 EUR on every arm. | data audit in the exploration document |

Every new pipeline first reproduces retained numbers exactly (June oracle 153.7614 EUR; later-period idle 1947.4997, persistence MPC 1946.6754 and Ridge MPC 1939.3432 EUR).

## 3. What this does and does not change

- It reframes the negative learner result: under four-hour resets the attainable value is about 3% of the bill, so near-idle behaviour is close to what the design allows.
- It shows that horizon and forecast shape interact: a longer horizon helps only with a forecast that anticipates the evening peak.
- It shows that the learner result is not only a design artefact: with the larger value available, MPC captures 40% of it and the learners none.
- It does not establish 24-hour superiority on unseen data, other tariffs, other batteries or the Polish market.

## 4. Proposed next step: held-out households

The StoreNet collection has twenty households; the thesis uses H1–H6. `docs/PROTOCOL_24H_HOLDOUT_DRAFT.md` tests 24-hour Ridge MPC once on H7–H20, with a 1% minimum relative saving, a joint-date block bootstrap and a pre-stated decision table. The pipeline refuses to read held-out households until the protocol is frozen, and a dry run on H1–H6 reproduces the exploratory numbers exactly.

## 5. Options for the thesis

| Option | Effort | Risk |
| --- | --- | --- |
| A. Mention in Limitations and Future Work only | Low | Leaves the design limitation as the main open question |
| B. Add this addendum as an appendix, labelled exploratory | Medium | Reviewers may ask why the main study used four-hour episodes |
| C. Freeze and run the held-out study before submission, then report it | Higher | Result could be null or negative; must be reported either way |

## 6. Decisions for the team and supervisor

1. Which option in Section 5 fits the approved scope and timeline.
2. Whether any coauthor has opened H7–H20 meter files (access declaration).
3. Whether 1% of idle cost is the right economic threshold.
4. Updating the GenAI declaration to cover this October work.
