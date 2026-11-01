# Live paper test

Day 7 of 15 · last scored delivery day: **November 1, 2026** · ledger intact (109 entries) · updated November 1, 2026, 9:54 AM (Warsaw)

Every morning, each agent fixes its schedule for the next day before the 12:00 day-ahead gate. Once the prices are published, the schedule is scored. Nothing is sent to the market: this is paper trading with a 1 MW / 2 MWh battery, and profits include a wear cost of €10 per MWh moved. The test started from fresh prices on October 26, 2026, so the agents that need a week of history joined later (see the Days column).

## Standings

| Agent | Days | Total (EUR) | Per day (EUR) | % of bound | Losing days |
|---|---:|---:|---:|---:|---:|
| Perfect foresight (bound) | 7 | 3,214.66 | 459.24 | 100.0 | 0 |
| MILP, yesterday's prices | 7 | 1,769.36 | 252.77 | 55.0 | 1 |
| PPO seed 44, LEAR | 1 | 138.13 | 138.13 | 67.2 | 0 |
| PPO seed 55, LEAR | 1 | 130.62 | 130.62 | 63.5 | 0 |
| PPO seed 11, LEAR | 1 | 126.53 | 126.53 | 61.6 | 0 |
| PPO seed 33, LEAR | 1 | 125.32 | 125.32 | 61.0 | 0 |
| PPO seed 22, LEAR | 1 | 120.45 | 120.45 | 58.6 | 0 |
| MILP, LEAR forecast | 1 | 67.07 | 67.07 | 32.6 | 0 |
| MILP, 7-day average | 1 | 40.19 | 40.19 | 19.6 | 0 |
| Threshold rule, LEAR | 1 | 16.39 | 16.39 | 8.0 | 0 |
| Do nothing | 7 | 0.00 | 0.00 | 0.0 | 0 |

"% of bound" compares an agent with perfect foresight on the same days.

## Cumulative profit

![Cumulative profit by agent](cumulative_profit.png)

## Daily reports

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
