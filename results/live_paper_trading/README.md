# Live paper test

Day 14 of 15 · last scored delivery day: **November 8, 2026** · ledger intact (256 entries) · updated November 8, 2026, 12:20 PM (Warsaw)

Every morning, each agent fixes its schedule for the next day before the 12:00 day-ahead gate. Once the prices are published, the schedule is scored. Nothing is sent to the market: this is paper trading with a 1 MW / 2 MWh battery, and profits include a wear cost of €10 per MWh moved. The test started from fresh prices on October 26, 2026, so the agents that need a week of history joined later (see the Days column).

## Standings

| Agent | Days | Total (EUR) | Per day (EUR) | % of bound | Losing days |
|---|---:|---:|---:|---:|---:|
| Perfect foresight (bound) | 14 | 6,796.09 | 485.43 | 100.0 | 0 |
| MILP, yesterday's prices | 14 | 3,710.41 | 265.03 | 54.6 | 1 |
| PPO seed 11, LEAR | 8 | 2,192.88 | 274.11 | 57.9 | 0 |
| MILP, LEAR forecast | 8 | 2,185.11 | 273.14 | 57.7 | 0 |
| MILP, 7-day average | 8 | 2,139.56 | 267.45 | 56.5 | 0 |
| PPO seed 33, LEAR | 8 | 1,828.65 | 228.58 | 48.3 | 0 |
| PPO seed 22, LEAR | 8 | 1,677.27 | 209.66 | 44.3 | 0 |
| PPO seed 55, LEAR | 8 | 1,674.20 | 209.28 | 44.2 | 0 |
| PPO seed 44, LEAR | 8 | 1,657.31 | 207.16 | 43.8 | 0 |
| Threshold rule, LEAR | 8 | 1,515.60 | 189.45 | 40.0 | 0 |
| Do nothing | 14 | 0.00 | 0.00 | 0.0 | 0 |

"% of bound" compares an agent with perfect foresight on the same days.

## Cumulative profit

![Cumulative profit by agent](cumulative_profit.png)

## Daily reports

- [Sunday, November 8, 2026](reports/GridMind_daily_report_2026-11-08.pdf)
- [Saturday, November 7, 2026](reports/GridMind_daily_report_2026-11-07.pdf)
- [Friday, November 6, 2026](reports/GridMind_daily_report_2026-11-06.pdf)
- [Thursday, November 5, 2026](reports/GridMind_daily_report_2026-11-05.pdf)
- [Wednesday, November 4, 2026](reports/GridMind_daily_report_2026-11-04.pdf)
- [Tuesday, November 3, 2026](reports/GridMind_daily_report_2026-11-03.pdf)
- [Monday, November 2, 2026](reports/GridMind_daily_report_2026-11-02.pdf)
- [Sunday, November 1, 2026](reports/GridMind_daily_report_2026-11-01.pdf)
- [Saturday, October 31, 2026](reports/GridMind_daily_report_2026-10-31.pdf)
- [Friday, October 30, 2026](reports/GridMind_daily_report_2026-10-30.pdf)
- [Thursday, October 29, 2026](reports/GridMind_daily_report_2026-10-29.pdf)
- [Wednesday, October 28, 2026](reports/GridMind_daily_report_2026-10-28.pdf)
- [Tuesday, October 27, 2026](reports/GridMind_daily_report_2026-10-27.pdf)
- [Monday, October 26, 2026](reports/GridMind_daily_report_2026-10-26.pdf)

## Files

- `ledger.jsonl`: the hash-chained ledger (schedules, scores, hashes). Check it with `python live_task.py status` in GridMind Lab, or recompute each SHA-256 over the entry without its `hash` field.
- `../../data/polish/live/provenance.json`: SHA-256 of every downloaded price file.
- ENTSO-E prices are not in this repository: their license does not allow redistribution. The public reports leave them out; anyone with an ENTSO-E token can download the same days and check them against the hashes.

How the test and the desktop workbench work: [docs/GRIDMIND_LAB.md](../../docs/GRIDMIND_LAB.md).
