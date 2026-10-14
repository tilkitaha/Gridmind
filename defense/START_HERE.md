# Complete research release

Start with `GridMind_Complete_PDF_Package.pdf`: 124 bookmarked pages (5-page scientific addendum, 80-page manuscript, 20 defense slides and 19-page guide). The addendum is also available as `GridMind_Scientific_Addendum.pdf`. New descriptive calculations can be regenerated with `python scripts/release_analysis.py` from the project root. This does not run new experiments.

# Güncel tez ve savunma paketi

29 Eylül 2026. Tez, sunum ve prova rehberi aynı deney sonuçlarıyla güncellendi.

- `GridMind_Thesis_Development.docx`: tamamlanan deneyler, yöntem, sonuçlar, sınırlar, Polonya uygulamasına geçiş ve katkı kaydı.
- `GridMind_Defense.pptx`: 12 ana slayt ve 8 teknik ek; İngilizce konuşmacı notları.
- `GridMind_Defense_Guide.docx`: Türkçe prova açıklamaları, İngilizce sunum metni, jüri soruları ve güncel bulgular.
- `../demo/defense_viewer.html`: ilk kontrol deneyinin kayıtlı sonuçlarını gösterir. Yeni ablasyonları veya yeni eğitim çalıştırmasını göstermez; bunlar ilgili CSV dosyalarındadır.

- `GridMind_Thesis_Development.pdf`: aynı tez metninin gözden geçirilen PDF çıktısı.

## Kayıt denetimi

```bash
python scripts/verify_defense_evidence.py
python scripts/verify_follow_up.py
python scripts/verify_saved_ledger.py
python scripts/verify_later_period.py
```

İlk komut standart kütüphaneyle paket özetlerini ve ilk deney kayıtlarını denetler. İkincisi NumPy/Pandas ile 60 yeni model ve tahmin-kontrol kayıtlarını denetler. Üçüncüsü cryptography ile 64 saklanmış imzayı doğrular. Dördüncüsü 65 sonraki dönem kolunun veri/model kimliğini, maliyetlerini ve kapsamasını denetler. Komutlar proje kökünden çalıştırılmalıdır. Bu komutlar yeni eğitim veya EVM deneyi yapmaz.

## Bulguları doğru anlatmak

Toplam 70 model kontrol noktası vardır: 10 ilk deney, 60 kontrollü ek koşu. Yeni koşular aynı Haziran tarihlerini kullanır; bağımsız test değildir. 300 güncellemede ayrık modeller boşta bataryayı taklit eder. Adalet cezası tutarlı iyileşme sağlamaz. Haziran döneminde Ridge MPC maliyeti azaltır ama iki hane kaybeder. Temmuz–Aralık değerlendirmesi 501 bölüm ve 168 günü içerir; bu dönemde Ridge bütün hanelerde toplam kazanç sağlar. Ön erişim ve eksik kapsama açıkça raporlanmıştır; bağımsız teyit iddiası yoktur. Araştırma testi sayısı Eylül sürümünde 37 idi; 14 Ekim 2026 itibarıyla 52’dir (Ekim keşifsel çalışması, H7–H20 hattı ve ENTSO-E testleri eklendi).

Polonya hedefi için zaman doğrulama ve fiziksel kısıtlı MILP hazırlanmıştır. Gerçek Polonya piyasa verisi edinilmemiştir ve bu piyasa için kâr sonucu yoktur. İrlanda hane sonuçları Polonya ticaret performansı diye sunulmamalıdır.

## Teslim öncesi insan incelemesi

Taha Can Tilkioğlu, Cem Yılmaz ve Serhat Yiğit metni ve kendi sorumluluk alanlarını incelemelidir. Cem ve Serhat’ın öğrenci numaraları, gerçek katkı beyanları, resmî kapak ve danışman onayı tamamlanmalıdır. Taslak tarihleri güncel üniversite son tarihi gibi yorumlamayın. Bu paket resmî kabul veya imzalı bağımsız çalışma beyanı değildir.
