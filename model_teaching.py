"""Student-facing numerical explanation; never fits a model or changes calculator state."""
import json
import math
from html import escape
from pathlib import Path
import streamlit as st
import brca_core as core
from model_teaching_content import ASSETS, SYMBOLS_TR, SYMBOLS_EN, METHODS, LABELS_TR, LABELS_EN

PUBLIC_URL = 'https://brca-istun.streamlit.app/'
PDF = {lang: ASSETS / f'BRCA_Model_Details_{lang.upper()}.pdf' for lang in ('tr', 'en')}
PRESETS = json.loads((ASSETS / 'synthetic_examples.json').read_text())[:3]


def trace(inputs):
    v = dict(inputs)
    if v['dx'] == 'ovarian':
        v.update(tnbc=0, ki67=30, ki67_missing=1)
    terms = [{'key': 'intercept', 'x': 1, 'beta': core.M['intercept'], 'contribution': core.M['intercept']}]
    for key, beta in core.M['coef'].items():
        if '=' in key:
            cat, level = key.split('='); x = int(v[cat] == level)
        elif key == 'ki67':
            x = core.M['ki67_impute'] if v['ki67_missing'] else v['ki67']
        else:
            x = v.get(key, 0)
        terms.append(dict(key=key, x=x, beta=beta, contribution=x*beta))
    prediction = core.predict(v)
    assert abs(sum(t['contribution'] for t in terms)-prediction['z']) < 1e-12
    return dict(v=v, terms=terms, **prediction, eta=core.M['platt']['a']+core.M['platt']['b']*prediction['z'],
                A=core.decide(v, prediction['p_cal'], 'A'), B=core.decide(v, prediction['p_cal'], 'B'))



def comparison(current, previous):
    """Explain only a synthetic input edit; this does not change any prediction."""
    if previous is None:
        return None
    changes = {k: (previous['v'][k], value) for k, value in current['v'].items()
               if value != previous['v'].get(k)}
    if not changes:
        return None
    before = {term['key']: term['contribution'] for term in previous['terms']}
    contributions = [(term['key'], term['contribution'] - before[term['key']])
                     for term in current['terms'] if abs(term['contribution'] - before[term['key']]) > 1e-14]
    return dict(changes=changes, delta_pp=100*(current['p_cal']-previous['p_cal']),
                delta_z=current['z']-previous['z'], delta_points=current['A']['total']-previous['A']['total'],
                contributions=contributions)



WORKBENCH_STYLE = """<style>
@media(min-width:1100px){
.block-container:has(#teaching-layout){max-width:none!important;width:100%;padding:0 28px 36px!important}
.block-container:has(#teaching-layout) h1{font-size:28px!important;margin:8px 0 4px!important;padding:0!important}
.st-key-teaching_inputs,.st-key-teaching_terms,.st-key-teaching_equations{height:calc(100dvh - 305px)!important;max-height:calc(100dvh - 305px)!important;overflow-y:auto;overflow-x:hidden;border:1px solid #dce1e8;border-radius:12px;padding:14px;background:#fff;box-sizing:border-box;scrollbar-gutter:stable}
.st-key-teaching_inputs [data-testid=stVerticalBlock],.st-key-teaching_terms [data-testid=stVerticalBlock],.st-key-teaching_equations [data-testid=stVerticalBlock]{gap:6px}
.st-key-teaching_inputs [data-testid=stWidgetLabel] p{font-size:12px;line-height:1.2}
.st-key-teaching_inputs input{font-size:14px;min-height:30px}
.st-key-teaching_inputs [data-baseweb=select]{font-size:13px}
.st-key-teaching_inputs [data-testid=stCaptionContainer] p{font-size:11px}
.st-key-teaching_equations .katex{font-size:1.02em}
.st-key-teaching_equations .katex-display{margin:.35em 0}
.st-key-teaching_terms [data-testid=stMetricValue]{font-size:22px}
.st-key-teaching_terms [data-testid=stMetricLabel] p{font-size:11px}
.st-key-teaching_terms [data-testid=stMetricDelta]{font-size:11px}
}
@media(max-width:1099px){
.st-key-teaching_workbench [data-testid=stHorizontalBlock]:has(.st-key-teaching_inputs){flex-direction:column}
.st-key-teaching_workbench [data-testid=stHorizontalBlock]:has(.st-key-teaching_inputs)>[data-testid=stColumn]{width:100%!important;flex:1 1 100%!important}
}
.st-key-teaching_workbench h3{font-size:19px!important;margin:0 0 8px!important;padding:0!important}
.teaching-arithmetic{width:100%;border-collapse:collapse;font-size:clamp(11px,.7vw,14px);font-variant-numeric:tabular-nums;color:#17212b}
.teaching-arithmetic th,.teaching-arithmetic td{padding:6px 5px;border-bottom:1px solid #e2e6eb;text-align:right;vertical-align:top}
.teaching-arithmetic th:first-child,.teaching-arithmetic td:first-child{text-align:left;width:28%}
.teaching-arithmetic th{background:#f0f2f8;font-size:11px}.teaching-arithmetic .edited{background:#fff1c7}
.teaching-arithmetic .product{white-space:nowrap}.teaching-arithmetic small{color:#627181}
.teaching-edit{padding:8px 10px;margin-top:8px;border-left:3px solid #7560ce;background:#f4f1fc;font-size:12px;line-height:1.45;color:#17212b}
</style><div id="teaching-layout"></div>"""


def contribution_html(current, change, lang):
    t=lambda a,b:a if lang=='tr' else b
    labels=LABELS_TR if lang=='tr' else LABELS_EN
    fmt=lambda x,d=8:f'{x:.{d}f}'.replace('.',',') if lang=='tr' else f'{x:.{d}f}'
    edited={key for key,_ in change['contributions']} if change else set()
    running=0;rows=[]
    for term in current['terms']:
        if not term['contribution'] and term['key'] not in edited:continue
        running+=term['contribution']
        x=fmt(term['x'],0 if float(term['x']).is_integer() else 3)
        rows.append(f"<tr class=\"{'edited' if term['key'] in edited else ''}\"><td>{escape(labels.get(term['key'],term['key']))}</td><td class='product'>{x} × ({fmt(term['beta'])})</td><td>{fmt(term['contribution'])}</td><td>{fmt(running)}</td></tr>")
    return f"""<table class="teaching-arithmetic" aria-label="{t('Canlı katkılar ve birikimli toplam','Live contributions and running sum')}"><thead><tr><th>{t('Terim','Term')}</th><th><i>x</i> × <i>β</i></th><th>{t('Katkı','Contribution')}</th><th>{t('Birikimli','Running sum')}</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"""


def render_compact_steps(r,lang):
    t=lambda a,b:a if lang=='tr' else b
    num=lambda x,d=8:f'{x:.{d}f}'.replace('.','{,}') if lang=='tr' else f'{x:.{d}f}'
    a,b=core.M['platt']['a'],core.M['platt']['b'];d=r['A']
    st.markdown(t('**1 · Katkıları topla → z**','**1 · Sum contributions → z**'))
    st.latex(r'z=\beta_0+\sum_{j=1}^{26}\beta_jx_j='+num(r['z']))
    st.markdown(t('**2 · Ham sigmoid (henüz son yüzde değil)**','**2 · Raw sigmoid (not the final percentage)**'))
    st.latex(r'p_{\mathrm{raw}}=\frac{1}{1+e^{-('+num(r['z'])+r')}}')
    st.latex(r'p_{\mathrm{raw}}=\frac{1}{1+'+num(math.exp(-r['z']))+r'}='+num(r['p_raw']))
    st.markdown(t('**3 · Kayıtlı kalibrasyona yerleştir**','**3 · Substitute into stored calibration**'))
    st.latex(r'\eta='+num(a)+r'+('+num(b)+r'\times('+num(r['z'])+r'))')
    st.latex(r'\eta='+num(r['eta']))
    st.markdown(t('**4 · Son sigmoid → yüzde**','**4 · Final sigmoid → percentage**'))
    st.latex(r'p_{\mathrm{cal}}=\frac{1}{1+e^{-('+num(r['eta'])+r')}}')
    st.latex(r'p_{\mathrm{cal}}=\frac{1}{1+'+num(math.exp(-r['eta']))+r'}='+num(r['p_cal'],9))
    st.latex(r'100p_{\mathrm{cal}}='+num(100*r['p_cal'],6)+r'\%\approx'+num(100*r['p_cal'],1)+r'\%')
    st.markdown(t('**5 · Kart ve şeritler (ayrı hesap)**','**5 · Card and lanes (separate calculation)**'))
    st.latex(r'S_{\mathrm{card}}='+('+'.join(str(it['c']) for it in d['items']) or '0')+'='+str(d['total']))
    st.latex(r'A=\max('+','.join(str(d[k]) for k in ('pl','ml','urg'))+')='+str(d['lane'])+r',\quad B=\max('+','.join(str(d[k]) for k in ('ml','urg'))+')='+str(r['B']['lane']))


def render_model_teaching(lang):
    tr = lang == 'tr'
    t = lambda a,b: a if tr else b
    labels = LABELS_TR if tr else LABELS_EN
    fmt = lambda x,d=12: f'{x:.{d}f}'.replace('.', ',') if tr else f'{x:.{d}f}'
    tex = lambda x,d=12: f'{x:.{d}f}'.replace('.', '{,}') if tr else f'{x:.{d}f}'
    st.html(WORKBENCH_STYLE)
    st.title(t('Model ayrıntıları ve elle hesap','Model details and manual calculations'))
    st.caption(t('Öğrenci eğitim sayfası · 2 Kasım 2026 · sabit model ', 'Student teaching page · 2 November 2026 · frozen model ')+core.M['build'])
    with st.container(key='teaching_workbench'):
        input_col,terms_col,steps_col=st.columns([0.95,1.15,1.05],gap='medium')
    with input_col:
        input_panel=st.container(key='teaching_inputs')
    with input_panel:
        st.subheader(t('Girdiler','Inputs'))
        names = [t('Temel profil: 50 yaş','Baseline profile: age 50'),t('Sitedeki örnek hasta: 38 yaş','Site example patient: age 38'),t('Kart ile modelin ayrıldığı profil','Card/model disagreement example')]
        preset_key = 'teaching_preset_'+lang
        st.session_state.setdefault(preset_key,st.session_state.get('_teaching_selected_preset',st.session_state.get('teaching_preset',1)))
        preset = st.selectbox(t('Eğitim profili','Teaching profile'),range(3),index=None,format_func=lambda i:names[i],key=preset_key)
        st.session_state['_teaching_selected_preset']=preset
        if st.button(t('Seçili örneği sıfırla','Reset selected example'),key='teaching_reset'):
            st.session_state.pop('_teaching_loaded',None)
        st.caption(t('Sayı yazınca Enter’a basın veya alandan çıkın. Orta sütun çarpımları, sağ sütun tüm hesap zincirini günceller.', 'After typing, press Enter or leave the field. The middle column updates the products; the right column updates the full calculation chain.'))
        if st.session_state.get('_teaching_loaded') != preset or 'teaching_age' not in st.session_state:
            v=PRESETS[preset]['inputs']
            for k,x in v.items():
                if k == 'ki67': st.session_state['teaching_ki67_value']=float(x)
                else: st.session_state['teaching_'+k]=bool(x) if k in ('tnbc','ki67_missing','urg_dec','urg_fam') else x
            st.session_state['_teaching_loaded']=preset
            st.session_state.pop('_teaching_previous',None)
            st.session_state.pop('_teaching_change',None)
            for category in ('dx','grade'):
                st.session_state['teaching_'+category+'_'+lang]=st.session_state['teaching_'+category]
        for category in ('dx','grade'):
            st.session_state.setdefault('teaching_'+category+'_'+lang,st.session_state['teaching_'+category])
        a,b=st.columns(2);c=a
        age=a.number_input(t('Tanı yaşı','Age at diagnosis'),18,95,key='teaching_age')
        dx_names=dict(zip(['breast','bilateral','breast_ovary','male','ovarian'],t(['Tek taraflı meme','Bilateral meme','Meme + over','Erkek meme','Yalnız over'],['Unilateral breast','Bilateral breast','Breast and ovarian','Male breast','Ovarian only'])))
        dx=b.selectbox(t('Tanı','Diagnosis'),list(dx_names),format_func=dx_names.get,key='teaching_dx_'+lang)
        st.session_state['teaching_dx']=dx
        grade=c.selectbox('Grade',['g1','g2','g3'],format_func=lambda g:t({'g1':'1','g2':'2 / bilinmiyor','g3':'3'},{'g1':'1','g2':'2 / unknown','g3':'3'})[g],key='teaching_grade_'+lang)
        st.session_state['teaching_grade']=grade
        region=a.selectbox(t('Köken bölgesi','Origin region'),core.M['categorical']['region'],key='teaching_region')
        ovarian=dx=='ovarian'
        if ovarian:
            st.session_state['teaching_tnbc']=False;st.session_state['teaching_ki67_missing']=True
        tnbc=b.checkbox('TNBC',key='teaching_tnbc',disabled=ovarian)
        miss=c.checkbox(t('Ki-67 bilinmiyor','Ki-67 unknown'),key='teaching_ki67_missing',disabled=ovarian)
        ki67=b.number_input('Ki-67 (%)',0.0,100.0,key='teaching_ki67_value',disabled=miss or ovarian)
        cols=st.columns(2);family={}
        for i,k in enumerate(core.FAMILY):family[k]=cols[i%2].number_input(labels[k],0,6,key='teaching_'+k)
        urg_dec=a.checkbox(t('Tedavi kararı bekliyor','Treatment decision awaits result'),key='teaching_urg_dec')
        urg_fam=b.checkbox(t('Ailede belgeli P/LP BRCA varyantı','Documented familial P/LP BRCA variant'),key='teaching_urg_fam')
    v=dict(age=age,age_missing=0,dx=dx,grade=grade,region=region,tnbc=int(tnbc),ki67=ki67,ki67_missing=int(miss),urg_dec=urg_dec,urg_fam=urg_fam,**family)
    r=trace(v);v=r['v'];d=r['A'];lanes=t(['Normal','Öncelikli','Acil'],['Normal','Priority','Urgent'])
    baseline = trace(PRESETS[preset]['inputs'])
    change = comparison(r,st.session_state.get('_teaching_previous'))
    if change: st.session_state['_teaching_change']=change
    st.session_state['_teaching_previous']=r
    change = st.session_state.get('_teaching_change')
    with terms_col:
        terms_panel=st.container(key='teaching_terms')
    with terms_panel:
        st.subheader(t('Çarpımlar ve birikimli toplam','Products and running sum'))
        st.caption(t('Sarı satır son değişen model terimidir. Sıfır katkılar ayrıntılı tabloda bulunur.', 'Yellow marks the last edited model term. Zero contributions are in the detailed table.'))
        st.html(contribution_html(r,change,lang))
        st.latex('z='+tex(r['z']))
        if change:
            label_map=dict(labels,dx=t('Tanı','Diagnosis'),grade='Grade',region=t('Bölge','Region'),urg_dec=t('Tedavi aciliyeti','Treatment urgency'),urg_fam=t('Ailede P/LP','Familial P/LP'))
            changes='; '.join(f'{label_map.get(k,k)}: {old} → {new}' for k,(old,new) in change['changes'].items())
            details=t('Son düzenleme: ','Last edit: ')+changes+' · Δz '+fmt(change['delta_z'],8)
            if not urg_fam:details+=' · '+fmt(change['delta_pp'],2)+t(' yüzde puan',' percentage points')
            st.html('<div class="teaching-edit">'+escape(details)+'</div>')
        st.caption(t('Ara basamaklar gösterim için yuvarlanır; hesap tam katsayılarla yapılır.', 'Intermediate values are rounded for display; calculations use full coefficients.'))
        m1,m2,m3=st.columns(3)
        m1.metric(t('Gösterilen olasılık','Displayed probability'),t('Aileye özgü değerlendirme','Family-specific assessment') if urg_fam else fmt(r['p_cal']*100,1)+'%',
                  delta=None if urg_fam else fmt(100*(r['p_cal']-baseline['p_cal']),2)+t(' yüzde puan',' percentage points'),delta_color='off')
        m2.metric(t('Kart toplamı','Card score'),d['total'],delta=d['total']-baseline['A']['total'],delta_color='off')
        m3.metric(t('A / B şeridi','A / B lane'),lanes[d['lane']]+' / '+lanes[r['B']['lane']])
    with steps_col:
        steps_panel=st.container(key='teaching_equations')
    with steps_panel:
        st.subheader(t('Canlı elle hesap','Live manual calculation'))
        if urg_fam:st.caption(t('Aile bilgisi modelde yoktur. Aşağıdaki yüzde yalnız iç eğitim hesabıdır.', 'Familial information is absent from the model. The percentage below is internal teaching arithmetic only.'))
        render_compact_steps(r,lang)
    with st.expander(t('Ayrıntılı açıklamalar ve tüm sembollerle çözüm','Detailed explanations and full-symbol walkthrough')):
        if change:
            with st.expander(t('Son düzenlemenin katkıları — ne değişti?','Last-edit contributions — what changed?'),expanded=True):
                st.write(t('Olasılık farkı yüzde puandır; Δz doğrusal skor farkıdır. Girdi etkileri bu profil için koşullu hesap değişimidir, nedensel biyolojik etki değildir.', 'Probability differences are percentage points; Δz is a linear-score difference. These are conditional changes in this profile’s calculation, not causal biological effects.'))
                st.table([{t('Girdi','Input'):labels.get(k,k),t('Önce','Before'):str(old),t('Sonra','After'):str(new)} for k,(old,new) in change['changes'].items()])
                if change['contributions']:
                    st.table([{t('Model terimi','Model term'):labels.get(k,k),'Δz':fmt(delta,8)} for k,delta in change['contributions']])
                else:st.write(t('Model skoru değişmedi; bu kutular yalnız karar şeridini etkiler.','The model score did not change; these boxes affect the decision lane only.'))
        if urg_fam:st.warning(t('Aşağıdaki olasılık yalnız iç matematik hesabıdır. Model aile varyantı bilgisini içermez; kişisel olasılık olarak yorumlanmaz.','The probability below is internal arithmetic only. The model does not include familial-variant information; do not interpret it as a personal probability.'))
        st.subheader(t('1. Girdileri kodlayın','1. Encode the inputs'))
        st.write(t(f'Yaş {age}; TNBC {v["tnbc"]}; Ki-67 {v["ki67"] if not v["ki67_missing"] else 30}; Ki-67 eksik göstergesi {v["ki67_missing"]}. Yaş biliniyor, age_missing = 0. Referanslar breast, g2 ve marmara’dır; kategori göstergeleri seçiliyse 1, değilse 0 olur.',
                   f'Age {age}; TNBC {v["tnbc"]}; Ki-67 {v["ki67"] if not v["ki67_missing"] else 30}; Ki-67 missing indicator {v["ki67_missing"]}. Age is known, so age_missing = 0. Reference categories are breast, g2 and marmara; category indicators are 1 when selected, otherwise 0.'))
        st.subheader(t('2. Her katkıyı çarpıp sırayla toplayın','2. Multiply each contribution and add in sequence'))
        st.latex(r'z=\beta_0+\sum_{j=1}^{26}\beta_j x_j')
        active=[x for x in r['terms'] if x['contribution']];running=0;rows=[]
        for x in active:
            running+=x['contribution'];rows.append({t('Terim','Term'):labels.get(x['key'],x['key']),t('x × β','x × β'):f'{fmt(x["x"],2)} × ({fmt(x["beta"])})',t('Katkı','Contribution'):fmt(x['contribution']),t('Birikimli toplam','Running total'):fmt(running)})
        st.table(rows)
        st.caption(t(f'Kalan {len(r["terms"])-len(active)} terim sıfır katkı yapar. Ara değerler gösterimde yuvarlanır; karar tam olasılıkla verilir.',f'The other {len(r["terms"])-len(active)} terms contribute zero. Displayed intermediate values are rounded; decisions use the full probability.'))
        for i in range(0,len(active),2):
            line=('+'.join(r'('+tex(x['x'],0 if float(x['x']).is_integer() else 6)+r'\times('+tex(x['beta'])+r'))' for x in active[i:i+2]))
            st.latex(('z=' if i==0 else r'\phantom{z=}+')+line)
        st.latex('z='+tex(r['z']))
        st.subheader(t('3. Ham olasılık — henüz ekran yüzdesi değil','3. Raw probability — not yet the displayed percentage'))
        st.latex(r'p_{\mathrm{raw}}=\frac{1}{1+e^{-z}}=\frac{1}{1+e^{-('+tex(r['z'])+r')}}')
        st.latex(r'p_{\mathrm{raw}}=\frac{1}{1+'+tex(math.exp(-r['z']),9)+r'}='+tex(r['p_raw']))
        st.subheader(t('4. Kayıtlı kalibrasyon','4. Apply the stored calibration'))
        a=core.M['platt']['a'];b=core.M['platt']['b']
        st.latex(r'\eta=a+bz='+tex(a)+r'+('+tex(b)+r'\times('+tex(r['z'])+r'))')
        st.latex(r'\eta='+tex(a)+r'+('+tex(b*r['z'])+r')='+tex(r['eta']))
        st.write(t('a sabit düzeltme, b eğim düzeltmesidir. Yeniden öğrenilmez ve kalibrasyon ikinci kez uygulanmaz.','a is the intercept correction and b the slope correction. They are not re-estimated, and calibration must not be applied twice.'))
        st.subheader(t('5. Son olasılık ve yüzde','5. Final probability and percentage'))
        st.latex(r'p_{\mathrm{cal}}=\frac{1}{1+e^{-\eta}}=\frac{1}{1+e^{-('+tex(r['eta'])+r')}}')
        st.latex(r'p_{\mathrm{cal}}=\frac{1}{1+'+tex(math.exp(-r['eta']),9)+r'}='+tex(r['p_cal']))
        st.latex(r'100p_{\mathrm{cal}}='+tex(100*r['p_cal'],10)+r'\%\approx'+tex(100*r['p_cal'],1)+r'\%')
        st.subheader(t('6. Kart ve karar şeritleri ayrı hesaplanır','6. Calculate the card and lanes separately'))
        st.table([{t('Ölçüt','Item'):it[lang],t('Sayım','Count'):it['x'],t('Puan katkısı','Point contribution'):it['c']} for it in d['items']] or [{t('Ölçüt','Item'):t('Puan getiren ölçüt yok','No scoring items'),t('Sayım','Count'):0,t('Puan katkısı','Point contribution'):0}])
        st.latex(r'S_{\mathrm{card}}='+('+'.join(str(x['c']) for x in d['items']) or '0')+'='+str(d['total']))
        st.write(METHODS[lang][5][1])
        st.latex(r's_{\mathrm{card}}='+str(d['pl'])+r',\quad s_{\mathrm{model}}='+str(d['ml'])+r',\quad u='+str(d['urg']))
        st.latex(r'A=\max('+','.join(str(d[k]) for k in ['pl','ml','urg'])+')='+str(d['lane'])+r',\qquad B=\max('+','.join(str(d[k]) for k in ['ml','urg'])+')='+str(r['B']['lane']))
        st.write(t('Hızlı paket tetiklenmesi — A: ','Rapid-package trigger — A: ')+str(d['rapid'])+'; B: '+str(r['B']['rapid']))
        st.subheader(t('7. Ekrandaki diğer sayılar','7. Other displayed numbers'))
        st.latex(r'N=\operatorname{round}\!\left(\frac{1}{'+tex(r['p_cal'])+r'}\right)=\operatorname{round}('+tex(1/r['p_cal'],6)+')='+str(core.one_in_n(r['p_cal'])))
        st.latex(r'\pi=\frac{167}{1295}\approx12.9\%')
        q=core.M['score_percentiles'];i=0
        while i<len(q)-1 and q[i+1]<=r['p_cal']:i+=1
        if i<len(q)-1:
            st.latex(r'\mathrm{Position}=\operatorname{round}\!\left[5\left('+str(i)+r'+\frac{'+tex(r['p_cal'],10)+'-'+tex(q[i],10)+'}{'+tex(q[i+1],10)+'-'+tex(q[i],10)+r'}\right)\right]='+str(core.percentile(r['p_cal'])))
        else:st.write(t('Kodun en üst kesimi: “en üst %5” gösterilir.','At the final stored knot, the code shows “top 5%”.'))
        st.latex(r'\mathrm{Fill}=\min\!\left(100,\frac{'+tex(r['p_cal'])+r'}{0.40}\times100\right)='+tex(min(100,r['p_cal']/.4*100),4))
        st.write(t('N yuvarlanmış anlatım, π geliştirme oranı, Position skor sırası ve Fill görsel çubuk doluluğudur. Bunlar birbirinin yerine kullanılmaz.','N is a rounded description, π the development proportion, Position a score rank, and Fill the visual bar fill. These quantities are not interchangeable.'))
        with st.expander(t('Tam katsayı tablosu ve sıfır katkılar','Full coefficient table and zero contributions')):
            st.dataframe([{t('Terim','Term'):labels.get(x['key'],x['key']),'x':x['x'],'β':x['beta'],'x × β':x['contribution']} for x in r['terms']],hide_index=True,width="stretch")
    st.write(t('Modelin nasıl eğitildiğini, her sembolü ve örnek hastanın sonucunu sayıları yerine koyarak izleyin. Bütün profiller kurgudur. Yeni hasta analizi veya yeniden eğitim yapılmamıştır.',
               'Follow the training method, every symbol and a worked patient example with numbers substituted step by step. All example profiles are synthetic. No new patient analysis or model fitting was performed.'))
    left,right=st.columns(2)
    left.download_button(t('Ayrıntılı eğitim PDF’sini indir (Türkçe)','Download the detailed teaching PDF (English)'),PDF[lang].read_bytes(),file_name=PDF[lang].name,mime='application/pdf',key='teaching_pdf')
    right.download_button(t('54 kurgu örneğin sayılarını indir (CSV)','Download numbers for 54 synthetic examples (CSV)'),(ASSETS/'synthetic_examples.csv').read_bytes(),file_name='BRCA_synthetic_teaching_examples.csv',mime='text/csv',key='teaching_csv')
    st.markdown(f"[Türkçe bağlantı]({PUBLIC_URL}?sayfa=model&dil=tr) · [English link]({PUBLIC_URL}?sayfa=model&dil=en)")
    st.info(t('Üç ayrı katman: lojistik model olasılığı, ayrı puan kartı ve A/B sıra kuralları. Kart puanı yüzdeye çevrilmez. Sağlıklı kişilerde gelecekte kanser olma riski hesaplanmaz.',
              'Three separate layers: logistic-model probability, a separately fitted points card, and A/B queue rules. Points are not converted into a percentage. This does not estimate future cancer risk in healthy people.'))
    st.caption(t('TNBC: üçlü negatif meme kanseri (ER, PR ve HER2 negatif). Ki-67: çoğalma belirteci yüzdesi. MLPA: Multiplex Ligation-dependent Probe Amplification; büyük delesyon/duplikasyonları değerlendiren yöntem. P/LP: patojenik / olası patojenik; VUS: anlamı belirsiz varyant.', 'TNBC: Triple-Negative Breast Cancer (negative ER, Estrogen Receptor; PR, Progesterone Receptor; HER2, Human Epidermal Growth Factor Receptor 2). Ki-67: proliferation-marker percentage. MLPA: Multiplex Ligation-dependent Probe Amplification for deletion/duplication assessment. P/LP: Pathogenic/Likely Pathogenic; VUS: Variant of Uncertain Significance.'))
    with st.expander(t('Sembol sözlüğü — her işaret ne anlama geliyor?','Symbol glossary — what does each sign mean?')):
        st.table([dict(zip([t('Sembol','Symbol'),t('Anlamı','Meaning')],row)) for row in (SYMBOLS_TR if tr else SYMBOLS_EN)])
        st.latex(r'\operatorname{logit}(p)=\log\!\left(\frac{p}{1-p}\right),\qquad\mathrm{odds}=\frac{p}{1-p}')
    st.header(t('Model nasıl eğitildi ve sınırları neler?','How was the model trained, and what are its limitations?'))
    for heading,body in METHODS[lang]:
        st.subheader(heading);st.write(body)
    st.latex(r'w_+=\frac{1295}{2\times167}=3.877246,\qquad w_-=\frac{1295}{2\times1128}=0.574025')
    with st.expander(t('Kapasite ve doğrulama sayılarının aritmetiği','Arithmetic behind capacity and validation totals')):
        st.write(t('Model ≥%20: 212,6 paket / 26,6 hedef; A: 280 paket /29,4 hedef. Bunlar kayıtlı tekrar ortalamalarıdır.','Model ≥20%: 212.6 packages /26.6 targets; A: 280 packages /29.4 targets. These are stored repeat means.'))
        st.latex(r'\Delta N=212.6-280=-67.4,\quad\Delta T=26.6-29.4=-2.8')
        st.latex(r'\mathrm{Yield}=\frac{26.6}{212.6}\times100=12.511759\%,\quad\mathrm{Packages/target}=\frac{212.6}{26.6}=7.992481')
        st.write(t('Oranların ortalaması 8,0129973 ile ortalamaların oranı 7,9924812 aynı işlem değildir.','The mean of ratios, 8.0129973, and ratio of means, 7.9924812, are different operations.'))
        st.latex(r'\mathrm{Sensitivity}=\frac{159}{167}=95.2096\%,\quad\mathrm{NPV}=\frac{150}{158}=94.9367\%')
        st.write(t('Bu son örnek tarihsel %95 duyarlılık çizgisine aittir (0,035019185420); ana %10/%20 şeritleri veya %5 + dışlama politikası değildir.','The last example concerns the historical 95%-sensitivity threshold (0.035019185420), not the main 10%/20% lanes or the 5%-plus-exclusions policy.'))
    st.caption(t('Kaynak: sabit model paketi ve özgün eğitim betiklerinin mevcut denetimi. 54 kurgu profil ile 47 kayıtlı öz-test yalnız hesap eşleşmesini denetler; bağımsız klinik doğrulama değildir.','Source: the frozen model package and the existing audit of original training scripts. The 54 synthetic profiles and 47 stored self-tests verify arithmetic agreement only, not independent clinical validity.'))
