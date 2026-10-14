# Episode-length exploration

14 October 2026. Exploratory, post hoc, on previously inspected July–December 2020 data. Perfect-foresight bounds only: no controller was trained, tuned or selected. Nothing here changes the retained evidence or its locks.

```bash
PYTHONPATH=src python scripts/explore_episode_length.py
```

Outputs go to `results/exploratory_episode_length/`. The script reimplements the `battery.mpc_action` LP with a variable horizon and simulates through the unchanged `battery.project` and `battery.settlement`. Before reporting anything it reproduces the retained June oracle cost (153.7614 EUR) and the later-period idle cost (1947.4997 EUR).

## Question

Every retained episode lasts four hours and must end at 1 kWh. The assumed tariff charges 0.20 EUR before 07:00 and 0.42 EUR from 16:00 to 20:00, but those windows never share a four-hour block, so night-to-peak shifting is unavailable by construction. How much attainable value does that remove?

## Captured share of the four-hour bound

On the exact 501 retained later-period episodes, perfect foresight saves 60.20 EUR (3.09% of idle cost). Share of that bound captured by retained arms:

| Arm | Saving (EUR) | Captured |
| --- | --- | --- |
| Ridge MPC | 8.16 | 13.6% |
| Persistence MPC | 0.82 | 1.4% |
| Discrete 300-update IPPO/MAPPO (all 10) | 0.00 | 0.0% |
| Daily MPC | −18.74 | −31.1% |
| Continuous 300-update IPPO | −84.08 (mean) | −139.7% (mean) |
| Rule | −117.84 | −195.8% |

Per-arm and per-family values are in `later_captured_share_by_arm.csv` and `later_captured_share_by_family.csv`.

## Four-hour versus 24-hour episodes

No 2020 day has all 96 quarter-hours; missing slots concentrate between 00:00 and 05:00. The comparison therefore keeps the 164 days with at least 80 complete slots (92.7% of their slots observed) and fills the remainder in two deliberately different ways. Both arms use identical days and identical filled data, with the battery at 1 kWh at each midnight.

| Fill | 4 h bound (EUR) | 24 h bound (EUR) | Ratio | % of idle, 4 h → 24 h |
| --- | --- | --- | --- | --- |
| Linear in time | 95.15 | 283.51 | 2.98 | 2.91% → 8.67% |
| Same month and slot median | 95.15 | 283.36 | 2.98 | 2.92% → 8.70% |

The 24-hour bound is at least as good on every day and higher for all six households. The monthly ratio ranges from 2.5 (September) to 3.6 (October). A back-of-envelope check agrees with the size: shifting 1.6 kWh of usable swing from 0.20 to 0.42 EUR is roughly 0.27 EUR per battery-day, about 265 EUR over 164 days and six households.

## Interpretation and limits

- The four-hour design leaves roughly two thirds of the perfect-foresight value outside every controller's reach. The retained discrete policies converging to idle, and the small MPC savings, should be read against a 3% ceiling rather than as a general verdict on the methods.
- These are upper bounds. Causal MPC results follow below; whether learned policies benefit is untested.
- The gain comes almost entirely from the assumed time-of-use spread. A different tariff would change it, and no retail bill was observed.
- Gap filling affects only the 24-hour comparison; the two fills agree to 0.05%. The captured-share table uses the retained 501 episodes without filling.
- All dates were inspected before this analysis. Any follow-up comparison of controllers needs a protocol fixed before access to genuinely unseen data.

## Causal MPC with 24-hour episodes

```bash
PYTHONPATH=src python scripts/explore_mpc_24h.py --fill linear
PYTHONPATH=src python scripts/explore_mpc_24h.py --fill slot_median
```

Outputs go to `results/exploratory_mpc_24h/<fill>/`. The receding-horizon loop replans every 15 minutes with the same LP. Forecasts read only raw meter rows before the decision time and use the retained Ridge coefficients; the filled series is used only as the settled realized load. Before the new comparison the script reproduces the retained 501-episode persistence (1946.6754 EUR) and Ridge (1939.3432 EUR) MPC costs exactly.

Same 164 days and linear fill (idle 3270.23 EUR); the median fill agrees within 0.6 EUR on every arm:

| Arm | 4 h saving (EUR) | 24 h saving (EUR) | 24 h share of 24 h bound | Households losing, 24 h |
| --- | --- | --- | --- | --- |
| Perfect foresight | 95.15 | 283.51 | 100% | 0 |
| Ridge MPC | −4.92 | **113.55** | **40.1%** | **0** |
| Persistence MPC | −26.13 | −36.22 | −12.8% | 4 |

- With 24-hour episodes, causal Ridge MPC saves 3.47% of idle cost, more than the four-hour perfect-foresight bound on the same days.
- Persistence MPC loses money at both lengths: a flat last-value forecast cannot anticipate the evening peak, so a longer horizon only adds cycling. The forecast's daily shape, not the horizon alone, carries the value.
- Both four-hour MPC arms lose money on these days, unlike on the 501 retained episodes. These days include blocks next to night gaps: 1149 of 15,744 decisions (7.3%) used a stale latest observation because the previous interval was missing, and those blocks were excluded from the retained set.
- One tariff, one battery, six households and inspected dates. This motivates a pre-registered 24-hour design; it does not confirm one.

## Learners with 24-hour episodes

```bash
PYTHONPATH=src python scripts/explore_rl_24h.py
```

Outputs go to `results/exploratory_rl_24h/`. The script keeps the retained `AblationPolicy` architecture, PPO settings (300 updates, 12 episodes per update, 4 epochs, learning rate 3e-4, clip 0.2, entropy 0.01, gamma 1, GAE 0.95), common reward and best-May-checkpoint rule; only the episode length changes from 16 to 96 steps. Training uses 115 January–April days and selection 31 May days, all with at least 80 observed slots and linear fills; evaluation uses the same 164 July–December days as the MPC comparison. The policy's previous-interval input is the latest complete raw row. Driving this environment with the 24-hour oracle plan reproduces 283.5063 EUR and the idle cost 3270.2303 EUR. Two complete runs gave bit-identical weights for all 20 policies.

| Family (5 seeds each) | Mean saving (EUR) | Range (EUR) | Seeds idle |
| --- | --- | --- | --- |
| Discrete IPPO | −49.25 | −172.75 to 0.00 | 3 |
| Discrete MAPPO | 0.00 | 0.00 | 5 |
| Continuous IPPO | −122.43 | −128.00 to −115.13 | 0 |
| Continuous MAPPO | −121.36 | −128.29 to −112.48 | 0 |
| *Ridge MPC, 24 h* | *113.55* | | |
| *Perfect foresight, 24 h* | *283.51* | | |

- No learner saves money. Every non-idle policy raises cost for all six households.
- No validation checkpoint was positive. All ten continuous policies selected their first checkpoint (update 10), and validation did not improve afterwards.
- All twelve non-idle policies have the same throughput, 1576.47 kWh (1.602 kWh per battery-day, one full swing out and back). The action trace (`scripts/trace_rl_24h.py`, `action_trace.json`) explains why: no policy conditions on time of day. Eleven request a discharge at every step, so the battery empties between 00:00 and 04:00 at the 0.20 EUR tariff, sits at 0.2 kWh through the 16:00–20:00 peak, and is recharged by the terminal projection after 23:00 at 0.30 EUR. One (discrete IPPO, seed 33) requests a charge at every step and holds a full battery through the peak. In both cases the schedule is set by the state-of-charge bounds and the terminal projection, not by the policy.
- The four-hour limit therefore does not explain the learner result on its own: the longer horizon opens value that Ridge MPC captures but these learners do not. The constant discharge is consistent with myopic credit assignment: a discharge lowers the current bill at once, while the forced recharge that pays it back arrives up to about 90 steps later, beyond what GAE 0.95 propagates. The unchanged 300-update budget may also contribute. This is a diagnosis from the trace, not a tested cause; a one-variable follow-up (for example GAE 1.0, or a terminal state-of-charge value in the reward) would test it.
