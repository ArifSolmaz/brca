"""Bilingual teaching text; no fitting, patient records or calculator state."""
import json
from pathlib import Path
ASSETS = Path(__file__).resolve().parent / 'assets' / 'model_details'
SYMBOLS_TR = json.loads((ASSETS / 'symbols_tr.json').read_text())
SYMBOLS_EN = [
('β₀','Intercept: the starting value for every patient’s z score, −1.608283515050.'),
('βⱼ','Learned raw-unit coefficient for input j. It is not a points-card weight.'),
('xⱼ','The patient’s input j: years, percentage, relative count, or a 0/1 indicator.'),
('j; 26','j indexes the inputs. There are 26 coefficient terms, excluding the intercept.'),
('Σ','Sum: add every βⱼ × xⱼ product from j = 1 to 26.'),
('z','Raw linear score: intercept plus all weighted inputs. It is not a percentage.'),
('p; p_ham / p_raw','p denotes a probability between 0 and 1. p_raw (Turkish: p_ham) is the sigmoid result before calibration.'),
('η; p_son / p_cal','η (eta) is the calibrated linear score. p_cal (Turkish: p_son) is converted to the displayed percentage.'),
('a; b','Platt calibration intercept and slope: a = −1.824095746896; b = 0.939227549588.'),
('e; exp(t)','e ≈ 2.71828 is Euler’s number. exp(t) means e raised to power t; t is the exponent. exp(−z) = e⁻ᶻ.'),
('log; logit(p)','log is the natural logarithm. logit(p) = log[p/(1−p)], converting probability to the linear-score scale.'),
('βⱼ*; β₀*','The star labels equivalent calibrated coefficients: βⱼ* = bβⱼ; β₀* = a + bβ₀. Do not calibrate again.'),
('OR; odds','Odds = p/(1−p). OR is a ratio of odds, not a percentage-point difference or a causal effect.'),
('c_model; c_missing; c₃₀','c_model is an input’s contribution to z. c_missing and c₃₀ are the contributions of missing Ki-67 and measured Ki-67 of 30%.'),
('n; min(n,2)','Number of relevant relatives. min selects the smaller number; a card row counts at most two relatives.'),
('S_card; s_card','Uppercase S is the total card score. Lowercase s is its lane code: 0, 1 or 2. Turkish labels use kart instead of card.'),
('s_model','Probability lane: p <0.10 → 0; 0.10 ≤ p <0.20 → 1; p ≥0.20 → 2.'),
('u','Urgency lane: 2 if a treatment decision awaits the result; otherwise 1 if the familial P/LP box is checked; otherwise 0.'),
('A; B; max','A and B are decision rules. max selects the highest lane. Codes: 0 normal, 1 priority, 2 urgent.'),
('min; round','min selects the smallest value. round selects the nearest integer; exact halves go to the even integer in the code.'),
('N','Approximate “1 in N” description: round(1/p). This is not an observed patient count.'),
('i; qᵢ; qᵢ₊₁','i is the zero-based index of the lower percentile knot; qᵢ and qᵢ₊₁ are the probabilities at two adjacent knots.'),
('Position; Fill','Position is the rank among development scores. Fill is the visual bar percentage. Neither is the patient’s probability.'),
('π','Development-group positive proportion, 167/1295. This is not the geometric constant π ≈3.14.'),
('w₊; w₋','Training weights assigned to the positive and other outcome classes. The +/− subscripts identify classes.'),
('ΔN; ΔT','Delta means difference. In capacity calculations, ΔN is the package-count difference and ΔT the target-positive difference. This N is separate from “1 in N”.'),
('TP; FN','True positives: carriers above the threshold. False negatives: carriers below the threshold.'),
('TN; FP','True negatives: noncarriers below the threshold. False positives: noncarriers above the threshold.'),
('NPV','Negative Predictive Value: noncarrier proportion below the threshold, TN/(TN+FN).'),
('AUC; ROC','Area Under the Curve: area under the Receiver Operating Characteristic curve, plotting sensitivity against false-positive rate. A single threshold table cannot give AUC.'),
('C; L2','C is the inverse regularisation-strength setting; smaller C gives stronger penalisation. L2 penalisation is based on squared coefficients.'),
('y; 0/1','Training outcome y is 1 for the historical Positive label, 0 for other labels. Input indicators use 1 for present/selected and 0 for absent/not selected.'),
('=; ≈; ×; /','= means equal; ≈ approximately; × multiplication; / or a fraction bar division. Minus denotes a negative value or subtraction.'),
('<; ≤; >; ≥','Less than; less than or equal; greater than; greater than or equal. Equality at a threshold matters.'),
('%; subscript; exponent','Multiply probability by 100 to obtain percent. Subscripts name terms; raw/cal are not multipliers. A superscript gives a power; the star on β* is a label, not a power.'),
]
METHODS = {
 'tr': [
 ('Eğitim verisi ve hedef', 'Özgün geliştirme grubu 1.295 kişi: 167 Positive, 1.128 diğer etiket. Meme grubu 1.088, yalnız over 207; tanı yılları 1988–2020. Hedef y, BRCA_status_v3_strict tam olarak Positive ise 1, diğer etiketlerde 0’dır. Bu kodlama bütün sıfırların güncel ve eksiksiz klinik negatifliği kanıtlandığı anlamına gelmez. Genişleyen arşiv ve 87 ailelik tümör boyutu bulgusu modele eklenmemiştir.'),
 ('Ön işleme', 'Aile sayımları sayısala çevrilip eksikler sıfırla doldurulmuş; yaş eksikse tanı grubu medyanı ve eksiklik göstergesi kullanılmıştır. Bölge eksikse Marmara; grade 1 ve 3 dışındakiler g2 referansıdır. Ki-67 eksikse 30 ve ayrı eksiklik göstergesi 1 kullanılır. Panel boş yaşla sonuç üretmez; yalnız over seçimi TNBC’yi kapatır ve Ki-67’yi eksik yapar.'),
 ('Modelin kurulması', 'Sınıf dengeli, L2 cezalı lojistik regresyon; max_iter = 5000, tohum = 2020. C adayları 0,01; 0,03; 0,1; 0,3; 1. Ana betik 5 dış kat × 5 tekrar ve her dış eğitimde 3 iç katla AUC üzerinden C seçer. Seçilen C’lerin en sık değeri 0,3’tür; final model bütün geliştirme verisine kurulur. Yaş, aile sayımları ve Ki-67 eğitimde standartlaştırılmış; katsayılar ham birimlere çevrilerek dışa aktarılmıştır. Panelde tekrar standartlaştırılmaz.'),
 ('Kalibrasyon ve ayrı kuyruk değerlendirmesi', 'Ana betikte kişi başına tekrarların kat dışı ham olasılıkları ortalanır; logit değerleri ile Platt kalibrasyonu öğrenilir. Panel kayıtlı a ve b’yi final z’ye uygular. combined_policy betiği ise dış eğitimde ölçekleme, iç kat dışı tahminlerle kalibrasyon ve dış testte kuyruk sayımı yapar. Bu yollar aynı değerlendirme zinciri değildir.'),
 ('Doğrulama sınırları', 'Ana betikte medyan atama ve standartlaştırma dış kat ayrımından önce yapılmıştır. Kuyruk betiği dış kat ölçeklemesini eğitimde yapsa da önceden doldurulmuş veriyi kullanır. StratifiedKFold aile gruplu ayırma değildir. Bu nedenle bütün işlem zinciri kat içinde öğrenilmiş veya aile bağımsızlığı güvence altına alınmış denemez. AUC aralığı kişi bazlı 2.000 bootstrap; iyimserlik düzeltmesi 200 bootstrap’a dayanır. Bağımsız klinik doğrulama değildir.'),
 ('Kart ve karar kuralları', 'Kart, 16 aday özelliğe kurulan ayrı sınıf dengeli L2 modelden gelir; C = 0,3. Katsayılar 0,5 log-odds birimine bölünüp tamsayıya yuvarlanmış, sıfır satırlar çıkarılmıştır; final kart 14 satırdır. Ana model β katsayılarının yuvarlanması değildir. Kart 0–3 normal, 4 öncelikli, ≥5 acil; model < %10 normal, %10–<%20 öncelikli, ≥%20 acildir. A üç şeridin en büyüğü; B model ve aciliyetin büyüğüdür. B öneridir. A’da acil şerit; B’de model ≥%20 hızlı paketi tetikler.'),
 ('Eksiklik ve aile kutusunun anlamı', 'Bilinmeyen Ki-67 ile ölçülmüş %30 aynı şey değildir: eksik göstergesi yalnız modelde ek katkı yapar; kartta yüksek Ki-67 puanı vermez. Aile sayımı tavanı kart satırında 2’dir, modelde sayımlar 6’ya kadar kullanılır. Ailede P/LP kutusu β toplamını değiştirmez fakat model bu bilgiyi içermediğinden kişisel yüzde başlığı bastırılır. Boş bilgi gerçek sıfır değildir.'),
 ('Kapasite ve test azaltma', 'Kapasite paneli yeni hasta tahmini yapmaz; altı kayıtlı stratejinin toplu sonuçlarını okur. Çapraz doğrulama sayıları tekrar ortalamaları, zamansal sayılar 477 kişi/52 taşıyıcı içindir. Varsayımsal %5 test azaltma çizgisi ayrıca kart ≥4, over, erkek meme, TNBC, ailede over, aciliyet ve açık yaş korumasında <45 yaşı dışlar. Tam test planı sürer; bu test atlama talimatı değildir.'),
 ],
 'en': [
 ('Development data and outcome', 'The original development group contains 1,295 people: 167 labelled Positive and 1,128 with other labels; 1,088 in the breast group and 207 ovarian-only, diagnosed in 1988–2020. The outcome y equals 1 only when BRCA_status_v3_strict is exactly Positive; other labels become 0. This does not establish complete, up-to-date clinical negativity for every zero. Neither the expanded archive nor the unvalidated 87-family tumour-size finding has been added to the model.'),
 ('Preprocessing', 'Family counts were converted to numbers and missing values filled with zero. Missing age used the diagnosis-group median plus a missingness indicator. Missing region maps to Marmara; grades other than 1 or 3 map to the g2 reference. Missing Ki-67 uses 30 plus a separate indicator set to 1. The panel gives no personal result for blank age; ovarian-only selection clears TNBC and sets Ki-67 to missing.'),
 ('Model fitting', 'Class-balanced L2 logistic regression used max_iter = 5000 and seed = 2020. Candidate C values were 0.01, 0.03, 0.1, 0.3 and 1. The main script used 5 outer folds × 5 repeats, with 3 inner folds selecting C by AUC. The modal selected C was 0.3; the final model was fitted to the complete development data. Age, family counts and Ki-67 were standardised for fitting; exported coefficients were converted back to raw units. The live panel does not standardise them again.'),
 ('Calibration and the separate queue evaluation', 'The main script averages repeated out-of-fold raw probabilities for each person and fits Platt calibration to their logits. The panel applies the stored a and b to the final-model z score. The combined_policy script instead learns scaling on outer training data, calibrates using inner out-of-fold predictions, and counts queue outcomes in the outer test fold. These are distinct evaluation pipelines.'),
 ('Validation limitations', 'The recovered main script imputes medians and standardises before the outer split. The queue script learns outer-fold scaling on training data but still uses pre-imputed data. StratifiedKFold does not group families. Therefore neither fully fold-contained preprocessing nor independence of relatives is guaranteed. The AUC interval uses 2,000 person-level bootstrap samples; optimism correction uses 200 bootstrap samples. These are not independent clinical validation.'),
 ('The separate card and decision rules', 'The card comes from a separate class-balanced L2 model with 16 candidate features and C = 0.3. Its coefficients were divided by 0.5 log-odds units and rounded; zero rows were removed, leaving 14 rows. It is not obtained by rounding the main model’s β coefficients. Card lanes: 0–3 normal, 4 priority, ≥5 urgent. Model lanes: <10% normal, 10–<20% priority, ≥20% urgent. A takes the maximum of card, model and urgency; B takes model and urgency only. B remains a proposal. Rapid-package triggers: urgent final lane for A, model ≥20% for B.'),
 ('Missingness and the familial-variant box', 'Unknown Ki-67 differs from measured 30%: the missingness indicator adds a model contribution but gives no high-Ki-67 card point. Each family card row is capped at two relatives; the model uses counts up to six. The familial P/LP box does not change the β sum, but the personal probability headline is suppressed because the model does not include this familial-variant information. Unknown information is not a known zero.'),
 ('Capacity and hypothetical test reduction', 'The capacity panel reads aggregate outcomes for six stored strategies; it does not predict new patients. Cross-validation counts are repeat means; temporal counts concern 477 people and 52 carriers. The hypothetical 5% test-reduction line also excludes card ≥4, ovarian cancer, male breast cancer, TNBC, ovarian family history, urgency and, when enabled, age <45. Full testing remains the plan; this is not an instruction to omit testing.'),
 ]}
LABELS_EN={'intercept':'Intercept','age':'Age at diagnosis','age_missing':'Age missing indicator','tnbc':'TNBC indicator','ki67':'Ki-67 (%)','ki67_missing':'Ki-67 missing indicator','fdr_breast_lt40':'First-degree breast cancer <40','fdr_breast_ge40':'First-degree breast cancer ≥40','sdr_breast_lt40':'Second-degree breast cancer <40','sdr_breast_ge40':'Second-degree breast cancer ≥40','tdr_breast':'Third/fourth-degree breast cancer','fdr_ovary':'First-degree ovarian cancer','sdr_ovary':'Second–fourth-degree ovarian cancer','fdr_other':'First-degree other cancer'}
LABELS_TR={'intercept':'Sabit','age':'Tanı yaşı','age_missing':'Yaş eksik göstergesi','tnbc':'TNBC göstergesi','ki67':'Ki-67 (%)','ki67_missing':'Ki-67 eksik göstergesi','fdr_breast_lt40':'1. derece meme <40','fdr_breast_ge40':'1. derece meme ≥40','sdr_breast_lt40':'2. derece meme <40','sdr_breast_ge40':'2. derece meme ≥40','tdr_breast':'3.–4. derece meme','fdr_ovary':'1. derece over','sdr_ovary':'2.–4. derece over','fdr_other':'1. derece başka kanser'}

# Shared wording for the student page and both teaching PDFs.
ORIGIN_INTRO = {
    'en': {
        'title': 'Where this model came from',
        'paragraphs': [
            'We used records from 1,295 past patients whose BRCA test results were already recorded. The computer looked for combinations of age, family history and tumour features that helped distinguish positive results from other recorded results.',
            'The calculator applies that learned pattern to the inputs you enter. We checked its performance within the original patient group, but we still need a separate group of patients to show how reliably it works beyond that group. Having more records in the archive does not automatically provide that proof.',
        ],
    },
    'tr': {
        'title': 'Önce bir soru sorduk',
        'paragraphs': [
            'Bir hastanın yaşı, ailedeki kanser öyküsü ve tümörünün özellikleri, BRCA testinin sonucuna dair ipucu verebilir mi? Model bu soruyla başladı. Test sonucu kayıtlarda bulunan 1.295 hastanın bilgileri kullanıldı. Bilgisayar, hangi bilgilerin birlikte pozitif sonuçla daha sık görüldüğünü öğrenerek her birine bir ağırlık, yani katsayı verdi.',
            'Arşivi büyütürken iş yalnız dosya toplamak değildi: aynı kişiye ait kayıtları bulmak, aileleri ayırmak ve raporlarla klinik bilgileri eşleştirmek gerekiyordu. Ama daha çok dosya, kendiliğinden daha güvenilir model demek değil. Hesaplayıcı hâlâ ilk hasta grubundan öğrendiği katsayıları kullanıyor. Başka hastalarda da işe yaradığını göstermek için ayrı bir hasta grubuyla sınanması gerekiyor.',
        ],
    },
}

# Readable names for encoded categories; the encoded inputs and weights stay unchanged.
LABELS_TR.update({'grade=g1':'Tümör derecesi 1', 'grade=g3':'Tümör derecesi 3',
 'dx=bilateral':'İki memede kanser', 'dx=breast_ovary':'Meme ve yumurtalık kanseri',
 'dx=ovarian':'Yalnız yumurtalık kanseri', 'dx=male':'Erkekte meme kanseri'})
LABELS_EN.update({'grade=g1':'Tumour grade 1', 'grade=g3':'Tumour grade 3',
 'dx=bilateral':'Bilateral breast cancer', 'dx=breast_ovary':'Breast and ovarian cancer',
 'dx=ovarian':'Ovarian-only cancer', 'dx=male':'Male breast cancer'})
for _key, _tr, _en in [('balkans','Balkanlar','Balkans'),('black_sea','Karadeniz','Black Sea'),
 ('middle_anatolia','İç Anadolu','Central Anatolia'),('eastern_anatolia','Doğu Anadolu','Eastern Anatolia'),
 ('southeastern_anatolia','Güneydoğu Anadolu','Southeastern Anatolia'),('aegean','Ege','Aegean'),
 ('mediterranean','Akdeniz','Mediterranean')]:
 LABELS_TR['region='+_key]='Köken bölgesi: '+_tr
 LABELS_EN['region='+_key]='Origin region: '+_en
