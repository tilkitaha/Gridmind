# Live paper test

Day 15 of 15 · last scored delivery day: **November 9, 2026** · ledger intact (267 entries) · updated November 8, 2026, 2:31 PM (Warsaw)

Every morning, each agent fixes its schedule for the next day before the 12:00 day-ahead gate. Once the prices are published, the schedule is scored. Nothing is sent to the market: this is paper trading with a 1 MW / 2 MWh battery, and profits include a wear cost of €10 per MWh moved. The test started from fresh prices on October 26, 2026, so the agents that need a week of history joined later (see the Days column).

## Standings

| Agent | Days | Total (EUR) | Per day (EUR) | % of bound | Losing days |
|---|---:|---:|---:|---:|---:|
| Perfect foresight (bound) | 15 | 7,918.83 | 527.92 | 100.0 | 0 |
| MILP, yesterday's prices | 15 | 4,666.30 | 311.09 | 58.9 | 1 |
| MILP, LEAR forecast | 9 | 3,168.81 | 352.09 | 64.5 | 0 |
| MILP, 7-day average | 9 | 3,167.79 | 351.98 | 64.5 | 0 |
| PPO seed 11, LEAR | 9 | 3,167.21 | 351.91 | 64.5 | 0 |
| PPO seed 33, LEAR | 9 | 2,475.11 | 275.01 | 50.4 | 0 |
| PPO seed 44, LEAR | 9 | 2,249.19 | 249.91 | 45.8 | 0 |
| Threshold rule, LEAR | 9 | 2,194.33 | 243.81 | 44.7 | 0 |
| PPO seed 55, LEAR | 9 | 2,103.24 | 233.69 | 42.8 | 0 |
| PPO seed 22, LEAR | 9 | 2,047.97 | 227.55 | 41.7 | 0 |
| Do nothing | 15 | 0.00 | 0.00 | 0.0 | 0 |

"% of bound" compares an agent with perfect foresight on the same days.

## Cumulative profit

![Cumulative profit by agent](cumulative_profit.png)

## Daily reports

- [Monday, November 9, 2026](reports/GridMind_daily_report_2026-11-09.pdf)
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
