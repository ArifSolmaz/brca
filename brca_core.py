"""Verified calculation core for the BRCA priority app (v7 conference app, 2026-10-05).

No Streamlit here: pure functions, so the same code is tested headless.
- predict / points / decide are line-for-line the logic of the verified v6.2.1 Streamlit mirror (../streamlit/app.py), which
  test_calculator.py checks against the published HTML page, and test_exhaustive.py checks (via the same JSON) against
  the printed paper card on 6.6 M input profiles. test_app.py re-checks THIS module against the HTML page directly.
- rule "A" = v6.2 approved by Prof. Yazıcı (2026-10-04): lane = max(card lane, model lane, urgency); rapid first test = urgent lane.
- rule "B" = proposal in Provenance/KARAR_NOTU_kart_ve_hizli_test_2026-10-04.md (decision pending):
  lane = max(model lane, urgency); the card is shown for explanation only; rapid first test = model >= 20 %.
The model file is the calculator's model_full_embedded.json (aggregate coefficients only, no patient data).
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, "model_full_embedded.json"), encoding="utf-8"))
SELFTEST = json.load(open(os.path.join(HERE, "selftest_vectors_synthetic.json"), encoding="utf-8"))
FAMILY = ["fdr_breast_lt40", "fdr_breast_ge40", "sdr_breast_lt40", "sdr_breast_ge40", "tdr_breast", "fdr_ovary", "sdr_ovary", "fdr_other"]
RULES = ("A", "B")


def sig(z):
    return 1 / (1 + math.exp(-z))


def predict(v, m=M):
    """Calibrated carrier probability. v: age, age_missing, tnbc, ki67, ki67_missing (1 = not entered), dx, grade, region, family counts."""
    z = m["intercept"] + sum(m["coef"][k] * v.get(k, 0) for k in m["numeric"])
    z += m["coef"].get("age_missing", 0) * v.get("age_missing", 0) + m["coef"]["tnbc"] * v.get("tnbc", 0)
    miss = 1 if v.get("ki67_missing", 1) else 0
    z += m["coef"]["ki67"] * (m["ki67_impute"] if miss else v["ki67"]) + m["coef"]["ki67_missing"] * miss
    for cat in ("dx", "grade", "region"):
        z += m["coef"].get(f"{cat}={v[cat]}", 0)
    return {"z": z, "p_raw": sig(z), "p_cal": sig(m["platt"]["a"] + m["platt"]["b"] * z)}


PT_VARS = {   # points-card items, exactly as the page and the printed card count them (family counts capped at 2 per row)
    "age_lt40": lambda v: 0 if v.get("age_missing") else int(v["age"] < 40),
    "age_40_49": lambda v: 0 if v.get("age_missing") else int(40 <= v["age"] < 50),
    "age_ge60": lambda v: 0 if v.get("age_missing") else int(v["age"] >= 60),
    "tnbc": lambda v: int(bool(v.get("tnbc"))), "grade3": lambda v: int(v["grade"] == "g3"),
    "ki67_ge30": lambda v: int(not v.get("ki67_missing", 1) and v["ki67"] >= 30),
    "fdr_breast_lt40": lambda v: min(2, v.get("fdr_breast_lt40", 0)), "fdr_breast_ge40": lambda v: min(2, v.get("fdr_breast_ge40", 0)),
    "sdr_breast": lambda v: min(2, v.get("sdr_breast_lt40", 0) + v.get("sdr_breast_ge40", 0)), "tdr_breast": lambda v: min(2, v.get("tdr_breast", 0)),
    "fdr_ovary": lambda v: min(2, v.get("fdr_ovary", 0)), "sdr_ovary": lambda v: min(2, v.get("sdr_ovary", 0)),
    "bilateral": lambda v: int(v["dx"] == "bilateral"), "breast_ovary": lambda v: int(v["dx"] == "breast_ovary"),
    "ovarian": lambda v: int(v["dx"] == "ovarian"), "male": lambda v: int(v["dx"] == "male")}


def points(v, m=M):
    items = []
    for it in m["points"]["items"]:
        x = PT_VARS[it["key"]](v); c = x * it["points"]
        if c: items.append({"key": it["key"], "tr": it["tr"], "en": it["en"], "x": x, "c": c})
    return sum(i["c"] for i in items), items


def lane_points(total, m=M):
    P = m["points"]["points_cuts"]; return 2 if total >= P["rapid"] else 1 if total >= P["fast"] else 0


def lane_model(p, m=M):
    P = m["points"]["model_cuts"]; return 2 if p >= P["rapid"] else 1 if p >= P["fast"] else 0


def decide(v, p_cal, rule="A", m=M):
    """Queue lane 0 normal / 1 priority / 2 urgent, the reasons, and whether the rapid first test is advised."""
    assert rule in RULES
    total, items = points(v, m); pl, ml = lane_points(total, m), lane_model(p_cal, m)
    urg = 2 if v.get("urg_dec") else 1 if v.get("urg_fam") else 0
    lane = max(pl, ml, urg) if rule == "A" else max(ml, urg)
    rapid = (lane == 2) if rule == "A" else (p_cal >= m["points"]["model_cuts"]["rapid"])
    raised_by = []
    if lane > ml:
        if rule == "A" and pl > ml and pl == lane: raised_by.append("card")
        if v.get("urg_dec"): raised_by.append("urg_dec")
        if v.get("urg_fam") and lane >= 1: raised_by.append("urg_fam")
    return dict(total=total, items=items, pl=pl, ml=ml, urg=urg, lane=lane, rapid=rapid, raised_by=raised_by, rule=rule)


def one_in_n(p):
    n = round(1 / max(p, 1e-9)); return n


def percentile(p, m=M):
    """Same as the page: position among the development cohort's predictions, in steps of 5 (">95" above the top)."""
    q = m["score_percentiles"]; i = 0
    while i < len(q) - 1 and q[i + 1] <= p: i += 1
    if i >= len(q) - 1: return 100
    f = (p - q[i]) / ((q[i + 1] - q[i]) or 1); return round((i + min(1, max(0, f))) * 5)


def selftest(m=M, vectors=SELFTEST, tol=1e-9):
    """Recompute the synthetic reference patients scored by sklearn; returns (n_ok, n_total)."""
    ok = sum(abs(predict(c["inputs"], m)["p_cal"] - c["p_cal"]) < tol for c in vectors)
    return ok, len(vectors)


def summary():
    """Aggregate validation numbers shown on the page (all read from the model file)."""
    C = M["points"]["combined"]; S = C["summary_cv"]
    return dict(n=M["n"], n_pos=M["n_pos"], n_breast=M["n_breast"], n_ovary=M["n"] - M["n_breast"], prevalence=M["prevalence"],
                year_min=M["year_min"], year_max=M["year_max"],
                moved=S["combined"]["prioritised_share"]["mean"], covered=S["combined"]["carriers_prioritised"]["mean"],
                moved_model=S["model_only"]["prioritised_share"]["mean"], covered_model=S["model_only"]["carriers_prioritised"]["mean"],
                t_moved=C["temporal"]["combined"]["prioritised_share"], t_covered=C["temporal"]["combined"]["carriers_prioritised"],
                build=M.get("build", ""))
