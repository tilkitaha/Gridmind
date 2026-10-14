# GridMind çalışma manifestosu

14 Ekim 2026. Bu belge ekibin nasıl çalışacağını tanımlar: Taha Can Tilkioğlu, Cem Yılmaz, Serhat Yiğit. Tezin kendisi değil, onu üretme kurallarıdır. Bir kural işi yavaşlatıyorsa kural değişmez; plan değişir.

## Neden

Bu tez büyük ölçüde yapay zekâ ile yazıldı ve kod da yapay zekâ ile üretildi. Sayılar kayıtlara dayanıyor; 14 Ekim denetiminde tezdeki 297 hassas sayının hepsi sonuç dosyalarına ya da onlardan yapılan basit aritmetiğe bağlandı. Ama jüri sayıları değil bizi sınayacak. Savunmada "yapay zekâ yaptı" bir cevap değildir. Üniversitenin GenAI kuralları (Senato kararı 195/2020–2024) sorumluluğu öğrenciye bırakır.

## On kural

1. **Kanıtsız iddia yok.** Tezde, sunumda ya da e-postada geçen her sayı bir sonuç dosyasına ya da onu üreten komuta bağlanır. Bağlanamayan cümle silinir ya da "varsayım" diye etiketlenir.

2. **Anlamadığını teslim etme.** Her yazar tezdeki her bölümü kendi cümleleriyle anlatabilmeli. Anlatamadığımız bir paragraf ya sadeleşir ya da anlaşılana kadar kalır. Ölçüt: "Jüri bu cümleyi sorarsa üçümüzden herhangi biri iki dakika konuşabilir mi?"

3. **Yapay zekâ taslak yazar, insan onaylar.** Yapay zekânın yazdığı her metin, kod ve "tamamlandı" işareti bir insan tarafından okunur ve doğrulanır. Onun koyduğu [x] işaretine güvenilmez; doğrulama komutu çalıştırılır.

4. **Beyan eksiksiz ve doğru.** Yapay zekâ yardımı GenAI beyanında ve Ek B'deki katkı kaydında gerçeği yansıtır: kim neyi yaptı, neyi yapay zekâ yaptı, kim neyi kontrol etti. Katkı kaydı şişirilmez, küçültülmez.

5. **Etiket kayıt kadar güçlüdür.** Ölçülen, varsayılan, hesaplanan ve önerilen ayrı yazılır. Daha önce bakılmış veri "keşifsel", sonuç görüldükten sonra seçilmiş bir ayar "sonradan (post hoc)" diye yazılır. Keşifsel bir bulgu, doğrulanmış gibi anlatılmaz.

6. **Test verisine dokunulmaz.** Doğrulama verisi (H7–H20 haneleri, Polonya Temmuz–Ağustos 2026) protokol dondurulmadan açılmaz. Kod bunu zorlar; kimse kilidi elle aşmaz. Biri baktıysa bunu söyler, veri "dokunulmamış" sayılmaz.

7. **Negatif sonuç da sonuçtur.** MPC öğrenen ajanı yenerse, veritabanı blockchain'den iyiyse, test sıfırı içerirse bunu yazarız. Sonucu kurtarmak için ayar değiştirmek yoktur. Değiştirirsek bunu kural 5'e göre etiketleriz.

8. **Hatayı savunma, kökünü düzelt.** Bir sayı ya da cümle yanlış çıkarsa nedeni bulunur, düzeltilir ve aynı hatanın başka yerde olup olmadığına bakılır. Yanlış bir sonuç "yorumla" kurtarılmaz.

9. **Yeniden üretilebilirlik bir özelliktir.** Her sonuç, depodaki bir komutla ve kayıtlı girdilerle yeniden üretilir. Kurallar:
   - Satır sonu LF.
   - Hash ile kilitlenmiş dosyalar düzenlenmez.
   - Değişen her takip edilen dosyada manifest güncellenir.
   - Dört doğrulama betiği, testler ve ruff geçmeden commit yok.
   - Windows'ta da Linux'ta da aynı baytlar üretilir.

10. **Kapsam bir karardır.** Konu, başlık ve deney kapsamı danışmanla kararlaştırılır ve yazılır. "Yapsak iyi olur" işleri ancak plana girince yapılır. Başlık, kanıtın gösterdiğinden fazlasını vaat etmez.

## Bitti tanımı

Bir iş ancak şunların hepsi sağlanınca biter:

- [ ] Çıktı depoda ya da paylaşılan bir yerde ve nerede olduğu yazılı
- [ ] Yeniden üretme komutu yazılı ve bir ekip üyesi tarafından çalıştırılmış
- [ ] İlgili testler ve doğrulamalar geçiyor
- [ ] Bulgu ve sınırları bir paragrafta yazılı
- [ ] İşi yapmayan bir ekip üyesi okuyup anladığını onaylamış

## Yapay zekâ ile çalışma

- İstem (prompt) ve çıktı önemliyse kaydedilir. "Nasıl buldunuz?" sorusuna cevap verebilmeliyiz.
- Yapay zekâya ne yapacağı değil, neyi kanıtlaması gerektiği söylenir; her yanıtın sonunda yapılan ve yapılmayan listesi istenir.
- Kod önerisi kabul edilmeden önce testleri çalıştırılır ve diff okunur.
- Kaynak önerileri, gerçekten açılıp okunmadan kaynakçaya girmez.
- Commit mesajında yazar, işi kontrol eden ekip üyesidir.
