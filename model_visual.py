"""Visualise a frozen synthetic prediction, without fitting or changing any weights."""
import math
import base64
from html import escape

from model_teaching_content import LABELS_TR, LABELS_EN
import brca_core as core


def model_visual_html(current, change, lang):
    t = lambda tr, en: tr if lang == 'tr' else en
    labels = LABELS_TR if lang == 'tr' else LABELS_EN
    previous = change.get('previous') if change else None
    old_terms = {term['key']: term for term in previous['terms']} if previous else {}
    def fmt(value, digits=4):
        text = f'{value:.{digits}f}'
        return text.replace('.', ',') if lang == 'tr' else text
    def pair(value, old, digits=4):
        number = fmt(value, digits)
        if old is None or value == old:
            return number
        return f'<mark>{number}</mark> <small>← {fmt(old, digits)}</small>'
    active = [term for term in current['terms'] if term['contribution'] or
              old_terms.get(term['key'], {}).get('contribution')]
    scale = max([abs(term['contribution']) for term in active] +
                [abs(term['contribution']) for term in old_terms.values()] + [1])
    rows = []
    for term in active:
        old = old_terms.get(term['key'])
        value = term['contribution']
        old_value = old['contribution'] if old else None
        width = abs(value) / scale * 49
        left = 50 if value >= 0 else 50 - width
        color = '#148579' if value >= 0 else '#9c5594'
        ghost = ''
        if old_value is not None and old_value != value:
            old_width = abs(old_value) / scale * 49
            old_left = 50 if old_value >= 0 else 50-old_width
            ghost = f'<span class="mv-oldbar" style="left:{old_left}%;width:{old_width}%"></span>'
        rows.append(f'''<div class="mv-term" data-term="{escape(term['key'])}">
          <div><b>{escape(labels.get(term['key'], term['key']))}</b>
          <span class="mv-product">{pair(term['x'], old['x'] if old else None, 1)} ×
          <span class="mv-beta">β {fmt(term['beta'], 6)} · {t('sabit', 'fixed')}</span>
          = {pair(value, old_value)}</span></div>
          <div class="mv-track"><span class="mv-zero"></span>{ghost}
          <span class="mv-bar" style="left:{left}%;width:{width}%;background:{color}"></span></div></div>''')
    a, b = core.M['platt']['a'], core.M['platt']['b']
    low = min(-6, current['z']-1, previous['z']-1 if previous else -6)
    high = max(6, current['z']+1, previous['z']+1 if previous else 6)
    x = lambda z: 42 + (z-low)/(high-low)*312
    y = lambda p: 150-120*p
    sigmoid = lambda z: 1/(1+math.exp(-(a+b*z)))
    points = ' '.join(f'{x(low+(high-low)*i/160):.2f},{y(sigmoid(low+(high-low)*i/160)):.2f}' for i in range(161))
    old_dot = ''
    if previous:
        old_dot = f'<circle cx="{x(previous["z"]):.2f}" cy="{y(previous["p_cal"]):.2f}" r="6" fill="white" stroke="#6b7280" stroke-width="2"/>'
    graph = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 190" role="img" aria-label="{t('Sabit kalibrasyon eğrisi üzerinde değişen skor', 'Changing score on the fixed calibration curve')}">
      <path d="M42 24V150H355" fill="none" stroke="#94a3b8"/>
      <text x="4" y="34">100%</text><text x="12" y="94">50%</text><text x="18" y="154">0%</text>
      <path d="M42 90H355" stroke="#e2e8f0"/>
      <polyline points="{points}" fill="none" stroke="#7560ce" stroke-width="3"/>
      {old_dot}<circle cx="{x(current['z']):.2f}" cy="{y(current['p_cal']):.2f}" r="5" fill="#0f766e" stroke="white" stroke-width="1.5"/>
      <text x="42" y="169">{fmt(low, 1)}</text><text x="326" y="169">{fmt(high, 1)}</text>
      <text x="145" y="187">{t('Doğrusal skor z', 'Linear score z')}</text>
      <style>text{{font:11px Arial;fill:#4b5563}}</style></svg>'''
    # st.html sanitises inline SVG; an SVG image preserves the fixed curve safely.
    graph = '<img class="mv-curve" alt="'+t('Sabit eğri; güncel ve önceki skor noktaları', 'Fixed curve with current and previous score points')+'" src="data:image/svg+xml;base64,'+base64.b64encode(graph.encode()).decode()+'">'
    stages = []
    for label, key, multiplier, digits in [(t('Katkıların toplamı', 'Sum of contributions'), 'z', 1, 6),
        (t('Ham olasılık', 'Raw probability'), 'p_raw', 100, 2),
        (t('Kalibrasyon skoru η', 'Calibration score η'), 'eta', 1, 6),
        (t('Kalibre edilmiş olasılık', 'Calibrated probability'), 'p_cal', 100, 2)]:
        suffix = '%' if multiplier == 100 else ''
        stages.append(f'<div class="mv-stage"><span>{label}</span><b>{pair(current[key]*multiplier, previous[key]*multiplier if previous else None, digits)}{suffix}</b></div>')
    return '''<style>
    .model-visual{color:#17212b;font-size:13px;line-height:1.45}
    .model-visual p{font-size:13px!important;margin:6px 0 12px}
    .model-visual small{color:#596579;font-size:11px}.model-visual mark{background:#fff1c7;color:#784000}
    .mv-product{display:block;font-variant-numeric:tabular-nums}.mv-beta{background:#eef2f7;border-radius:4px;padding:1px 3px}
    .mv-term{margin:10px 0}.mv-track{position:relative;height:16px;background:#f2f5f8;margin-top:3px;border-radius:3px}
    .mv-zero{position:absolute;left:50%;height:16px;border-left:1px solid #718096}
    .mv-bar{position:absolute;top:5px;height:7px;border-radius:2px}
    .mv-oldbar{position:absolute;top:1px;height:14px;border:1px dashed #596579;box-sizing:border-box}
    .mv-stages{display:grid;grid-template-columns:1fr 1fr;gap:6px}.mv-stage{background:#eef2f7;padding:8px;border-radius:6px;min-width:0}
    .mv-stage span,.mv-stage b{display:block}.mv-stage small{display:inline-block}.model-visual .mv-curve{width:100%;height:auto;display:block}
    </style><div class="model-visual">''' + f'''
    <p><b>{t('Bir hasta bilgisini değiştirin; hesaba katkısını ve sonucu birlikte izleyin.', 'Change an input → contributions change → the result changes.')}</b>
    {t('β katsayıları ve kalibrasyon sabittir; bu ekran modeli yeniden eğitmez.', 'The β coefficients and calibration stay fixed; this page does not retrain the model.')}</p>
    <p>{t('Sola uzanan çubuk toplamı azaltır, sağa uzanan artırır. Kesikli çizgi önceki katkıyı, sarı renk değişen sayıyı gösterir. Burada hesabın nasıl değiştiğine bakıyoruz; biyolojik bir neden-sonuç ilişkisi ölçmüyoruz.', 'Left: a contribution reducing the score. Right: a contribution increasing it. Dashed outline: previous contribution; yellow: a changed number. These are calculation effects in this example, not causal effects.')}</p>
    {''.join(rows)}
    <p>{t('Sıfır katkılı diğer terimler gösterilmiyor. Çubuklar yüzdeyi değil, z skoruna katkıyı gösterir.', 'Other zero-contribution terms are omitted. Bars show contributions to z, not percentages.')}</p>
    <div class="mv-stages">{''.join(stages)}</div>
    <p>{t('Sabit kalibrasyon:', 'Fixed calibration:')} a = {fmt(a, 6)}; b = {fmt(b, 6)}.</p>
    {graph}
    <p>{t('Mor eğri sabit model dönüşümüdür; yeşil nokta güncel, boş nokta önceki örnektir. Katsayıların değişmesi, etiketli hasta verileriyle yeniden eğitim gerektirir; burada yapılmaz.', 'The purple curve is the fixed model transformation; the green point is current and the hollow point is previous. Changing coefficients requires retraining with labelled patient data; that does not happen here.')}</p>
    {('<p><b>'+t('Ailede belgeli varyant seçili: bu yüzde yalnız iç eğitim hesabıdır, kişisel olasılık değildir.', 'Documented familial variant selected: this percentage is internal teaching arithmetic, not a personal probability.')+'</b></p>') if current['v'].get('urg_fam') else ''}
    </div>'''
