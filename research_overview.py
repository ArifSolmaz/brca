"""Portable, aggregate-only presentation of existing research. No fitting or analysis."""
from html import escape
import json
import hashlib
import io
import zipfile
import importlib
from pathlib import Path
import research_report
# Refresh this stateless renderer when Cloud keeps imported modules between deployments.
importlib.reload(research_report)
from research_report import report_html, PDF as REPORT_PDF

EVIDENCE = Path(__file__).parent / "evidence" / "research"


def build_evidence_bundle():
    """Package only explicitly allowlisted, already-published aggregate evidence."""
    root = EVIDENCE.parent.parent
    names = ['evidence/KANIT_REHBERI_TR.md', 'model_full_embedded.json',
             'evidence/research_report_tr.json', 'evidence/research_report_manifest.json',
             'output/pdf/BRCA_arastirma_raporu_TR.pdf',
             'evidence/calculator_prediction_date_audit.json',
             'evidence/calculator_validation_eligibility.json',
             'evidence/rapid_threshold.json', 'evidence/matched_workload.json', 'evidence/sources.json']
    names += ['evidence/research/' + name for name in
              ['cohort_census.json', 'curation_results.json', 'identity_gaps.json',
               'size_results.json', 'previous_size_primary.json', 'sources.json']]
    files = {name.removeprefix('evidence/'): (root / name).read_bytes() for name in names}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr('paket_manifestosu.json', json.dumps(manifest, indent=2))
    return out.getvalue()


def calculator_evidence_note(lang="tr", calculator_n=1295):
    if lang == "tr":
        n = f"{calculator_n:,}".replace(",", ".")
        return (f"Arşiv genişledi; hesaplayıcının modeli henüz yeni kayıtlarla doğrulanmadı. Hesaplayıcı hâlâ özgün {n} hastadan oluşan "
                "geliştirme grubuna dayanıyor; yeni kayıtlarla yeniden eğitilmedi veya yeniden doğrulanmadı. "
                "87 ailedeki henüz doğrulanmamış tümör boyutu bulgusu, olasılık ve test önceliği hesabına dahil değil.")
    return (f"The archive has expanded; the calculator’s evidence has not yet been updated. The calculator still uses "
            f"the original {calculator_n:,}-patient development cohort; it has not been retrained or revalidated with the recovered records. "
            "The unvalidated 87-family tumor-size finding does not contribute to probabilities or test priority.")


def calculator_update_requirements(lang="tr"):
    if lang == "tr":
        return ("Hesaplayıcıyı güncellemek için: uygun hastalarda doğrulanmış BRCA pozitif ve negatif sonuçları, "
                "BRCA sonucu bilinmeden önceki değerlendirmede mevcut model girdileri, hasta/aile tekrarlarının ve eksik verilerin denetimi gerekir. "
                "Önce mevcut model bu verilerde değerlendirilmeli; gerekirse yeniden kalibre edilmeli veya eğitilmeli "
                "ve ayrı doğrulama verisinde sınanmalı. Arşivdeki toplam kayıt sayısı tek başına yeterli değildir.")
    return ("Updating the calculator requires verified BRCA-positive and negative results in eligible patients, "
            "model inputs available at an assessment before the BRCA result, and checks for patient/family duplicates and missing data. "
            "First evaluate the existing model in these records; recalibrate or retrain if needed, then test on separate "
            "validation data. The total archive count alone is insufficient.")


def calculator_provenance_body(lang="tr"):
    """Display the completed, aggregate-only timing audit. Never score patients."""
    d = json.loads((EVIDENCE.parent / 'calculator_prediction_date_audit.json').read_text(encoding='utf-8'))
    s, v = d['summary'], d['validation']
    def t(tr, en): return tr if lang == 'tr' else en
    def e(value): return escape(str(value))
    rows = [
        (t('İncelenen temkinli grup', 'Conservative set reviewed'), t(f"{s['patients']} hasta / {s['recorded_family_groups']} kayıtlı aile grubu", f"{s['patients']} patients / {s['recorded_family_groups']} recorded family groups")),
        (t('Rapor destekli BRCA sonucu', 'Report-supported BRCA outcome'), t(f"{s['positive']} pozitif / {s['negative']} negatif", f"{s['positive']} positive / {s['negative']} negative")),
        (t('Geliştirme aileleriyle bilinen örtüşme', 'Known development-family overlap'), s['known_development_family_overlap']),
        (t('Meme tanı yılı kayıtlı / hâlâ eksik', 'Breast diagnosis year recorded / still missing'), f"{s['original_diagnosis_year_available']} / {s['missing_diagnosis_year_after']}"),
        (t('Bu kontrolde tamamlanan meme tanı yılı', 'Breast diagnosis years recovered in this review'), s['new_diagnosis_years_recovered']),
        (t('Tüm girdileri sonuç öncesinde belgelenmiş hasta', 'Patients with all inputs documented before the result'), s['dated_complete_pre_result_profiles']),
        (t('Doğrulamaya uygun hasta', 'Patients eligible for validation'), s['validation_eligible']),
    ]
    table = '<table><tbody>' + ''.join(f'<tr><td>{e(label)}</td><td>{e(value)}</td></tr>' for label, value in rows) + '</tbody></table>'
    needs = [
        t('Tarihli test öncesi klinik/genetik değerlendirme ve ilk BRCA sonucunun öğrenildiği tarih ya da sıralamayı açıkça gösteren tarih sınırları. O dönemde hesaplayıcının kullanılmış olması gerekmiyor.', 'A dated pre-test clinical/genetics assessment and the first BRCA result/disclosure date, or unambiguous date bounds. Historical use of this calculator is not required.'),
        t('O değerlendirmede bilinen sekiz aile öyküsü girdisini gösteren tarihli soy ağacı, başvuru formu veya izlenebilir özgün kayıt. “Yok” ile “bilinmiyor” ayrı tutulmalı; sonradan öğrenilen aile öyküsü geriye taşınmamalı.', 'A dated pedigree, intake form or auditable original entry showing the eight family-history inputs known at that assessment. Keep absent and unknown distinct; do not backdate later family-history updates.'),
        t('Aynı tarihte bilinen tanı türü, tanı yaşı, bölge, tümör derecesi ve ER/PR/HER2 sonuçları; bunları destekleyen tarihli özgün kayıtlar. İki taraflı meme veya meme–over tanısının hangi tarihte oluştuğu ayrılmalı. Ki67 kayıtlıysa o gün mevcut olduğu belgelenmeli; gerçekten eksikse mevcut eksik-veri kuralı korunur.', 'Dated original records supporting diagnosis type, diagnosis age, region, grade and ER/PR/HER2 results available at that assessment. Establish when bilateral or breast–ovarian diagnoses occurred. A recorded Ki67 needs availability evidence; genuine absence follows the existing missing-value rule.'),
        t('Tanı yılı eksik on hasta için doğru meme tümörüne ait açık tanı tarihi/yılı. Over tanısı, laboratuvar başvurusu veya takip tarihi bunun yerine kullanılamaz. Yalnız tanı yılının tamamlanması diğer tarih eksiklerini çözmez.', 'For the ten missing-year cases, an explicit diagnosis date/year for the correct breast tumor. Ovarian diagnosis, laboratory application and follow-up dates cannot substitute. Recovering diagnosis year alone does not resolve the other timing gaps.'),
        t('Dahil/dışlama ve eksik kayıt listesi ile hasta/aile kimlik bağlantıları korunmalı; geliştirme aileleri dışarıda kalmalı. Bu grupta bir değerlendirme yapılabilse bile aynı arşivden geldiği için bağımsız dış doğrulama sayılmaz.', 'Retain inclusion/exclusion and missing-record logs and patient/family links, keeping development families excluded. Any eventual evaluation of this same-archive group would not constitute independent external validation.'),
    ]
    missing = ''.join(f'<li>{e(item)}</li>' for item in needs)
    yrp, yrn = s['missing_year_positive'], s['missing_year_negative']
    kip, kin = s['ki67_unrecorded_positive'], s['ki67_unrecorded_negative']
    return f"""<section id='hesaplayici-dogrulama' aria-labelledby='provenance-title'>
<h2 id='provenance-title'>{e(t('51 aday neden henüz doğrulamaya uygun değil?', 'Why are none of the 51 candidates eligible yet?'))}</h2>
<p><b>{e(t('Sonuç: 51 adaydan 0’ı tarihli veri kontrolünü geçti. Bu, modelin başarısız olduğu anlamına gelmiyor; güvenilir bir doğrulama için gereken kayıtlar eksik.', 'Result: 0 of 51 candidates passed the dated-provenance checks. This does not mean the model failed; the records needed for a credible validation are missing.'))}</b></p>
{table}
<p>{e(t('Klinik tablolarda değerler var; ancak bunların BRCA sonucu öğrenilmeden önceki hangi değerlendirmede bilindiği gösterilemiyor. Genetik rapor ve laboratuvar tarihleri bu boşluğu doldurmuyor. Tanı yılı bulunan 41 kişi de aynı zamanlama engeline takılıyor. Tanı yılı hesaplayıcının bir girdisi değil; olayların sırasını kontrol etmek için aranıyor.', 'Clinical tables contain values, but do not establish the pre-result assessment at which they were known. Genetic report and laboratory dates do not fill this gap. The 41 with diagnosis years face the same timing barrier. Diagnosis year is not a calculator input; it is needed here to check chronology.'))}</p>
<h3>{e(t('Eksikleri olanları çıkarmak neden çözüm değil?', 'Why not simply exclude incomplete records?'))}</h3>
<p>{e(t(f"Meme tanı yılı {yrp['total']} taşıyıcının {yrp['missing']}’sında, {yrn['total']} negatif hastanın {yrn['missing']}’ünde eksik. Bu hastaları çıkarmak grupları eşit etkilemiyor ve sonuç öncesi veri sorununu çözmüyor. Ki67 de taşıyıcılarda {kip['missing']}/{kip['total']}, negatiflerde {kin['missing']}/{kin['total']} oranında kayıtlı değil. Ki67 için yeni bir tamlık şartı konmadı; mevcut isteğe bağlı alan kuralı korundu.", f"Breast diagnosis year is missing in {yrp['missing']}/{yrp['total']} carriers versus {yrn['missing']}/{yrn['total']} non-carriers. Excluding them selects the groups unevenly and does not resolve pre-result availability. Ki67 is unrecorded in {kip['missing']}/{kip['total']} carriers versus {kin['missing']}/{kin['total']} non-carriers. No new complete-Ki67 requirement was imposed; the existing optional-input rule was retained."))}</p>
<h3>{e(t('Tam olarak hangi kayıtlar eksik?', 'Exactly which records are missing?'))}</h3><ol>{missing}</ol>
<details><summary>{e(t('Drive’da neler kontrol edildi?', 'What was checked in Drive?'))}</summary>
<p>{e(t(f"{s['patient_root_folders']} hasta klasörü ve {s['nested_folders']} alt klasörün envanteri; {s['inventoried_files']} dosya kaydı, {s['readable_document_fetches']} belge okuma isteği, {s['patient_workbooks_inspected']} hasta çalışma kitabı ve {s['clinical_source_rows_checked']} kabul edilmiş klinik kaynak satırı kontrol edildi. Bunlar benzersiz hasta sayıları değildir. Eski iki 2018 dosyasındaki {s['older_identifier_free_rows']:,} satırda eşleştirmeye uygun kimlik ve tanı tarihi yok; benzer tümör özellikleriyle hasta eşleştirilmedi. İki over tanı tarihi meme tanı tarihi olarak aktarılmadı.", f"The inventory covered {s['patient_root_folders']} patient folders and {s['nested_folders']} nested folders: {s['inventoried_files']} file entries, {s['readable_document_fetches']} document fetches, {s['patient_workbooks_inspected']} patient workbooks and {s['clinical_source_rows_checked']} accepted clinical-source rows were checked. These are not unique-patient counts. Two older 2018 files contain {s['older_identifier_free_rows']:,} rows without usable identifiers or diagnosis dates; tumor-feature similarity was not used for linkage. Two ovarian diagnosis dates were not transferred to breast tumors."))}</p>
<p>{e(t('Hasta bazındaki kaynak ve eksik kayıt listeleri özel araştırma dosyasında tutuluyor; bu ekranda hasta kimliği veya özgün rapor gösterilmiyor. Kayıtlı aile ayrılığı, belgelenmemiş akrabalığı dışlamaz.', 'Patient-level source and missing-record lists remain in the private research archive; this screen contains no patient identities or original reports. Recorded-family separation cannot exclude undocumented kinship.'))}</p>
<p class='ro-muted'>{e(t('Tamamlanmış denetim · 24 Ekim 2026 · Yalnız Drive · Sabit model', 'Completed audit · 24 October 2026 · Drive only · Frozen model'))}</p>
</details>
<p><b>{e(t(f"{v['prediction_calls']} yeni tahmin, {v['fit_calls']} model eğitimi, {v['new_hypotheses']} yeni biyolojik test. AUC, Brier skoru, kalibrasyon ve eşik performansı hesaplanamadı; bunlar sıfır performans sonucu değildir. Hesaplayıcı, katsayıları ve eşikleri değişmedi.", f"{v['prediction_calls']} new predictions, {v['fit_calls']} model fits and {v['new_hypotheses']} new biological tests. AUC, Brier score, calibration and threshold performance are not estimable; these are not zero performance results. The calculator, coefficients and thresholds are unchanged."))}</b></p>
</section>"""


def calculator_audit_body(lang="tr", include_provenance=True):
    """Present the source-record eligibility audit, never fit or score a model."""
    d=json.loads((EVIDENCE.parent/'calculator_validation_eligibility.json').read_text(encoding='utf-8'))
    def t(tr,en):return tr if lang=='tr' else en
    rows=[
        (t('Özgün modelde olmayan, klinik bağlantısı kabul edilmiş hastalar','Linked patients outside the original model'),d['linked_outside_training_patients']),
        (t('Geliştirme aileleriyle örtüştüğü için dışlanan','Excluded for development-family overlap'),d['excluded_training_family_overlap']),
        (t('Uygun meme/over klinik kaydı olmadığı için dışlanan','Excluded without an eligible breast/ovarian record'),d['excluded_no_eligible_cancer_record']),
        (t('Kalan adaylar','Remaining candidates'),t('185 hasta / 184 kayıtlı aile grubu','185 patients / 184 recorded family groups')),
        (t('Temel model girdileri tam aile temsilcisi','Family representatives with complete core inputs'),d['complete_core_input_families']),
        (t('Arşiv sınıflamalarıyla rapor destekli adaylar','Report-supported candidates using archived classifications'),t('91: 14 pozitif / 77 negatif','91: 14 positive / 77 negative')),
        (t('Eski VUS sınıflamasına dayanmayan daha temkinli grup','More conservative set without historical-VUS reliance'),t('51: 14 pozitif / 37 negatif','51: 14 positive / 37 negative')),
    ]
    table=''.join(f'<tr><td>{escape(label)}</td><td>{escape(str(value))}</td></tr>' for label,value in rows)
    return (calculator_provenance_body(lang) if include_provenance else '') + f"""<p><b>{escape(t('Hesaplayıcı güncelleme denetimi · 24 Ekim 2026','Calculator update eligibility audit · 24 October 2026'))}</b></p>
<table><tbody>{table}</tbody></table>
<p>{escape(t('Yeni eşleşen 32 hastanın 29’u zaten özgün geliştirme grubundaydı. Bu nedenle 32 yeni doğrulama hastası sayılmıyor. Aile başına temsilci, girdi ve sonuç tamlığına bakılmadan seçildi; önceki tartışmalı aile çifti tek grup tutuldu. Kayıtlı aile ayrılığı, genetik olarak ilişkisizliği kanıtlamaz.', 'Of 32 newly linked patients, 29 were already in development; they are not 32 new validation patients. One representative per family was selected before input/outcome completeness, preserving the earlier conservative family merge. Recorded-family separation is not proof of genomic unrelatedness.'))}</p>
<p>{escape(t('53 alel/sınıflama eşleştirmesi çözüldü; 42 hasta diğer rapor kontrollerini de geçerek önceki 49 adaya eklendi. 40 kişinin dahil edilmesi, Trujillano ve arkadaşlarının 2015 tarihli çalışmasının (Tablo 2, s. 166) BRCA2 NM_000059.3:c.7008-62A>G / rs76584943 için verdiği “Uncertain” bilgisine dayanıyor. Bu tarihsel VUS bilgisi benign veya güncel klinik sınıflama olarak sunulmadı. Bu bilgiye dayanmadan aday sayısı 51’dir.', 'All 53 allele/classification mappings were reconciled; 42 patients passed the other report checks and joined the previous 49. Inclusion of 40 relies on Trujillano et al. (2015, Table 2, p. 166), listing BRCA2 NM_000059.3:c.7008-62A>G / rs76584943 as Uncertain. This is historical VUS evidence, not a benign or current clinical classification. Without relying on it, the candidate count is 51.'))}</p>
<p>{escape(t('Makale kaynağı: ', 'Article reference: '))}<a href="https://doi.org/10.1016/j.jmoldx.2014.11.004" target="_blank" rel="noopener noreferrer">Trujillano et al. Next-Generation Sequencing of the BRCA1 and BRCA2 Genes for the Genetic Diagnostics of Hereditary Breast and/or Ovarian Cancer. J Mol Diagn. 2015;17(2):162-170.</a> {escape(t('Tablo 2, s. 166. Tarihsel sınıflamadır; güncel klinik sınıflama iddiası değildir.', 'Table 2, p. 166. A historical classification, not a claim of current clinical classification.'))}</p>
<p><b>{escape(t('91 kişi geniş arşiv aday havuzudur; bunlar doğrulamaya uygun hasta sayısı değildir.','The 91 form the wider archival candidate pool, not the validation-eligible patient count.'))}</b> {escape(t('Hepsi meme kanseri hastasıdır; over grubunu doğrulamaz. Bu geniş havuzdaki 20 kişide tanı yılı, 59 kişide isteğe bağlı Ki67 eksik; taşıyıcı sayısı 14. Ayrıntılı tarih kontrolü yapılan 51 kişilik daha temkinli grupta uygun hasta sayısı sıfırdır.', 'All have breast cancer; they cannot validate the ovarian subgroup. Within this wider pool, 20 lack diagnosis year and 59 lack optional Ki67; there are 14 carriers. The detailed timing review of the conservative 51 found zero eligible patients.'))}</p>
<p>{escape(t('73 aile temsilcisinde en az bir temel girdi eksik/çelişkili: yaş 8, tanı grubu 1, grade 36, bölge 18, TNBC 36, aile öyküsü 4. Alan sayıları örtüşür. Girdileri tam 20 kişide kalan ilk engeller: 5 dışlanmış artifakt çağrısı için sonuç/kalite değerlendirmesi, 8 her iki genin dizileme kapsamının teyidi, 5 her iki genin kopya sayısı sonucu, 2 okunabilir imzalı özgün rapor. Artifaktlar benign sayılmadı.', 'Seventy-three representatives still lack a core input: age 8, diagnosis group 1, grade 36, region 18, TNBC 36, family history 4; field counts overlap. Twenty core-complete patients remain blocked: five excluded-artifact call/QC adjudications, eight both-gene sequencing-scope confirmations, five both-gene copy-number results and two interpretable signed original reports. Artifacts were not relabelled benign.'))}</p>
<p>{escape(t('77 negatif aday yalnız çağrı tablosunda varyant bulunmamasına dayanmıyor: özgün rapor alelleri kaynak sınıflamalarla eşleşiyor ve her iki genin kopya sayısı normal. Tam laboratuvar kapsamı/kalitesi ve 40 kişide tarihli güncel sınıflama onayı ayrıca gerekli.', 'The 77 negative candidates have original-report alleles mapped to source classifications and explicit normal copy numbers in both genes, rather than mere absence of a positive call. Full laboratory scope/QC and dated current classification sign-off for the 40 remain necessary.'))}</p>
<p>{escape(t('Seçim yanlılığı: 26 belgeli taşıyıcının 14’ü ve 158 kayıtlı negatifin 77’si aday grupta. Bu grubun taşıyıcılık oranıyla doğrudan yeniden kalibrasyon yapılmadı. Sonraki adım: tarihli girdileri, sınıflama onayını, test kapsamını ve dahil/dışlama kayıtlarını tamamlamak; sabit modeli değerlendirmek; gerekiyorsa ayrı doğrulama verisi ayırarak güncellemek. Yeni performans hesabı, model eğitimi veya eşik değişikliği yapılmadı.', 'Selection remains: 14 of 26 documented carriers and 77 of 158 registry-negative patients enter the candidate set. Its carrier fraction was not used for recalibration. Next: verify dated inputs, classification sign-off, assay scope and inclusion/exclusion logs; evaluate the frozen model; update if needed while reserving separate validation data. No new performance estimates, fitting or threshold changes were run.'))}</p>"""


def snapshot():
    def read(name):
        return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
    result = read("size_results.json")
    return dict(cohort=read("cohort_census.json"), gaps=read("identity_gaps.json"),
                curation=read("curation_results.json"), result=result,
                primary=next(r for r in result["primary"] if r["group"] == "pooled"),
                previous=read("previous_size_primary.json"), sources=read("sources.json"))


STYLE = """
.research-overview{--ri:#1b2128;--rm:#4c5966;--rl:#d9dee3;color:var(--ri);font-family:system-ui,-apple-system,sans-serif;line-height:1.6;margin:22px auto;max-width:1080px}
.research-overview *{box-sizing:border-box}.research-overview h1{font-size:38px;line-height:1.15;letter-spacing:-.035em;margin:14px 0}
.research-overview h2{font-size:26px;line-height:1.25;letter-spacing:-.025em;margin:34px 0 14px}.research-overview h3{font-size:18px;margin:0 0 6px}
.research-overview p{margin:8px 0 12px}.research-overview .ro-muted{color:var(--rm);font-size:14px}.research-overview .ro-lead{font-size:18px;max-width:850px}
.research-overview .ro-badge{display:inline-block;border:1px solid #d8b56d;background:#fff5df;color:#68470d;border-radius:30px;font-size:14px;padding:5px 12px;font-weight:600}
.research-overview .ro-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:22px 0 12px}
.research-overview .ro-card,.research-overview .ro-need{border:1px solid var(--rl);border-radius:14px;background:white;padding:19px}
.research-overview .ro-number{font-size:32px;font-weight:700;letter-spacing:-.03em;font-variant-numeric:tabular-nums;line-height:1.2}
.research-overview .ro-label{font-weight:650;margin:8px 0 3px}.research-overview .ro-card p{font-size:13px;color:var(--rm);margin:0}
.research-overview .ro-result{border:1px solid #dac48e;background:#fffbf2;border-radius:18px;padding:24px;margin-top:28px}
.research-overview .ro-result h2{margin:0 0 12px}.research-overview .ro-result .ro-number{font-size:44px}
.research-overview .ro-result-grid{display:grid;grid-template-columns:1fr 1.7fr;gap:22px;align-items:start}
.research-overview .ro-result ul{padding-left:22px;margin:8px 0}.research-overview li{margin:5px 0}
.research-overview .ro-notice{border-left:3px solid #8c7fc0;padding:3px 0 3px 16px;margin:18px 0;color:var(--rm)}
.research-overview .ro-needs{display:grid;grid-template-columns:1fr 1fr;gap:12px}.research-overview .ro-need p{margin:4px 0 0;font-size:15px}
.research-overview .ro-table-wrap{overflow-x:auto;margin:12px 0}.research-overview table{width:100%;border-collapse:collapse;font-size:14px;background:white}
.research-overview th,.research-overview td{text-align:left;padding:12px;border-bottom:1px solid var(--rl);vertical-align:top}.research-overview th{font-weight:650;background:#f0edf9}
.research-overview details{border:1px solid var(--rl);background:white;border-radius:12px;padding:14px 18px;margin:16px 0}.research-overview summary{cursor:pointer;font-weight:650}
.research-overview code{font-size:12px;overflow-wrap:anywhere}.research-overview .ro-foot{margin-top:30px;border-top:1px solid var(--rl);padding-top:14px;color:var(--rm);font-size:13px}
@media(max-width:760px){.research-overview h1{font-size:29px}.research-overview h2{font-size:23px}.research-overview .ro-grid{grid-template-columns:1fr 1fr}.research-overview .ro-card{padding:14px}.research-overview .ro-number{font-size:27px}.research-overview .ro-result-grid,.research-overview .ro-needs{grid-template-columns:1fr}.research-overview .ro-result{padding:18px}}
@media print{.research-overview{margin:0;max-width:none}.research-overview .ro-card,.research-overview .ro-need,.research-overview .ro-result{break-inside:avoid}.research-overview details>*{display:block!important}.research-overview details summary{display:none!important}.research-overview h2{break-after:avoid}}
"""


def overview_article(lang="tr", calculator_n=1295):
    d = snapshot()
    c, p, old, gaps = d["cohort"], d["primary"], d["previous"], d["gaps"]
    tr = lang == "tr"
    def t(turkish, english):
        return turkish if tr else english
    def number(value, decimals=0):
        text = f"{value:,.{decimals}f}"
        return text.replace(",", "X").replace(".", ",").replace("X", ".") if tr else text
    def e(value):
        return escape(str(value))
    def items(values):
        return "<ul>" + "".join(f"<li>{e(v)}</li>" for v in values) + "</ul>"
    def table(headers, rows):
        return "<div class='ro-table-wrap'><table><thead><tr>" + "".join(f"<th scope='col'>{e(v)}</th>" for v in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in row) + "</tr>" for row in rows) + "</tbody></table></div>"
    cards = [
        (c["operational_genetic_patient_entities"], t("Genetik hasta kimliği", "Genetic patient identities"), t("Kayıtlı kimlikler; tüm arşivin kesin benzersiz kişi sayısı değil.", "Established identities; not a certified archive-wide unique-patient count.")),
        (c["strict_clinical_linked_genetic_people"], t("Klinik kaydı eşleşen", "With accepted clinical links"), t("Son eşleştirmede 32 hasta eklendi.", "32 patients gained accepted clinical links.")),
        (c["confirmed_BRCA_female_breast_family_representatives"], t("BRCA aile temsilcisi", "BRCA family representatives"), t("152 kadın meme kanseri hastasından; aile bağlantıları korunarak.", "From 152 female breast-cancer patients, preserving possible relatedness.")),
        (p["n"], t("Boyut karşılaştırmasında", "In the size comparison"), t("İki varyant sınıfı, boyut, yaş ve yıl bilgisi tam olan aileler.", "Families complete for variant class, size, age and diagnosis year.")),
    ]
    card_html = "".join(f"<div class='ro-card'><div class='ro-number'>{number(n)}</div><div class='ro-label'>{e(label)}</div><p>{e(note)}</p></div>" for n, label, note in cards)
    interval = f"{number(p['lo'], 4)}–{number(p['hi'], 4)}"
    limitations = [
        t("Güven aralığı 1'i de içeriyor; fark olmaması hâlâ mümkün.", "The interval includes 1; no difference remains compatible with the data."),
        t("Geçmiş testleri içeren çoklu-test düzeltmesinden sonra sonuç anlamlı değil.", "The result is not significant after correction including the historical testing ledger."),
        t("Basit düzeltmede p=0,089; eşleştirmede yalnız 6 çift var, gereken en az 10 çift yok.", "Simpler adjustment gives p=0.089; matching yields six pairs, below the frozen minimum of ten."),
        t("Yeni kayıtlar aynı arşivden geldi; bağımsız doğrulama değiller.", "Recovered records belong to the same archive; they are not independent validation."),
    ]
    needs = [
        (t("1 · Bağımsız hastalar ve aileler", "1 · Independent patients and families"), t("Mevcut keşif arşiviyle örtüşmeyen hasta/aile kimlikleri; tekrar örnek kontrolü, merkez, başvuru ölçütleri ve dahil edilme tarihleri. Verisi eksik uygun hastalar da listede kalmalı.", "Patient/family IDs that do not overlap the discovery archive; duplicate-specimen checks, center, referral criteria and recruitment dates. Keep eligible patients with missing measurements in the inclusion log.")),
        (t("2 · Özgün genetik rapor", "2 · Original genetic reports"), t("BRCA geni, HGVS ve transkript, varyant sınıfı, P/LP sınıflaması ve tarihi, test yöntemi ve laboratuvar kaynağı. Aynı iki varyant sınıfı önceden belirlenen kuralla karşılaştırılmalı.", "BRCA gene, HGVS/transcript, variant class, P/LP classification and date, assay and laboratory source. Use the same two variant classes under the frozen eligibility rules.")),
        (t("3 · Hangi tümörün ölçüldüğü", "3 · A clearly identified index tumor"), t("Meme tanısı, tümör kimliği ve tarafı, ilk/ikinci primer ayrımı, invaziv/in situ durumu ve gerçek tanı tarihi. İki taraflı veya ikinci tümörler ayrı kaydedilmeli.", "Breast diagnosis, tumor ID and laterality, first/second-primary status, invasive/in-situ status and actual diagnosis date. Record bilateral and second tumors separately.")),
        (t("4 · Tedavi öncesi boyut ve zamanlama", "4 · Pretreatment size and timing"), t("En büyük tümör çapı, birimi, ölçüm tarihi ve yöntemi, özgün patoloji/görüntüleme kaynağı; neoadjuvan tedavi başlangıcı ve ameliyat tarihi. Tedavi sonrası kalan tümör boyutu ayrıca işaretlenmeli.", "Maximum tumor diameter, unit, measurement date/method and original pathology/imaging source; neoadjuvant treatment start and surgery date. Mark post-treatment residual measurements separately.")),
        (t("5 · Aynı düzeltme değişkenleri", "5 · The same adjustment variables"), t("Tanı yaşı ve yılı, bildirilen köken, bölge ve genetik test kaynağı; her alanın belgesi ve eksik/çelişkili olma nedeni. Bilinmeyen bilgi, yok kabul edilmemeli.", "Diagnosis age/year, reported ancestry, region and genotype source, with provenance and missing/conflicting-data reasons. Unknown information must not become an absent finding.")),
        (t("6 · Önceden sabitlenmiş doğrulama planı", "6 · A frozen independent-validation plan"), t("Tek birincil karşılaştırma; aile temsilcisi sonuç görülmeden seçilmeli. Klinik olarak anlamlı fark ve örneklem hedefi bağımsız tasarıma göre önceden belirlenmeli; uygun hastaların seçilme ve dışlanma nedenleri tutulmalı.", "One primary comparison; select family representatives before outcomes are examined. Prespecify a clinically meaningful effect and recruitment target for the independent design; retain inclusion/exclusion reasons.")),
    ]
    need_html = "".join(f"<div class='ro-need'><h3>{e(title)}</h3><p>{e(body)}</p></div>" for title, body in needs)
    gaps_rows = [
        [number(c['operational_genetic_patient_entities'] - c['strict_clinical_linked_genetic_people']), t("Genetik hastada kabul edilmiş klinik bağlantı yok", "Genetic patients without accepted clinical links")],
        [number(gaps['components_with_single_genetic_BR_candidate']), t("Aday klinik bileşeni çözülemedi; bunlar kesin yeni hastalar değil", "Unresolved candidate clinical components; not confirmed additional patients")],
        [number(c['family_status']['missing']), t("Aile kimliği eksik", "Missing family identifiers")],
        [number(c['family_status']['conflicting']), t("Aile kimliği çelişkili", "Conflicting family identifiers")],
    ]
    previous_table = table(
        [t("Sabit birincil sonuç", "Frozen primary result"), t("Önceki", "Previous"), t("Güncel", "Current")],
        [[t("Tam aile sayısı", "Complete families"), number(old['n']), number(p['n'])],
         [t("Düzeltilmiş boyut oranı", "Adjusted size ratio"), number(old['effect'],4), number(p['effect'],4)],
         [t("%95 güven aralığı", "95% confidence interval"), f"{number(old['lo'],4)}–{number(old['hi'],4)}", interval],
         ["p", number(old['empirical_p'],5), number(p['empirical_p'],5)],
         [t("Geçmiş testlerle düzeltilmiş q", "Cumulative multiple-testing q"), number(old['q_cumulative'],4), number(p['q_cumulative'],4)]] )
    method = t(
        "Tek karşılaştırma: stop-gain / frameshift. Log tümör boyutu; tanı yaşı/yılı, BRCA geni, bildirilen köken, bölge ve test kaynağıyla aynı sabit model. Aile kümeli belirsizlik; en düşük BR aile temsilcisi bütün sonuç filtrelerinden önce seçildi. Daha önce tartışmalı olan aile çifti tek grup tutuldu. Aynı destek eşikleri ve yanlılık kontrolleri korundu.",
        "One comparison: stop-gain versus frameshift. The same frozen model for log tumor size adjusts for diagnosis age/year, BRCA gene, reported ancestry, region and genotype source. Family-clustered uncertainty; the lowest-BR representative is selected before outcome filtering. The previously disputed family pair remains one group. Support gates and bias checks are unchanged.")
    evidence_rows = [
        [t("Hasta grubu ve eşleştirme", "Cohort and linkage"), "24.10.2026", t("Kaynak kayıt ve aile denetimi", "Source-record and family audit")],
        [t("87 ailelik sabit karşılaştırma", "Frozen 87-family comparison"), "24.10.2026", t("Önceki sonuç ve bütün yanlılık kontrolleri korunarak", "Preserving the previous result and all registered bias checks")],
    ]
    source_html = "".join(f"<li>{e(name)} · <code>SHA-256 {e(value['sha256'])}</code></li>" for name, value in d['sources']['files'].items())
    evidence_map = table(
        [t('Gösterilen bilgi', 'Displayed information'), t('Kaynak ve denetim', 'Source and audit')],
        [[t('2.148 genetik kimlik · 1.445 klinik bağlantı · 143 aile temsilcisi', '2,148 genetic identities · 1,445 clinical links · 143 family representatives'),
          t('Drive kaynaklarının kimlik/aile eşleştirme sayımı · 24.10.2026 · cohort_census.json, curation_results.json, identity_gaps.json', 'Drive identity/family linkage census · 24 Oct 2026 · cohort_census.json, curation_results.json, identity_gaps.json')],
         [t('87 ailelik tümör boyutu karşılaştırması', '87-family tumor-size comparison'),
          t('Önceden sabitlenmiş karşılaştırmanın kayıtlı sonucu · 24.10.2026 · size_results.json. Bağımsız doğrulanmış bulgu değil.', 'Recorded result of the frozen comparison · 24 Oct 2026 · size_results.json. Not an independently validated finding.')],
         [t('51 aday · 41 tanı yılı kayıtlı / 10 eksik · 0 uygun hasta', '51 candidates · 41 diagnosis years recorded / 10 missing · 0 eligible'),
          t('Tamamlanmış Drive zamanlama denetimi · 24.10.2026 · calculator_prediction_date_audit.json. Performans testi yapılamadı.', 'Completed Drive timing audit · 24 Oct 2026 · calculator_prediction_date_audit.json. Performance evaluation was not possible.')],
         [t('Hesaplayıcı: 1.295 hasta / 167 taşıyıcı', 'Calculator: 1,295 patients / 167 carriers'),
          t('Özgün geliştirme grubunun model paketi · model_full_embedded.json. Genişleyen arşiv bu sayıya eklenmedi.', 'Original development-group model package · model_full_embedded.json. Expanded archive records were not added to this evidence.')],
         [t('Kapasite grafiği', 'Capacity chart'),
          t('04.10.2026 tarihli hızlı test ve aynı iş yükü analizleri · rapid_threshold.json, matched_workload.json. Özgün Drive bağlantıları hesaplayıcıdaki “Kaynaklar ve model kanıtı” bölümünde.', 'Recorded rapid-test and matched-workload analyses dated 4 Oct 2026 · rapid_threshold.json, matched_workload.json. Original Drive links are in the calculator’s Sources and model evidence section.')]])
    return f"""<article class='research-overview' id='arastirma' aria-labelledby='research-title'>
<p class='ro-muted'>{e(t('Araştırma özeti · 24 Ekim 2026', 'Research overview · 24 October 2026'))}</p>
<h1 id='research-title'>{e(t('Elimizde ne var, neye ihtiyacımız var?', 'What do we have, and what do we need?'))}</h1>
<p class='ro-lead'>{e(t('Proje ekibi için güncel hasta grubu, öncelikli biyolojik aday ve onu doğrulamak için gereken veri.', 'The current cohort, the one prioritized biological candidate, and the data needed to validate it.'))}</p>
<span class='ro-badge'>{e(t('Biyolojik sonuç henüz doğrulanmış değil', 'The biological result remains unvalidated'))}</span>
<div class='ro-grid'>{card_html}</div>
<p class='ro-muted'>{e(t('Özgün raporlarla 32 hastanın klinik bağlantısı ve 5 eksik aile kimliği tamamlandı. Kayıtlı 1.988 olası aile grubu, genetik olarak ilişkisiz aile sayısı olarak yorumlanmamalı.', 'Original reports recovered clinical links for 32 patients and five missing family IDs. The 1,988 recorded possible-family groups are not proven genomically unrelated families.'))}</p>
<div class='ro-notice' role='note'><p><b>{e(calculator_evidence_note(lang, calculator_n))}</b></p><p>{e(calculator_update_requirements(lang))}</p></div>
{calculator_provenance_body(lang)}
<details><summary>{e(t('Önceki aday sayımı: 51 temkinli / 91 arşiv adayı', 'Previous candidate census: 51 conservative / 91 archival candidates'))}</summary>{calculator_audit_body(lang, include_provenance=False)}</details>
<section class='ro-result' aria-labelledby='size-title'><h2 id='size-title'>{e(t('87 aile bize ne söylüyor?', 'What do the 87 families tell us?'))}</h2>
<p>{e(t('İki tür BRCA değişikliği karşılaştırıldı: 20 aile ve 67 aile. Dört yeni aile eklendiğinde tahmin neredeyse değişmedi.', 'Two types of BRCA changes were compared: 20 and 67 families. Adding four families barely changed the estimate.'))}</p>
<div class='ro-result-grid'><div><div class='ro-number'>{number(p['effect'],3)}</div><b>{e(t('Düzeltilmiş tümör boyutu oranı', 'Adjusted tumor-size ratio'))}</b><p>{e(t('Oranın 1 olması, fark olmamasıyla uyumludur.', 'A ratio of 1 is compatible with no difference.'))}</p><p><b>{e(t('%95 güven aralığı', '95% confidence interval'))}: {interval}</b></p><p>p = {number(p['empirical_p'],5)} · q = {number(p['q_cumulative'],3)}</p></div><div><h3>{e(t('Neden henüz doğrulanmış değil?', 'Why does it remain unvalidated?'))}</h3>{items(limitations)}</div></div>
</section>
<details><summary>{e(t('Önceki sonuç ve sabit model', 'Previous result and frozen methods'))}</summary>{previous_table}<p>{e(method)}</p><p class='ro-muted'>{e(t('Kaynakta kayıtlı boyut karşılaştırmasıdır; nedensel etki veya kanser riski tahmini değildir. Bu görünüm mevcut sonuçları gösterir, yeni analiz çalıştırmaz.', 'This compares recorded sizes; it is not a causal effect or cancer-risk estimate. This view displays existing results and runs no new analysis.'))}</p></details>
<h2>{e(t('Bugün veriyle ne yapabiliriz?', 'What can the data support today?'))}</h2>
<p>{e(t('Kaynakları izlenebilir kalıtsal kanser başvuru grubunu, genetik bulguları ve kayıtlı tümör özelliklerini tanımlayabiliriz. Nadir genetik değiştiriciler, sağkalım ve tedavi yanıtı için karşılaştırılabilir genetik negatifler, yeterli taşıyıcı sayısı ve doğrulanmış takip verileri hâlâ eksik.', 'We can describe a source-traceable hereditary-cancer referral cohort, its genetic findings and recorded tumor features. Rare-modifier, survival and treatment-response questions still lack comparable genetic negatives, sufficient carrier groups or verified longitudinal endpoints.'))}</p>
<h2>{e(t('Doğrulama için tam olarak hangi veri gerekiyor?', 'Exactly which data are needed for validation?'))}</h2>
<p>{e(t('Öncelik, aynı tek soruyu bağımsız hasta verisiyle sınamak. Aşağıdaki alanlar olmadan yeni kayıt sayısı tek başına sonucu doğrulamaz.', 'The priority is to test this one frozen question in independent patient data. More records alone cannot validate it without the following information.'))}</p>
<div class='ro-needs'>{need_html}</div>
<h2>{e(t('Arşivde hâlâ açık kalanlar', 'What remains unresolved in the archive'))}</h2>
{table([t('Sayı','Count'),t('Veri açığı','Data gap')],gaps_rows)}
<p class='ro-muted'>{e(t('Tüm 2.259 hasta klasörünün metadata sayımı yapıldı; her ekin yeni okunması tamamlanmış değil. Okunabilir kabul edilmiş rapor bulunmaması, Drive’da hiç rapor olmadığı anlamına gelmez. Eksik veya çelişkili bilgi yok sayılmadı.', 'Metadata for all 2,259 patient folders was counted; not every attachment has been freshly read. No accepted readable report in the cache does not establish that Drive contains no report. Missing/conflicting information remains unknown.'))}</p>
<p>{e(t('Daha geniş taşıyıcı karşılaştırmaları için tam laboratuvar negatifleri ve panel/çağrılabilirlik bilgisi; sağkalım veya yanıt için olay tanımı, başlangıç, tedavi ve olaysız takip bitişi de gerekir.', 'Broader carrier comparisons also need complete laboratory-negative findings and panel/callability information; survival or response studies need event definitions, entry, treatment chronology and event-free censoring.'))}</p>
<section id='kanit-rehberi'><h2>{e(t('Bu rakamlar nereden geliyor?', 'Where do these numbers come from?'))}</h2>
{evidence_map}
<p>{e(t('Özgün genetik raporlar Drive’daki bireysel hasta klasörlerinde; klinik kaynaklar Veri1/Veri2 altındaki 2019, 2020 ve 2022 dosyalarında. Hasta bazındaki eşleştirme, kaynak belge/satır ve dahil/dışlama listeleri özel araştırma çalışma dosyalarında tutuluyor. Bu sayfa ve indirilebilir kanıt paketi yalnız toplu sonuçları içerir; özgün hasta raporlarını paylaşmaz.', 'Original genetic reports are in individual patient folders in Drive; clinical sources are the 2019, 2020 and 2022 files under Veri1/Veri2. Patient-level linkage, source-document/row and inclusion/exclusion lists remain in private research working files. This page and its downloadable evidence bundle contain aggregate results only, without original patient reports.'))}</p>
<p>{e(t('Sayfanın altındaki “Toplu kanıt paketini indir” düğmesi, kaynak rehberini ve bu rakamların dayandığı kayıtlı sonuç dosyalarını birlikte verir. Dosya sağlama toplamları sürümü doğrular; bilimsel geçerliliği tek başına kanıtlamaz. Toplu dosyalar, hasta bazındaki özgün kayıt denetiminin yerine geçmez.', 'The Download aggregate evidence bundle button below provides the source guide and recorded result files supporting these numbers. Checksums identify file versions; they do not establish scientific validity. Aggregate files do not replace review of original patient-level records.'))}</p></section>
<details><summary>{e(t('Teknik kaynak sürümleri ve kapsam', 'Technical source versions and scope'))}</summary>{table([t('Kaynak','Source'),t('Tarih','Date'),t('Kapsam','Scope')],evidence_rows)}<p>{e(t('Yalnız toplu sonuçlar kullanıldı. Önceki 26.035 test/duyarlılık/yanlılık girişimi kaydı korunuyor; uygulamaya bu özet eklenirken yeni analiz yapılmadı.', 'Aggregate results only. The existing 26,035 test/sensitivity/bias-check attempt ledger is retained; adding this overview runs no new analysis.'))}</p><ul>{source_html}</ul></details>
<p class='ro-foot'>{e(t('Sunum için mevcut araştırma özeti · 24 Ekim 2026. Bağımsız doğrulama hâlâ gerekli.', 'Presentation of existing research · 24 October 2026. Independent validation is still required.'))}</p>
</article>"""


def build_overview_html(lang="tr", calculator_n=1295):
    title = "BRCA araştırma özeti" if lang == "tr" else "BRCA research overview"
    return (f"<!doctype html><html lang='{escape(lang)}'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title>"
            f"<style>body{{margin:24px;background:#f4f6f8}}{STYLE}</style></head><body>"
            + overview_article(lang, calculator_n) + "</body></html>")


def render_research_overview(lang, calculator_n):
    import streamlit as st
    st.html(f"<style>{STYLE}</style>" + overview_article(lang, calculator_n))
    tr = lang == "tr"
    st.subheader('Araştırma raporu' if tr else 'Research report (Turkish)')
    st.caption('Hasta seçim akışı, sabit yöntemler ve belirsizlikler · Rapor: 25 Ekim 2026 · Mevcut sonuçlar: 24 Ekim 2026. Yeni analiz yapılmadı.'
               if tr else 'Patient selection, frozen methods and uncertainty · Report: 25 October 2026 · Existing results: 24 October 2026. No new analyses.')
    st.download_button(
        'Araştırma raporunu indir (PDF)' if tr else 'Download research report (Turkish PDF)',
        REPORT_PDF.read_bytes(), file_name=REPORT_PDF.name, mime='application/pdf',
        key='research_report_pdf_download')
    with st.expander('Tam araştırma raporunu web sayfasında oku' if tr else 'Read the full research report in Turkish'):
        st.html(f'<style>{STYLE}</style>' + report_html())
    st.download_button(
        "Sunum özetini indir" if tr else "Download the presentation summary",
        build_overview_html(lang, calculator_n).encode("utf-8"),
        file_name=f"BRCA_arastirma_ozeti_{lang.upper()}.html", mime="text/html",
        key="research_overview_download")
    st.download_button(
        "Toplu kanıt paketini indir (ZIP)" if tr else "Download aggregate evidence bundle (ZIP)",
        build_evidence_bundle(), file_name="BRCA_toplu_kanit_paketi.zip", mime="application/zip",
        key="research_evidence_download")
    st.caption("İndirilen dosya çevrimdışı açılır; tarayıcıdan yazdırılabilir. Yalnız toplu verileri içerir."
               if tr else "The downloaded file opens offline and can be printed from the browser. Aggregate data only.")
