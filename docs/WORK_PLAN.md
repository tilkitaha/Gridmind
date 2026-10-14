# GridMind iş planı

14 Ekim 2026. Kurallar için `docs/MANIFESTO.md`. Takvim, danışmanın konu kararını vereceği toplantıya göre yazılmıştır (Hafta 0). Teslim tarihi: **[__ / __ / 2026, fakülte takviminden doldurulacak]**. Sorumlular birer öneridir; ekip ilk toplantıda kesinleştirir.

## Bugünkü durum

| Alan | Durum | Kanıt |
| --- | --- | --- |
| İrlanda topluluk çalışması | Tamamlandı, keşifsel; sayılar kayıtlara bağlı | 4 doğrulama betiği, `results/` |
| Ekim keşifsel bulguları | 24 saatlik dönem, MPC ve RL teşhisi; doğrulanmadı | `docs/EPISODE_LENGTH_EXPLORATION.md` |
| Polonya tasarımı (22 Eylül, danışmana sunulan) | Fiziksel model, MILP ve veri sözleşmesi hazır; 7 deneyin hiçbiri tam değil | `configs/polish_market_protocol.json` |
| ENTSO-E erişimi | Hesap açıldı, API izni istendi (14 Ekim), en geç 3 iş günü | Onay e-postası |
| Konu onayı | **Yok**; danışman bu sunumdan sonra karar verecek | – |
| Fakülte format kuralları | 10 eksik | `docs/THESIS_FORMAT_REVIEW.md` |
| Ekibin projeye hâkimiyeti | Cem ve Taha projenin ayrıntılarını bilmiyor | – |
| CI | Yeşil | GitHub Actions |

## Sorumluluk alanları (öneri)

| Kişi | Alan | Savunmada cevaplayacağı sorular |
| --- | --- | --- |
| Serhat Yiğit | Depo, veri hattı, batarya kontrolü (MPC, RL), yeniden üretilebilirlik | "Sonucu nasıl yeniden üretirim?", "Neden MPC kazandı?" |
| Cem Yılmaz | Tahmin (Ridge; Polonya için naive, LEAR, LightGBM), istatistik (bootstrap) | "Tahmin hatası maliyete nasıl yansıyor?", "Aralık neden sıfırı içeriyor?" |
| Taha Can Tilkioğlu | Piyasa kuralları (SDAC, 15 dakikalık aralık, kapanış saati), blockchain ve imzalı veritabanı uzlaşması, tez metni ve fakülte formatı | "Neden blockchain?", "Polonya pazarı nasıl işliyor?" |

Herkes kendi alanının dışındaki her konuda da en az iki dakika konuşabilmelidir (manifesto, kural 2).

## Faz 0 · Danışman toplantısına kadar

| # | İş | Sorumlu | Bitti kanıtı |
| --- | --- | --- | --- |
| 0.1 | ENTSO-E onayı gelince geliştirme dönemi fiyatlarını (Ekim 2025–Haziran 2026) indir ve ilk yanıtı elle kontrol et | Serhat | `data/polish/prices/provenance.json`, ham XML hash'leri |
| 0.2 | Pilot analizi çalıştır: fiyat farkları, negatif fiyatlar, oracle MILP kârı, naive tahminle yakalanan pay | Serhat, Cem | `results/polish_pilot/results.json` |
| 0.3 | Konu onayı sunumu: seminer yapısı (başlık → içindekiler → amaç ve problem → literatür → çözüm konsepti → kaynakça), artı bir pilot ve bir "mevcut altyapı" slaytı | Taha, Serhat | Sunum bağlantısı, üç kişinin provası |
| 0.4 | Erişim beyanı: H7–H20 ölçümlerini ya da Temmuz–Ağustos 2026 Polonya fiyatlarını gören var mı? | Üçü | Yazılı, tarihli beyan |
| 0.5 | Başlık seçenekleri: APD kaydına uygun 2–3 seçenek | Taha | `docs/THESIS_REVISION_DRAFTS.md` §2 |

**Karar kapısı K0, danışman toplantısı.** Kararlaştırılıp yazılacaklar: konu ve başlık; aşağıdaki yollardan hangisi; hangi deneylerin zorunlu olduğu; teslim tarihi.

- **Yol A · İrlanda tezi:** Tamamlanan çalışma ve Ekim bulguları ek olarak; H7–H20 testi isteğe bağlı.
- **Yol B · Polonya tasarımı:** 22 Eylül tasarımı. İrlanda çalışması yöntem ve altyapı kanıtı olarak bir bölümde kalır.
- **Yol C · İkisi birden:** İrlanda tamamlanmış çalışma ve Polonya'da dar kapsamlı tek bir doğrulama testi (E1 ve E2'nin çekirdeği).

## Faz 1 · Hafta 1–2: ekip bilgi transferi (her yolda zorunlu)

| # | İş | Bitti kanıtı |
| --- | --- | --- |
| 1.1 | Her üye depoyu kendi bilgisayarına kurar ve 4 doğrulama betiği ile testleri çalıştırır | Çıktının ekran görüntüsü ya da logu |
| 1.2 | Okuma sırası: `README` → `SCIENTIFIC_RELEASE` → tez bölüm 1, 3, 4, 6, 9 → `OCTOBER_ADDENDUM_DRAFT` | Her üyenin bir sayfalık kendi özeti |
| 1.3 | Öğretme oturumları: herkes kendi alanını diğer ikisine 20 dakikada anlatır, soru-cevap yapılır | Oturum notları |
| 1.4 | Soru bankası: savunma rehberindeki ve yeni sorular, en az 30 soru; her soru için kim cevaplıyor ve kanıt nerede | `defense/` altında güncel liste |
| 1.5 | Eskimiş bilgileri düzelt: "37 test" (şimdi 54), öğrenci numaraları, `START_HERE` | Diff |

## Faz 2 · Hafta 2–6: seçilen yolun deneyleri

### Yol B ya da C seçilirse: Polonya

| # | İş | Not | Bitti kanıtı |
| --- | --- | --- | --- |
| 2.1 | Özellik verisi: 6.1.B yük tahmini, 6.1.A, 16.1.B&C, 12.1.E; yayın zamanı kontrolüyle | Kapanıştan sonra yayımlanan veri kullanılmaz | Yayın zamanı denetimi |
| 2.2 | Tahmin karşılaştırması: seasonal naive, LEAR, LightGBM; Transformer yalnızca zaman kalırsa | Güçlü basit modelleri yenmeden Transformer anlamsız | Doğrulama dönemi MAE ve pinball |
| 2.3 | Ticaret: kural tabanlı, MILP, PPO | PPO'da 24 saatlik dönem ve uzun kredi ataması (Ekim dersi: λ) | Doğrulama dönemi kârı |
| 2.4 | **Protokolü dondur:** tarihler, modeller, hiperparametreler, birincil sonuç, eşik, bootstrap | H7–H20 protokolü örnek alınır | Commit hash'i ve üç imza |
| 2.5 | Temmuz–Ağustos 2026'yı tek bir çalıştırmayla değerlendir | Sonuç ne çıkarsa yazılır | Kilit ve sonuç dosyası |
| 2.6 | Uzlaşma: 10 sahip senaryosu, imzalı veritabanı ile akıllı sözleşme, gecikme ve gas | Escrow yalnızca zaman kalırsa | Doğruluk ve değiştirme testleri |

### Yol A ya da C seçilirse: İrlanda

| # | İş | Bitti kanıtı |
| --- | --- | --- |
| 2.7 | H7–H20 protokolünü dondur (erişim beyanı, eşik, isteğe bağlı RL kolu) ve tek çalıştırma yap | `results/holdout_24h/` |
| 2.8 | Ekim bulgularını eke ya da bölüme taşı, etiketleriyle birlikte | Tez diff'i |

## Faz 3 · Tez revizyonu (Faz 2 ile paralel)

| # | İş | Kaynak |
| --- | --- | --- |
| 3.1 | Fakülte formatındaki 10 eksiği kapat | `THESIS_FORMAT_REVIEW.md`, `THESIS_REVISION_DRAFTS.md` |
| 3.2 | Başlığı ve object / subject / objective cümlelerini K0 kararına göre yaz | APD |
| 3.3 | GenAI beyanı ve katkı kaydı (Ek B): gerçek dağılım | Manifesto, kural 4 |
| 3.4 | Kaynakça: gerçekten okunan kitaplar ve standartlar | Her kaynak bir kişi tarafından açılmış |
| 3.5 | Her bölümü yazmayan bir üye okur ve onaylar | Okuma onay listesi |

## Faz 4 · Savunma hazırlığı (teslimden 2 hafta önce)

| # | İş | Bitti kanıtı |
| --- | --- | --- |
| 4.1 | Final sunum: seminerin 6 bölümlük yapısı | Sunum |
| 4.2 | İki deneme savunması: biri ekip içinde, biri dışarıdan birine | Notlar ve düzeltmeler |
| 4.3 | Soru bankasındaki her soruyu notsuz cevaplama turu | Kontrol listesi |

## Faz 5 · Teslim

Kapak (fakülte şablonu), öğrenci numaraları, beyanlar, APD yüklemesi, PDF son kontrolü, depoda etiketli bir sürüm (`git tag`).

## Risk listesi

| Risk | Olasılık | Etki | Önlem |
| --- | --- | --- | --- |
| Ekip savunmada projeyi açıklayamaz | Yüksek | Çok yüksek | Faz 1 zorunlu; soru bankası; deneme savunmaları |
| GenAI beyanı ya da katkı kaydı gerçeği yansıtmıyor | Orta | Çok yüksek | Kural 4; danışmanla açık konuşmak |
| Danışman Polonya tasarımında ısrar eder ama süre yetmez | Orta | Yüksek | Yol C: dar kapsamlı tek test; Transformer ve escrow isteğe bağlı |
| ENTSO-E onayı gecikir | Düşük | Orta | Sunum pilot slaytı olmadan da kurulabilir |
| Test penceresi daha önce görülmüş çıkar | Bilinmiyor | Yüksek | Erişim beyanı (0.4); gerekirse Eylül–Ekim 2026'yı test olarak ayır |
| PPO Polonya'da da başarısız olur | Orta | Orta | Negatif sonuç geçerli (kural 7); MILP güçlü bir referans |
| Fiyatlar PLN gelir | Düşük | Düşük | Ayrıştırıcı dönüştürmeden saklar; kur kaynağı kayda geçer |

## Geçmiş projelerden alınan dersler

- **"Tamamlandı" demek için kullanıcı yolundan kanıt gerekir.** Burada: doğrulama betiği ya da testi çalıştırılmadan bir iş bitmiş sayılmaz.
- **Yapay zekânın işaretlediği [x]'e güvenme, kendin doğrula.** Bu depoda testler yerelde geçiyordu, ama CI ilk sürümden beri kırmızıydı ve bunu kimse fark etmemişti.
- **"İnsan bunu yapar mı?" testi.** Burada: "Jüri bunu kabul eder mi?" Ekim'deki 4 saatlik dönem bulgusu tam olarak bu soruyla ortaya çıktı.
- **Hatayı savunma, kökünü düzelt.** RL ajanlarının başarısızlığı yorumlanmadı, davranışları izlendi; mekanizma bu sayede bulundu.
- **Platform farkları sessizce kanıtı bozar.** CRLF satır sonları ve Windows yolları, yeniden üretilebilirliği bozuyordu. Kurallar manifestoda (kural 9).
- **Uzun işlerde ara çıktıyı önce kaydet.** Ekim'deki RL çalıştırmasında eğitim logları bu yüzden kayboldu; artık model dosyasının içinde.
