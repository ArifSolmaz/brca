"""Short, bilingual input explanations; presentation only."""
HELP = {
    "tr": {
        "age": "İlk kanser tanısının konduğu yaş; bugünkü yaş değil. Modelin kabul ettiği aralık 18–95 yaştır.",
        "ki67": "Patoloji raporundaki Ki-67 yüzdesi: çoğalmakta olan tümör hücrelerinin oranını gösterir. Bilinmiyorsa boş bırakın; sıfır yazmayın. Yalnız over kanserinde kullanılmaz.",
        "dx": "Hastanın kanser tanısını seçin. Bilateral, her iki memede kanser demektir; over, yumurtalıktır. Meme + over, iki tanının da bulunduğu durumdur.",
        "grade": "Patoloji raporundaki tümör derecesi (grade), hücrelerin normal hücrelerden ne kadar farklı göründüğünü anlatır; kanser evresi değildir. Derece bilinmiyorsa 2 / bilinmiyor seçin.",
        "tnbc": "Üçlü negatif meme kanseri: ER (östrojen reseptörü), PR (progesteron reseptörü) ve HER2 sonucu negatiftir. Patoloji raporuna göre işaretleyin; yalnız over kanserinde kullanılmaz.",
        "region": "Çalışmada kaydedilen aile köken bölgesi; şu an yaşanan şehir değildir. Bilinmiyorsa Marmara / bilinmiyor seçeneği kullanılır; modelde bunlar aynı gruptadır.",
        "urg_dec": "BRCA sonucu beklenen bir ameliyat veya sistemik tedavi kararı varsa işaretlenir. Hesaplanan olasılığı değiştirmez; araştırmadaki test sırasını Acil yapar. Bu etiket tıbbi acil durum anlamına gelmez.",
        "urg_fam": "Akrabanın genetik raporunda hastalık yapıcı (P) veya büyük olasılıkla hastalık yapıcı (LP) BRCA1/2 değişikliği belgelenmişse işaretlenir. Önemi belirsiz değişiklik (VUS) buna dahil değildir. Bu bilgi model yüzdesine katılmaz; bu nedenle kişisel yüzde gösterilmez ve ailedeki değişikliğe yönelik test açıklaması açılır.",
        "mode": "Öncelik sırası, araştırmadaki test sırasını gösterir. Test azaltma ise yalnız varsayımsal bir araştırma senaryosudur; testten vazgeçme talimatı değildir.",
        "ro_line": "Varsayımsal senaryoda kullanılan olasılık sınırı. Yalnız bu sınırın altında olmak test dışı kalmak için yeterli değildir; diğer dışlama kuralları da denetlenir.",
        "ro_strict": "Açıksa, varsayımsal test azaltma senaryosunda tanı yaşı 45'in altında olanlar her zaman test grubunda tutulur. Model olasılığını değiştirmez.",
    },
    "en": {
        "age": "Age at the first cancer diagnosis, not current age. The model accepts ages 18–95.",
        "ki67": "Ki-67 percentage from the pathology report: the proportion of tumour cells that are proliferating. Leave blank if unknown; do not enter zero. Not used for ovarian-only cancer.",
        "dx": "Select the patient's cancer diagnosis. Bilateral means cancer in both breasts; ovarian refers to the ovaries. Breast + ovarian means both diagnoses are present.",
        "grade": "Tumour grade from the pathology report describes how different the cells look from normal cells; it is not cancer stage. Select 2 / unknown when grade is unavailable.",
        "tnbc": "Triple-negative breast cancer: ER (oestrogen receptor), PR (progesterone receptor) and HER2 are all negative. Use the pathology report. Not used for ovarian-only cancer.",
        "region": "Family region of origin as recorded in the study, not current residence. If unknown, select Marmara / unknown; the model groups these together.",
        "urg_dec": "Select when a surgery or systemic-treatment decision is awaiting the BRCA result. It does not change the probability; it sets the research test queue to Urgent. This label does not mean a medical emergency.",
        "urg_fam": "Select only if a relative's genetic report documents a pathogenic (P) or likely pathogenic (LP) BRCA1/2 variant. A variant of uncertain significance (VUS) does not qualify. The model percentage does not include this information, so the personal percentage is hidden and an explanation about testing for the familial variant appears.",
        "mode": "Priority order shows the research test queue. Test reduction is a hypothetical research scenario only, not an instruction to withhold testing.",
        "ro_line": "Probability threshold for the hypothetical scenario. Being below it alone does not qualify for skipping testing; the other exclusion rules are also checked.",
        "ro_strict": "When enabled, the hypothetical test-reduction scenario always retains patients diagnosed before age 45 for testing. This does not change model probability.",
    },
}
_DEGREE = {
    "tr": {
        "fdr": "1. derece: anne, baba, kardeş ve çocuklar.",
        "sdr": "2. derece: büyükanne, büyükbaba, teyze, hala, dayı, amca, yeğen ve torunlar.",
        "sdr_ovary": "2.–4. derece: büyükanne, teyze veya hala gibi 2. derece akrabalar ile kuzen gibi daha uzak akrabalar.",
        "tdr": "3.–4. derece: kuzen, büyük büyükanne veya büyük büyükbaba gibi daha uzak akrabalar.",
    },
    "en": {
        "fdr": "First degree: parents, siblings and children.",
        "sdr": "Second degree: grandparents, aunts, uncles, nieces, nephews and grandchildren.",
        "sdr_ovary": "Second–fourth degree: relatives such as grandparents, aunts or uncles, and more distant relatives such as cousins.",
        "tdr": "Third–fourth degree: more distant relatives such as first cousins or great-grandparents.",
    },
}


def input_help(lang, key):
    if key in HELP[lang]:
        return HELP[lang][key]
    group = "sdr_ovary" if key == "sdr_ovary" else key.split("_")[0]
    degree = _DEGREE[lang][group]
    if lang == "tr":
        text = "Hastanın kendisini saymadan, bu gruptaki kanser tanılı akraba sayısını girin. " + degree
        if "lt40" in key:
            text += " Akrabanın tanı yaşı 40'ın altında olmalı."
        elif "ge40" in key:
            text += " Akrabanın tanı yaşı 40 veya üzerinde olmalı."
        elif "ovary" in key:
            text += " Over, yumurtalık kanseridir."
        elif key == "fdr_other":
            text += " Meme ve over dışındaki kanserler içindir."
    else:
        text = "Enter the number of relatives with cancer in this group, excluding the patient. " + degree
        if "lt40" in key:
            text += " The relative was diagnosed before age 40."
        elif "ge40" in key:
            text += " The relative was diagnosed at age 40 or later."
        elif "ovary" in key:
            text += " Count relatives with ovarian cancer."
        elif key == "fdr_other":
            text += " For cancers other than breast or ovarian cancer."
    return text
