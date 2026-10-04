"""BRCA1/2 Test Öncelik Hesaplayıcı — conference app (v7, 2026-10-05). Research use only.

Look: a dark product-style landing band over a light, high-legibility clinical calculator (designs 3 + 4 of the canvas).
All numbers come from brca_core.py (verified against the published HTML page and the printed paper card) and from
model_full_embedded.json / verification.json (aggregate values only). Nothing typed in is stored.
RUN: streamlit run app.py        Rule B preview: add ?kural=B to the address.
"""
import json, os, hmac, time
import streamlit as st
import brca_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
V = json.load(open(os.path.join(HERE, "verification.json")))
S = core.summary(); M = core.M

st.set_page_config(page_title="BRCA Öncelik Hesaplayıcı", page_icon=os.path.join(HERE, "assets", "icon.png") if os.path.exists(os.path.join(HERE, "assets", "icon.png")) else None,
                   layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- text (TR / EN)
TX = {
 "tr": dict(
  brand="BRCA Öncelik", research="Araştırma amaçlıdır · klinik karar destek aracı değildir · girilen bilgiler kaydedilmez",
  pill_ok="Öz-test ✓ {ok}/{n} · {prof} girdi kombinasyonunda doğrulandı", pill_bad="Öz-test başarısız ({ok}/{n}) — hesaplama durduruldu",
  h1="Test kuyruğunu taşıyıcılara göre sırala.",
  lead="Tanı gününde bilinen bilgilerle BRCA1/2 taşıyıcılık olasılığını hesaplar ve hastayı test kuyruğunda normal, öncelikli ya da acil şeride koyar. Kimse testten çıkarılmaz; yalnız sıra değişir.",
  cta1="Nasıl doğrulandı ↓", cta2="Kâğıt kart (PDF)",
  s1="taşıyıcı öne alınır", s1b="hastaların %{m}'i öne alınarak",
  s2="sonraki dönemde", s2b="2015'e kadar kurulup 2016–2020 hastalarına uygulanınca",
  s3="fark", s3b="sayfa, Python ve basılı kart arasında, {prof} girdi kombinasyonunda",
  s4="hasta", s4b="{pos} taşıyıcı · geliştirme kohortu, tanı yılları {y0}–{y1}",
  calc_h="BRCA1/2 taşıyıcılık olasılığı ve test önceliği", calc_lead="Tanı günündeki bilgiler yeterli; sonuç anında güncellenir. Bilinmeyen alanları boş bırakın.",
  example="Örnek hasta", clear="Temizle",
  step1="Hasta ve tümör", step2="Aile öyküsü", step3="Klinik aciliyet",
  age="Tanı yaşı", age_ph="yıl (18–95)", dx="Tanı", grade="Histolojik grade", grade_lbl={"g1": "1", "g2": "2 / bilinmiyor", "g3": "3"},
  tnbc="Üçlü negatif (ER−, PR−, HER2−)", tnbc_ov="Üçlü negatif — yalnız meme tümöründe", ki67="Ki-67 (%)", ki67_ph="bilinmiyor", ki67_ov="Ki-67 — yalnız meme tümöründe",
  region="Köken bölgesi", fam_help="Hasta dışındaki akrabalar; kişi sayısı.",
  fam={"fdr_breast_lt40": "1. derece · meme kanseri < 40 yaş", "fdr_breast_ge40": "1. derece · meme kanseri ≥ 40 yaş", "fdr_ovary": "1. derece · over kanseri",
       "sdr_breast_lt40": "2. derece · meme kanseri < 40 yaş", "sdr_breast_ge40": "2. derece · meme kanseri ≥ 40 yaş", "sdr_ovary": "2.–4. derece · over kanseri",
       "tdr_breast": "3.–4. derece · meme kanseri", "fdr_other": "1. derece · başka kanser"},
  fam_more="Diğer akrabalar", urg_help="Olasılığı değiştirmez, yalnız sırayı.",
  urg_dec="Ameliyat veya sistemik tedavi kararı bu sonuca bağlı", urg_fam="Ailede belgelenmiş P/LP BRCA1/2 varyantı var (VUS değil)",
  dx_lbl={"breast": "Tek taraflı meme", "bilateral": "Bilateral meme", "breast_ovary": "Meme + over", "ovarian": "Yalnız over", "male": "Erkek meme"},
  reg_lbl={"marmara": "Marmara / bilinmiyor", "balkans": "Balkanlar", "black_sea": "Karadeniz", "middle_anatolia": "İç Anadolu", "eastern_anatolia": "Doğu Anadolu",
           "southeastern_anatolia": "Güneydoğu Anadolu", "aegean": "Ege", "mediterranean": "Akdeniz"},
  wait_h="Sonuç burada görünecek", wait_b="Başlamak için tanı yaşını girin ya da <b>Örnek hasta</b> düğmesine basın.",
  lane_kicker="Önerilen şerit", lanes=["NORMAL SIRA", "ÖNCELİKLİ", "ACİL"],
  act=["Tam test olağan sırada. “Test etmeyin” anlamına gelmez.", "Tam test sıranın önüne alınır.", "Tam test hemen istenir."],
  rapid="Paralelde hızlı ilk test: BRCA1 MLPA + c.5266dupC. Hızlı test negatifse hiçbir şey dışlanmaz; tam test sürer.",
  famtest="Ailedeki varyant belgeli: önce o varyanta özgü hedefli test (gen ve varyant akrabanın raporundan).",
  fulltest="Tam test = dizileme + büyük delesyon/duplikasyon analizi.",
  prob="taşıyıcılık olasılığı", one_in="≈ {n} hastadan 1'i", one_in_half="her 2 hastadan 1'inden fazlası", pctl="{p}. yüzdelik", pctl_top="en üst %5",
  cohort="kohort ortalaması {p}", card="Puan kartı", pts="puan", no_pts="puan yok", why="Neden bu şerit?",
  why_card="Puan kartı {t} puan → {l}", why_model="Model olasılığı {p} → {l}", why_urg_dec="Sonucu bekleyen tedavi/cerrahi kararı → acil",
  why_urg_fam="Ailede belgelenmiş P/LP varyant → en az öncelikli", why_card_b=" (kural B: yalnız açıklama, karara katılmaz)", why_rule_a="Karar = üçünün en yükseği (kural A, onaylı v6.2).",
  why_rule_b="Kural B (öneri, karar bekliyor): karar = model ve aciliyetin yükseği; kart yalnız açıklama içindir; hızlı ilk test model ≥ %20 ise.",
  lane_lc=["normal", "öncelikli", "acil"], counsel_h="Hastaya nasıl anlatılır",
  counsel_low="Bu profilde yaklaşık {f} BRCA1/2 varyantı taşır. Pozitif sonuç beklenmedik olur, ama olanaksız değildir.",
  counsel_mid="Bu profilde yaklaşık {f} BRCA1/2 varyantı taşır. Kalıtsal neden azınlıkta, ama dışlanamaz.",
  counsel_high="Bu profilde yaklaşık {f} BRCA1/2 varyantı taşır. Kanserin kalıtsal olma ihtimali gerçektir; sonuç gelmeden pozitif sonucun tedavi ve akrabalar için anlamını konuşmak yerindedir.",
  counsel_fam="Ailede belgelenmiş P/LP varyant var. Bu olasılık o bilgiyi içermez; danışma, hastanın ailedeki varyantı taşıyıp taşımadığı üzerinden yapılır.",
  not_h="Ne değildir", not_b="Tanı değildir; kanser riski de değildir. Tanı almış hastada genetik testin pozitif çıkma olasılığıdır. Normal sırada da taşıyıcı vardır (çoğu BRCA2); bu yüzden herkes tam testini olur.",
  ev_h="Ne kadar güvenilir?", ev1="Doğrulama", ev1b="Model ve kart her doğrulama katında yeniden kuruldu (iç içe çapraz doğrulama, 5 tekrar). Kural hastaların %{m}'ini öne alıp taşıyıcıların %{c}'ini kapsadı.",
  ev2="Hesap denetimi", ev2b="{tests} otomatik test geçti. {prof} girdi kombinasyonunda sayfa, bağımsız Python ve basılı kart aynı puanı ve şeridi verdi; {rnd} rastgele profilde olasılık farkı < 10⁻¹⁴.",
  ev3="Sınırlar", ev3b="Tek merkez, geriye dönük veri ({y0}–{y1}). Dış ve ileriye dönük doğrulama planlandı. Klinik aciliyetin etkisi kohortta ölçülemedi.",
  card_h="Kâğıt kart", card_b="Hesaplayıcı yokken aynı kural kâğıt üzerinde: 14 madde, 0–3 normal, 4 öncelikli, ≥ 5 acil.", card_dl="Tek sayfalık algoritmayı indir (PDF)",
  rule_b_badge="Kural B önizlemesi", foot="Prof. Dr. Hülya Yazıcı · Dr. Öğr. Üyesi Arif Solmaz · İstanbul Sağlık ve Teknoloji Üniversitesi (İSTÜN)", build="model {b} · {tests} test ✓",
  sticky_go="Sonuç ↓", age_needed="yaş girin",
  login_h="Bu sayfa şifre ile korunuyor", login_b="Araştırma prototipi; yalnız davet edilen katılımcılar içindir.", login_lbl="Şifre", login_btn="Giriş",
  login_bad="Şifre yanlış.", login_missing="Şifre tanımlanmamış. Yönetici: Streamlit → App settings → Secrets içine APP_PASSWORD ekleyin."),
 "en": dict(
  brand="BRCA Priority", research="Research use only · not a clinical decision-support tool · nothing you enter is stored",
  pill_ok="Self-test ✓ {ok}/{n} · verified on {prof} input combinations", pill_bad="Self-test failed ({ok}/{n}) — calculation stopped",
  h1="Order the test queue by who is likely a carrier.",
  lead="From what is known on the day of diagnosis, the calculator estimates BRCA1/2 carrier probability and places the patient in the normal, priority or urgent lane of the test queue. Nobody is removed from testing; only the order changes.",
  cta1="How it was validated ↓", cta2="Paper card (PDF)",
  s1="of carriers moved forward", s1b="by moving {m}% of patients forward",
  s2="in a later period", s2b="built on diagnoses up to 2015, applied to 2016–2020",
  s3="mismatches", s3b="between page, Python and the printed card on {prof} input combinations",
  s4="patients", s4b="{pos} carriers · development cohort, diagnosed {y0}–{y1}",
  calc_h="BRCA1/2 carrier probability and test priority", calc_lead="What is known on the day of diagnosis is enough; the result updates instantly. Leave unknown fields empty.",
  example="Example patient", clear="Clear",
  step1="Patient and tumour", step2="Family history", step3="Clinical urgency",
  age="Age at diagnosis", age_ph="years (18–95)", dx="Diagnosis", grade="Histological grade", grade_lbl={"g1": "1", "g2": "2 / unknown", "g3": "3"},
  tnbc="Triple-negative (ER−, PR−, HER2−)", tnbc_ov="Triple-negative — breast tumours only", ki67="Ki-67 (%)", ki67_ph="unknown", ki67_ov="Ki-67 — breast tumours only",
  region="Region of origin", fam_help="Relatives other than the patient; number of people.",
  fam={"fdr_breast_lt40": "1st degree · breast cancer < 40", "fdr_breast_ge40": "1st degree · breast cancer ≥ 40", "fdr_ovary": "1st degree · ovarian cancer",
       "sdr_breast_lt40": "2nd degree · breast cancer < 40", "sdr_breast_ge40": "2nd degree · breast cancer ≥ 40", "sdr_ovary": "2nd–4th degree · ovarian cancer",
       "tdr_breast": "3rd–4th degree · breast cancer", "fdr_other": "1st degree · other cancer"},
  fam_more="Other relatives", urg_help="Does not change the probability, only the order.",
  urg_dec="A surgery or systemic-treatment decision depends on this result", urg_fam="Documented P/LP BRCA1/2 variant in the family (not a VUS)",
  dx_lbl={"breast": "Unilateral breast", "bilateral": "Bilateral breast", "breast_ovary": "Breast + ovary", "ovarian": "Ovarian only", "male": "Male breast"},
  reg_lbl={"marmara": "Marmara / unknown", "balkans": "Balkans", "black_sea": "Black Sea", "middle_anatolia": "Central Anatolia", "eastern_anatolia": "Eastern Anatolia",
           "southeastern_anatolia": "South-eastern Anatolia", "aegean": "Aegean", "mediterranean": "Mediterranean"},
  wait_h="The result will appear here", wait_b="Enter the age at diagnosis, or press <b>Example patient</b>.",
  lane_kicker="Recommended lane", lanes=["NORMAL QUEUE", "PRIORITY", "URGENT"],
  act=["Full test in the usual order. This does not mean “do not test”.", "Full test moves to the front of the queue.", "Request the full test now."],
  rapid="In parallel, a rapid first test: BRCA1 MLPA + c.5266dupC. A negative rapid test rules nothing out; the full test continues.",
  famtest="Documented familial variant: first a targeted test for that variant (gene and variant from the relative's report).",
  fulltest="Full test = sequencing + large deletion/duplication analysis.",
  prob="carrier probability", one_in="≈ 1 in {n} patients", one_in_half="more than 1 in 2 patients", pctl="{p}th percentile", pctl_top="top 5%",
  cohort="cohort average {p}", card="Points card", pts="points", no_pts="no points", why="Why this lane?",
  why_card="Points card {t} points → {l}", why_model="Model probability {p} → {l}", why_urg_dec="Treatment/surgery decision waiting → urgent",
  why_urg_fam="Documented familial P/LP variant → at least priority", why_card_b=" (rule B: explanation only, not part of the decision)", why_rule_a="Decision = the highest of the three (rule A, approved v6.2).",
  why_rule_b="Rule B (proposal, decision pending): decision = the higher of model and urgency; the card only explains; rapid first test if model ≥ 20%.",
  lane_lc=["normal", "priority", "urgent"], counsel_h="How to explain it to the patient",
  counsel_low="About {f} with this profile carries a BRCA1/2 variant. A positive result would be unexpected, but not impossible.",
  counsel_mid="About {f} with this profile carries a BRCA1/2 variant. A hereditary cause is the minority, but cannot be ruled out.",
  counsel_high="About {f} with this profile carries a BRCA1/2 variant. A hereditary cause is a real possibility; it is worth discussing what a positive result would mean for treatment and relatives before it arrives.",
  counsel_fam="A documented familial P/LP variant: this probability does not include that information; counselling is about whether the patient carries the family's variant.",
  not_h="What it is not", not_b="Not a diagnosis and not a cancer risk. It is the probability that genetic testing is positive in a patient already diagnosed. Carriers also occur in the normal queue (mostly BRCA2), which is why everybody gets the full test.",
  ev_h="How far can it be trusted?", ev1="Validation", ev1b="Model and card were refitted inside every validation fold (nested cross-validation, 5 repeats). The rule moved {m}% of patients forward and covered {c}% of carriers.",
  ev2="Calculation audit", ev2b="{tests} automatic tests pass. On {prof} input combinations the page, an independent Python version and the printed card gave the same points and lane; on {rnd} random profiles the probability differed by < 10⁻¹⁴.",
  ev3="Limits", ev3b="Single centre, retrospective data ({y0}–{y1}). External and prospective validation is planned. The effect of clinical urgency could not be measured in the cohort.",
  card_h="Paper card", card_b="The same rule on paper when the calculator is unavailable: 14 items; 0–3 normal, 4 priority, ≥ 5 urgent.", card_dl="Download the one-page algorithm (PDF, Turkish)",
  rule_b_badge="Rule B preview", foot="Prof. Dr. Hülya Yazıcı · Dr. Arif Solmaz · Istanbul Health and Technology University (İSTÜN)", build="model {b} · {tests} tests ✓",
  sticky_go="Result ↓", age_needed="enter age",
  login_h="This page is password protected", login_b="Research prototype; for invited participants only.", login_lbl="Password", login_btn="Sign in",
  login_bad="Wrong password.", login_missing="No password is set. Admin: Streamlit → App settings → Secrets, add APP_PASSWORD."),
}
LANE_BG = ["#00703C", "#FFB81C", "#D5281B"]; LANE_FG = ["#FFFFFF", "#1B2128", "#FFFFFF"]

# ---------------------------------------------------------------- state
DEFAULTS = dict(age=None, dx="breast", grade="g2", tnbc=False, ki67=None, region="marmara", urg_dec=False, urg_fam=False, **{k: 0 for k in core.FAMILY})
EXAMPLE = dict(DEFAULTS, age=38, tnbc=True, fdr_breast_lt40=1)
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
def load(d):
    for k, v in d.items(): st.session_state[k] = v
rule = str(st.query_params.get("kural", st.query_params.get("rule", "A"))).upper()
rule = rule if rule in core.RULES else "A"

L = st.session_state.get("lang_sel") or "tr"; T = TX[L]   # the language switch widget is the only source of truth
def num(x, d=1):
    s = f"{x:,.{d}f}"; return s.replace(",", "X").replace(".", ",").replace("X", ".") if L == "tr" else s
def pct(p, d=1):
    return f"%{num(100 * p, d)}" if L == "tr" else f"{num(100 * p, d)}%"
def n_int(n):
    return f"{n:,}".replace(",", ".") if L == "tr" else f"{n:,}"
PROF = n_int(V["exhaustive_profiles"]) if L == "tr" else f"{V['exhaustive_profiles']/1e6:.1f} million"
if L == "tr": PROF = f"{V['exhaustive_profiles']/1e6:.1f}".replace(".", ",") + " milyon"
ST_OK, ST_N = core.selftest()

# ---------------------------------------------------------------- style
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Geist:wght@500;600;700&family=Geist+Mono:wght@400;500&display=swap');
:root{--ink:#1B2128;--muted:#4C5966;--line:#D9DEE3;--bg:#F4F6F8;--card:#FFFFFF;--accent:#6D5BD0;--dark:#0E0F13;--dark2:#16181D;--darkline:#2A2E38;--darkmuted:#A9AFB9;}
html, body, [data-testid="stAppViewContainer"]{background:var(--bg);}
[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{display:none !important;}
.block-container{max-width:1120px; padding:0 24px 96px 24px !important;}
html, body, [class*="st-"], .stMarkdown, label, input, select, button, textarea{font-family:'Atkinson Hyperlegible', system-ui, sans-serif;}
h1,h2,h3,.disp{font-family:'Geist', system-ui, sans-serif !important; letter-spacing:-0.02em;}
.mono{font-family:'Geist Mono', ui-monospace, monospace;}
[data-testid="stIconMaterial"], .material-symbols-rounded{font-family:'Material Symbols Rounded' !important;}
.topbar{display:flex; align-items:center; gap:10px; padding:14px 0 10px 0; font-family:'Geist',sans-serif; font-weight:600; color:var(--ink);}
.ver{font-family:'Geist Mono',monospace; font-size:12px; color:var(--muted); border:1px solid var(--line); border-radius:999px; padding:2px 8px; font-weight:400;}
.research{font-size:14px; color:var(--muted);}
.hero{background:var(--dark); color:#E8E9ED; border-radius:20px; padding:56px 48px 40px 48px; margin:6px 0 40px 0;}
.pill{display:inline-flex; align-items:center; gap:8px; border:1px solid var(--darkline); border-radius:999px; padding:6px 14px; font-size:14px; color:#C9CDD4;}
.dot{width:8px; height:8px; border-radius:50%; display:inline-block;}
.hero .hh{color:#F2F3F5; font-size:44px; letter-spacing:-0.02em; font-family:'Geist',sans-serif; font-weight:600; line-height:1.05; margin:22px 0 0 0; max-width:820px; font-weight:600;}
.hero p.lead{font-size:19px; line-height:1.55; color:#C9CDD4; max-width:680px; margin:18px 0 0 0;}
.ctas{display:flex; flex-wrap:wrap; gap:12px; margin-top:28px;}
.btn{display:inline-flex; align-items:center; min-height:48px; padding:0 22px; border-radius:10px; text-decoration:none !important; font-weight:700; font-size:16px;}
.btn.p{background:#8B7CF6; color:#0E0F13 !important;} .btn.s{border:1px solid var(--darkline); color:#E8E9ED !important;}
.stats{display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin-top:40px;}
.stat{border:1px solid var(--darkline); border-radius:14px; padding:18px; background:var(--dark2);}
.stat .v{font-family:'Geist Mono',monospace; font-size:32px; color:#F2F3F5;} .stat .k{font-size:15px; color:#E8E9ED; margin-top:4px;} .stat .d{font-size:13px; color:var(--darkmuted); margin-top:6px; line-height:1.45;}
.sec-h{font-size:34px; margin:0 0 6px 0; color:var(--ink);} .sec-h.top{font-size:42px; line-height:1.08;}
.pill-l{display:inline-flex; align-items:center; gap:8px; border:1px solid var(--line); background:var(--card); border-radius:999px; padding:6px 14px; font-size:14px; color:var(--muted);}
/* toggles: clearly visible in both states (the default off track is almost white) */
[data-testid='stCheckbox'] label > div:not([data-testid]){background:#8C96A3 !important; border:1px solid #6B7682 !important;}
[data-testid='stCheckbox'] label:has(input:checked) > div:not([data-testid]){background:var(--accent) !important; border-color:var(--accent) !important;}
[data-testid='stCheckbox'] label > div:not([data-testid]) > div{background:#FFFFFF !important; box-shadow:0 1px 3px rgba(0,0,0,.35);}
[data-testid='stCheckbox'] label:has(input:disabled){opacity:.55;} .sec-lead{font-size:18px; color:var(--muted); margin:0 0 18px 0;}
.st-key-formcard{background:var(--card); border-radius:18px; border:1px solid var(--line); padding:14px 16px 18px 16px;}
.st-key-resultcard{background:var(--card); border-radius:18px; border:1px solid var(--line); padding:0 0 14px 0; overflow:hidden; gap:0;}
.st-key-resultcard [data-testid='stExpander']{margin:0 16px; width:auto !important;}
.step{display:flex; align-items:center; gap:10px; font-family:'Geist',sans-serif; font-weight:600; font-size:19px; color:var(--ink); margin:6px 0 2px 0;}
.step b{display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:50%; background:var(--accent); color:#fff; font-size:14px;}
.help{font-size:15px; color:var(--muted); margin:0 0 6px 0;}
[data-testid="stNumberInput"] input{font-size:19px; min-height:48px;}
[data-testid="stNumberInput"] button{min-width:44px;}
[data-baseweb="select"] > div{min-height:48px; font-size:17px;}
label p{font-size:16px !important; color:var(--ink) !important;}
.stButton button{min-height:48px; border-radius:10px; font-weight:700; font-size:16px; padding:0 18px;}
[data-testid="stPills"] button, [data-testid="stButtonGroup"] button{min-height:44px; font-size:16px;}
.res-wait{padding:28px; text-align:center; color:var(--muted); font-size:17px;} .res-wait h3{color:var(--ink); font-size:22px; margin:0 0 8px 0;}
.lane{padding:20px 24px;} .lane .k{font-size:15px; opacity:.9;} .lane .v{font-family:'Geist',sans-serif; font-weight:700; font-size:38px; letter-spacing:.01em;}
.res{padding:18px 22px 6px 22px; font-size:17px; line-height:1.55; color:var(--ink);}
.big{font-family:'Geist',sans-serif; font-weight:600; font-variant-numeric:tabular-nums; font-size:60px; line-height:1; letter-spacing:-0.03em; color:var(--ink);}
.sub{font-size:15px; color:var(--muted); margin-top:6px;}
.scale{position:relative; height:10px; border-radius:999px; background:#E6E9ED; margin:18px 0 4px 0;}
.scale .fill{position:absolute; left:0; top:0; height:10px; border-radius:999px; background:var(--accent);}
.scale .tick{position:absolute; top:-5px; width:2px; height:20px; background:var(--ink);}
.scale-l{position:relative; height:18px; font-family:'Geist Mono',monospace; font-size:12px; color:var(--muted);}
.scale-l span{position:absolute;}
.box{border:1px solid var(--line); border-radius:12px; padding:14px 16px; margin-top:16px;}
.box h4{margin:0 0 8px 0; font-size:15px; color:var(--muted); font-weight:700; font-family:'Atkinson Hyperlegible',sans-serif; letter-spacing:0;}
.row{display:flex; justify-content:space-between; gap:12px; padding:6px 0; border-top:1px solid #EEF0F3; font-size:16px;} .row:first-of-type{border-top:0;}
.row .c{font-family:'Geist Mono',monospace; color:var(--accent); white-space:nowrap;}
.why li{margin:4px 0;}
.badge{display:inline-block; font-size:13px; font-weight:700; padding:4px 10px; border-radius:999px; background:#EDE9FF; color:#3F2F9E;}
.ev{display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px;}
.evc{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:22px;} .evc h3{font-size:20px; margin:0 0 8px 0; color:var(--ink);} .evc p{margin:0; font-size:16px; line-height:1.55; color:var(--ink);}
.foot{display:flex; flex-wrap:wrap; justify-content:space-between; gap:10px; border-top:1px solid var(--line); margin-top:40px; padding-top:16px; font-size:14px; color:var(--muted);}
.sticky{display:none;}
@media (max-width: 760px){
  .block-container{padding:0 14px 96px 14px !important;}
  .hero{padding:32px 22px 26px 22px; border-radius:16px;} .hero .hh{font-size:30px;} .sec-h.top{font-size:30px;} .hero p.lead{font-size:17px;}
  .stats{grid-template-columns:repeat(2,minmax(0,1fr));} .stat .v{font-size:26px;}
  .ev{grid-template-columns:1fr;} .sec-h{font-size:26px;} .big{font-size:46px;} .lane .v{font-size:30px;}
  .sticky{display:flex; position:fixed; left:12px; right:12px; bottom:12px; z-index:1000; align-items:center; justify-content:space-between; gap:12px;
          padding:12px 16px; border-radius:14px; box-shadow:0 6px 24px rgba(0,0,0,.25); font-weight:700; font-size:17px; text-decoration:none !important;}
  .sticky .mono{font-family:'Geist',sans-serif; font-variant-numeric:tabular-nums;}
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- password gate
# The password lives in Streamlit Secrets (APP_PASSWORD) or the BRCA_APP_PASSWORD environment variable, never in the code.
# With neither set the app stays closed, except locally with BRCA_NO_PASSWORD=1.
def _password():
    try:
        pw = st.secrets.get("APP_PASSWORD")
    except Exception:
        pw = None
    return pw or os.environ.get("BRCA_APP_PASSWORD")
if not st.session_state.get("auth"):
    PW = _password()
    if not PW and os.environ.get("BRCA_NO_PASSWORD") == "1":
        st.session_state.auth = True
    else:
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.html(f"""<div style='margin-top:12vh; text-align:center'>
<svg width='44' height='44' viewBox='0 0 24 24' fill='none' stroke='#6D5BD0' stroke-width='2' aria-hidden='true'><rect x='4' y='11' width='16' height='10' rx='2'/><path d='M8 11V7a4 4 0 0 1 8 0v4'/></svg>
<h1 class='disp' style='font-size:30px; margin:14px 0 6px 0; color:var(--ink)'>{T['brand']}</h1>
<p style='font-size:18px; margin:0; color:var(--ink)'>{T['login_h']}</p><p style='font-size:15px; color:var(--muted); margin:6px 0 0 0'>{T['login_b']}</p></div>""")
            if not PW:
                st.error(T["login_missing"]); st.stop()
            with st.form("login", border=True):
                pw_in = st.text_input(T["login_lbl"], type="password", key="pw_in")
                go = st.form_submit_button(T["login_btn"], type="primary", use_container_width=True)
            if go:
                if hmac.compare_digest(pw_in.encode("utf-8"), str(PW).encode("utf-8")):
                    st.session_state.auth = True; st.rerun()
                time.sleep(1.0); st.error(T["login_bad"])
            st.segmented_control("Dil / Language", ["tr", "en"], default="tr", format_func=lambda x: x.upper(), key="lang_sel", label_visibility="collapsed")
        st.stop()

# ---------------------------------------------------------------- top bar + language
tb1, tb2 = st.columns([5, 1], vertical_alignment="center")
with tb1:
    st.html(f"<div class='topbar'><svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#6D5BD0' stroke-width='2' aria-hidden='true'><path d='M7 3c0 6 10 6 10 12s-10 6-10 6'/><path d='M17 3c0 6-10 6-10 12s10 6 10 6'/></svg><span class='disp'>{T['brand']}</span><span class='ver'>v7 · {S['build'][-10:]}</span>"
            + (f"<span class='badge'>{T['rule_b_badge']}</span>" if rule == "B" else "") + f"</div><div class='research'>{T['research']}</div>")
with tb2:
    st.segmented_control("Dil / Language", ["tr", "en"], default="tr", format_func=lambda x: x.upper(), key="lang_sel", label_visibility="collapsed")

# ---------------------------------------------------------------- self-test (before anything is calculated)
ok_all = ST_OK == ST_N
if not ok_all:
    st.error(T["pill_bad"].format(ok=ST_OK, n=ST_N)); st.stop()

# ---------------------------------------------------------------- calculator
st.html(f"<div id='hesapla'></div><p style='margin:18px 0 10px 0'><span class='pill-l'><span class='dot' style='background:#1E9E61'></span>{T['pill_ok'].format(ok=ST_OK, n=ST_N, prof=PROF)}</span></p>"
        f"<h1 class='sec-h top'>{T['calc_h']}</h1><p class='sec-lead'>{T['calc_lead']}</p>")
b1, b2, _ = st.columns([1, 1, 3])
b1.button(T["example"], on_click=load, args=(EXAMPLE,), type="primary", use_container_width=True, key="btn_example")
b2.button(T["clear"], on_click=load, args=(DEFAULTS,), use_container_width=True, key="btn_clear")

left, right = st.columns([7, 5], gap="large")
with left:
    with st.container(key="formcard"):
        st.html(f"<div class='step'><b>1</b>{T['step1']}</div>")
        dx = st.session_state.dx or "breast"; ovarian = dx == "ovarian"
        if ovarian:
            st.session_state.tnbc = False; st.session_state.ki67 = None
        c1, c2 = st.columns(2)
        c1.number_input(T["age"], min_value=18, max_value=95, step=1, placeholder=T["age_ph"], key="age")
        c2.number_input(T["ki67_ov"] if ovarian else T["ki67"], min_value=0.0, max_value=100.0, step=1.0, placeholder=T["ki67_ph"], key="ki67", disabled=ovarian)
        st.pills(T["dx"], ["breast", "bilateral", "breast_ovary", "ovarian", "male"], selection_mode="single", format_func=lambda x: T["dx_lbl"][x], key="dx")
        st.segmented_control(T["grade"], ["g1", "g2", "g3"], format_func=lambda x: T["grade_lbl"][x], key="grade")
        st.toggle(T["tnbc_ov"] if ovarian else T["tnbc"], key="tnbc", disabled=ovarian)
        st.selectbox(T["region"], M["categorical"]["region"], format_func=lambda x: T["reg_lbl"].get(x, x), key="region")
        st.html(f"<div class='step' style='margin-top:14px'><b>2</b>{T['step2']}</div><p class='help'>{T['fam_help']}</p>")
        f1, f2 = st.columns(2)
        for i, k in enumerate(["fdr_breast_lt40", "fdr_breast_ge40", "fdr_ovary", "sdr_breast_lt40"]):
            (f1 if i % 2 == 0 else f2).number_input(T["fam"][k], min_value=0, max_value=6, step=1, key=k)
        more = sum(st.session_state[k] for k in ["sdr_breast_ge40", "sdr_ovary", "tdr_breast", "fdr_other"])
        with st.expander(T["fam_more"] + (f" · {more}" if more else "")):
            g1, g2 = st.columns(2)
            for i, k in enumerate(["sdr_breast_ge40", "sdr_ovary", "tdr_breast", "fdr_other"]):
                (g1 if i % 2 == 0 else g2).number_input(T["fam"][k], min_value=0, max_value=6, step=1, key=k)
        st.html(f"<div class='step' style='margin-top:14px'><b>3</b>{T['step3']}</div><p class='help'>{T['urg_help']}</p>")
        st.toggle(T["urg_dec"], key="urg_dec")
        st.toggle(T["urg_fam"], key="urg_fam")

ss = st.session_state
with right:
    with st.container(key="resultcard"):
        if ss.age is None:
            st.html(f"<div class='res-wait'><h3>{T['wait_h']}</h3><p>{T['wait_b']}</p></div>")
            d = None
        else:
            v = dict(age=float(ss.age), age_missing=0, dx=dx, grade=ss.grade or "g2", region=ss.region, tnbc=0 if ovarian else int(ss.tnbc),
                     **({"ki67": float(ss.ki67), "ki67_missing": 0} if (ss.ki67 is not None and not ovarian) else {"ki67": M["ki67_impute"], "ki67_missing": 1}),
                     **{k: int(ss[k]) for k in core.FAMILY}, urg_dec=bool(ss.urg_dec), urg_fam=bool(ss.urg_fam))
            r = core.predict(v); p = r["p_cal"]; d = core.decide(v, p, rule)
            act = T["act"][d["lane"]] + (" " + T["rapid"] if d["rapid"] else "") + (" " + T["famtest"] if ss.urg_fam else "")
            n = core.one_in_n(p); frac = T["one_in"].format(n=n) if n >= 2 else T["one_in_half"]
            pc = core.percentile(p); pc_txt = T["pctl_top"] if pc >= 100 else T["pctl"].format(p=pc)
            fill = min(100, p / 0.40 * 100)
            items = "".join(f"<div class='row'><span>{it[L]}{' ×' + str(it['x']) if it['x'] > 1 else ''}</span><span class='c'>+{it['c']}</span></div>" for it in d["items"]) \
                    or f"<div class='row'><span>{T['no_pts']}</span><span class='c'>0</span></div>"
            why = [T["why_card"].format(t=d["total"], l=T["lane_lc"][d["pl"]]) + ("" if rule == "A" else T["why_card_b"]),
                   T["why_model"].format(p=pct(p), l=T["lane_lc"][d["ml"]])]
            if ss.urg_dec: why.append(T["why_urg_dec"])
            if ss.urg_fam: why.append(T["why_urg_fam"])
            lvl = "low" if p < M["triage"]["95"]["threshold"] else "mid" if p < 0.10 else "high"
            counsel = T["counsel_fam"] if ss.urg_fam else T["counsel_" + lvl].format(f=frac.replace("≈ ", ""))
            st.html(f"""
<div class='lane' id='sonuc' style='background:{LANE_BG[d['lane']]}; color:{LANE_FG[d['lane']]}'><div class='k'>{T['lane_kicker']}</div><div class='v'>{T['lanes'][d['lane']]}</div></div>
<div class='res'>
<p style='margin:0 0 16px 0'><b>{act}</b></p>
<div class='big' data-testid='pcal'>{pct(p)}</div>
<div class='sub'>{T['prob']} · {frac} · {pc_txt} · {T['cohort'].format(p=pct(M['prevalence']))}</div>
<div class='scale' role='img' aria-label='{pct(p)}'><div class='fill' style='width:{fill:.1f}%'></div><div class='tick' style='left:25%'></div><div class='tick' style='left:50%'></div></div>
<div class='scale-l'><span style='left:0'>0</span><span style='left:25%; transform:translateX(-50%)'>{pct(0.10, 0)}</span><span style='left:50%; transform:translateX(-50%)'>{pct(0.20, 0)}</span><span style='right:0'>{pct(0.40, 0)}+</span></div>
<div class='box'><h4>{T['card']} · <span class='mono' style='color:var(--ink)'>{d['total']}</span> {T['pts']}</h4>{items}</div>
<div class='box'><h4>{T['why']}</h4><ul class='why' style='margin:0; padding-left:20px'>{''.join(f'<li>{w}</li>' for w in why)}</ul>
<p style='margin:8px 0 0 0; font-size:14px; color:var(--muted)'>{T['why_rule_a'] if rule == 'A' else T['why_rule_b']} {T['fulltest']}</p></div>
</div>""")
            with st.expander(T["counsel_h"]):
                st.write(counsel)
                st.caption(f"**{T['not_h']}.** {T['not_b']}")

# mobile: a result bar fixed at the bottom of the screen
if d is not None:
    st.html(f"<a class='sticky' href='#sonuc' style='background:{LANE_BG[d['lane']]}; color:{LANE_FG[d['lane']]}'><span>{T['lanes'][d['lane']]}</span>"
            f"<span class='mono'>{pct(p)} · {d['total']} {T['pts']}</span><span>{T['sticky_go']}</span></a>")
else:
    st.html(f"<a class='sticky' href='#hesapla' style='background:#1B2128; color:#fff'><span>{T['wait_h']}</span><span>{T['age_needed']}</span></a>")

# ---------------------------------------------------------------- about band (was the hero; now below the calculator)
st.html(f"""<section class='hero' style='margin-top:56px'>
<h2 class='hh'>{T['h1']}</h2><p class='lead'>{T['lead']}</p>
<div class='ctas'><a class='btn p' href='#guven'>{T['cta1']}</a><a class='btn s' href='#kart'>{T['cta2']}</a></div>
<div class='stats'>
<div class='stat'><div class='v'>{pct(S['covered'], 0)}</div><div class='k'>{T['s1']}</div><div class='d'>{T['s1b'].format(m=round(100 * S['moved']))}</div></div>
<div class='stat'><div class='v'>{pct(S['t_covered'], 0)}</div><div class='k'>{T['s2']}</div><div class='d'>{T['s2b']}</div></div>
<div class='stat'><div class='v'>{V['points_mismatch'] + V['lane_mismatch']}</div><div class='k'>{T['s3']}</div><div class='d'>{T['s3b'].format(prof=PROF)}</div></div>
<div class='stat'><div class='v'>{n_int(S['n'])}</div><div class='k'>{T['s4']}</div><div class='d'>{T['s4b'].format(pos=S['n_pos'], y0=S['year_min'], y1=S['year_max'])}</div></div>
</div></section>""")

# ---------------------------------------------------------------- evidence
st.html(f"""<div id='guven'></div><h2 class='sec-h' style='margin-top:48px'>{T['ev_h']}</h2>
<div class='ev'>
<div class='evc'><h3>{T['ev1']}</h3><p>{T['ev1b'].format(m=round(100 * S['moved']), c=round(100 * S['covered']))}</p></div>
<div class='evc'><h3>{T['ev2']}</h3><p>{T['ev2b'].format(tests=V['tests_passed'], prof=PROF, rnd=n_int(V['random_profiles']))}</p></div>
<div class='evc'><h3>{T['ev3']}</h3><p>{T['ev3b'].format(y0=S['year_min'], y1=S['year_max'])}</p></div>
</div>""")

st.html(f"<div id='kart'></div><h2 class='sec-h' style='margin-top:40px'>{T['card_h']}</h2><p class='sec-lead'>{T['card_b']}</p>")
_pdf = os.path.join(HERE, "assets", "BRCA_Oncelik_Algoritmasi_TR.pdf")
if os.path.exists(_pdf):
    with open(_pdf, "rb") as fh:
        st.download_button(T["card_dl"], fh.read(), file_name="BRCA_Oncelik_Algoritmasi_TR.pdf", mime="application/pdf", key="dl_pdf")

st.html(f"<div class='foot'><span>{T['foot']}</span><span class='mono'>{T['build'].format(b=S['build'], tests=V['tests_passed'])}</span></div>")
