"""Aggregate-only laboratory planning view; never changes patient decisions."""
import csv
import io
import json
import math
from pathlib import Path

EVIDENCE = Path(__file__).parent / "evidence"
with (EVIDENCE / "rapid_threshold.json").open() as fh:
    RAPID = json.load(fh)
with (EVIDENCE / "matched_workload.json").open() as fh:
    MATCHED = json.load(fh)

STRATEGIES = (
    ("model>=0.2", "Model ≥ 20%"),
    ("model>=0.25", "Model ≥ 25%"),
    ("model>=0.275", "Model ≥ 27.5%"),
    ("model>=0.3", "Model ≥ 30%"),
    ("card>=5", "Card ≥ 5"),
    ("card>=5 or model>=0.2 (v6.2 urgent lane)", "A: card ≥ 5 or model ≥ 20%"),
)


def rapid_rows(period="cv"):
    """Recorded strategies only; no interpolation, refitting or prevalence scaling."""
    if period not in ("cv", "temporal"):
        raise ValueError("Unknown evaluation period")
    source = RAPID["cv_mean" if period == "cv" else "temporal"]
    n, carriers = (1295, 167) if period == "cv" else (477, 52)
    rows = []
    for key, label in STRATEGIES:
        r = source[key]
        rows.append(dict(key=key, strategy=label, patients=n, carriers=carriers,
                         packages=r["packages"], hits=r["detectable_hits"],
                         detectable=r["of_all_detectable"],
                         # Ratio of displayed totals, not mean of repeat-specific ratios.
                         packages_per_hit=r["packages"] / r["detectable_hits"],
                         unselected_detectable=round(r["of_all_detectable"] - r["detectable_hits"], 10)))
    return rows


def budget_options(period, ceiling):
    """All measured strategies that fit the package ceiling for this cohort."""
    if not math.isfinite(ceiling) or ceiling < 0:
        raise ValueError("Package ceiling must be finite and non-negative")
    return [r for r in rapid_rows(period) if r["packages"] <= ceiling]


def queue_rows(model, period="cv"):
    if period not in ("cv", "temporal"):
        raise ValueError("Unknown evaluation period")
    combined = model["points"]["combined"]
    if period == "cv":
        rows = MATCHED["cv"]["prioritised"]
        n = len(rows)
        count = sum(r["k"] for r in rows) / n
        a = sum(r["combined"] for r in rows) / n
        b = sum(r["model_same_k"] for r in rows) / n
        out = combined["summary_cv"]["model_only"]
        fixed_count = out["prioritised_share"]["mean"] * model["n"]
        fixed_coverage = out["carriers_prioritised"]["mean"]
    else:
        r = MATCHED["temporal"]["prioritised"]
        count, a, b = r["k"], r["combined"], r["model_same_k"]
        out = combined["temporal"]["model_only"]
        fixed_count = out["prioritised_share"] * out["n"]
        fixed_coverage = out["carriers_prioritised"]
    return [dict(policy="A", patients=count, coverage=a),
            dict(policy="B", patients=fixed_count, coverage=fixed_coverage),
            dict(policy="same_workload", patients=count, coverage=b)]


def export_csv(period):
    out = io.StringIO()
    rows = rapid_rows(period)
    writer = csv.DictWriter(out, fieldnames=["evaluation", *rows[0].keys()])
    writer.writeheader()
    writer.writerows(dict(evaluation=period, **r) for r in rows)
    return out.getvalue().encode("utf-8-sig")


def render_capacity_explorer(model, lang):
    import streamlit as st

    tr = lang == "tr"
    def t(turkish, english):
        return turkish if tr else english

    st.html("<div id='kapasite'></div>")
    st.subheader(t("Laboratuvar kapasitesi: iş yükü ve verim", "Laboratory capacity: workload and yield"))
    st.write(t(
        "Aynı hasta grubunda kaç hızlı test paketi kullanılır, kaç taşıyıcıda hızlı test pozitif olabilir? Kuyruk önceliği ve hızlı test seçimi aşağıda ayrı karşılaştırılır. Tam test herkes için devam eder.",
        "How many rapid-test packages are used, and how many carriers have a detectable result? Queue priority and rapid-test selection are compared separately below. Full testing continues for everyone."))
    st.info(t(
        "Araştırma görünümü · Buradaki seçimler yukarıdaki hastanın şeridini veya test planını değiştirmez. Sonuç süresi, maliyet ve ameliyat sonucunda iyileşme ölçülmedi. Hızlı test negatifse taşıyıcılık dışlanmaz.",
        "Research view · These controls do not change the patient's lane or testing plan above. Improvements in turnaround time, cost and surgical outcomes were not measured. A negative rapid test does not rule out a carrier."))
    period = st.radio(t("Kanıt kümesi", "Evidence set"), ["cv", "temporal"], horizontal=True,
                      format_func=lambda x: t("İç içe ÇD · 1.295 hasta", "Nested CV · 1,295 patients") if x == "cv"
                      else t("2016–2020 · 477 hasta", "2016–2020 · 477 patients"), key="capacity_period")
    st.caption(t(
        "ÇD: 5 tekrarın ortalaması; ondalıklı sayılar farklı hastalar değil, tekrar ortalamalarıdır. Zamansal: ≤2015'te kurulup 2016–2020'de sınandı. Aciliyet kutularının ek iş yükü ölçülmedi. Bu aynı merkezin geliştirme kanıtıdır; dış doğrulama değildir.",
        "CV: means over 5 repeats; fractional counts are repeat averages. Temporal: fitted on diagnoses ≤2015, evaluated in 2016–2020. Extra workload from urgency overrides was not measured. This is development evidence from the same centre, not external validation."))

    policies = dict(A=t("A · kart + model", "A · card + model"),
                    B=t("B · model ≥ %10 (öneri)", "B · model ≥ 10% (proposal)"),
                    same_workload=t("Model · A ile aynı iş yükü¹", "Model · same workload as A¹"))
    with st.expander(t("1 · Kuyruk önceliği: kart ne ekliyor?", "1 · Queue priority: what does the card add?"), expanded=True):
        st.dataframe([{
            t("Strateji", "Strategy"): policies[r["policy"]],
            t("Öne alınan hasta", "Patients prioritised"): round(r["patients"], 1),
            t("Taşıyıcı kapsamı (%)", "Carrier coverage (%)"): round(r["coverage"] * 100, 1),
        } for r in queue_rows(model, period)], hide_index=True, width="stretch")
        st.caption(t(
            "¹ En yüksek model skorları A ile aynı sayıda hasta alınana kadar seçildi. Bu bir top-k karşılaştırmasıdır; %10 eşiği veya uygulanacak yeni bir klinik kural değildir. Kart aynı iş yükünde ek üstünlük göstermedi; elle kullanım ve açıklama için değerlidir.",
            "¹ Highest model scores selected until the same number of patients as A is reached. This is a top-k comparison, not the 10% threshold or a new clinical rule. The card showed no added advantage at equal workload; it remains useful for manual use and explanation."))

    rows = rapid_rows(period)
    def label(r):
        return r["strategy"].replace("Card", "Kart").replace("card", "kart").replace(" or ", " veya ") if tr else r["strategy"]
    st.markdown(t("**2 · Hızlı ilk test: BRCA1 MLPA + c.5266dupC**", "**2 · Rapid first test: BRCA1 MLPA + c.5266dupC**"))
    st.caption(t(
        "Paket sayısı tam test sayısı değildir. ‘Saptanabilir pozitif’, seçilen grupta bu dar testin hedefini taşıyan hastadır; doğrulanmış erken rapor veya kazanılan gün değildir.",
        "Package count is not full-test count. A ‘detectable positive’ is a selected carrier with a target covered by this narrow test; it is not a confirmed early report or days saved."))
    selected = st.selectbox(t("Karşılaştırılacak hızlı test stratejisi", "Rapid-test strategy to compare"),
                            list(range(len(rows))), format_func=lambda i: label(rows[i]), key="capacity_strategy")
    chosen, baseline = rows[selected], rows[-1]
    cols = st.columns(3)
    cols[0].metric(t("Hızlı test paketi", "Rapid-test packages"), f"{chosen['packages']:.1f}",
                   f"{chosen['packages'] - baseline['packages']:+.1f}", delta_color="off")
    cols[1].metric(t("Saptanabilir pozitif", "Detectable positives"), f"{chosen['hits']:.1f}",
                   f"{chosen['hits'] - baseline['hits']:+.1f}", delta_color="off")
    cols[2].metric(t("Saptanabilir pozitif / paket", "Detectable positives / package"),
                   f"{100 * chosen['hits'] / chosen['packages']:.1f}%")
    st.caption(t("Farklar A'nın kart/model tetikleyicisine göredir; aciliyet ek yükü dahil değildir.",
                 "Deltas are relative to A's card/model trigger; urgency workload is excluded."))

    chart_rows = [dict(strategy=label(r), packages=r["packages"], hits=r["hits"]) for r in rows]
    st.vega_lite_chart({"data": {"values": chart_rows}, "mark": {"type": "point", "filled": True, "size": 150},
                       "encoding": {
                           "x": {"field": "packages", "type": "quantitative", "title": t("Hızlı test paketi", "Rapid-test packages"), "scale": {"zero": True, "nice": True}, "axis": {"tickCount": 8, "titlePadding": 12}},
                           "y": {"field": "hits", "type": "quantitative", "title": t("Saptanabilir pozitif", "Detectable positives"), "scale": {"zero": True, "nice": True}, "axis": {"tickCount": 6, "titlePadding": 12}},
                           "color": {"field": "strategy", "type": "nominal", "title": t("Strateji", "Strategy"),
                                     "legend": {"orient": "bottom", "columns": 1, "labelLimit": 340}},
                           "tooltip": [{"field": "strategy", "title": t("Strateji", "Strategy")}, {"field": "packages", "format": ".1f"}, {"field": "hits", "format": ".1f"}]
                       },
                       # Streamlit's fitted height includes axes and the six-row legend.
                       # Reserve room for both so the plot is not reduced to a thin strip.
                       "autosize": {"type": "fit", "contains": "padding"},
                       "padding": {"top": 16, "right": 16, "bottom": 16, "left": 16}},
                       width="stretch", height=560)

    table = [{t("Strateji", "Strategy"): label(r),
              t("Paket", "Packages"): round(r["packages"], 1),
              t("Saptanabilir pozitif", "Detectable positives"): round(r["hits"], 1),
              t("Hızlı testle seçilmeyen hedef taşıyıcı", "Target carriers outside rapid selection"): round(r["unselected_detectable"], 1),
              t("Paket / saptanabilir pozitif", "Packages / detectable positive"): round(r["packages_per_hit"], 1)
              } for r in rows]
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption(t(
        f"Bu kümede toplam {chosen['carriers']} BRCA1/2 taşıyıcısının {chosen['detectable']:.0f}'i hızlı testin hedeflerini taşır. Seçilmeyenler tam testte kalır. Paket/pozitif, gösterilen toplamların oranıdır.",
        f"In this set, {chosen['detectable']:.0f} of {chosen['carriers']} BRCA1/2 carriers have a target covered by the rapid test. Unselected patients retain full testing. Packages/positive is the ratio of the displayed totals."))

    budget = st.slider(t("Bu hasta grubu için hızlı test paket tavanı", "Rapid-test package ceiling for this cohort"),
                       min_value=0, max_value=chosen["patients"], value=220 if period == "cv" else 40,
                       key="capacity_budget_" + period)
    options = budget_options(period, budget)
    if options:
        st.write(t("Tavana uyan ölçülmüş seçenekler: ", "Measured options within the ceiling: ") + "; ".join(label(r) for r in options))
    else:
        st.write(t("Ölçülmüş seçeneklerin hiçbiri bu tavana uymuyor. Yeni bir eşik için ayrı analiz gerekir.",
                   "None of the measured options fits this ceiling. A new threshold requires a separate analysis."))
    st.caption(t(
        "Tavan aynı hasta grubuna aittir; aylık kapasite veya yeni hasta sayısına projeksiyon yapılmaz. ÇD ortalamasının tavana uyması her tekrarda veya gerçek hizmette tavana uyacağını garanti etmez. Aradaki eşikler tahmin edilmez.",
        "The ceiling applies to this cohort; there is no projection to monthly capacity or a new patient population. A CV mean below the ceiling does not guarantee that every repeat or real service will fit it. Intermediate thresholds are not estimated."))
    st.download_button(t("Karşılaştırmayı indir (CSV)", "Download comparison (CSV)"), export_csv(period),
                       file_name=f"BRCA_capacity_{period}.csv", mime="text/csv", key="capacity_csv")
    with st.expander(t("Kaynaklar ve model kanıtı", "Sources and model evidence")):
        st.markdown(t(
            "Analiz: **04.10.2026** · [Hızlı test eşikleri](https://drive.google.com/file/d/1LelUqIaYDtKTbKnR-LoVbyJ0b9qZisY_/view) · [Aynı iş yükü](https://drive.google.com/file/d/1Uj9IY8bgEdhv1Qim37-LQysSLLc-7Lgi/view) · [Karar notu](https://drive.google.com/file/d/1upXKw5w8xNV_QbzAx3WEK0_hgwTQ4bLv/view). B ve eşik değişiklikleri öneridir; bu görünüm onay vermez.",
            "Analysis: **4 October 2026** · [Rapid thresholds](https://drive.google.com/file/d/1LelUqIaYDtKTbKnR-LoVbyJ0b9qZisY_/view) · [Matched workload](https://drive.google.com/file/d/1Uj9IY8bgEdhv1Qim37-LQysSLLc-7Lgi/view) · [Decision note](https://drive.google.com/file/d/1upXKw5w8xNV_QbzAx3WEK0_hgwTQ4bLv/view). B and threshold changes are proposals; this view does not approve them."))
        st.write(t("Normal şeritte kalan taşıyıcılar (A, 5 tekrar ortalaması): 37; yaklaşık 28 BRCA2 ve 9 BRCA1.",
                   "Carriers remaining in the normal lane (A, mean of 5 repeats): 37; approximately 28 BRCA2 and 9 BRCA1."))
        perf = model["performance"]
        st.write(t("Model AUC (havuzlanmış çapraz doğrulama): ", "Model AUC (pooled cross-validation): ") +
                 f"{perf['auc_nested_cv']:.3f} (95% CI {perf['auc_ci'][0]:.3f}–{perf['auc_ci'][1]:.3f}); " +
                 t("zamansal AUC: ", "temporal AUC: ") + f"{perf['auc_temporal']:.3f}.")
        calibration = model["nested_validation"]
        st.write(t("İç içe doğrulama kalibrasyon eğimi / kesişimi: ", "Nested-validation calibration slope / intercept: ") +
                 f"{calibration['cal_slope']:.3f} / {calibration['cal_intercept']:.3f}; Brier {calibration['brier']:.3f}.")
        st.caption(t("Bunlar modelin ayrım ve kalibrasyon ölçütleridir; kuyruk kuralının faydası veya zaman kazancı değildir. Hasta kayıtları bu pakette bulunmaz. Kaynak dosyaların sağlama toplamları evidence/sources.json içindedir.",
                     "These measure model discrimination and calibration, not queue benefit or time saved. This package contains no patient records. Source checksums are recorded in evidence/sources.json."))
