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
- These are upper bounds. A causal controller with 24-hour episodes would capture less; whether learned policies benefit is untested.
- The gain comes almost entirely from the assumed time-of-use spread. A different tariff would change it, and no retail bill was observed.
- Gap filling affects only the 24-hour comparison; the two fills agree to 0.05%. The captured-share table uses the retained 501 episodes without filling.
- All dates were inspected before this analysis. Any follow-up comparison of controllers needs a protocol fixed before access to genuinely unseen data.
