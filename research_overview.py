"""Portable, aggregate-only presentation of existing research. No fitting or analysis."""
from html import escape
import json
from pathlib import Path

EVIDENCE = Path(__file__).parent / "evidence" / "research"


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
        [t("Kohort ve eşleştirme", "Cohort and linkage"), "24.10.2026", t("Kaynak kayıt ve aile denetimi", "Source-record and family audit")],
        [t("87 ailelik sabit karşılaştırma", "Frozen 87-family comparison"), "24.10.2026", t("Önceki sonuç ve bütün yanlılık kontrolleri korunarak", "Preserving the previous result and all registered bias checks")],
    ]
    source_html = "".join(f"<li>{e(name)} · <code>SHA-256 {e(value['sha256'])}</code></li>" for name, value in d['sources']['files'].items())
    return f"""<article class='research-overview' id='arastirma' aria-labelledby='research-title'>
<p class='ro-muted'>{e(t('Araştırma özeti · 24 Ekim 2026', 'Research overview · 24 October 2026'))}</p>
<h1 id='research-title'>{e(t('Elimizde ne var, neye ihtiyacımız var?', 'What do we have, and what do we need?'))}</h1>
<p class='ro-lead'>{e(t('Hülya hoca için güncel kohort, tek öncelikli biyolojik aday ve onu doğrulamak için gereken veri.', 'The current cohort, the one prioritized biological candidate, and the data needed to validate it.'))}</p>
<span class='ro-badge'>{e(t('Biyolojik sonuç henüz doğrulanmış değil', 'The biological result remains unvalidated'))}</span>
<div class='ro-grid'>{card_html}</div>
<p class='ro-muted'>{e(t('Özgün raporlarla 32 hastanın klinik bağlantısı ve 5 eksik aile kimliği tamamlandı. Kayıtlı 1.988 olası aile grubu, genetik olarak ilişkisiz aile sayısı olarak yorumlanmamalı.', 'Original reports recovered clinical links for 32 patients and five missing family IDs. The 1,988 recorded possible-family groups are not proven genomically unrelated families.'))}</p>
<p class='ro-notice'>{e(t(f'Bu sayılar araştırma arşivine ait. Hesaplayıcının geliştirme ve kuyruk doğrulama kanıtı {number(calculator_n)} hastadan oluşan ayrı bir kohorta dayanıyor.', f'These counts describe the research archive. The calculator’s development and queue-validation evidence uses a separate cohort of {number(calculator_n)} patients.'))}</p>
<section class='ro-result' aria-labelledby='size-title'><h2 id='size-title'>{e(t('87 aile bize ne söylüyor?', 'What do the 87 families tell us?'))}</h2>
<p>{e(t('İki tür BRCA değişikliği karşılaştırıldı: 20 aile ve 67 aile. Dört yeni aile eklendiğinde tahmin neredeyse değişmedi.', 'Two types of BRCA changes were compared: 20 and 67 families. Adding four families barely changed the estimate.'))}</p>
<div class='ro-result-grid'><div><div class='ro-number'>{number(p['effect'],3)}</div><b>{e(t('Düzeltilmiş tümör boyutu oranı', 'Adjusted tumor-size ratio'))}</b><p>{e(t('Oranın 1 olması, fark olmamasıyla uyumludur.', 'A ratio of 1 is compatible with no difference.'))}</p><p><b>{e(t('%95 güven aralığı', '95% confidence interval'))}: {interval}</b></p><p>p = {number(p['empirical_p'],5)} · q = {number(p['q_cumulative'],3)}</p></div><div><h3>{e(t('Neden henüz doğrulanmış değil?', 'Why does it remain unvalidated?'))}</h3>{items(limitations)}</div></div>
</section>
<details><summary>{e(t('Önceki sonuç ve sabit model', 'Previous result and frozen methods'))}</summary>{previous_table}<p>{e(method)}</p><p class='ro-muted'>{e(t('Kaynakta kayıtlı boyut karşılaştırmasıdır; nedensel etki veya kanser riski tahmini değildir. Bu görünüm mevcut sonuçları gösterir, yeni analiz çalıştırmaz.', 'This compares recorded sizes; it is not a causal effect or cancer-risk estimate. This view displays existing results and runs no new analysis.'))}</p></details>
<h2>{e(t('Bugün veriyle ne yapabiliriz?', 'What can the data support today?'))}</h2>
<p>{e(t('Kaynakları izlenebilir kalıtsal kanser başvuru kohortunu, genetik bulguları ve kayıtlı tümör özelliklerini tanımlayabiliriz. Nadir genetik değiştiriciler, sağkalım ve tedavi yanıtı için karşılaştırılabilir genetik negatifler, yeterli taşıyıcı sayısı ve doğrulanmış takip verileri hâlâ eksik.', 'We can describe a source-traceable hereditary-cancer referral cohort, its genetic findings and recorded tumor features. Rare-modifier, survival and treatment-response questions still lack comparable genetic negatives, sufficient carrier groups or verified longitudinal endpoints.'))}</p>
<h2>{e(t('Doğrulama için tam olarak hangi veri gerekiyor?', 'Exactly which data are needed for validation?'))}</h2>
<p>{e(t('Öncelik, aynı tek soruyu bağımsız hasta verisiyle sınamak. Aşağıdaki alanlar olmadan yeni kayıt sayısı tek başına sonucu doğrulamaz.', 'The priority is to test this one frozen question in independent patient data. More records alone cannot validate it without the following information.'))}</p>
<div class='ro-needs'>{need_html}</div>
<h2>{e(t('Arşivde hâlâ açık kalanlar', 'What remains unresolved in the archive'))}</h2>
{table([t('Sayı','Count'),t('Veri açığı','Data gap')],gaps_rows)}
<p class='ro-muted'>{e(t('Tüm 2.259 hasta klasörünün metadata sayımı yapıldı; her ekin yeni okunması tamamlanmış değil. Okunabilir kabul edilmiş rapor bulunmaması, Drive’da hiç rapor olmadığı anlamına gelmez. Eksik veya çelişkili bilgi yok sayılmadı.', 'Metadata for all 2,259 patient folders was counted; not every attachment has been freshly read. No accepted readable report in the cache does not establish that Drive contains no report. Missing/conflicting information remains unknown.'))}</p>
<p>{e(t('Daha geniş taşıyıcı karşılaştırmaları için tam laboratuvar negatifleri ve panel/çağrılabilirlik bilgisi; sağkalım veya yanıt için olay tanımı, başlangıç, tedavi ve olaysız takip bitişi de gerekir.', 'Broader carrier comparisons also need complete laboratory-negative findings and panel/callability information; survival or response studies need event definitions, entry, treatment chronology and event-free censoring.'))}</p>
<details><summary>{e(t('Kanıt, kaynak ve kapsam', 'Evidence, sources and scope'))}</summary>{table([t('Kaynak','Source'),t('Tarih','Date'),t('Kapsam','Scope')],evidence_rows)}<p>{e(t('Yalnız toplu sonuçlar kullanıldı. Önceki 26.035 test/duyarlılık/yanlılık girişimi kaydı korunuyor; uygulamaya bu özet eklenirken yeni analiz yapılmadı.', 'Aggregate results only. The existing 26,035 test/sensitivity/bias-check attempt ledger is retained; adding this overview runs no new analysis.'))}</p><ul>{source_html}</ul></details>
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
    st.download_button(
        "Sunum özetini indir" if tr else "Download the presentation summary",
        build_overview_html(lang, calculator_n).encode("utf-8"),
        file_name=f"BRCA_arastirma_ozeti_{lang.upper()}.html", mime="text/html",
        key="research_overview_download")
    st.caption("İndirilen dosya çevrimdışı açılır; tarayıcıdan yazdırılabilir. Yalnız toplu verileri içerir."
               if tr else "The downloaded file opens offline and can be printed from the browser. Aggregate data only.")
