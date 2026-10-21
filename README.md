# BRCA Öncelik Hesaplayıcı · BRCA Priority Calculator

**Araştırma prototipi; klinik karar destek aracı değildir. Research prototype, not a clinical decision-support tool.**

Tanı gününde bilinen bilgilerle BRCA1/2 taşıyıcılık olasılığını hesaplar ve hastayı test kuyruğunda normal, öncelikli ya da acil şeride koyar. Varsayılan kullanımda kimse testten çıkarılmaz, yalnız sıra değişir; test azaltma varsayımsal bir araştırma senaryosudur.

Estimates BRCA1/2 carrier probability from what is known on the day of diagnosis and places the patient in the normal, priority or urgent lane of the test queue. By default nobody is removed from testing, only the order changes; test reduction is a hypothetical research scenario.

![preview](docs/preview.png)

- **Kohort / cohort:** geliştirme kohortu, 1.295 hasta (167 taşıyıcı), tanı yılları 1988–2020.
- **Doğrulama / validation:** iç içe çapraz doğrulama; hastaların %48'i öne alınır, taşıyıcıların %78'i kapsanır. 2015'e kadar kurulup 2016–2020'ye uygulanınca %38 / %75.
- **Hesap denetimi / calculation audit:** yayımlanan HTML hesaplayıcı, bağımsız Python ve basılı kâğıt kart 6.635.520 girdi kombinasyonunda aynı sonucu verir. Bu uygulamanın çekirdeği (`brca_core.py`) HTML hesaplayıcıyla 200.000 profilde aynıdır. Özet: `verification.json`, `test_app_results.json`.
- **Veri / data:** depoda hasta verisi yoktur. `model_full_embedded.json` yalnız model katsayılarını ve toplu doğrulama sayılarını içerir; `selftest_vectors_synthetic.json` sentetik referans hastalardır. Uygulama girilen bilgileri kaydetmez.

```
pip install -r requirements.txt
streamlit run app.py
```

Uygulama şifre ister: Streamlit Cloud → App settings → Secrets içine `APP_PASSWORD = "..."` yazın (yerelde `BRCA_APP_PASSWORD` ortam değişkeni ya da `BRCA_NO_PASSWORD=1`). Şifre kodda veya depoda tutulmaz.

Varsayılan karar kuralı A'dır (onaylı v6.2). `?kural=B` adresi, karar bekleyen öneri B'yi önizler.

**Test azaltma araştırma görünümü / Test-reduction research view:** `?mod=azalt` yalnız varsayımsal kurala uygunluğu gösterir; hastaya test atlama talimatı vermez. Tam test planı her iki görünümde korunur. / Shows hypothetical eligibility only; never instructs the patient to skip testing. The full-test plan remains in both views.

`rule_out_policy.json` contains stored exploratory nested-CV and temporal summaries. Its generating script and policy approval record are not included in the available package; the app explicitly discloses this limitation. Approximate intervals from repeated validation are not independent clinical safety guarantees.

**Laboratuvar kapasitesi / Laboratory capacity explorer (v7.1):** Compare A, B and model ranking at matched workload; explore six measured rapid-test triggers with a scatter plot, package-ceiling filter and CSV download. Switch between nested CV (1,295 patients, 167 carriers; five-repeat means) and temporal evaluation (477 patients, 52 carriers). The package ceiling refers to the selected historical cohort, not monthly throughput. Controls never change the patient calculator. Full testing continues for everyone; rapid-test packages are additional tests. The app reports target detectability, not measured time savings or clinical outcomes. No interpolation between tested thresholds or projections to new populations.

Aggregate evidence is copied unchanged from the October 4 Drive analysis into `evidence/rapid_threshold.json` and `evidence/matched_workload.json`. Source links, retrieval date and SHA-256 checksums are in `evidence/sources.json`. No patient-level records are included. B remains a proposal; its displayed queue figures use model-only validation (44% prioritised / 76.5% of carriers), while A uses combined validation (48% / 77.8%). Urgency effects were not measurable in the cohort. A familial P/LP variant suppresses the personal probability headline and one-in-N interpretation because that information is absent from the cohort model.

**Verification:**

```
python -m unittest discover -s tests -v
```

The suite tests source checksums, recorded workload/yield totals, budget boundaries, policy-specific evidence, bilingual app flows, familial-variant output, hypothetical reduction, and independence of capacity controls from patient decisions. `verification.json` and `test_app_results.json` remain historical records of the original calculator; the 47 synthetic startup checks cover probability calculation only. Model coefficients and patient decision rules A/B are unchanged.

Prof. Dr. Hülya Yazıcı · Dr. Öğr. Üyesi Arif Solmaz · İstanbul Sağlık ve Teknoloji Üniversitesi (İSTÜN)
