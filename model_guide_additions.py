"""Shared teaching additions; no patient analysis or clinical-model fitting."""

def guide_additions(lang):
    tr = lang == 'tr'
    def t(a,b): return a if tr else b
    blocks=[]
    def chapter(n,a,b): blocks.append(dict(type='chapter',number=n,text=t(a,b)))
    def p(a,b): blocks.append(dict(type='paragraph',text=t(a,b)))
    def heading(a,b): blocks.append(dict(type='heading',text=t(a,b)))
    def note(a,b): blocks.append(dict(type='note',text=t(a,b)))
    def equation(text,steps=None):
        block=dict(type='math',text=text)
        if steps:block['mobile_steps']=steps
        blocks.append(block)
    def table(a,b,rows):blocks.append(dict(type='table',headers=t(a,b),rows=rows))
    def link(text,url):blocks.append(dict(type='link',text=text,url=url))

    chapter(16,'Yapay zekâ diyoruz; bizim modelimiz bunun neresinde?','Where does our calculator fit within AI?')
    p('Yapay zekâ (AI, Artificial Intelligence), bilgisayarlara öğrenme ve problem çözme gibi görevler yaptıran geniş alandır. Makine öğrenmesi (ML, Machine Learning), kuralları yalnız elle yazmak yerine veriden örüntü öğrenen yöntemleri kapsar. Derin öğrenme (DL, Deep Learning) ise çok katmanlı yapay sinir ağlarını kullanan makine öğrenmesi yöntemleridir.',
      'Artificial intelligence (AI) is the broad field of making computers perform tasks such as learning and problem solving. Machine learning (ML) includes methods that learn patterns from data rather than relying only on hand-written rules. Deep learning (DL) uses artificial neural networks with many layers and is one part of machine learning.')
    note('Yapay zekâ → makine öğrenmesi → denetimli öğrenme → bizim lojistik regresyon modelimiz. Derin öğrenme, makine öğrenmesinin başka bir yöntem grubudur; hesaplayıcımız derin sinir ağı kullanmaz.',
         'AI → machine learning → supervised learning → our logistic regression model. Deep learning is another family of machine-learning methods; our calculator does not use a deep neural network.')
    p('Denetimli öğrenmede eğitim örneklerinin kayıtlı sonuç etiketleri vardır. Bizim çalışmamızda girdiler tanı yaşı, aile öyküsü ve belirli tümör özellikleri; öğrenilmek istenen etiket ise kayıtlı BRCA sonucudur. Eğitimde sonucu biliriz. Yeni bir kişiye tahmin yaparken ise sonuç-öncesi bilgileri kullanmak gerekir. Sonucu öğrendikten sonra kaydedilen bilgileri sanki önceden biliniyormuş gibi kullanmak, gerçek kullanımın güvenilir bir denemesi olmaz.',
      'In supervised learning, training examples have recorded outcome labels. Our inputs include diagnosis age, family history and selected tumour features; the target is the recorded BRCA result. We know the outcome during training. For a new prediction, the inputs must be available before the result. Treating information recorded afterwards as if it had been known earlier does not faithfully test intended use.')
    heading('Aynı alanda farklı sorular','Different questions in the same field')
    table(['Soru','Girdi → çıktı','Bizim hesaplayıcı mı?'],['Question','Input → output','Our calculator?'],[
        (t('BRCA sonucu olasılığı','BRCA-result probability'),t('Klinik bilgiler → kayıtlı pozitif sonuç olasılığı','Clinical features → probability of a recorded positive result'),t('Evet; araştırma modeli','Yes; a research model')),
        (t('Varyant çağırma','Variant calling'),t('Dizileme okumaları → DNA değişikliği çağrısı','Sequencing reads → DNA variant call'),t('Hayır; ör. DeepVariant ayrı görevdir','No; DeepVariant is an example of a separate task')),
        (t('Varyantın anlamı','Variant interpretation'),t('Bir değişiklik ve kanıtları → klinik sınıflama','A variant and supporting evidence → clinical classification'),t('Hayır; VUS bu modelle yeniden sınıflanmaz','No; this model does not reclassify a VUS')),
        (t('Gelecekte kanser / tedavi yanıtı','Future cancer / treatment response'),t('Uygun başlangıç bilgileri ve takip → gelecekteki sonuç','Suitable baseline data and follow-up → a future outcome'),t('Hayır; farklı hedef ve doğrulama gerekir','No; a different target and validation are required')),
    ])
    p('Karmaşıklık, doğruluğun garantisi değildir. Lojistik regresyon her girdiye bir katsayı verir; karar ağacı sorularla dallanır; K-en yakın komşu (KNN, K-Nearest Neighbours) benzer eğitim örneklerine bakar; destek vektör makinesi (SVM, Support Vector Machine) sınıfları ayıran bir sınır öğrenir; sinir ağları katmanlar boyunca dönüşümler öğrenir. Bu açıklamalar bir algoritma yarışmasının sonucu değildir. Bizim verimizde hangisinin daha iyi olduğunu söylemek, aynı hastalar ve aileleri ayıran aynı değerlendirme düzeniyle adil bir karşılaştırma gerektirir; burada böyle bir yeni karşılaştırma yapılmadı.',
      'Complexity does not guarantee accuracy. Logistic regression assigns a coefficient to each input; a decision tree branches through questions; K-nearest neighbours (KNN) looks at similar training examples; a support vector machine (SVM) learns a separating boundary; neural networks learn transformations through layers. These descriptions are not the results of an algorithm competition. Establishing which works better for our data would require a fair comparison using the same patients and family-separated evaluation. No new comparison was performed here.')
    link(t('DeepVariant: özgün varyant çağırma çalışması','DeepVariant: original variant-calling study'),'https://www.nature.com/articles/nbt.4235')

    chapter(17,'Bilgisayar hatalarından nasıl öğreniyor?','How does the computer learn the coefficients?')
    note('Aşağıdaki sayılar yalnız kurgu bir ders örneğidir. Gerçek hasta, gerçek eğitim adımı veya yeni performans sonucu değildir. Hesaplayıcının kayıtlı katsayıları değiştirilmedi.',
         'The numbers below are a fictional classroom example only. They are not a real patient, an actual training iteration or a new performance estimate. The calculator’s stored coefficients were not changed.')
    p('Öğrenme döngüsü: katsayılarla tahmin üret → kayıtlı etiketle karşılaştır → kaybı hesapla → katsayıları birlikte güncelle → tekrar et. En sonda yalnız eğitim hatası değil, eğitim dışında tutulan örneklerdeki sonuç da önemlidir. 5. bölüm, geçmiş çalışmada bu işin hangi ayarlar ve sınırlılıklarla yapıldığını anlatır.',
      'The learning cycle is: predict using coefficients → compare with the recorded label → calculate loss → update coefficients together → repeat. Performance on examples held outside fitting matters as well as training error. Chapter 5 describes the settings and limitations of how the historical work did this.')
    p('Kayıp (loss), bir tahminin kayıtlı etiketten ne kadar uzak olduğunu ölçen eğitim ölçütüdür. Logaritmik kayıp (log loss), yanlış bir sonuca aşırı güvenmeyi ağır cezalandırır. Aşağıda y kayıtlı etikettir: pozitif için 1, diğer etiket için 0. p, eğitim sırasında üretilen ham pozitif olasılığıdır; ekrandaki son kalibre yüzde değildir. ℓ (küçük L), bir örneğin kaybı; ln doğal logaritmadır.',
      'Loss measures how far a prediction is from its recorded label during training. Logarithmic loss (log loss) strongly penalises confident wrong predictions. Here y is the recorded label: 1 for Positive, 0 for other labels. p is the raw positive probability during training, not the final calibrated percentage on screen. ℓ (lower-case L) is one example’s loss; ln is the natural logarithm.')
    equation(r'\ell=-\left[y\ln(p)+(1-y)\ln(1-p)\right]',[
        r'y=1:\quad\ell=-\ln(p)',r'y=0:\quad\ell=-\ln(1-p)'])
    heading('Tek bir pozitif etiketli kurgu örnek','One fictional example labelled positive')
    p('Kayıtlı etiketi pozitif olan bir örneğe %20 ham olasılık verilirse kayıp yaklaşık 1,609 olur. Aynı örneğe %80 verilirse yaklaşık 0,223 olur. Pozitif örneğe yalnız %1 vermek ise yaklaşık 4,605 kayıp üretir: bu, güvenle yapılmış yanlış tahminin daha ağır cezasıdır.',
      'For an example labelled positive, predicting a raw probability of 20% gives a loss of about 1.609. Predicting 80% for that same example gives about 0.223. Assigning only 1% to a positive example gives about 4.605: a larger penalty for a confident wrong prediction.')
    equation(r'-\ln(0.20)\approx1.609')
    equation(r'-\ln(0.80)\approx0.223')
    equation(r'-\ln(0.01)\approx4.605')
    p('Eğitim, tek bir örneğin yüzdesini artırma işi değildir: başka örneklerdeki hatalar da hesaba katılır. Sınıf ağırlıkları, az sayıdaki pozitif kayıtlardaki hatalara daha fazla ağırlık verir. L2 cezası, aşırı büyük katsayılara karşı denge kurar. Kaybın azalması eğitim verisine daha iyi uyum anlamına gelebilir; yeni hastalarda daha iyi sonuç alınacağını tek başına göstermez.',
      'Training does not simply increase one example’s percentage: errors on other examples also matter. Class weights give more influence to errors on the smaller positive class. The L2 penalty counterbalances excessively large coefficients. Lower loss can mean a better fit to the training data; it does not by itself establish better performance in new patients.')
    p('Bir katsayı β olsun. Kare cezasında β=1 için katkı 1, β=3 için katkı 9’dur; toplam cezanın büyüklüğü ayrıca ceza ayarına bağlıdır. Bu yalnız cezanın biçimini anlatır. Bizim kayıtlı ayarımızda C küçüldükçe düzenlileştirme güçlenir. C, elle hastaya göre ayarlanan bir risk düğmesi değildir.',
      'For a coefficient β, the squared-penalty contribution is 1 when β=1 and 9 when β=3; total penalty strength also depends on its setting. This illustrates only the shape of the penalty. Under our stored parameterisation, smaller C means stronger regularisation. C is not a patient-specific risk control to adjust manually.')
    equation(r'1^2=1,\qquad3^2=9')
    heading('Eğitim ile kullanım farklı işlerdir','Training and use are different activities')
    p('Eğitimde etiketlerden katsayılar öğrenilir; daha sonra kalibrasyon ve karar kuralları değerlendirilir. Canlı kullanımda kayıtlı katsayılar sabittir: girdiyi değiştirdiğinizde yalnız mevcut formüller yeniden hesaplanır. Girdileriniz yeni eğitim örneği olarak kaydedilmez. Bir öğrencinin kurgu profilindeki yüzdeyi değiştirmesi, modelin başarısını veya biyolojik bir etkiyi ölçmez.',
      'During training, labels help determine coefficients; calibration and decision rules are then evaluated. During live use, the stored coefficients are fixed: editing an input only recomputes the existing formulas. Your entries are not stored as new training examples. Changing a fictional profile’s percentage does not measure model performance or a biological effect.')
    p('Web sayfasındaki sekiz kurgu örnekle öğrenmeyi adım adım izleyebilirsiniz. Geri dönüp katsayıları, hataları ve yeni tahminleri karşılaştırın. Bu küçük ders deneyi gerçek modelin eğitim kaydı değildir.',
      'The web lesson lets you follow learning step by step with eight fictional examples. Go back to compare weights, errors and new predictions. This small classroom experiment is not a record of the actual model’s training.')
    link(t('Kurgu verilerle öğrenmeyi izleyin','Watch learning with fictional data'),'https://brca-istun.streamlit.app/?sayfa=model&dil='+lang+'&ogren=1')
    link(t('Log loss: yöntem açıklaması','Log loss: method explanation'),'https://developers.google.com/machine-learning/crash-course/logistic-regression/loss-regularization')
    link(t('Lojistik regresyon ve düzenlileştirme: yöntem belgesi','Logistic regression and regularisation: method documentation'),'https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html')

    chapter(18,'Önceki makale ile bu hesaplayıcı aynı çalışma mı?','The earlier publication and today’s calculator')
    p('Adibi ve Yazıcı’nın 2023 tarihli “Artificial Intelligence and Machine Learning Applications in Precision Medicine and Genomic Diagnostics” başlıklı kitap bölümü, alandaki uygulamaları tanıtan bir derlemedir. Bugünkü hesaplayıcının bağımsız doğrulama raporu değildir. Bölümün 72. sayfasındaki BRCA örneği, Yazıcı ve arkadaşlarının 2020 çalışmasına atıf yapar. Algoritma ve performans ayrıntıları için aşağıdaki özgün makaleyi esas alıyoruz.',
      'The 2023 book chapter by Adibi and Yazıcı, “Artificial Intelligence and Machine Learning Applications in Precision Medicine and Genomic Diagnostics”, reviews applications in the field. It is not an independent validation report for today’s calculator. Its BRCA example on printed page 72 cites Yazıcı and colleagues’ 2020 study. For algorithm and performance details, we use the original paper linked below.')
    table(['Özellik','2020 yayını','Bugünkü hesaplayıcı'],['Aspect','2020 publication','Today’s calculator'],[
        (t('Veri grubu','Data group'),t('2.070 yüksek riskli meme kanseri hastası; başlangıçta 125 özellik','2,070 high-risk breast cancer patients; initially 125 features'),t('Özgün geliştirme grubu: 1.295 kişi','Original development group: 1,295 people')),
        (t('Hedef','Target'),t('BRCA1/2 negatifliğini belirleme','Identification of BRCA1/2 negativity'),t('Kayıtlı pozitif sonuç olasılığı ve ayrı test sırası kuralları','Probability of a recorded positive result and separate test-priority rules')),
        (t('Yöntem','Method'),t('KNN, karar ağacı ve SVM karşılaştırmaları; dokuz özellikli veri grubu öne çıkarılır','Comparisons involving KNN, decision trees and SVM; highlights a nine-feature dataset'),t('Sınıf dengeli L2 lojistik regresyon + kayıtlı kalibrasyon; ayrı puan kartı','Class-balanced L2 logistic regression + stored calibration; a separate points card')),
        (t('Bildirilen ölçüt','Reported measure'),t('%92,88 doğruluk (accuracy)','92.88% accuracy'),t('Kayıtlı iç çapraz doğrulama AUC: 0,776; yöntem sınırlılıkları 11. bölümde','Stored internal cross-validation AUC: 0.776; methodological limitations in chapter 11')),
        (t('Bağımsız doğrulama','Independent validation'),t('Bu yayının bulunması bugünkü modeli doğrulamaz','This publication does not validate today’s model'),t('Geniş arşivden henüz uygun, tarihli bağımsız grup sağlanmadı','The expanded archive has not yet supplied an eligible, dated independent set')),
    ])
    note('2.070, 1.295 ve arşivdeki 2.148 farklı kayıt kapsamlarını anlatır. Bu sayılar toplanamaz veya birbirinden çıkarılarak yeni/bağımsız hasta sayısı bulunamaz. Yayın ile bugünkü veriler arasındaki kişi ve aile örtüşmesi, yalnız bu sayılardan anlaşılamaz.',
         'The published 2,070, the development group of 1,295 and the archive’s 2,148 describe different record scopes. They cannot be added or subtracted to infer new or independent patients. Counts alone do not establish patient or family overlap between the publication and today’s data.')
    p('Doğruluk, belirli bir karar eşiğinde doğru sınıflananların oranıdır. AUC ise eşikler boyunca sıralamayı özetler. %92,88 doğruluk ile 0,776 AUC aynı ölçekte iki başarı oranı değildir; doğrudan büyük-küçük karşılaştırması yapılamaz. Veri grubu, hedef etiket, sınıf dağılımı, hasta/aile ayrımı ve değerlendirme düzeni de eşleşmelidir.',
      'Accuracy is the proportion classified correctly at a particular decision threshold. AUC summarises ranking across thresholds. A reported accuracy of 92.88% and an AUC of 0.776 are not two success rates on the same scale and cannot be directly ranked. Data group, outcome labels, class balance, patient/family separation and evaluation design also matter.')
    p('Aynı araştırma alanı, yazarlar veya arşiv, aynı eğitilmiş model demek değildir. İki dakikadan kısa hesaplama süresi; bir genetik testin yerini alma, güvenli test azaltma, maliyet tasarrufu veya tedavi yararının ölçüldüğü anlamına gelmez. Bizim sitemiz bu sonuçları kanıtlanmış bir klinik yarar olarak sunmaz.',
      'Shared research interests, authors or archives do not establish that two tools are the same fitted model. A calculation taking under two minutes does not establish replacement of genetic testing, safe test reduction, cost savings or measured treatment benefit. Our site does not present those outcomes as established clinical benefits.')
    link(t('2020 özgün makale: PubMed kaydı ve tam metin bağlantısı','2020 original paper: PubMed record and full-text link'),'https://pubmed.ncbi.nlm.nih.gov/33488844/')
    link(t('2020 özgün makale: DOI','2020 original paper: DOI'),'https://doi.org/10.1155/2020/8594090')
    link(t('2023 derleme bölümü: İstanbul Üniversitesi yayınevi kaynağı','2023 review chapter: Istanbul University publisher source'),'https://cdn.istanbul.edu.tr/file/JTA6CLJ8T5/EC25505B5D6143DC9EFBED00E3B2F6A5')
    p('Bu ek bölümler eğitim içindir. Gerçek hasta verileriyle yeni analiz veya algoritma karşılaştırması yapılmadı; klinik model yeniden eğitilmedi, hesaplayıcının hesabı değiştirilmedi.',
      'These additions are educational. No new patient analysis or algorithm comparison was performed; the clinical model was not retrained and the calculator’s arithmetic was not changed.')
    return blocks
