# Live paper test

Day 9 of 15 · last scored delivery day: **November 3, 2026** · ledger intact (151 entries) · updated November 2, 2026, 3:16 PM (Warsaw)

Every morning, each agent fixes its schedule for the next day before the 12:00 day-ahead gate. Once the prices are published, the schedule is scored. Nothing is sent to the market: this is paper trading with a 1 MW / 2 MWh battery, and profits include a wear cost of €10 per MWh moved. The test started from fresh prices on October 26, 2026, so the agents that need a week of history joined later (see the Days column).

## Standings

| Agent | Days | Total (EUR) | Per day (EUR) | % of bound | Losing days |
|---|---:|---:|---:|---:|---:|
| Perfect foresight (bound) | 9 | 4,077.33 | 453.04 | 100.0 | 0 |
| MILP, yesterday's prices | 9 | 2,026.37 | 225.15 | 49.7 | 1 |
| PPO seed 44, LEAR | 3 | 635.12 | 211.71 | 59.5 | 0 |
| PPO seed 22, LEAR | 3 | 607.94 | 202.65 | 56.9 | 0 |
| PPO seed 55, LEAR | 3 | 596.71 | 198.90 | 55.9 | 0 |
| PPO seed 33, LEAR | 3 | 557.10 | 185.70 | 52.2 | 0 |
| Threshold rule, LEAR | 3 | 485.04 | 161.68 | 45.4 | 0 |
| PPO seed 11, LEAR | 3 | 473.45 | 157.82 | 44.3 | 0 |
| MILP, 7-day average | 3 | 348.95 | 116.32 | 32.7 | 0 |
| MILP, LEAR forecast | 3 | 315.24 | 105.08 | 29.5 | 0 |
| Do nothing | 9 | 0.00 | 0.00 | 0.0 | 0 |

"% of bound" compares an agent with perfect foresight on the same days.

## Cumulative profit

![Cumulative profit by agent](cumulative_profit.png)

## Daily reports

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
