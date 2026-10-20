# GridMind research

Engineering Management thesis by Taha Can Tilkioğlu, Cem Yılmaz and Serhat Yiğit. Scientific results recomputed 28 September 2026; manuscript and defense revision 29 September 2026.

The completed empirical study uses six Irish StoreNet households and explicit tariff/battery assumptions. The intended application is a Polish BESS trader; its separate market dataset and empirical validation remain pending. Do not report Irish community savings as Polish arbitrage profit.

## Read the thesis

- [Complete PDF package: 124 pages](defense/GridMind_Complete_PDF_Package.pdf)
- [80-page thesis](defense/GridMind_Thesis_Development.pdf)
- [Scientific release addendum](defense/GridMind_Scientific_Addendum.pdf)
- [Defense slides PDF](defense/GridMind_Defense.pdf) and [editable PowerPoint](defense/GridMind_Defense.pptx)
- [Defense guide](defense/GridMind_Defense_Guide.pdf)
- [Scientific release and decision gates](docs/SCIENTIFIC_RELEASE.md)

Release packaging and descriptive synthesis updated 30 September 2026. The complete PDF includes the addendum, manuscript, slides and guide, with bookmarks. No new independent test was performed.

## Completed evidence

- Ten original IPPO/MAPPO policies and sixty additional training runs, with checkpoint replay and household outcomes.
- A 2-by-2 action/budget study: discrete versus bounded continuous actions at 60 versus 300 updates, two algorithms and five seeds.
- A matched fairness-reward study: two fourteen-input reward arms, two algorithms and five seeds. One fixed penalty weight; no consistent improvement.
- Actual forecast-to-MPC coupling: persistence, previous-day, recursive household Ridge and a non-causal oracle on the same 44 episodes.
- Local Solidity execution and Ed25519-signed SQLite agreement over the same 64 transactions.
- A tested aggregate Polish BESS MILP and strict clock/forecast input validation, with analytical fixtures only.

The 300-update discrete learners all reproduce idle cost, 159.4083 EUR. Persistence MPC costs 159.1604 EUR and Ridge MPC 158.8618 EUR. Ridge MPC leaves two households worse off than idle. All June results are exploratory on reused dates, not confirmation on an untouched test.

## Later temporal evaluation

The frozen-model extension adds 501 episodes from July–December 2020, across 168 retained days (45.38% of candidate blocks). All sixty follow-up policies are evaluated without retraining against five baseline controllers. Idle costs 1947.4997 EUR, persistence MPC 1946.6754 and Ridge MPC 1939.3432. Ridge saves 7.3322 EUR against persistence; all six households gain against idle in aggregate over the retained later period. The primary discrete-IPPO versus persistence seven-day interval includes zero. Strong missingness at midnight and 04:00 limits interpretation. Prior partial access is disclosed, so this remains exploratory.

See [temporal reproduction](docs/LATER_PERIOD_REPRODUCTION.md), `results/later_period/` and the read-only `scripts/verify_later_period.py` audit.

## Episode length (exploratory, October 2026)

Every retained episode lasts four hours and ends at 1 kWh, so the 0.20 EUR night tariff and the 0.42 EUR evening peak never share an episode. On the 501 later-period episodes a perfect-foresight controller saves only 60.20 EUR (3.09% of idle); Ridge MPC captures 13.6% of that bound and the discrete learners 0%. On 164 days with at least 80 of 96 observed slots, 24-hour episodes raise the bound from 95.15 to 283.51 EUR, and causal Ridge MPC saves 113.55 EUR (3.47% of idle) with no household worse off. Persistence MPC loses money at both lengths, and the retained IPPO/MAPPO learners trained on 24-hour episodes do not save money (8 of 20 stay idle, the rest lose 73–173 EUR); with GAE λ = 1.0, chosen post hoc, 5 of 10 continuous learners save 66–101 EUR. No 2020 day has all 96 slots; two gap fills agree within 0.6 EUR. These dates were inspected before, so the result is exploratory.

See [episode-length exploration](docs/EPISODE_LENGTH_EXPLORATION.md), `scripts/explore_episode_length.py`, `scripts/explore_mpc_24h.py`, `scripts/explore_rl_24h.py` and `results/exploratory_*`.

## Held-out household study (draft)

The StoreNet collection has twenty households; this repository uses only H1–H6. A [draft protocol](docs/PROTOCOL_24H_HOLDOUT_DRAFT.md) tests 24-hour Ridge MPC once on H7–H20. Its pipeline (`src/gridmind_research/holdout.py`, `scripts/holdout_*.py`) refuses to download or evaluate held-out households until the protocol is frozen, and locks protocol, data and code hashes between stages. A dry run on H1–H6 (`results/holdout_24h_dry_run/`) reproduces the exploratory numbers exactly. No held-out meter data have been read.

## Profit-oriented forecast selection (October 2026)

An exploratory selector chooses among LEAR and simple forecasts using only their past
28-calendar-day MILP profit. On 166 common development days it averages 183.91 EUR/day,
versus 181.83 for always-LEAR and 183.08 for the seven-day mean profile. These are reused
development outcomes, not independent evidence of improvement. No new forecast is trained.
See [method, limits and reproduction](docs/PROFIT_ORIENTED_FORECASTING.md).

## Reproduction

Python 3.12 and the pinned research dependencies are used. Included StoreNet data and saved results require no API key.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-extension.txt
export PYTHONPATH=src
python -m unittest discover -s research_tests -v
python scripts/verify_defense_evidence.py
python scripts/verify_follow_up.py
python scripts/verify_saved_ledger.py
python scripts/verify_later_period.py
```

Windows PowerShell uses `.venv\Scripts\Activate.ps1` and `$env:PYTHONPATH = "src"`.

CI runs `ruff check .`, `pytest -q` and the research tests on every push, with CPU-only PyTorch.

See [original reproduction](docs/EXTENSION_REPRODUCTION.md), [follow-up reproduction](docs/ABLATION_REPRODUCTION.md), [Polish study boundary](docs/POLISH_MARKET_STUDY.md), and [defense materials](defense/START_HERE.md). Training and forecast reruns replace their own result directories; preserve an unchanged archive first. Verification scripts only read retained records.

## Evidence boundary

The input contains measured consumption and PV, not observed retail bills or market trades. Tariffs, batteries and the single-bus model are assumptions. Forecast/control uses the source clock without an external market-price join. The independent test, daily risk constraint and Polish forecast-conditioned PPO are unfinished. The 52 research tests establish specific invariants; they do not validate profitability or deployment.

## Source

Trivedi, Bahloul, Saif, Patra and Khadem (2024), Comprehensive Dataset on Electrical Load Profiles for Energy Community in Ireland, Scientific Data 11, 621. [Paper](https://doi.org/10.1038/s41597-024-03454-2). [Collection](https://doi.org/10.6084/m9.figshare.c.6829134). The retained source metadata specify CC0; the bundled CSV is a derived subset. `scripts/rebuild_data.py` checks original hashes if public downloads are accessible. The 28 September download succeeded and all six original file hashes matched. Both the original subset and full-year processed input are included; raw file identifiers and CC0 provenance remain in the manifest.

`src/app` is a legacy API scaffold and is not the research controller. Product plans in `docs/archive` are historical. Software retains its MIT license; source data have their own license.
