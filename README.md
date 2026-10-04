# BRCA Öncelik Hesaplayıcı · BRCA Priority Calculator

**Araştırma prototipi; klinik karar destek aracı değildir. Research prototype, not a clinical decision-support tool.**

Tanı gününde bilinen bilgilerle BRCA1/2 taşıyıcılık olasılığını hesaplar ve hastayı test kuyruğunda normal, öncelikli ya da acil şeride koyar. Kimse testten çıkarılmaz; yalnız sıra değişir.

Estimates BRCA1/2 carrier probability from what is known on the day of diagnosis and places the patient in the normal, priority or urgent lane of the test queue. Nobody is removed from testing; only the order changes.

![preview](docs/preview.png)

- **Kohort / cohort:** İÜ Onkoloji Enstitüsü, 1.295 hasta (167 taşıyıcı), 1988–2020.
- **Doğrulama / validation:** iç içe çapraz doğrulama; hastaların %48'i öne alınır, taşıyıcıların %78'i kapsanır. 2015'e kadar kurulup 2016–2020'ye uygulanınca %38 / %75.
- **Hesap denetimi / calculation audit:** yayımlanan HTML hesaplayıcı, bağımsız Python ve basılı kâğıt kart 6.635.520 girdi kombinasyonunda aynı sonucu verir. Bu uygulamanın çekirdeği (`brca_core.py`) HTML hesaplayıcıyla 200.000 profilde aynıdır. Özet: `verification.json`, `test_app_results.json`.
- **Veri / data:** depoda hasta verisi yoktur. `model_full_embedded.json` yalnız model katsayılarını ve toplu doğrulama sayılarını içerir; `selftest_vectors_synthetic.json` sentetik referans hastalardır. Uygulama girilen bilgileri kaydetmez.

```
pip install -r requirements.txt
streamlit run app.py
```

Varsayılan karar kuralı A'dır (onaylı v6.2). `?kural=B` adresi, karar bekleyen öneri B'yi önizler.

Prof. Dr. Hülya Yazıcı · Arif Solmaz · İÜ Onkoloji Enstitüsü
