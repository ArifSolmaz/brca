"""Typeset the existing bilingual explanation; no patient analysis or model fitting.

Requires XeLaTeX. Reads aggregate evidence and frozen coefficients only.
"""
from pathlib import Path
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'tmp/pdfs/model_guides'
OUT = ROOT / 'output/pdf'
ASSETS = ROOT / 'assets/model_details'
MODEL = json.loads((ROOT / 'model_full_embedded.json').read_text())


def esc(value):
    text = ''.join({'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
                    '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
                    '^': r'\textasciicircum{}'}.get(c, c) for c in str(value))
    for symbol,tex in [('xⱼ',r'$x_j$'),('βⱼ',r'$\beta_j$'),('β₀',r'$\beta_0$'),('pᵢ',r'$p_i$'),('yᵢ',r'$y_i$')]:text=text.replace(symbol,tex)
    return text


def build(lang, web=False):
    tr = lang == 'tr'
    def t(a, b): return a if tr else b
    parts = []
    blocks = []
    def p(a, b):
        blocks.append({'type': 'paragraph', 'text': t(a,b)})
        parts.append(esc(t(a, b)).replace('\n',r'\par\smallskip ') + '\n\n')
    def raw(value):
        parts.append(value + '\n')
        if r'\href{' in value:
            import re
            match = re.search(r'\\href\{(.*?)\}\{(.*)\}', value)
            if match:
                blocks.append({'type':'link','url':match[1].replace(r'\&','&'),'text':match[2].replace(r'\_','_')})
    def math(value):
        blocks.append({'type':'math','text':value})
        raw('\\[\n' + value + '\n\\]')
    def heading(a, b):
        blocks.append({'type':'heading','text':t(a,b)})
        raw(r'\subsection*{' + esc(t(a, b)) + '}')
    def page(number, a, b):
        blocks.append({'type':'chapter','number':number,'text':t(a,b)})
        if number: raw(r'\clearpage')
        raw(r'\section*{' + (str(number) + ' · ' if number else '') + esc(t(a, b)) + '}')
    def note(a, b):
        blocks.append({'type':'note','text':t(a,b)})
        raw(r'\begin{quote}\color{accent}\bfseries ' + esc(t(a, b)) + r'\end{quote}')
    def table(headers_tr, headers_en, rows, widths=None):
        headers = headers_tr if tr else headers_en
        blocks.append({'type':'table','headers':headers,'rows':rows})
        spec = widths or ('X' + 'r' * (len(headers) - 1))
        raw(r'\begin{tabularx}{\linewidth}{' + spec + r'}\toprule')
        raw(' & '.join(r'\textbf{' + esc(x) + '}' for x in headers) + r'\\\midrule')
        for row in rows:
            raw(' & '.join(esc(x) for x in row) + r'\\')
        raw(r'\bottomrule\end{tabularx}\par\medskip')

    title = t('BRCA MODEL REHBERİ', 'BRCA MODEL GUIDE')
    subtitle = t('Gerçek kayıtlardan modele, hesaplamalara ve kanıtın sınırlarına',
                 'From actual records to the model, calculations and limits of the evidence')
    preamble = r'''\documentclass[10pt,a4paper]{article}
\usepackage[margin=21mm,headheight=15pt,headsep=9mm,footskip=10mm]{geometry}
\usepackage{fontspec}
\setmainfont{Arial}
\usepackage{amsmath,amssymb,booktabs,tabularx,array,xcolor,fancyhdr,lastpage,enumitem}
\usepackage[unicode,colorlinks=true,urlcolor=accent,linkcolor=accent]{hyperref}
\definecolor{accent}{HTML}{554491}
\definecolor{ink}{HTML}{202B38}
\color{ink}
\hypersetup{pdftitle={TITLE},pdfauthor={Project team},pdfsubject={SUBJECT}}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlength{\emergencystretch}{2em}
\renewcommand{\arraystretch}{1.35}
\setlength{\tabcolsep}{5pt}
\setlist{nosep,leftmargin=1.5em}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\color{accent}HEADER}
\fancyhead[R]{\small DATE}
\fancyfoot[L]{\scriptsize FOOTER}
\fancyfoot[R]{\small\thepage\ / \pageref*{LastPage}}
\renewcommand{\headrulewidth}{0.6pt}
\begin{document}
'''.replace('TITLE', esc(title)).replace('SUBJECT', esc(subtitle)).replace(
        'HEADER', esc(title)).replace('DATE', t('3 Kasım 2026', '3 November 2026')).replace(
        'FOOTER', esc(t('Mevcut sonuçların anlatımı · Yeni analiz yok · Hasta kimliği içermez',
                        'Existing results explained · No new analysis · No patient identifiers')))

    page(0, 'Veriden kanıta: bütün hikâye', 'From data to evidence: the complete story')
    raw(r'{\Huge\bfseries\color{accent}' + esc(title) + r'}\par\bigskip')
    raw(r'{\Large ' + esc(subtitle) + r'}\par\bigskip')
    p('Genetik, istatistik veya programlama bilmeyen; konuyu sıfırdan öğrenmek isteyen öğrenciler için hazırlanmıştır.',
      'For students starting without prior knowledge of genetics, statistics or programming.')
    note('Bu rehber mevcut çalışmayı açıklar. Yeni hasta analizi, hipotez testi, yeniden eğitim veya hesaplayıcı değişikliği yapılmadı.',
         'This guide explains the existing work. No new patient analysis, hypothesis test, model fitting or calculator change was performed.')
    heading('Birbirinden ayıracağımız üç iş', 'Three distinct parts of the work')
    p('1. Arşiv: dosya, örnek, kişi ve aileleri eşleştirmek; hangi verilerin kullanılabildiğini belirlemek.\n2. Tahmin: özgün 1.295 kişide geliştirilen modelin hesabını ve değerlendirmesini açıklamak.\n3. Biyolojik araştırma: genetik özellikler ile klinik özellikler arasındaki mevcut karşılaştırmaları ve belirsizliklerini incelemek.',
      '1. Archive: link files, specimens, people and families, and establish which data are usable.\n2. Prediction: explain the calculations and evaluation of the model developed in the original 1,295 people.\n3. Biological research: understand existing comparisons between genetic and clinical features and their uncertainty.')
    heading('Okuma yolu', 'Reading route')
    p('Biyoloji → arşiv → modelin hasta grubu → kodlama ve eksikler → öğrenme → katsayılar → elle hesap → puan kartı → istatistik → laboratuvar ödünleşimleri → biyolojik bulgu → bağımsız doğrulama → yazılım ve kaynaklar.',
      'Biology → archive → development patients → encoding and missing data → learning → coefficients → manual calculation → points card → statistics → laboratory trade-offs → biological finding → independent validation → software and sources.')
    p('Rehber tarihi 3 Kasım 2026’dır. Arşiv ve doğrulama sayıları mevcut 24 Ekim denetiminden alınmıştır. Ayrı araştırma raporunun 25 Ekim tarihi değiştirilmemiştir. Modelin kayıtlı sürümü: '+MODEL['build']+'.',
      'Guide date: 3 November 2026. Archive and validation counts come from the existing 24 October audit. The separate research report retains its 25 October date. Stored model version: '+MODEL['build']+'.')
    raw(r'\href{https://brca-istun.streamlit.app/?sayfa=model\&dil='+lang+r'}{'+esc(t('Model ayrıntıları sayfasını aç', 'Open the model details page'))+'}')

    page(1, 'Biyoloji ve genetik dili', 'The language of biology and genetics')
    p('Vücudumuz hücrelerden oluşur. DNA (deoksiribonükleik asit), protein üretiminde kullanılan genetik bilgiyi taşır. Gen, bu bilginin belirli bir işlevle ilişkili bölümüdür. Proteinler hücrenin birçok işini yapan moleküllerdir.',
      'Our bodies consist of cells. DNA (deoxyribonucleic acid) carries genetic information used to make proteins. A gene is a section associated with a particular function. Proteins perform many of the cell’s jobs.')
    p('BRCA1 ve BRCA2, DNA hasarını onarmaya yardımcı olan proteinlerle ilişkili genlerdir. Bir genetik değişikliğe varyant denir. Kalıtsal bir varyant aile içinde aktarılabilir. Tümörde sonradan oluşan somatik değişiklik ise bununla aynı şey değildir.',
      'BRCA1 and BRCA2 are genes associated with proteins that help repair damaged DNA. A genetic change is called a variant. An inherited variant can be passed through a family. A somatic change acquired in a tumour is a different concept.')
    table(['Terim', 'Anlamı'], ['Term', 'Meaning'], [
        ('P / Pathogenic',t('Patojenik; hastalıkla ilişkili zarar verici etkisi gösterilmiş.', 'A disease-related harmful effect is established.')),
        ('LP / Likely Pathogenic',t('Olası patojenik; zarar verici etkiye ilişkin güçlü kanıt.', 'Strong evidence suggests a harmful effect.')),
        ('VUS / Variant of Uncertain Significance',t('Anlamı belirsiz varyant; etkisi yeterince bilinmiyor.', 'Its significance is not sufficiently understood.')),
        ('B / LB',t('Benign / likely benign: zararsız / olası zararsız.', 'Benign / likely benign: harmless or likely harmless.')),
        ('CNV / Copy Number Variant',t('Bir DNA bölümünün kopya sayısındaki değişiklik.', 'A change in the copy number of a DNA segment.')),
        ('NGS / Next-Generation Sequencing',t('Çok sayıda DNA bölgesini paralel inceleyen dizileme yöntemleri.', 'Sequencing methods examining many DNA regions in parallel.')),
        ('MLPA / Multiplex Ligation-dependent Probe Amplification',t('Belirli bölgelerde kopya kaybı veya artışını değerlendiren yöntem.', 'A method assessing copy-number losses or gains in selected regions.')),
    ], r'p{.40\linewidth}X')
    note('Her varyant zararlı değildir. Hastalıkla ilişkili bir BRCA varyantını taşımak, kesinlikle kanser olunacağı anlamına gelmez.',
         'Not every variant is harmful. Carrying a disease-related BRCA variant does not mean cancer is inevitable.')
    p('Tahmin sorumuz, kişinin gelecekte kanser olup olmayacağı değildir. Mevcut klinik bilgilerin kayıtlı BRCA test sonucunu tahmin etmeye yardımcı olup olamayacağını araştırıyoruz.',
      'Our prediction question is not whether someone will develop cancer in the future. It is whether existing clinical information can help predict the recorded BRCA test result.')

    page(2, 'Gerçek arşiv: dosya, satır, kişi ve aile', 'The actual archive: files, rows, people and families')
    p('Başlangıçta tek bir temiz tablo yoktu. Drive’da bireysel hasta klasörleri, genetik raporlar, varyant çalışma kitapları ve 2019, 2020, 2022 gibi farklı yıllara ait klinik dosyalar bulunuyordu. Aynı hasta farklı sürümlerde veya tekrar örneklerle yer alabilir.',
      'We did not start with one clean table. Drive contained individual patient folders, genetic reports, variant workbooks and clinical files from years including 2019, 2020 and 2022. The same person can appear in different versions or with repeat specimens.')
    table(['Kayıt düzeyi', 'Sayı'], ['Record level', 'Count'], [
        (t('Hasta klasörleri','Patient folders'),'2,259'),
        (t('Kabul edilmiş operasyonel genetik kişi kimlikleri','Established operational genetic patient entities'),'2,148'),
        (t('Klinik kaynak sürümlerindeki satırlar','Rows across clinical source versions'),'7,939'),
        (t('Kabul edilmiş klinik bağlantısı olan genetik kişiler','Genetic entities with accepted clinical links'),'1,445'),
        (t('Tutarlı kayıtlı aile kimlikleri','Consistently recorded family IDs'),'1,989'),
        (t('Temkinli analizde tutulan varyant çağrı satırları','Conservatively retained variant-call rows'),'84,492'),
    ])
    p('Bu sayılar aynı şeyi saymaz ve tek bir hasta seçim zinciri gibi birbirinden çıkarılamaz. 2.148, bütün arşivin kesin benzersiz hasta toplamı değildir; klinik kayıtları olup genetik bağlantısı henüz kabul edilmeyen bileşenler otomatik olarak ek kişi sayılamaz. Aile numarası farklı olması, belgelenmemiş akrabalığı dışlamaz.',
      'These are different counting units, not a single flow from which all exclusions can be subtracted. The 2,148 entities are not a certified unique-patient total for the entire archive. Clinical-only components without an accepted genetic link cannot automatically be counted as additional people. Different recorded family IDs do not exclude undocumented relatedness.')
    p('84.492 satır, 84.492 benzersiz varyant değildir. Aynı varyant farklı kişilerde görülebilir. Bir varyantın tabloda olmaması da o DNA bölgesinin yeterli kalitede incelenip negatif bulunduğunu kanıtlamaz; tam incelenebilirlik maskeleri mevcut değildir.',
      '84,492 rows do not mean 84,492 unique variants. A variant can recur in different people. Absence from a table does not establish adequate examination and a negative result for that region; complete callability masks are unavailable.')
    p('Kimlik eşleştirmesinde hasta kodu, isim, doğum tarihi, aile numarası, protokol ve özgün rapor birlikte değerlendirilir. Çelişkili bağlantıları zorla kabul etmek, yanlış bir kişiye genetik veya klinik bilgi atayabilir.',
      'Identity linkage considers patient code, name, date of birth, family number, protocol ID and original reports together. Forcing a conflicting link can assign genetic or clinical information to the wrong person.')
    note('Dosya sayısı ≠ satır sayısı ≠ örnek sayısı ≠ kişi sayısı ≠ bağımsız aile sayısı.',
         'Files ≠ rows ≠ specimens ≠ people ≠ independent families.')

    page(3, 'Modelin hasta grubu ve klinik alanlar', 'Development patients and clinical fields')
    p('Hesaplayıcı, genişleyen arşivin tamamıyla değil, özgün 1.295 kişilik geliştirme grubuyla kurulmuştur. Tanı yılları 1988–2020 arasındadır. Meme ile ilişkili ilk dört kategori toplam 1.088 kişi; yalnız over grubu 207 kişidir.',
      'The calculator was developed using the original 1,295-person group, not the entire expanded archive. Diagnosis years range from 1988 to 2020. The first four breast-related categories total 1,088 people; 207 are ovarian-only.')
    table(['Tanı','Kişi','Positive'],['Diagnosis','People','Positive'],[
        (t('Tek taraflı meme','Unilateral breast'),978,104),(t('Bilateral meme','Bilateral breast'),75,17),
        (t('Meme ve over','Breast and ovarian'),22,10),(t('Erkek meme','Male breast'),13,2),
        (t('Yalnız over','Ovarian only'),207,34),(t('Toplam','Total'),1295,167)])
    p('Hedef değişken y, kaydın BRCA_status_v3_strict etiketi tam olarak Positive ise 1, diğer etiketlerde 0’dır. Diğer 1.128 etiketin tamamını güncel, eksiksiz klinik negatiflik olarak kabul etmiyoruz.',
      'The target y is 1 when BRCA_status_v3_strict is exactly Positive, and 0 for other labels. We do not treat all 1,128 other labels as established complete, up-to-date clinical negatives.')
    math(r'\pi=\frac{167}{1295}\approx0.12896=12.9\%')
    p('Burada π, geliştirme grubunun pozitif etiket oranıdır; genel toplumun taşıyıcılık oranı veya geometrik π sabiti değildir.',
      'Here π is the positive-label proportion in the development group, not general-population carrier frequency or the geometric constant pi.')
    table(['Alan','Açıklama'],['Field','Explanation'],[
        (t('Tanı yaşı','Age at diagnosis'),t('Tanı konduğu zamanki yaş; bugünkü yaş değil.','Age when diagnosed, not current age.')),
        (t('Aile öyküsü','Family history'),t('Akrabalık derecesi, kanser türü, tanı yaşı ve kişi sayımı.','Relationship degree, cancer type, diagnosis age and relative counts.')),
        ('Grade',t('Mikroskobik hücre farklılığı; evre ile aynı değildir.','Microscopic abnormality; not the same as stage.')),
        (t('Evre','Stage'),t('Kanserin anatomik yayılımı; bu hesaplayıcıda kullanılmaz.','Anatomical extent; not used by this calculator.')),
        (t('Köken bölgesi','Origin region'),t('Kayıtlı coğrafi kategori; doğrudan genetik soy ölçümü değil.','Recorded geographical category, not measured genetic ancestry.')),
    ],r'p{.25\linewidth}X')
    p('Birinci derece akrabalar anne, baba, kardeş ve çocukları; ikinci derece örneğin büyükanne, büyükbaba, teyze, hala, dayı ve amcayı kapsar. Her arşiv alanı model girdisi değildir: tümör boyutu ve lenf nodu durumu bu modelde kullanılmaz.',
      'First-degree relatives include parents, siblings and children; second-degree relatives include grandparents, aunts and uncles. Not every archive field is a model input: tumour size and lymph-node status are not used here.')

    page(4, 'Kodlama, tümör belirteçleri ve eksik bilgi', 'Encoding, tumour markers and missing information')
    table(['Terim','Tam açılım ve anlam'],['Term','Full name and meaning'],[
        ('ER','Estrogen Receptor. '+t('Östrojen reseptörü.','')),
        ('PR','Progesterone Receptor. '+t('Progesteron reseptörü.','')),
        ('HER2','Human Epidermal Growth Factor Receptor 2. '+t('Tümör değerlendirmesinde kullanılan reseptör/protein.','A receptor/protein assessed in tumours.')),
        ('TNBC','Triple-Negative Breast Cancer. '+t('ER, PR ve HER2 negatif meme kanseri.','Breast cancer classified as negative for ER, PR and HER2.')),
        ('Ki-67',t('Hücre çoğalmasıyla ilişkili belirteç; genellikle yüzde olarak kaydedilir.','A proliferation-related marker, usually recorded as a percentage.')),
        ('IHC','Immunohistochemistry. '+t('Dokuda proteinleri boyamayla değerlendirme.','Staining-based assessment of proteins in tissue.')),
        ('ISH / FISH','In Situ Hybridization / Fluorescence In Situ Hybridization. '+t('Dokuda belirli DNA/RNA hedeflerini değerlendiren yöntemler.','Methods assessing selected DNA/RNA targets in tissue.')),
    ],r'p{.18\linewidth}X')
    p('Kodlama: yaş 38 gibi sayısal; akraba sayısı 1 gibi sayım; TNBC varsa 1, yoksa 0 şeklinde gösterge olur. Tanı, grade ve bölge kategorilere ayrılır. Tek taraflı meme, g2 ve Marmara referanstır; bunlar için ek kategori katsayısı yoktur.',
      'Encoding uses numbers such as age 38, counts such as one relative, and indicators such as TNBC present = 1 or absent = 0. Diagnosis, grade and region are categorical. Unilateral breast, g2 and Marmara are reference categories with no additional category coefficient.')
    p('Geliştirme paketinde 87 yaş eksik, 16 bölge kayıt dışıdır. Ki-67, 464 kişide kayıtlıdır. Eksik veriyi hesapta kullanılabilir hale getirmeye atama (imputation) denir.',
      'The development package records 87 missing ages, 16 unrecorded regions and 464 recorded Ki-67 measurements. Filling missing values for calculation is called imputation.')
    p('Tarihsel işlem: eksik aile sayımları 0; eksik yaş tanı grubu medyanı ve eksiklik göstergesi; eksik bölge Marmara; eksik Ki-67 değeri 30 ve ayrı eksiklik göstergesi 1. Grade 1 veya 3 dışındakiler g2 referansına gider. Canlı panel boş yaşla kişisel sonuç üretmez. Yalnız over seçimi TNBC’yi kapatır ve Ki-67’yi eksik yapar.',
      'Historical processing: missing family counts became 0; missing age used the diagnosis-group median plus an indicator; missing region became Marmara; missing Ki-67 used 30 plus an indicator set to 1. Grades other than 1 or 3 map to g2. The live panel does not give a personal result for blank age. Ovarian-only selection clears TNBC and sets Ki-67 to missing.')
    note('Bilinmeyen bilgi, bilinen sıfır değildir. Ki-67 bilinmiyor ile ölçülmüş %30 aynı şey değildir. Bu işlemler geçmiş modelin kurallarıdır; yeni klinik gerçekler değildir.',
         'Unknown information is not a known zero. Unknown Ki-67 differs from measured 30%. These are existing model rules, not newly established clinical facts.')

    page(5, 'Öğrenme: katsayılar nasıl bulundu?', 'Learning: how were the coefficients obtained?')
    p('Yöntem lojistik regresyondur; derin sinir ağı değildir. Bilgisayar katsayılarla tahmin yapar, tahminleri kayıtlı y sonuçlarıyla karşılaştırır ve hatayı azaltacak katsayıları arar. Katsayıları bulmaya eğitim veya model kurma denir.',
      'The method is logistic regression, not a deep neural network. The computer predicts using coefficients, compares predictions with recorded outcomes y, and searches for coefficients reducing error. Finding the coefficients is called training or fitting.')
    p('Pozitifler azınlık olduğundan sınıf ağırlıkları kullanılmıştır. Bir pozitif kayıttaki hata, eğitimde bir diğer etiketli kayıttaki hatadan daha fazla ağırlık alır; yeni hasta yaratılmaz.',
      'Because positives are the smaller class, class weights give an error on a positive record more influence during fitting than an error on an other-labelled record. This does not create new patients.')
    math(r'w_+=\frac{1295}{2\times167}\approx3.877246,\qquad w_-=\frac{1295}{2\times1128}\approx0.574025')
    p('L2 düzenlileştirme, katsayıların karelerine dayanan ceza ile aşırı büyük katsayıları sınırlar. C, cezanın ters güç ayarıdır: küçük C daha güçlü ceza demektir. Aşırı uyum (overfitting), geçmiş örneklere fazla özel uyup yeni örneklerde başarısız olma sorunudur.',
      'L2 regularisation penalises squared coefficients to discourage excessively large coefficients. C is the inverse penalty-strength setting: smaller C gives stronger penalisation. Overfitting means adapting too specifically to development examples and performing poorly on new ones.')
    p('C adayları: 0,01; 0,03; 0,1; 0,3; 1. Ana betik 5 dış kat × 5 tekrar kullanır. Her dış eğitim grubunda 3 iç kat ile AUC üzerinden C seçilir. En sık seçilen değer 0,3’tür; son model bütün geliştirme verisine kurulur. max_iter = 5000 bir üst yineleme sınırı; seed = 2020 tekrarlanabilirlik ayarıdır, kalite garantisi değildir.',
      'Candidate C values: 0.01, 0.03, 0.1, 0.3 and 1. The main script uses five outer folds × five repeats. Three inner folds select C by AUC within each outer training set. The modal selection is 0.3; the final model is fitted on the complete development data. max_iter = 5000 is an iteration limit; seed = 2020 is a reproducibility setting, not a quality guarantee.')
    p('Standartlaştırma, yaş ve Ki-67 gibi farklı ölçeklerdeki girdileri eğitim için ortak ölçeğe taşır. Katsayılar daha sonra ham birimlere dönüştürülmüştür. Canlı panelde tekrar standartlaştırma yapılmaz.',
      'Standardisation puts differently scaled inputs such as age and Ki-67 on a common scale for fitting. Exported coefficients were converted back to raw units, so the live panel does not standardise again.')
    p('Ana yolda kişi başına tekrarlı kat dışı ham olasılıklar ortalanmış, logit değerleriyle Platt kalibrasyonu öğrenilmiştir. Ayrı kuyruk değerlendirme betiği ise dış eğitimde ölçekleme, iç kat dışı tahminlerle kalibrasyon ve dış testte sayım yapar. Bu yollar tek bir özdeş değerlendirme zinciri değildir.',
      'In the main path, repeated out-of-fold raw probabilities are averaged per person and their logits used to learn Platt calibration. A separate queue-evaluation script learns scaling on outer training data, calibrates using inner out-of-fold predictions and counts outer-test outcomes. These are distinct evaluation pipelines.')

    page(6, 'Öğrenilmiş 26 katsayı ve sabit', 'The 26 learned coefficients and intercept')
    p('Katsayı β, bir girdinin doğrusal skor z’ye katkısını belirler. Pozitif katsayı skoru artırır; negatif katsayı azaltır. Bu tablo yüzde puanları veya nedensel etkiler tablosu değildir. Gösterim yuvarlanmıştır; uygulama tam hassasiyeti kullanır.',
      'A coefficient β determines an input’s contribution to the linear score z. Positive coefficients raise the score; negative coefficients lower it. These are not percentage-point or causal effects. Values are rounded here; the app uses full precision.')
    labels = [
        ('age','Tanı yaşı','Age at diagnosis'),('fdr_breast_lt40','1. derece meme <40','First-degree breast <40'),
        ('fdr_breast_ge40','1. derece meme ≥40','First-degree breast ≥40'),('sdr_breast_lt40','2. derece meme <40','Second-degree breast <40'),
        ('sdr_breast_ge40','2. derece meme ≥40','Second-degree breast ≥40'),('tdr_breast','3.–4. derece meme','Third/fourth-degree breast'),
        ('fdr_ovary','1. derece over','First-degree ovarian'),('sdr_ovary','2.–4. derece over','Second–fourth-degree ovarian'),
        ('fdr_other','1. derece diğer kanser','First-degree other cancer'),('age_missing','Yaş eksik göstergesi','Age-missing indicator'),
        ('tnbc','TNBC','TNBC'),('ki67','Ki-67, yüzde birimi başına','Ki-67, per percentage unit'),
        ('ki67_missing','Ki-67 eksik göstergesi','Ki-67-missing indicator'),('dx=bilateral','Bilateral meme','Bilateral breast'),
        ('dx=breast_ovary','Meme ve over','Breast and ovarian'),('dx=male','Erkek meme','Male breast'),('dx=ovarian','Yalnız over','Ovarian only'),
        ('grade=g1','Grade 1','Grade 1'),('grade=g3','Grade 3','Grade 3'),('region=black_sea','Karadeniz','Black Sea'),
        ('region=eastern_anatolia','Doğu Anadolu','Eastern Anatolia'),('region=middle_anatolia','İç Anadolu','Central Anatolia'),
        ('region=balkans','Balkanlar','Balkans'),('region=southeastern_anatolia','Güneydoğu Anadolu','Southeastern Anatolia'),
        ('region=aegean','Ege','Aegean'),('region=mediterranean','Akdeniz','Mediterranean')]
    raw(r'{\small')
    table(['Girdi','Katsayı'],['Input','Coefficient'],[(t('Sabit başlangıç','Intercept'),f"{MODEL['intercept']:.6f}")]+[
        (t(a,b),f"{MODEL['coef'][key]:.6f}") for key,a,b in labels])
    raw('}')
    p('Referanslar: tek taraflı meme, g2 ve Marmara. Bir hastada bütün göstergeler etkin değildir. Etnik köken gibi araştırmada kullanılan bazı düzeltme değişkenleri bu tahmin modelinde yer almaz.',
      'References: unilateral breast, g2 and Marmara. Not every indicator is active in one patient. Some adjustment variables used in biological research, such as ethnicity, are not inputs to this prediction model.')

    page(7, 'Örnek hasta: girdiler ve katkılar', 'Worked patient: inputs and contributions')
    note('Bu bir kurgu eğitim profilidir; kimliği belirlenebilir gerçek hasta değildir.', 'This is a synthetic teaching profile, not an identifiable real patient.')
    table(['Özellik','Değer'],['Feature','Value'],[
        (t('Tanı yaşı','Age at diagnosis'),'38'),(t('Tanı / grade / bölge','Diagnosis / grade / region'),t('Tek taraflı meme / 2 / Marmara','Unilateral breast / 2 / Marmara')),
        ('TNBC','1'),(t('1. derece meme <40','First-degree breast <40'),'1'),(t('Diğer aile sayımları','Other family counts'),'0'),
        ('Ki-67',t('Bilinmiyor','Unknown')),(t('Aciliyet kutuları','Urgency boxes'),t('Seçili değil','Unchecked'))], r'p{.48\linewidth}X')
    math(r'z=\beta_0+\sum_{j=1}^{26}\beta_jx_j')
    p('xⱼ: hastanın j numaralı girdisi. βⱼ: o girdinin katsayısı. β₀: sabit başlangıç. j: girdi sırası. Σ: bütün katkıları topla. z: doğrusal skor, yüzde değil.',
      'xⱼ: patient input j. βⱼ: its coefficient. β₀: intercept. j: input index. Σ: sum the contributions. z: linear score, not a percentage.')
    math(r'''\begin{aligned}
z={}&-1.608283515050\\
&+38(-0.029741519309)\\
&+1(1.617774083556)\\
&+1(0.809503755804)\\
&+30(0.025035821777)\\
&+1(0.377172660529)
\end{aligned}''')
    math(r'''\begin{aligned}
z={}&-1.608283515050-1.130177733759\\
&+1.617774083556+0.809503755804\\
&+0.751074653320+0.377172660529\\
={}&0.817063904400
\end{aligned}''')
    p('Ki-67 bilinmediği için hem 30 ataması hem eksiklik göstergesi katkı yapar. Ölçülmüş %30 olsaydı eksiklik katkısı olmazdı. Diğer kategori ve aile göstergeleri bu örnekte sıfır katkı yapar.',
      'Unknown Ki-67 activates both the imputed 30 and the missingness indicator. Measured 30% would not activate the missingness contribution. The other category and family indicators contribute zero here.')

    page(8, 'Skordan yüzdeye: sigmoid ve kalibrasyon', 'From score to percentage: sigmoid and calibration')
    p('Sigmoid, herhangi bir doğrusal skoru 0–1 aralığına dönüştürür. e ≈ 2,71828 Euler sayısıdır; üstteki ifade üs anlamına gelir. p bir olasılık, raw ham, cal kalibre edilmiş demektir.',
      'The sigmoid converts a linear score to a number between 0 and 1. e ≈ 2.71828 is Euler’s number; the superscript is an exponent. p means probability, raw means uncalibrated, and cal means calibrated.')
    math(r'\sigma(t)=\frac{1}{1+e^{-t}}')
    math(r'p_{\mathrm{raw}}=\frac{1}{1+e^{-0.817063904400}}\approx0.693612733313')
    p('Yaklaşık %69,4, ekrandaki son yüzde değildir. Kalibrasyon, yüzdelerin gözlenen oranlarla uyumunu ele alır. Sınıf ağırlıklı modelin ham yüzdesi, doğrudan son yüzde olarak kullanılmaz.',
      'Approximately 69.4% is not the final displayed result. Calibration concerns agreement between predicted probabilities and observed frequencies. The class-weighted model’s raw probability is not used directly as the final percentage.')
    math(r'\eta=a+bz,\quad a=-1.824095746896,\quad b=0.939227549588')
    math(r'''\begin{aligned}
\eta&=-1.824095746896+0.939227549588(0.817063904400)\\
&=-1.824095746896+0.767408928786\\
&=-1.056686818109
\end{aligned}''')
    math(r'p_{\mathrm{cal}}=\frac{1}{1+e^{-\eta}}=\frac{1}{1+e^{1.056686818109}}=0.257943116995')
    math(r'100p_{\mathrm{cal}}=25.7943116995\%\approx\boxed{25.8\%}')
    p('η (eta), düzeltilmiş doğrusal skordur; a sabit, b eğim düzeltmesidir. Kalibrasyon yalnız bir kez uygulanır. a+bz içine z yerine ham olasılığı koymak yanlış olur. Logit, sigmoidin ters dönüşümüdür: log[p/(1−p)]. Odds = p/(1−p); OR (Odds Ratio) iki odds değerinin oranıdır, yüzde puan değildir. Son kalibre edilmiş log-odds için katsayı bβ’dır.',
      'η (eta) is the adjusted linear score; a is the intercept correction and b the slope correction. Apply calibration once. Substituting the raw probability instead of z into a+bz is incorrect. The logit is the inverse sigmoid: log[p/(1−p)]. Odds = p/(1−p); OR (Odds Ratio) is a ratio of odds, not a percentage-point difference. On the calibrated log-odds scale the coefficient is bβ.')
    heading('Yalnız yaşı 38’den 48’e değiştirirsek', 'Changing only age from 38 to 48')
    math(r'\Delta z=10(-0.029741519309)=-0.297415193094')
    math(r'z_{\mathrm{new}}=0.519648711306,\qquad p_{\mathrm{new}}\approx0.208164117=20.8\%')
    p('Düşüş yaklaşık 4,98 yüzde puandır. Bu, on yıl yaşlanmanın koruyucu etkisi değildir; sabit modelin farklı bir girdiye verdiği koşullu hesaptır. Önceki değerleri gösteren oklar, son düzenlemeden etkilenen sayıları izlemeye yarar.',
      'The decrease is about 4.98 percentage points. This is not a protective effect of becoming ten years older; it is the frozen model’s conditional response to a different input. Previous-value arrows let students follow quantities affected by the last edit.')

    page(9, 'Ayrı puan kartı ve sıra kuralları', 'The separate points card and queue rules')
    p('Kart ayrı bir sınıf dengeli, L2 cezalı modelden gelir: 16 aday özellik, C = 0,3. Katsayılar 0,5 log-odds birimine bölünüp yuvarlanmış; sıfır puanlı satırlar çıkarılınca 14 satır kalmıştır. Ana modelin β katsayılarını doğrudan yuvarlamak değildir.',
      'The card comes from a separate class-balanced L2 model with 16 candidate features and C = 0.3. Coefficients were divided into 0.5 log-odds units and rounded; removing zero-point rows left 14 items. It is not a rounding of the main model’s β coefficients.')
    raw(r'{\small')
    table(['Ölçüt','Puan'],['Item','Points'],[(item['tr'] if tr else item['en'],item['points']) for item in MODEL['points']['items']])
    raw('}')
    p('Örnekte: yaş <40 için 1, TNBC için 2, birinci derece meme <40 için 3; toplam 6. Ki-67 bilinmiyor olduğundan yüksek Ki-67 kart puanı yoktur. Aile sayımı kart satırında en çok 2, modelde panel sınırı 6’dır.',
      'Example: age <40 gives 1, TNBC gives 2, first-degree breast <40 gives 3: total 6. Unknown Ki-67 earns no high-Ki-67 card point. Each family card row caps at two; the panel allows model counts up to six.')
    table(['Şerit','Model','Kart'],['Lane','Model','Card'],[(t('Normal','Normal'),'<10%','0–3'),(t('Öncelikli','Priority'),'10%–<20%','4'),(t('Acil','Urgent'),'≥20%','≥5')])
    math(r'A=\max(s_{\mathrm{card}},s_{\mathrm{model}},u),\qquad B=\max(s_{\mathrm{model}},u)')
    p('s değerleri 0 normal, 1 öncelikli, 2 acil kodlarıdır; max en büyüğü seçer. Tedavi kararı bekliyorsa u=2; aksi halde ailede belgeli P/LP kutusu seçiliyse u=1; değilse 0. B öneridir. A’da acil şerit, B’de model ≥%20 hızlı paketi tetikler. Aile P/LP kutusu β toplamını değiştirmez; ancak bilgi modelde olmadığı için kişisel yüzde başlığı bastırılır.',
      's values are lane codes: 0 normal, 1 priority, 2 urgent; max takes the highest. u=2 if a treatment decision awaits the result; otherwise u=1 for documented familial P/LP, else 0. B remains a proposal. A’s urgent lane triggers the rapid package; B uses model ≥20%. Familial P/LP does not change the β sum, but suppresses the personal probability headline because that information is absent from the model.')

    page(10, 'Diğer ekran sayıları ve başarı ölçütleri', 'Other displayed numbers and performance measures')
    heading('Aynı hastanın farklı sayılarını karıştırmayın', 'Do not confuse different numbers for one patient')
    math(r'N=\operatorname{round}(1/p)=\operatorname{round}(3.876824)=4')
    p('“Yaklaşık dört kişiden biri” yuvarlanmış anlatımdır; dört gözlenmiş kişi değildir. Round en yakın tamsayıya yuvarlar; kodda tam yarımlar çift tamsayıya gider.',
      '“Approximately one in four” is a rounded description, not four observed people. Round chooses the nearest integer; exact halves go to the even integer in the code.')
    math(r'\mathrm{Position}=\operatorname{round}\left[5\left(17+\frac{0.257943117-0.2133526175}{0.2763791363-0.2133526175}\right)\right]=89')
    p('Skor sırası yaklaşık 89. yüzdeliktir: geliştirme skor dağılımındaki konum, %89 taşıyıcılık olasılığı değil. 17 alt düğümün sıfırdan başlayan sırası; kesrin paydası iki komşu düğüm arasındaki farktır.',
      'The score is near the 89th percentile: a position in the development-score distribution, not an 89% carrier probability. 17 is the zero-based lower-knot index; the denominator is the gap between adjacent knots.')
    math(r'\mathrm{Fill}=\min\left(100,\frac{p}{0.40}\times100\right)\approx64.5\%')
    p('Fill görsel çubuk doluluğudur; min küçük olanı seçer. Bu %64,5 ikinci bir tıbbi olasılık değildir.',
      'Fill is the visual bar fill; min takes the smaller value. This 64.5% is not another medical probability.')
    heading('Kayıtlı performans değerleri', 'Stored performance estimates')
    table(['Ölçüt','Değer'],['Metric','Value'],[
        (t('İç içe çapraz doğrulama AUC','Nested cross-validation AUC'),'0.776'),
        (t('AUC güven aralığı','AUC confidence interval'),'0.733–0.817'),
        (t('Görünür / iyimserlik düzeltilmiş AUC','Apparent / optimism-corrected AUC'),'0.815 / 0.784'),
        ('PR-AUC','0.404'),(t('Zamansal test AUC','Temporal-test AUC'),'0.788'),
        (t('Yeniden kalibre edilmiş Brier','Recalibrated Brier'),'0.095'),(t('Temel oran Brier','Base-rate Brier'),'0.112')])
    p('AUC: Area Under the Receiver Operating Characteristic Curve. Pozitif bir kaydı diğer etiketli bir kaydın üstünde sıralama yeteneğidir; 0,776 “kişilerin %77,6’sını doğru bildi” demek değildir. ROC, duyarlılığı yanlış pozitif oranına karşı çizer. PR-AUC: Precision–Recall eğrisi altındaki alan; pozitif sınıfı bulma performansını ele alır.',
      'AUC: Area Under the Receiver Operating Characteristic Curve. It measures ranking of a positive record above an other-labelled record; 0.776 does not mean 77.6% of individual answers are correct. ROC plots sensitivity against false-positive rate. PR-AUC is the area under the Precision–Recall curve, focusing on positive-class retrieval.')

    page(11, 'Doğrulama, eşikler ve hata tablosu', 'Validation, thresholds and the error table')
    math(r'\mathrm{Brier}=\frac{1}{n}\sum_{i=1}^{n}(p_i-y_i)^2')
    p('n değerlendirilen kişi sayısı; pᵢ kişinin tahmini, yᵢ kayıtlı sonucu. Brier, olasılık hatasını ölçer; düşük daha iyidir. Kalibrasyon, örneğin %20 denilen gruplarda gözlenen oranın buna yakın olup olmadığıdır. İyi sıralama, iyi kalibrasyonu garanti etmez.',
      'n is the number evaluated, pᵢ the prediction and yᵢ the recorded outcome. Brier measures probability error; lower is better. Calibration asks whether groups predicted at, for example, 20% have observed rates near that value. Good ranking does not guarantee good calibration.')
    p('Kat dışı tahmin, kişi o adımda eğitim dışında tutulurken üretilir. Ancak ana betikte bazı atama ve ölçekleme dış kat ayrımından önce yapılmıştır: veri sızıntısı riski vardır. StratifiedKFold sınıf oranlarını gözetir ama aileleri gruplamaz. Akrabalar farklı katlara düşebilir. AUC aralığı 2.000 kişi bazlı bootstrap; iyimserlik düzeltmesi 200 bootstrap kullanır. Bootstrap, örnekten tekrar yerine koyarak örnekleme işlemidir.',
      'An out-of-fold prediction is made while that person is excluded from the relevant fitting step. However, some imputation and scaling in the main script preceded the outer split, creating leakage concerns. StratifiedKFold balances classes but does not group families; relatives can enter different folds. The AUC interval uses 2,000 person-level bootstrap samples, and optimism correction uses 200. Bootstrap resamples observations with replacement.')
    p('Zamansal tabloda 796 eğitim ve 477 test kişisi vardır; test dönemindeki pozitif sayısı 52’dir. Aynı merkezin daha sonraki dönemi, bağımsız dış doğrulama değildir. Farklı değerlendirme tablolarının paydaları ve işlem yolları birbirinin yerine kullanılamaz.',
      'The temporal table records 796 training and 477 test patients, with 52 positives in the test period. A later period at the same centre is not independent external validation. Denominators and processing paths from different evaluation tables are not interchangeable.')
    heading('Tarihsel yaklaşık %3,5 eşik örneği', 'Historical approximately 3.5% threshold example')
    table(['','Positive','Diğer','Toplam'],['','Positive','Other','Total'],[
        (t('Eşik üstü','Above threshold'),'TP 159','FP 978','1,137'),(t('Eşik altı','Below threshold'),'FN 8','TN 150','158'),(t('Toplam','Total'),'167','1,128','1,295')])
    math(r'\mathrm{Sensitivity}=\frac{TP}{TP+FN}=\frac{159}{167}=95.21\%')
    math(r'\mathrm{Specificity}=\frac{TN}{TN+FP}=\frac{150}{1128}=13.30\%')
    math(r'\mathrm{NPV}=\frac{TN}{TN+FN}=\frac{150}{158}=94.94\%,\quad \mathrm{PPV}=\frac{159}{1137}=13.98\%')
    p('TP/FP: True/False Positive; TN/FN: True/False Negative, kayıt etiketlerine göre doğru/yanlış eşik sınıflaması. Duyarlılık pozitifleri yakalama; özgüllük diğerlerini aşağıda tutma; NPV (Negative Predictive Value) eşik altındakilerin diğer etiket oranı; PPV (Positive Predictive Value) eşik üstündekilerin pozitif oranıdır. Yüksek duyarlılık tek başına yeterli değildir. Bu örnek güncel %10/%20 sıra sınırları değildir; tek eşik tablosu AUC vermez.',
      'TP/FP: True/False Positive; TN/FN: True/False Negative, relative to the recorded labels. Sensitivity captures positives; specificity keeps others below threshold; NPV (Negative Predictive Value) is the other-label proportion below threshold; PPV (Positive Predictive Value) is the positive proportion above threshold. High sensitivity alone is insufficient. This is not the current 10%/20% queue boundary; one threshold table cannot give AUC.')

    page(12, 'Laboratuvar kapasitesi: iş yükü ve verim', 'Laboratory capacity: workload and yield')
    p('İki karar ayrıdır: kim sırada öne alınır, kime dar kapsamlı hızlı ilk test paketi uygulanır? Hızlı paket BRCA1 MLPA delesyon/duplikasyon incelemesi ve c.5266dupC hedefini kapsar. Bütün BRCA varyantlarını inceleyen tam test değildir. Hızlı test negatifliği taşıyıcılığı dışlamaz; tam test devam eder.',
      'Two decisions are distinct: who is prioritised in the queue, and who receives the narrow rapid first-test package? The package covers BRCA1 deletions/duplications by MLPA plus c.5266dupC. It is not complete testing for all BRCA variants. A negative rapid result does not exclude a carrier; full testing continues.')
    table(['Strateji','Paket','Saptanabilir hedef'],['Strategy','Packages','Detectable targets'],[
        (t('Model ≥%20','Model ≥20%'),'212.6','26.6'),(t('Kart veya model A tetikleyicisi','Card-or-model A trigger'),'280.0','29.4')])
    p('Bunlar beş tekrarın ortalamalarıdır; ondalık sayılar parçalı hastalar değildir. Saptanabilir hedef, bu dar paketin kapsadığı hedefi taşıyan seçilmiş kişidir; bütün BRCA pozitifleriyle aynı payda değildir.',
      'These are means over five repeats, not fractional patients. A detectable target is a selected carrier with a target covered by the narrow package; it is not the same denominator as all BRCA positives.')
    math(r'\Delta N=212.6-280=-67.4,\qquad\Delta T=26.6-29.4=-2.8')
    math(r'\mathrm{Yield}=\frac{26.6}{212.6}\times100=12.511759\%')
    math(r'\mathrm{Packages/target}=\frac{212.6}{26.6}=7.992481')
    p('Δ fark demektir; burada N paket sayısı, T saptanabilir hedef sayısıdır. Daha az paket karşılığında daha az hedef saptama ödünleşimi vardır. Tekrar oranlarının ortalaması 8,013; ortalamaların oranı yaklaşık 7,992’dir. Farklı işlemlerdir.',
      'Δ means difference; here N is package count and T detectable-target count. Fewer packages trade off against fewer detectable targets. The mean of repeat-specific ratios is about 8.013; the ratio of means is about 7.992. These are different operations.')
    p('Kapasite paneli altı kayıtlı stratejinin toplu sonuçlarını okur; yeni hasta analizi yapmaz. Zamansal seçenek 477 kişi ve 52 taşıyıcıya aittir. Aciliyet kutularının ek iş yükü ölçülmemiştir. Aynı sayıda hasta seçilen karşılaştırmada kart ek üstünlük göstermemiş; elle kullanım ve açıklama değeri ayrıdır.',
      'The capacity panel reads aggregate results for six stored strategies; it performs no new patient analysis. The temporal option concerns 477 people and 52 carriers. Extra workload from urgency overrides was not measured. In the equal-workload comparison, the card showed no added advantage; its manual and explanatory value is separate.')
    note('Bekleme süresi, maliyet veya tedavi sonucundaki iyileşme ölçülmedi. Varsayımsal test azaltma paneli bir test atlama talimatı değildir.',
         'Improvements in waiting time, cost or treatment outcomes were not measured. The hypothetical test-reduction panel is not an instruction to omit tests.')
    p('Varsayımsal azaltma politikası düşük olasılığa ek olarak kart ≥4, over, erkek meme, TNBC, ailede over, aciliyet ve sıkı seçenekte <45 yaşı dışlar. Kayıtlı üretim betiği bu pakette olmadığından toplu azaltma sonuçları burada bağımsız yeniden üretilmiş sayılmaz.',
      'The hypothetical reduction policy excludes card ≥4, ovarian cancer, male breast cancer, TNBC, ovarian family history, urgency and, in the strict option, age <45. Its generating script is absent from this package, so the stored aggregate reduction results are not independently regenerated here.')

    page(13, 'Biyolojik bulgu ve istatistiksel belirsizlik', 'The biological finding and statistical uncertainty')
    p('Tahmin, hangi bilgi birleşiminin sonucu öngördüğünü sorar. Biyolojik ilişki araştırması ise örneğin iki varyant grubunun tümör boyutlarının farklı olup olmadığını sorar. İyi tahmin, neden-sonuç ilişkisi kanıtı değildir.',
      'Prediction asks which information combinations predict an outcome. Biological association research might ask whether tumour sizes differ between variant classes. Useful prediction does not establish causation.')
    p('Mevcut karşılaştırma 87 aile temsilcisidir: stop-gain grubunda 20, frameshift grubunda 67 aile. Stop-gain protein üretimine erken dur işareti getirir; frameshift DNA’nın üçlü okunma düzenini kaydırır. Yaş, yıl, gen, kayıtlı etnik köken, bölge ve genotip kaynağına göre düzeltilmiş kaydedilmiş boyut oranı aşağıdadır.',
      'The existing comparison uses 87 family representatives: 20 stop-gain and 67 frameshift families. Stop-gain introduces an early stop in protein production; frameshift shifts the three-letter reading frame. The recorded-size ratio below adjusts for age, year, gene, recorded ethnicity, region and genotype source.')
    math(r'R=0.649,\qquad\text{interval: }0.421\text{ to }1.001')
    p('Nokta tahmini yaklaşık %35 daha küçük kaydedilmiş boyuta karşılık gelir. Aralık fark olmamasını belirten 1’i içerir. Birincil ampirik p yaklaşık 0,0504; birikimli çoklu test düzeltmesi q yaklaşık 0,527’dir. Bu doğrulanmış bir fark değildir ve hesaplayıcıya eklenmemiştir.',
      'The point estimate corresponds to about 35% smaller recorded size. The interval includes 1, meaning no difference. The primary empirical p is about 0.0504; the cumulative multiple-testing-adjusted q is about 0.527. This is not a validated difference and was not added to the calculator.')
    table(['Terim','Anlam'],['Term','Meaning'],[
        (t('Etki büyüklüğü','Effect size'),t('İlişkinin büyüklüğü; burada boyut oranı.','Magnitude of the association; here a size ratio.')),
        (t('Güven aralığı','Confidence interval'),t('Örnekleme belirsizliğini anlatır; bu tek aralığa ilişkin doğruluk olasılığı değildir.','Describes sampling uncertainty, not a probability that this one interval is correct.')),
        ('p-value',t('Sıfır hipotezi ve model varsayımları altında en az bu kadar uç sonuç olasılığı; hipotezin yanlış olma olasılığı değil.','Probability of a result at least this extreme under the null and assumptions; not the probability the hypothesis is false.')),
        (t('Karıştırıcı','Confounder'),t('Hem grup hem sonuçla ilişkili olup karşılaştırmayı bozabilen değişken.','A variable related to group and outcome that can distort the comparison.')),
        (t('Seçilim yanlılığı','Selection bias'),t('Dahil edilen ve dışlanan kişilerin sistematik farklılığı.','Systematic differences between included and excluded people.')),
        (t('Güç','Power'),t('Belirli bir gerçek etkiyi belirli tasarımla saptayabilme olasılığı.','Probability of detecting a specified true effect with a specified design.')),
        ('FDR / False Discovery Rate',t('Çoklu karşılaştırmalarda yanlış keşif oranını kontrol eden yaklaşım.','An approach controlling false discoveries across multiple comparisons.')),
    ],r'p{.30\linewidth}X')
    p('Çok karşılaştırma tesadüfi bulgu fırsatını artırır. İstatistiksel düzeltme bütün eksiklik, seçilim ve ölçüm yanlılıklarını gidermez. Bu gözlemde eksiklik/seçilim sorunları çözülmüş değildir; bağımsız doğrulama yoktur.',
      'Many comparisons create more opportunities for chance findings. Statistical adjustment does not eliminate missingness, selection or measurement bias. These issues remain unresolved for this observation; independent validation is absent.')

    page(14, 'Yeni kayıtlar neden henüz doğrulama sayılmıyor?', 'Why are the additional records not yet a validation set?')
    p('Arşivin büyümesi, modelin yeniden eğitildiği veya bağımsız doğrulandığı anlamına gelmez. Bir kişi eğitimde kullanıldıysa ya da aynı aileden geliyorsa bağımsız test için uygun olmayabilir. Kayıtlı aile ayrılığı, genomik akrabasızlık kanıtı değildir.',
      'An expanded archive does not mean the model has been retrained or independently validated. A person used in development, or from the same family, may not be eligible for an independent test. Recorded family separation is not genomic proof of unrelatedness.')
    table(['Mevcut denetim aşaması','Sayı'],['Existing audit stage','Count'],[
        (t('Geliştirme dışında klinik bağlantılı kişiler','Clinically linked people outside development'),'206'),
        (t('Bilinen geliştirme aile örtüşmesiyle dışlanan','Excluded for known development-family overlap'),'20'),
        (t('Uygun kanser kaydı olmayan','Without an eligible cancer record'),'1'),
        (t('Kalan aday kişiler / aile grupları','Remaining candidate people / family groups'),'185 / 184'),
        (t('Temel girdileri tam aile temsilcileri','Family representatives with complete core inputs'),'111'),
        (t('Rapor destekli, temel girdileri tam','Report-supported, core-complete representatives'),'91'),
        (t('Tarihsel VUS bağımlılığı olmadan kalan','Remaining without historical-VUS dependency'),'51'),
        (t('51 adayda pozitif / negatif','Positive / negative in the 51 candidates'),'14 / 37'),
        (t('Tanı yılı var / eksik','Diagnosis year available / missing'),'41 / 10'),
        (t('Tam tarihli sonuç-öncesi profil / uygun doğrulama','Complete dated pre-result profile / eligible validation'),'0 / 0'),
    ])
    p('91 rapor destekli temsilciden 40’ı tarihsel varyant sınıflandırmasına bağımlı olduğu için daha temkinli 51 kişilik incelemenin dışında tutuldu. Eksik tanı yılı bir model girdisi değildir; zaman sıralamasını doğrulamayı zorlaştırır. Yılı bulunan 41 kişide de bütün klinik girdilerin BRCA sonucundan önce kayıtlı olduğu gösterilemedi.',
      'Forty of the 91 report-supported representatives depended on historical variant classification and were excluded from the more conservative 51-person review. Diagnosis year is not a model input, but its absence limits chronology checks. Even the 41 with a year lacked adequate dated evidence that the complete clinical profile preceded the BRCA result.')
    note('Genetik raporlar Drive’da var. Eksik olan, tüm girdileri doğru tahmin zamanında belgeleyen tarihli klinik kayıtlar. Sıfır uygun hasta, sıfır performans demek değildir; performans hesaplanamadı.',
         'Genetic reports exist in Drive. What is missing is dated clinical documentation of the full input profile at the prediction time. Zero eligible patients does not mean zero performance; performance could not be estimated.')
    p('Gerekenler: sonuç öncesi tarihli klinik değerlendirme ve model girdileri; izlenebilir genetik sonuç ve rapor tarihi; güvenilir kişi/aile bağlantıları; hem pozitif hem negatif sonuçlardan yeterli sayıda bağımsız kişi. Yeni katsayı, kalibrasyon veya eşik değişikliği sadece arşiv büyüklüğüyle gerekçelendirilemez.',
      'Needed: dated pre-result clinical assessment covering model inputs; traceable genetic outcomes and report dates; reliable identity/family links; enough independent positive and negative outcomes. Archive size alone does not justify new coefficients, recalibration or threshold changes.')

    page(15, 'Yazılım, kaynaklar ve bütün hikâye', 'Software, sources and the complete story')
    p('Bir girdi değişince model yeniden öğrenmez. Uygulama girdileri okur; kodlama/eksiklik kurallarını uygular; kayıtlı β’larla z, kayıtlı kalibrasyonla yüzde, ayrı kartla puan, A/B kurallarıyla sıra hesaplar. Eğitim sayfası yalnız kurgu profiller kullanır.',
      'An input edit does not retrain the model. The app reads inputs, applies encoding/missingness rules, calculates z with stored coefficients, a percentage with stored calibration, a separate card score and A/B queue lanes. The teaching page uses synthetic profiles only.')
    p('54 kurgu örnek ve 47 kayıtlı öz-test, hesap eşleşmesini kontrol eder. Otomatik testler ile canlı masaüstü/mobil kontroller, yazılımın amaçlanan hesabı yaptığını gösterebilir. Dil geçişi girdileri korumalı; sıfırlama seçili profilin başlangıcına dönmelidir. Bunlar yeni hastalarda klinik başarı kanıtı değildir.',
      'The 54 synthetic examples and 47 stored self-tests check arithmetic agreement. Automated tests and live desktop/mobile checks can establish intended software behaviour. Language switches should retain inputs; reset should restore the selected profile. These are not evidence of clinical performance in new patients.')
    p('SHA-256 sağlama toplamı hangi dosya sürümünün kullanıldığını doğrular; verinin doğruluğunu veya bilimsel geçerliliği kanıtlamaz. Özgün genetik raporlar ve özel kimlik/aile bağlantı listeleri yetkili ekibin Drive kayıtlarındadır; bu rehber hasta kimliği içermez.',
      'A SHA-256 checksum verifies a file version, not data correctness or scientific validity. Original genetic reports and private identity/family linkage lists remain in authorised Drive records; this guide contains no patient identifiers.')
    heading('Bütün çalışmayı bir paragrafta anlatmak', 'Explain the complete work in one paragraph')
    p('Dağınık genetik ve klinik kayıtları eşleştirerek dosya, örnek, kişi ve aileyi ayırdık. Özgün 1.295 kişide kurulan lojistik modelin hesabını açıklıyoruz: ağırlıklı toplam, kalibrasyon ve yüzde. Puan kartı ile sıra kuralları ayrı katmanlardır. İç değerlendirme yararlı sıralama gösterse de veri işleme ve aile bağımsızlığı sınırlılıkları vardır. Biyolojik analizlerdeki 87 ailelik gözlem doğrulanmış keşif değildir. Geniş arşiv henüz tarihli, bağımsız bir doğrulama grubu sağlamadı. Elimizde hesabı açıklanabilen araştırma prototipi ve açık veri ihtiyaçları var; yeni hastalarda güvenilirlik için bağımsız doğrulama gerekiyor.',
      'We linked scattered genetic and clinical records, separating files, specimens, people and families. We explain the logistic model developed in the original 1,295 people: weighted sum, calibration and probability. The points card and queue rules are separate layers. Internal evaluation suggests useful ranking, but preprocessing and family-independence limitations remain. The 87-family biological observation is not a validated discovery. The expanded archive has not yet supplied a dated, independent validation set. We have an explainable research prototype and explicit data needs; reliability in new patients requires independent validation.')
    heading('İzlenebilir mevcut kaynaklar', 'Traceable existing sources')
    sources=[('model_full_embedded.json',t('Sabit katsayılar, hasta sayıları ve kayıtlı performans','Frozen coefficients, development counts and stored performance')),
             ('brca_core.py',t('Hesap, kart ve A/B kuralları','Calculation, card and A/B rules')),
             ('model_teaching_content.py',t('Mevcut yöntem denetimi ve semboller','Existing methods audit and symbols')),
             ('evidence/research/cohort_census.json',t('Arşiv sayımı','Archive census')),
             ('evidence/research/size_results.json',t('87 ailelik sonuç','87-family result')),
             ('evidence/calculator_validation_eligibility.json',t('Doğrulama aday seçimi','Validation candidate selection')),
             ('evidence/calculator_prediction_date_audit.json',t('51 adayda tarih denetimi','Prediction-date audit of 51 candidates')),
             ('evidence/rapid_threshold.json',t('Hızlı test kapasitesi','Rapid-test capacity'))]
    raw(r'\begin{itemize}\small')
    for path,label in sources:
        raw(r'\item\href{https://github.com/ArifSolmaz/brca/blob/main/'+path+'}{'+esc(label)+'}')
    raw(r'\end{itemize}')
    p('Bağlantılar kullanılan toplu kayıtlara gider; bunlar hasta düzeyindeki özgün belge denetiminin yerine geçmez. Rehber yeni bir klinik sınıflandırma veya test önerisi sunmaz.',
      'Links lead to the aggregate records used here; they do not replace original patient-level document review. This guide introduces no new clinical classification or testing recommendation.')

    if web:
        return blocks
    raw(r'\end{document}')
    tex = WORK / f'BRCA_Model_Guide_{lang.upper()}.tex'
    tex.write_text(preamble + '\n'.join(parts))
    for _ in range(2):
        result = subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error',
                                 '-output-directory', str(WORK), str(tex)],capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout[-5000:] + result.stderr[-1000:])
    pdf = tex.with_suffix('.pdf')
    for directory in (OUT,ASSETS):shutil.copy2(pdf,directory/pdf.name)
    print(lang, pdf.stat().st_size, OUT/pdf.name)


if __name__ == '__main__':
    for directory in (WORK,OUT,ASSETS):directory.mkdir(parents=True,exist_ok=True)
    for language in ('tr','en'):build(language)
