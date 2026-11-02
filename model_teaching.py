"""Student-facing numerical explanation; never fits a model or changes calculator state."""
import json
import math
import re
from itertools import count
from html import escape
from pathlib import Path
import streamlit as st
import brca_core as core
from model_teaching_content import ASSETS, SYMBOLS_TR, SYMBOLS_EN, METHODS, LABELS_TR, LABELS_EN, ORIGIN_INTRO

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
                contributions=contributions, previous=previous)



WORKBENCH_STYLE = """<style>
@media(min-width:1100px){
.block-container:has(.st-key-teaching_workbench){max-width:none!important;width:100%;padding:0 28px 36px!important}
.block-container:has(.st-key-teaching_workbench) h1{font-size:28px!important;margin:8px 0 4px!important;padding:0!important}
.st-key-teaching_inputs,.st-key-teaching_terms,.st-key-teaching_equations{height:calc(100dvh - 305px)!important;max-height:calc(100dvh - 305px)!important;overflow-y:auto;overflow-x:hidden;border:1px solid #dce1e8;border-radius:12px;padding:14px;background:#fff;box-sizing:border-box;scrollbar-gutter:stable}
.st-key-teaching_inputs [data-testid=stVerticalBlock],.st-key-teaching_terms [data-testid=stVerticalBlock],.st-key-teaching_equations [data-testid=stVerticalBlock]{gap:6px}
.st-key-teaching_inputs [data-testid=stWidgetLabel] p{font-size:12px;line-height:1.2}
.st-key-teaching_inputs input{font-size:14px;min-height:30px}
.st-key-teaching_inputs [data-baseweb=select]{font-size:13px}
.st-key-teaching_inputs [data-testid=stCaptionContainer] p{font-size:11px}
.st-key-teaching_equations .katex{font-size:clamp(11px,.65vw,16px)}
.st-key-teaching_equations .katex-display{margin:.35em 0}
.st-key-teaching_terms [data-testid=stMetricValue]{font-size:22px}
.st-key-teaching_terms [data-testid=stMetricLabel] p{font-size:11px}
.st-key-teaching_terms [data-testid=stMetricDelta]{font-size:11px}
}
@media(max-width:1099px){
.st-key-teaching_workbench [data-testid=stHorizontalBlock]:has(.st-key-teaching_inputs){flex-direction:column}
.st-key-teaching_workbench [data-testid=stHorizontalBlock]:has(.st-key-teaching_inputs)>[data-testid=stColumn]{width:100%!important;flex:1 1 100%!important}
}
@media(max-width:1799px){.st-key-teaching_family [data-testid=stHorizontalBlock]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.st-key-teaching_family [data-testid=stColumn]{width:100%!important;min-width:0!important}}
.st-key-teaching_workbench h3{font-size:19px!important;margin:0 0 8px!important;padding:0!important}
.teaching-arithmetic{width:100%;border-collapse:collapse;font-size:clamp(11px,.7vw,14px);font-variant-numeric:tabular-nums;color:#17212b}
.teaching-arithmetic th,.teaching-arithmetic td{padding:6px 5px;border-bottom:1px solid #e2e6eb;text-align:right;vertical-align:top}
.teaching-arithmetic th:first-child,.teaching-arithmetic td:first-child{text-align:left;width:28%}
.teaching-arithmetic th{background:#f0f2f8;font-size:11px}.teaching-arithmetic .edited{background:#fff1c7}
.teaching-arithmetic .product{white-space:normal}.formula-current{background:#fff1c7;color:#784000;padding:1px 2px;border-radius:3px}.formula-previous{color:#596579;white-space:nowrap;font-size:.78em;display:inline-block}.st-key-teaching_equations .katex{max-width:100%}.teaching-arithmetic small{color:#627181}
.st-key-teaching_origin_header h1{font-size:24px!important}.st-key-teaching_origin_header [data-testid=stCaptionContainer] p{font-size:12px}@media(max-width:1799px){.st-key-teaching_origin_header [data-testid=stHorizontalBlock]{flex-direction:column}.st-key-teaching_origin_header [data-testid=stColumn]{width:100%!important;flex:1 1 100%!important}}
.teaching-origin{padding:10px 14px;border-left:3px solid #7560ce;background:#eef2f7;border-radius:6px;color:#17212b}.teaching-origin h2{font-size:16px!important;line-height:1.3;margin:0 0 5px!important;padding:0!important}.teaching-origin>div{display:grid;grid-template-columns:1fr 1fr;gap:24px}.teaching-origin p{font-size:13px;line-height:1.45;margin:0}@media(max-width:1099px){.teaching-origin>div{grid-template-columns:1fr;gap:8px}}
[data-testid=stLayoutWrapper]:has(>[class*=st-key-teaching_formula_mobile_]),[class*=st-key-teaching_formula_mobile_]{display:none!important}
@media(max-width:1099px){
 [data-testid=stLayoutWrapper]:has(>[class*=st-key-teaching_formula_desktop_]),[class*=st-key-teaching_formula_desktop_]{display:none!important}
 [data-testid=stLayoutWrapper]:has(>[class*=st-key-teaching_formula_mobile_]),[class*=st-key-teaching_formula_mobile_]{display:flex!important;gap:0!important}
 [class*=st-key-teaching_formula_mobile_] .katex{font-size:clamp(14px,4.1vw,18px)!important}
 [class*=st-key-teaching_formula_mobile_] .katex-display{padding:.65em .12em!important}
}

.teaching-edit{padding:8px 10px;margin-top:8px;border-left:3px solid #7560ce;background:#f4f1fc;font-size:12px;line-height:1.45;color:#17212b}
/* KaTeX fractions and superscripts draw above/below their text baseline.
   Reserve ink space inside the horizontal scroller instead of clipping that ink. */
.block-container:has(.st-key-teaching_workbench) [data-testid=stMarkdownContainer]:has(.katex-display){overflow:visible!important;margin-bottom:0!important}
.block-container:has(.st-key-teaching_workbench) .katex-display{overflow-x:auto!important;overflow-y:hidden!important;padding:.65em .12em!important;margin:0!important;box-sizing:content-box}
@media(min-width:1100px){.st-key-teaching_equations [data-testid=stVerticalBlock]{gap:2px}}
</style>"""




_formula_ids = count()


def _tex_parts(formula, separators):
    """Split only between complete top-level expressions, never inside a fraction."""
    parts=[];start=0;braces=0;parens=0;i=0
    while i<len(formula):
        c=formula[i]
        if c=='{':braces+=1
        elif c=='}':braces-=1
        elif not braces:
            if c in '([':parens+=1
            elif c in ')]':parens-=1
        if not braces and not parens and c in separators:
            parts.append(formula[start:i]);start=i+1
        i+=1
    parts.append(formula[start:])
    return parts


def mobile_formula_steps(formula):
    # Place the previous value below the current value inside its existing box.
    formula=re.sub(r'(\\boxed\{)([-\d.,{}]+)\\;\{\\scriptstyle\\color\{#596579\}\{(\[\\leftarrow .*?\])\}\}',
                   lambda m:m[1]+r'\substack{'+m[2]+r'\\{\scriptstyle\color{#596579}{'+m[3]+r'}}}',formula)
    groups=[]
    for equation in re.split(r',?\\q(?:quad|uad)\s*',formula):
        chain=_tex_parts(equation,'=')
        if len(chain)==1:
            terms=_tex_parts(equation,'+')
            if len(terms)>1:
                terms=[term for term in terms if term and term != r'\phantom{z=}']
                groups.append(r'\begin{aligned}'+r'\\'.join(('' if j==0 and not equation.startswith(r'\phantom') else '+')+term for j,term in enumerate(terms))+r'\end{aligned}')
            else:groups.append(equation)
            continue
        rows=[]
        lhs=chain[0]
        for rhs in chain[1:]:
            visible=re.sub(r'\\[A-Za-z]+|[{}]','',rhs)
            terms=_tex_parts(rhs,'+') if len(visible)>30 else [rhs]
            rows.append(lhs+'&='+terms[0])
            for term in terms[1:]:
                product=re.fullmatch(r'\((.*?)\\times\((.*)\)\)',term)
                if product:
                    term=r'\left(\begin{gathered}'+product[1]+r'\\\times('+product[2]+r')\end{gathered}\right)'
                if term:rows.append('&+'+term)
        groups.append(r'\begin{aligned}'+r'\\'.join(rows)+r'\end{aligned}')
    return groups


def teaching_latex(formula, mobile_steps=None):
    """Keep desktop equations intact; show a sequence of short equations on mobile."""
    ident=next(_formula_ids)
    with st.container(key=f'teaching_formula_desktop_{ident}'):
        st.latex(formula)
    with st.container(key=f'teaching_formula_mobile_{ident}'):
        for source in (mobile_steps or [formula]):
            for step in mobile_formula_steps(source):
                st.markdown('$$\n'+step+'\n$$')


def paired_tex(value, previous, lang, digits=8, rounded=False):
    """Mark a changed displayed quantity, with its previous value beside it."""
    if rounded:
        value=round(value,digits)
        previous=None if previous is None else round(previous,digits)
    changed=previous is not None and value != previous
    precision=digits
    if changed and not rounded and f'{value:.{digits}f}' == f'{previous:.{digits}f}':precision=14
    def number(x):
        result=f'{x:.{precision}f}'
        return result.replace('.','{,}') if lang=='tr' else result
    current=number(value)
    if not changed:return current
    return r'\color{#955000}{\boxed{'+current+r'\;{\scriptstyle\color{#596579}{[\leftarrow '+number(previous)+r']}}}}'


def contribution_html(current, change, lang):
    t=lambda a,b:a if lang=='tr' else b
    labels=LABELS_TR if lang=='tr' else LABELS_EN
    previous=change.get('previous') if change else None
    old_terms={term['key']:term for term in previous['terms']} if previous else {}
    fmt=lambda x,d=8:f'{x:.{d}f}'.replace('.',',') if lang=='tr' else f'{x:.{d}f}'
    def pair(value,old,digits=8):
        text=fmt(value,digits)
        if old is None or value==old:return text
        if text==fmt(old,digits):text=fmt(value,14);digits=14
        return '<mark class="formula-current">'+text+'</mark><small class="formula-previous"> ← '+fmt(old,digits)+'</small>'
    running=old_running=0;rows=[]
    for term in current['terms']:
        old=old_terms.get(term['key'])
        running+=term['contribution']
        old_running+=old['contribution'] if old else 0
        if not term['contribution'] and not (old and old['contribution']):continue
        digits=0 if float(term['x']).is_integer() and (not old or float(old['x']).is_integer()) else 3
        product=pair(term['x'],old['x'] if old else None,digits)+' × ('+fmt(term['beta'])+')'
        contribution=pair(term['contribution'],old['contribution'] if old else None)
        cumulative=pair(running,old_running if old else None)
        edited=old is not None and term['contribution'] != old['contribution']
        rows.append(f"<tr class=\"{'edited' if edited else ''}\"><td>{escape(labels.get(term['key'],term['key']))}</td><td class='product'>{product}</td><td>{contribution}</td><td>{cumulative}</td></tr>")
    return f"""<table class="teaching-arithmetic" aria-label="{t('Canlı katkılar ve birikimli toplam','Live contributions and running sum')}"><thead><tr><th>{t('Terim','Term')}</th><th><i>x</i> × <i>β</i></th><th>{t('Katkı','Contribution')}</th><th>{t('Birikimli','Running sum')}</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"""



def decision_formulas(r,previous,lang):
    d=r['A'];parts=[]
    now={it['key']:it['c'] for it in d['items']}
    old={it['key']:it['c'] for it in previous['A']['items']} if previous else {}
    for item in core.M['points']['items']:
        k=item['key'];new=now.get(k,0);before=old.get(k,0)
        if new or before:parts.append(paired_tex(new,before if previous else None,lang,0))
    total=paired_tex(d['total'],previous['A']['total'] if previous else None,lang,0)
    lane=lambda rule,k:paired_tex(r[rule][k],previous[rule][k] if previous else None,lang,0)
    return [r'S_{\mathrm{card}}='+('+'.join(parts) or '0')+'='+total,
            r'A=\max('+','.join(lane('A',k) for k in ('pl','ml','urg'))+')='+lane('A','lane'),
            r'B=\max('+','.join(lane('B',k) for k in ('ml','urg'))+')='+lane('B','lane')]

def render_compact_steps(r,lang,previous=None):
    t=lambda a,b:a if lang=='tr' else b
    num=lambda x,d=8:paired_tex(x,None,lang,d)
    field=lambda key,d=8:paired_tex(r[key],previous[key] if previous else None,lang,d)
    derived=lambda fn,d=8:paired_tex(fn(r),fn(previous) if previous else None,lang,d)
    a,b=core.M['platt']['a'],core.M['platt']['b'];d=r['A']
    st.markdown(t('**1 · Katkıları topla → z**','**1 · Sum contributions → z**'))
    teaching_latex(r'z=\beta_0+\textstyle\sum_{j=1}^{26}\beta_jx_j='+field('z'))
    st.markdown(t('**2 · Ham sigmoid (henüz son yüzde değil)**','**2 · Raw sigmoid (not the final percentage)**'))
    teaching_latex(r'p_{\mathrm{raw}}=\frac{1}{1+e^{-('+field('z')+r')}}=\frac{1}{1+'+derived(lambda x:math.exp(-x['z']))+r'}='+field('p_raw'))
    st.markdown(t('**3 · Kayıtlı kalibrasyona yerleştir**','**3 · Substitute into stored calibration**'))
    teaching_latex(r'\eta='+num(a)+r'+('+num(b)+r'\times('+field('z')+r'))')
    teaching_latex(r'\eta='+field('eta'))
    st.markdown(t('**4 · Son sigmoid → yüzde**','**4 · Final sigmoid → percentage**'))
    teaching_latex(r'p_{\mathrm{cal}}=\frac{1}{1+e^{-('+field('eta')+r')}}=\frac{1}{1+'+derived(lambda x:math.exp(-x['eta']))+r'}='+field('p_cal',9))
    teaching_latex(r'100p_{\mathrm{cal}}='+derived(lambda x:100*x['p_cal'],6)+r'\%\approx'+paired_tex(100*r['p_cal'],100*previous['p_cal'] if previous else None,lang,1,rounded=True)+r'\%')
    st.markdown(t('**5 · Kart ve şeritler (ayrı hesap)**','**5 · Card and lanes (separate calculation)**'))
    for formula in decision_formulas(r,previous,lang):teaching_latex(formula)


def render_model_teaching(lang):
    tr = lang == 'tr'
    t = lambda a,b: a if tr else b
    labels = LABELS_TR if tr else LABELS_EN
    fmt = lambda x,d=12: f'{x:.{d}f}'.replace('.', ',') if tr else f'{x:.{d}f}'
    tex = lambda x,d=12: f'{x:.{d}f}'.replace('.', '{,}') if tr else f'{x:.{d}f}'
    st.html(WORKBENCH_STYLE)
    with st.container(key='teaching_origin_header'):
        title_col,intro_col=st.columns([1.1,3],vertical_alignment='center')
    with title_col:
        st.title(t('Model ayrıntıları ve elle hesap','Model details and manual calculations'))
        st.caption(t('Öğrenci eğitim sayfası · 2 Kasım 2026 · sabit model ', 'Student teaching page · 2 November 2026 · frozen model ')+core.M['build'])
    with intro_col:
        origin=ORIGIN_INTRO[lang]
        st.html('<section class="teaching-origin" aria-label="'+escape(origin['title'])+'"><h2>'+escape(origin['title'])+'</h2><div>'+''.join('<p>'+escape(paragraph)+'</p>' for paragraph in origin['paragraphs'])+'</div></section>')
    with st.container(key='teaching_workbench'):
        input_col,terms_col,steps_col=st.columns([0.95,1.15,1.05],gap='medium')
    with input_col:
        input_panel=st.container(key='teaching_inputs')
    with input_panel:
        st.subheader(t('Girdiler','Inputs'))
        names = [t('Temel profil: 50 yaş','Baseline profile: age 50'),t('Sitedeki örnek hasta: 38 yaş','Site example patient: age 38'),t('Kart ile modelin ayrıldığı profil','Card/model disagreement example')]
        preset_key = 'teaching_preset_'+lang
        selected=st.session_state.get('_teaching_selected_preset',1)
        if type(selected) is not int or not 0 <= selected < len(PRESETS):selected=1
        # A cleared/stale widget must never become a PRESETS index. A nonempty
        # default also removes the selectbox's clear-selection control.
        widget_preset=st.session_state.get(preset_key)
        if widget_preset is None or type(widget_preset) is not int or not 0 <= widget_preset < len(PRESETS):
            st.session_state.pop(preset_key,None)
        if st.session_state.get('_teaching_input_language') != lang:
            st.session_state.pop(preset_key,None)
            # Widget labels change with the language. Restore their values from
            # a non-widget snapshot before Streamlit registers the new labels.
            for k,x in st.session_state.get('_teaching_input_snapshot',{}).items():
                key='teaching_ki67_value' if k=='ki67' else 'teaching_'+k
                st.session_state[key]=bool(x) if k in ('tnbc','ki67_missing','urg_dec','urg_fam') else x
                if k in ('dx','grade'):st.session_state[key+'_'+lang]=x
            st.session_state['_teaching_input_language']=lang
        preset_col,reset_col=st.columns([3,1],vertical_alignment='bottom')
        preset = preset_col.selectbox(t('Eğitim profili','Teaching profile'),range(3),index=selected,format_func=lambda i:names[i],key=preset_key)
        if preset is None:preset=selected
        st.session_state['_teaching_selected_preset']=preset
        if reset_col.button(t('Sıfırla','Reset'),key='teaching_reset',width='stretch'):
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
        with st.container(key='teaching_family'):
            cols=st.columns(4);family={}
            for i,k in enumerate(core.FAMILY):family[k]=cols[i%4].number_input(labels[k],0,6,key='teaching_'+k)
        urg_dec=a.checkbox(t('Tedavi kararı bekliyor','Treatment decision awaits result'),key='teaching_urg_dec')
        urg_fam=b.checkbox(t('Ailede belgeli P/LP BRCA varyantı','Documented familial P/LP BRCA variant'),key='teaching_urg_fam')
    v=dict(age=age,age_missing=0,dx=dx,grade=grade,region=region,tnbc=int(tnbc),ki67=ki67,ki67_missing=int(miss),urg_dec=urg_dec,urg_fam=urg_fam,**family)
    st.session_state['_teaching_input_snapshot']=dict(v)
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
        st.caption(t('Sarı değer güncel; ← önceki değer. Birikimli toplamda değişen her hücre işaretlenir.', 'Yellow values are current; ← previous. Every affected running-sum cell is marked.'))
        st.html(contribution_html(r,change,lang))
        teaching_latex('z='+paired_tex(r['z'],change['previous']['z'] if change and change.get('previous') else None,lang,12))
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
        previous=change.get('previous') if change else None
        st.caption(t('Kutudaki sayı güncel değerdir; yanındaki ← önceki değeri gösterir. Yalnız son düzenlemeden etkilenen değerler işaretlenir.', 'Boxed values are current; ← shows the previous value beside each one. Only quantities affected by the last edit are marked.'))
        if urg_fam:st.caption(t('Aile bilgisi modelde yoktur. Aşağıdaki yüzde yalnız iç eğitim hesabıdır.', 'Familial information is absent from the model. The percentage below is internal teaching arithmetic only.'))
        render_compact_steps(r,lang,previous)
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
        teaching_latex(r'z=\beta_0+\sum_{j=1}^{26}\beta_j x_j')
        active=[x for x in r['terms'] if x['contribution']];running=0;rows=[]
        for x in active:
            running+=x['contribution'];rows.append({t('Terim','Term'):labels.get(x['key'],x['key']),t('x × β','x × β'):f'{fmt(x["x"],2)} × ({fmt(x["beta"])})',t('Katkı','Contribution'):fmt(x['contribution']),t('Birikimli toplam','Running total'):fmt(running)})
        st.table(rows)
        st.caption(t(f'Kalan {len(r["terms"])-len(active)} terim sıfır katkı yapar. Ara değerler gösterimde yuvarlanır; karar tam olasılıkla verilir.',f'The other {len(r["terms"])-len(active)} terms contribute zero. Displayed intermediate values are rounded; decisions use the full probability.'))
        for i in range(0,len(active),2):
            line=('+'.join(r'('+paired_tex(x['x'],next((old['x'] for old in previous['terms'] if old['key']==x['key']),0) if previous else None,lang,0 if float(x['x']).is_integer() else 6)+r'\times('+tex(x['beta'])+r'))' for x in active[i:i+2]))
            teaching_latex(('z=' if i==0 else r'\phantom{z=}+')+line)
        teaching_latex('z='+paired_tex(r['z'],previous['z'] if previous else None,lang,12))
        st.subheader(t('3. Ham olasılık — henüz ekran yüzdesi değil','3. Raw probability — not yet the displayed percentage'))
        teaching_latex(r'p_{\mathrm{raw}}=\frac{1}{1+e^{-z}}=\frac{1}{1+e^{-('+paired_tex(r['z'],previous['z'] if previous else None,lang,12)+r')}}')
        teaching_latex(r'p_{\mathrm{raw}}=\frac{1}{1+'+paired_tex(math.exp(-r['z']),math.exp(-previous['z']) if previous else None,lang,9)+r'}='+paired_tex(r['p_raw'],previous['p_raw'] if previous else None,lang,12))
        st.subheader(t('4. Kayıtlı kalibrasyon','4. Apply the stored calibration'))
        a=core.M['platt']['a'];b=core.M['platt']['b']
        teaching_latex(r'\eta=a+bz='+tex(a)+r'+('+tex(b)+r'\times('+paired_tex(r['z'],previous['z'] if previous else None,lang,12)+r'))')
        teaching_latex(r'\eta='+tex(a)+r'+('+paired_tex(b*r['z'],b*previous['z'] if previous else None,lang,12)+r')='+paired_tex(r['eta'],previous['eta'] if previous else None,lang,12))
        st.write(t('a sabit düzeltme, b eğim düzeltmesidir. Yeniden öğrenilmez ve kalibrasyon ikinci kez uygulanmaz.','a is the intercept correction and b the slope correction. They are not re-estimated, and calibration must not be applied twice.'))
        st.subheader(t('5. Son olasılık ve yüzde','5. Final probability and percentage'))
        teaching_latex(r'p_{\mathrm{cal}}=\frac{1}{1+e^{-\eta}}=\frac{1}{1+e^{-('+paired_tex(r['eta'],previous['eta'] if previous else None,lang,12)+r')}}')
        teaching_latex(r'p_{\mathrm{cal}}=\frac{1}{1+'+paired_tex(math.exp(-r['eta']),math.exp(-previous['eta']) if previous else None,lang,9)+r'}='+paired_tex(r['p_cal'],previous['p_cal'] if previous else None,lang,12))
        teaching_latex(r'100p_{\mathrm{cal}}='+paired_tex(100*r['p_cal'],100*previous['p_cal'] if previous else None,lang,10)+r'\%\approx'+paired_tex(100*r['p_cal'],100*previous['p_cal'] if previous else None,lang,1,rounded=True)+r'\%')
        st.subheader(t('6. Kart ve karar şeritleri ayrı hesaplanır','6. Calculate the card and lanes separately'))
        st.table([{t('Ölçüt','Item'):it[lang],t('Sayım','Count'):it['x'],t('Puan katkısı','Point contribution'):it['c']} for it in d['items']] or [{t('Ölçüt','Item'):t('Puan getiren ölçüt yok','No scoring items'),t('Sayım','Count'):0,t('Puan katkısı','Point contribution'):0}])
        teaching_latex(decision_formulas(r,previous,lang)[0])
        st.write(METHODS[lang][5][1])
        teaching_latex(r's_{\mathrm{card}}='+paired_tex(d['pl'],previous['A']['pl'] if previous else None,lang,0)+r',\quad s_{\mathrm{model}}='+paired_tex(d['ml'],previous['A']['ml'] if previous else None,lang,0)+r',\quad u='+paired_tex(d['urg'],previous['A']['urg'] if previous else None,lang,0))
        teaching_latex(decision_formulas(r,previous,lang)[1])
        teaching_latex(decision_formulas(r,previous,lang)[2])
        st.write(t('Hızlı paket tetiklenmesi — A: ','Rapid-package trigger — A: ')+str(d['rapid'])+'; B: '+str(r['B']['rapid']))
        st.subheader(t('7. Ekrandaki diğer sayılar','7. Other displayed numbers'))
        pair=lambda value,old,d=8:paired_tex(value,old if previous else None,lang,d)
        old_p=previous['p_cal'] if previous else r['p_cal']
        teaching_latex(r'N=\operatorname{round}\!\left(\frac{1}{'+pair(r['p_cal'],old_p,12)+r'}\right)=\operatorname{round}('+pair(1/r['p_cal'],1/old_p,6)+')='+pair(core.one_in_n(r['p_cal']),core.one_in_n(old_p),0))
        teaching_latex(r'\pi=\frac{167}{1295}\approx12.9\%')
        q=core.M['score_percentiles']
        def knot(probability):
            i=0
            while i<len(q)-1 and q[i+1]<=probability:i+=1
            return i
        i=knot(r['p_cal']);old_i=knot(old_p)
        if i<len(q)-1:
            old_lower=q[old_i];old_upper=q[min(old_i+1,len(q)-1)]
            teaching_latex(r'\mathrm{Position}=\operatorname{round}\!\left[5\left('+pair(i,old_i,0)+r'+\frac{'+pair(r['p_cal'],old_p,10)+'-'+pair(q[i],old_lower,10)+'}{'+pair(q[i+1],old_upper,10)+'-'+pair(q[i],old_lower,10)+r'}\right)\right]='+pair(core.percentile(r['p_cal']),core.percentile(old_p),0), mobile_steps=[r'd='+pair(q[i+1],old_upper,10)+'-'+pair(q[i],old_lower,10),r'n='+pair(r['p_cal'],old_p,10)+'-'+pair(q[i],old_lower,10),r'f=\frac{n}{d}=\frac{'+pair(r['p_cal']-q[i],old_p-old_lower,10)+r'}{'+pair(q[i+1]-q[i],old_upper-old_lower,10)+r'}',r'\mathrm{Position}=\operatorname{round}[5('+pair(i,old_i,0)+'+f)]',r'\mathrm{Position}='+pair(core.percentile(r['p_cal']),core.percentile(old_p),0)])
        else:st.write(t('Kodun en üst kesimi: “en üst %5” gösterilir.','At the final stored knot, the code shows “top 5%”.'))
        teaching_latex(r'\mathrm{Fill}=\min\!\left(100,\frac{'+pair(r['p_cal'],old_p,12)+r'}{0.40}\times100\right)='+pair(min(100,r['p_cal']/.4*100),min(100,old_p/.4*100),4))
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
        teaching_latex(r'\operatorname{logit}(p)=\log\!\left(\frac{p}{1-p}\right),\qquad\mathrm{odds}=\frac{p}{1-p}')
    st.header(t('Model nasıl eğitildi ve sınırları neler?','How was the model trained, and what are its limitations?'))
    for heading,body in METHODS[lang]:
        st.subheader(heading);st.write(body)
    teaching_latex(r'w_+=\frac{1295}{2\times167}=3.877246,\qquad w_-=\frac{1295}{2\times1128}=0.574025')
    with st.expander(t('Kapasite ve doğrulama sayılarının aritmetiği','Arithmetic behind capacity and validation totals')):
        st.write(t('Model ≥%20: 212,6 paket / 26,6 hedef; A: 280 paket /29,4 hedef. Bunlar kayıtlı tekrar ortalamalarıdır.','Model ≥20%: 212.6 packages /26.6 targets; A: 280 packages /29.4 targets. These are stored repeat means.'))
        teaching_latex(r'\Delta N=212.6-280=-67.4,\quad\Delta T=26.6-29.4=-2.8')
        teaching_latex(r'\mathrm{Yield}=\frac{26.6}{212.6}\times100=12.511759\%,\quad\mathrm{Packages/target}=\frac{212.6}{26.6}=7.992481')
        st.write(t('Oranların ortalaması 8,0129973 ile ortalamaların oranı 7,9924812 aynı işlem değildir.','The mean of ratios, 8.0129973, and ratio of means, 7.9924812, are different operations.'))
        teaching_latex(r'\mathrm{Sensitivity}=\frac{159}{167}=95.2096\%,\quad\mathrm{NPV}=\frac{150}{158}=94.9367\%')
        st.write(t('Bu son örnek tarihsel %95 duyarlılık çizgisine aittir (0,035019185420); ana %10/%20 şeritleri veya %5 + dışlama politikası değildir.','The last example concerns the historical 95%-sensitivity threshold (0.035019185420), not the main 10%/20% lanes or the 5%-plus-exclusions policy.'))
    st.caption(t('Kaynak: sabit model paketi ve özgün eğitim betiklerinin mevcut denetimi. 54 kurgu profil ile 47 kayıtlı öz-test yalnız hesap eşleşmesini denetler; bağımsız klinik doğrulama değildir.','Source: the frozen model package and the existing audit of original training scripts. The 54 synthetic profiles and 47 stored self-tests verify arithmetic agreement only, not independent clinical validity.'))
