# Savunma soru bankası (ek sorular 25–44)

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
**Answer.** The completed evidence is a measured six-household community in Ireland with simulated batteries. Autonomous trading in the Polish day-ahead market is the intended application: its scheduling model, data contract and clock checks are implemented and tested, but no market data have been scored. Risk appears as a diagnostic CVaR, not an enforced constraint.
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
**Answer.** *[Pilot sonucu gelince doldurulacak: oracle EUR/gün, D-1 ve D-7 naive tahminle yakalanan pay, negatif fiyatlı aralık sayısı.]* This is a development-period description, not a test of any controller.
**Kanıt.** `results/polish_pilot/results.json`. **Sorumlu:** Cem, Serhat

### 35. Why a MILP with a binary variable?
**Answer.** With negative prices, a linear model can profit by charging and discharging at the same time and burning energy in efficiency losses, which is physically impossible. One binary variable per interval forbids simultaneous charge and discharge.
**Kanıt.** `polish_market.optimize_schedule`. **Sorumlu:** Serhat

### 36. Why is July–August 2026 locked?
**Answer.** It is the untouched test window of the proposed design. Download and analysis code refuse any range that touches it until the protocol is frozen, so the final comparison can be run once on data nobody has seen.
**Kanıt.** `polish_pilot.refuse_test_window`. **Sorumlu:** Serhat

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
