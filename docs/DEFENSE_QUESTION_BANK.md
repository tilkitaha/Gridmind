# Savunma soru bankası (ek sorular 25–48)

14 Ekim 2026. `defense/GridMind_Defense_Guide.docx` içindeki 1–24 numaralı jüri sorularının devamıdır. İş planındaki 1.4 maddesi.

**Kullanım:** Cevapları ezberleme. Her sorunun "Kanıt" satırındaki dosyayı aç ve cevabı oradan kendi cümlelerinle kur (manifesto, kural 2). İngilizce cevap jüriye söylenecek çekirdek; Türkçe satır neden öyle olduğunu açıklar. Sorumlu kişi cevabı bilmekle yükümlü; diğer ikisi de en az özünü anlatabilmeli.

**Ekim bulguları teze girerse rehberdeki şu cevaplar güncellenmeli:**

- **8 (Why four-hour episodes?):** 24 saatlik sonucu ekle.
- **12 (Why did learning fail?):** Davranış izi ve λ bulgusunu ekle.
- **14 (Did the training converge?):** λ=1,0'da 5 ajanın doğrulamada pozitif olduğunu ekle.
- **24 (What next?):** H7–H20 ve Polonya testini ekle.

---

## A · Kapsam ve başlık

### 25. Your title promises autonomous trading and risk optimisation. Where are they?
**Answer.** The completed evidence is a measured six-household community in Ireland with simulated batteries. Autonomous trading in the Polish day-ahead market is the intended application: the scheduling model, forecasts and a learned policy have been run on development data (October 2025 to June 2026), but the test on unseen months has not been run. Risk appears as a diagnostic CVaR, not an enforced constraint.
**Türkçe.** Başlık, tamamlanan işten büyük. Bunu saklamıyoruz, ayırıyoruz. Başlık K0 kararına göre değişebilir.
**Kanıt.** `docs/SCIENTIFIC_RELEASE.md` §01; `docs/POLISH_MARKET_STUDY.md`. **Sorumlu:** Taha

### 26. Who is the beneficiary?
**Answer.** In the completed study, the coordinator of a prosumer community who minimises total electricity cost and must not make any household worse off. In the intended application, a price-taking battery trader in the Polish zone who maximises net arbitrage profit. These are different objectives, and the Irish savings are never reported as Polish profit.
**Kanıt.** Tez §1.1. **Sorumlu:** Taha

## B · Ekim keşifsel bulguları (teze girerse)

### 27. What limits the value of the battery in your experiments?
**Answer.** The four-hour episode design. The cheap night tariff (before 07:00) and the evening peak (16:00–20:00) never share a four-hour block, and each block must end at 1 kWh. Perfect foresight therefore saves at most 3.09% of idle cost. With 24-hour episodes on the same days the bound rises from 95.15 to 283.51 EUR, 2.98 times.
**Türkçe.** Ucuz saatte şarj edip pahalı saatte kullanma fırsatı, tasarım gereği yoktu.
**Kanıt.** `docs/EPISODE_LENGTH_EXPLORATION.md`; `results/exploratory_episode_length/`. **Sorumlu:** Serhat

### 28. Why does MPC exploit 24 hours and the learners do not?
**Answer.** Ridge MPC plans with a forecast that has the daily load shape and saves 113.55 EUR (3.47% of idle) with no household worse off. The learners chose one fixed action: 11 of 12 non-idle policies discharge at every step, empty the battery at night and are forced to refill it after 23:00. The action trace shows this behaviour, consistent with credit assignment that does not reach the end-of-day cost.
**Türkçe.** Ajanlar saate göre karar vermeyi öğrenmedi; bataryanın seyrini kısıtlar belirledi.
**Kanıt.** `results/exploratory_rl_24h/action_trace.json`. **Sorumlu:** Serhat

### 29. With GAE λ = 1.0 some learners succeed. Isn't that tuning on the test?
**Answer.** Yes, it is post hoc. λ was changed after we saw the first result on the same days, and we label it that way. It is a diagnosis: one variable changed, five of ten continuous policies learned night charging and peak discharge, and the best saved 100.70 EUR, still below Ridge MPC. Confirming it would need a frozen protocol on unseen data.
**Türkçe.** Bunu açıkça söylemek, gizlemekten çok daha güçlü bir savunmadır (manifesto, kural 5).
**Kanıt.** `results/exploratory_rl_24h_lambda1/`. **Sorumlu:** Serhat

### 30. How do you know your 24-hour environment is correct?
**Answer.** Driving it with the oracle plan reproduces the independently computed 24-hour bound (283.5063 EUR) and the idle cost exactly. Every new pipeline first reproduces retained numbers: the June oracle 153.7614 EUR, and the later-period persistence and Ridge MPC costs. Two complete RL runs gave bit-identical weights.
**Kanıt.** `scripts/explore_*.py`, `research_tests/test_holdout.py`. **Sorumlu:** Serhat

### 31. Your data have gaps. How did you handle them?
**Answer.** No 2020 day has all 96 quarter-hours for the six homes; gaps cluster between 00:00 and 05:00. We kept days with at least 80 observed slots and filled the rest in two different ways, for settlement only; forecasts never see filled values. The two fills change every result by less than 0.6 EUR.
**Kanıt.** `docs/EPISODE_LENGTH_EXPLORATION.md`. **Sorumlu:** Cem

## C · Polonya pazarı

### 32. How does the Polish day-ahead market work?
**Answer.** Poland is part of Single Day-Ahead Coupling (SDAC). Orders for delivery day D close at 12:00 on D-1, and EUPHEMIA clears all zones jointly, producing one price per zone and market time unit. Since 1 October 2025 the unit is 15 minutes, so a normal day has 96 prices; clock-change days have 92 or 100. A small battery trader is a price taker.
**Kanıt.** `docs/POLISH_MARKET_STUDY.md`; `polish_market.delivery_index`, `gate_closure`. **Sorumlu:** Taha

### 33. How do you prevent look-ahead in the Polish study?
**Answer.** A forecast file must carry an issue time strictly before the D-1 12:00 gate, or it is rejected. The schedule is fixed before the realized-price file is read. The naive forecasts in the pilot use only D-1 and D-7 prices, which are published before the gate.
**Kanıt.** `polish_market.validate_day`; `scripts/evaluate_polish_day.py`; `polish_pilot.py`. **Sorumlu:** Cem

### 34. What is the best possible arbitrage profit, and how close do simple forecasts get?
**Answer.** On real Polish prices for October 2025 to June 2026 (273 complete days), a MILP that knows the realized prices earns about 199 EUR per day for the 1 MW / 2 MWh battery, roughly 73,000 EUR per MW-year. Planning with yesterday’s prices captures 63% of that on comparable days but loses money on 52 of 260 days; the remaining 37%, about 73 EUR a day, is what a better forecast and policy can win. Prices were negative in 900 quarter-hours on 59 days. This describes the development period only; the July–August test months were not downloaded.
**Kanıt.** `results/polish_pilot/results.json`. **Sorumlu:** Cem, Serhat

### 35. Why a MILP with a binary variable?
**Answer.** With negative prices, a linear model can profit by charging and discharging at the same time and burning energy in efficiency losses, which is physically impossible. One binary variable per interval forbids simultaneous charge and discharge.
**Kanıt.** `polish_market.optimize_schedule`. **Sorumlu:** Serhat

### 36. Why is July–August 2026 locked?
**Answer.** It is the untouched test window of the proposed design. Download and analysis code refuse any range that touches it until the protocol is frozen, so the final comparison can be run once on data nobody has seen.
**Kanıt.** `polish_pilot.refuse_test_window`; `configs/polish_test_protocol.json`. **Sorumlu:** Serhat

### 45. PPO and the optimiser see the same forecast. Why does PPO earn less?
**Answer.** For a given forecast, the MILP finds the best schedule for the whole day exactly. PPO has to learn that mapping by trial and error from 150 training days. It does learn to trade: it moves about as much energy as the MILP and beats a threshold rule by 47 EUR/day. But it times the trades worse. In June it earns 214 EUR/day against 236 for the MILP; all five seeds are below, with every interval below zero. Longer training helps with diminishing returns: 195, 210 and 214 EUR/day for 300, 1,000 and 2,000 updates.
**Türkçe.** Bu, bilgi değil öğrenme farkı. Aynı bilgiyle optimizer kesin çözüyor; PPO yaklaşıyor. June doğrulama ayı, test değil.
**Kanıt.** `results/polish_rl`, `results/polish_rl_ablation`, `docs/POLISH_MARKET_STUDY.md`. **Sorumlu:** Serhat

### 46. A seven-day average has more error than LEAR but earns the same. Does that undermine your forecasting work?
**Answer.** It shows which yardstick matters. The MILP only needs to know when prices are low and high; error measures the level. LEAR's errors keep the daily shape, so at about the same error size they cost 51 EUR/day where random noise costs 171. We added the seven-day average after seeing the first results, so we label it exploratory, keep LEAR as the forecast fixed in the protocol, and add the average as a secondary comparator. Forecasters are compared by the profit of their schedules.
**Türkçe.** Bunu sonradan bulduk ve saklamıyoruz; sunumdaki eski "daha iyi tahmin daha çok kazandırır" cümlesini bu yüzden düzelttik.
**Kanıt.** `results/polish_profile`, `results/polish_controls`. **Sorumlu:** Cem

### 47. Why not keep tuning PPO until it beats the optimiser?
**Answer.** Every choice made by looking at June makes June less informative. A policy tuned until it wins on the validation month would win there by construction and tell us nothing about new months. So the five checkpoints are fixed now, by file hash, in the test protocol, and the test is run once on months nobody has looked at. If PPO still loses, that is the result.
**Kanıt.** `configs/polish_test_protocol.json`, `docs/PROTOCOL_POLISH_TEST_DRAFT.md`. **Sorumlu:** Serhat

### 48. Where are the Polish raw data?
**Answer.** ENTSO-E puts only the items on its open-data list under CC-BY 4.0. The day-ahead load forecast is on that list; day-ahead prices, actual load and generation are not. So we do not redistribute them. The repository keeps the SHA-256 of every raw response and day file; anyone with a free API token downloads the same data with our fetch scripts and checks it with `verify_polish_data.py`.
**Kanıt.** `data/polish/*/provenance.json`, `scripts/verify_polish_data.py`. **Sorumlu:** Serhat

## D · İstatistik

### 37. What is a circular moving-block bootstrap, and why use it?
**Answer.** Daily costs are serially correlated, so resampling single days would understate uncertainty. We resample blocks of consecutive days, seven by default, wrapping around the end, recompute the statistic each time and take percentiles. Other block lengths are reported as sensitivity.
**Kanıt.** `holdout.block_bootstrap`; `configs/later_period_protocol.json`. **Sorumlu:** Cem

### 38. Your interval includes zero. Does that mean there is no effect?
**Answer.** No. It means the data cannot distinguish the effect from zero. Showing no meaningful difference would need an equivalence test with a pre-stated margin.
**Sorumlu:** Cem

### 39. Five seeds: are they five independent observations?
**Answer.** No. Seeds are repeated realisations of the training algorithm on the same households and dates. They measure algorithmic variability, not population variability, and we report them separately from day-to-day uncertainty.
**Sorumlu:** Cem

## E · Yeniden üretilebilirlik ve bütünlük

### 40. How can someone else reproduce your results?
**Answer.** Clone the repository, install the pinned dependencies, and run four read-only verification scripts plus the tests; continuous integration does this on every change. Result files are identified by SHA-256 in a manifest, and the code that produced the later-period results is hash-locked.
**Kanıt.** `README.md` → Reproduction; `.github/workflows/ci.yml`. **Sorumlu:** Serhat

### 41. What does a hash lock prove?
**Answer.** Identity, not correctness: these exact files produced these exact results. Correctness is argued separately, by tests, physical checks and reproduction.
**Sorumlu:** Serhat

### 42. What did AI do in this thesis, and what did you do?
**Answer.** *[Her yazar kendi gerçek cevabını yazar. Bu cevap başkası ya da yapay zekâ tarafından yazılamaz.]* It must agree with the GenAI declaration (§1.3, Appendix B) and the contribution record.
**Türkçe.** En olası ve en kritik soru. Dürüst ve tutarlı olmalı (manifesto, kural 4). **Sorumlu:** Üçü de

### 43. How do you know AI-generated numbers in the text are right?
**Answer.** We checked every precise number in the manuscript and slides against the result files. All 297 in the manuscript trace either to a result file or to simple arithmetic on one, such as 158.8618 − 153.7614 = 5.1005.
**Kanıt.** 14 Ekim izlenebilirlik kontrolü; `docs/WORK_PLAN.md`. **Sorumlu:** Serhat

### 44. What happens if a meter reports false data?
**Answer.** The ledger cannot know. A signature proves which key signed a record, not that the measurement is true; a smart contract cannot repair a compromised measurement source. That is why we test settlement consistency, not meter truth, and compare the contract with a simpler signed database.
**Kanıt.** `docs/SCIENTIFIC_RELEASE.md` §04. **Sorumlu:** Taha
