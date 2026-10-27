# Rakamlar nereden geliyor?

Bu paket, uygulamadaki mevcut toplu sonuçların kaynak rehberidir. 27 Ekim 2026 tarihinde sunuma eklendi; aşağıdaki araştırma denetimleri 24 Ekim 2026 tarihlidir. Paket hazırlanırken yeni hasta analizi, hipotez testi veya model güncellemesi yapılmadı.

| Sayfada görülen bilgi | Dayandığı kayıt / analiz | Paketteki dosya |
|---|---|---|
| 2.148 genetik hasta kimliği, 1.445 kabul edilmiş klinik bağlantı, 143 BRCA aile temsilcisi | Drive'daki klasörler, genetik raporlar ve farklı yıllara ait klinik dosyaların kimlik/aile eşleştirme denetimi | research/cohort_census.json; research/curation_results.json; research/identity_gaps.json |
| 87 aile: 20 ve 67 ailelik iki varyant sınıfı; düzeltilmiş tümör boyutu oranı ve belirsizliği | Önceden sabitlenmiş tek karşılaştırmanın, aile birleştirmesi ve kurtarılan klinik kayıtlarla güncellenmiş sonucu | research/size_results.json; research/previous_size_primary.json |
| 51 temkinli aday, 14 pozitif / 37 negatif; 41 tanı yılı kayıtlı, 10 eksik; 0 uygun hasta | Geliştirme aileleri dışlanmış adaylarda tamamlanmış Drive kaynak ve sonuç öncesi veri zamanlaması denetimi | calculator_prediction_date_audit.json; calculator_validation_eligibility.json |
| Hesaplayıcının 1.295 hastası ve 167 taşıyıcısı | Özgün geliştirme grubunun kayıtlı model paketi; genişleyen arşivle yeniden eğitilmiş bir model değildir | model_full_embedded.json |
| Kapasite grafiğinin paket ve saptanabilir pozitif sayıları | 4 Ekim 2026 tarihli kayıtlı hızlı test ve aynı iş yükü analizleri; yeni hasta veya hizmet süresi ölçümü değildir | rapid_threshold.json; matched_workload.json; sources.json |

## Özgün kanıt nerede?

Özgün genetik raporlar Drive'daki bireysel hasta klasörlerinde; klinik kaynaklar ise Veri1/Veri2 altındaki 2019, 2020 ve 2022 dosyalarında bulunuyor. Tarihli genetik raporun bulunması, bütün klinik girdilerin sonuçtan önce kaydedildiğini tek başına göstermez. Sonuç öncesi klinik kayıtları yeterince belgelenemediği için 51 aday henüz doğrulamaya uygun değildir.

Hasta bazındaki kimlik, aile, kaynak satırı, belge kimliği ve dahil/dışlama listeleri özel araştırma çalışma dosyalarında tutuluyor. Bu paket özgün hasta raporlarını veya hasta kimliklerini içermez. Yetkili proje ekibi, gerektiğinde ilgili özel kaynak listesi üzerinden özgün Drive kaydına kadar iz sürebilir. Bu toplu paket, tek başına hasta bazındaki denetimin yerine geçmez.

## Sınırlar

- 2.148 sayısı kabul edilmiş genetik hasta kimliklerini gösterir; bütün arşivin kesin benzersiz kişi sayısı değildir.
- Farklı yıllardaki klinik satırlar aynı hastayı tekrar içerebilir; satır sayısı yeni hasta sayısı değildir. Kayıtlı aile ayrılığı, belgelenmemiş akrabalığı dışlamaz.
- 87 ailelik bulgu keşifseldir; güven aralığı fark olmamasını içerir ve geçmiş denemeleri kapsayan çoklu test düzeltmesinden sonra anlamlı değildir. Bağımsız hasta verisiyle doğrulanmamıştır; hesaplayıcıya eklenmemiştir.
- 0 uygun hasta, modelin sıfır performans gösterdiği anlamına gelmez. Yeni AUC, kalibrasyon veya eşik performansı hesaplanmamıştır.
- Dosya sağlama toplamları hangi sürümün sunulduğunu doğrular; verinin doğruluğuna veya bilimsel sonucun geçerliliğine tek başına kanıt değildir. ZIP içindeki paket_manifestosu.json paket dosyalarının SHA-256 değerlerini içerir.
