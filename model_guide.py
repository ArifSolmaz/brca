"""Read-only web edition of the existing bilingual Model Guide."""
import json
from html import escape
from pathlib import Path
import streamlit as st
from model_teaching import mobile_formula_steps
from model_guide_additions import guide_additions
from learning_demo import render_learning_demo

ASSETS = Path(__file__).resolve().parent / 'assets/model_details'

STYLE = '''<style>
.st-key-model_guide_body{max-width:1000px;margin:auto;line-height:1.7}
.st-key-model_guide_body h2{margin-top:2rem;scroll-margin-top:5rem}
.st-key-model_guide_body [data-testid=stMarkdownContainer]:has(.katex-display){overflow:visible!important}
.st-key-model_guide_body .katex-display{overflow-x:auto!important;overflow-y:hidden!important;padding:1em .2em!important;margin:.4em 0!important}
.st-key-model_guide_body .guide-table{overflow-x:auto;margin:.8rem 0}
.st-key-model_guide_body table{width:100%;border-collapse:collapse}
.st-key-model_guide_body th,.st-key-model_guide_body td{text-align:left;padding:.6rem;border-bottom:1px solid #dce1e8;vertical-align:top}
.st-key-model_guide_body .guide-back{display:inline-block;min-height:44px;padding:.6rem 0;touch-action:manipulation}
.st-key-model_guide_body #guide-contents{scroll-margin-top:2rem}
.st-key-model_guide_body .guide-toc{padding:1rem 1.5rem;background:#f0edf8;border-radius:12px}
.st-key-model_guide_body [class*=st-key-guide_math_mobile_],.st-key-model_guide_body [data-testid=stLayoutWrapper]:has(>[class*=st-key-guide_math_mobile_]){display:none!important}
@media(max-width:700px){
.st-key-model_guide_body .guide-toc a{display:block;touch-action:manipulation}
.st-key-model_guide_body [class*=st-key-guide_math_desktop_],.st-key-model_guide_body [data-testid=stLayoutWrapper]:has(>[class*=st-key-guide_math_desktop_]){display:none!important}
.st-key-model_guide_body [class*=st-key-guide_math_mobile_],.st-key-model_guide_body [data-testid=stLayoutWrapper]:has(>[class*=st-key-guide_math_mobile_]){display:flex!important}
.st-key-model_guide_body .katex{font-size:14px}.st-key-model_guide_body td,.st-key-model_guide_body th{padding:.4rem}}
</style>'''


# Handle guide links locally: cloud iframe hash forwarding can otherwise swallow
# repeated clicks. Capture only guide navigation; leave all other links alone.
NAV_SCRIPT = """<script>
if (window.__brcaGuideNavigation) document.removeEventListener('click',window.__brcaGuideNavigation,true);
window.__brcaGuideNavigation = function(event) {
  const link = event.target.closest?.('.guide-toc a[href^="#guide-"], .guide-back[href="#guide-contents"]');
  if (!link) return;
  const target = document.getElementById(link.getAttribute('href').slice(1));
  if (!target) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  target.scrollIntoView({behavior:'instant',block:'start'});
};
document.addEventListener('click',window.__brcaGuideNavigation,true);
</script>"""


def guide_mobile_steps(formula):
    """Reformat existing arithmetic only; desktop TeX stays byte-for-byte intact."""
    if formula.startswith(r'\mathrm{Position}'):
        return [r'f=\frac{0.257943117-0.2133526175}{0.2763791363-0.2133526175}',
                r'\mathrm{Position}=\operatorname{round}[5(17+f)]',
                r'\mathrm{Position}=89']
    if formula.startswith(r'\begin{aligned}'):
        if r'\eta&=' in formula:
            return [r'\eta=-1.824095746896',r'\phantom{\eta=}+0.939227549588(0.817063904400)',
                    r'\eta=-1.824095746896+0.767408928786',r'\eta=-1.056686818109']
        if '-1.130177733759' in formula:
            return [r'\begin{aligned}z={}&-1.608283515050\\&-1.130177733759\\&+1.617774083556\\&+0.809503755804\\&+0.751074653320\\&+0.377172660529\\={}&0.817063904400\end{aligned}']
        return [formula]
    return mobile_formula_steps(formula)


def guide_latex(formula, ident, mobile_steps=None):
    with st.container(key=f'guide_math_desktop_{ident}'):
        st.latex(formula)
    with st.container(key=f'guide_math_mobile_{ident}'):
        for step in (mobile_steps or guide_mobile_steps(formula)):
            st.latex(step)


def render_model_guide(lang='tr'):
    tr = lang == 'tr'
    blocks = json.loads((ASSETS / f'model_guide_{lang}.json').read_text())
    blocks += guide_additions(lang)
    st.html(STYLE)
    with st.container(key='model_guide_body'):
        st.title('Model rehberi' if tr else 'Model guide')
        st.caption('3 Kasım 2026 · Mevcut çalışmanın anlatımı · Yeni analiz yapılmadı' if tr else
                   '3 November 2026 · Explanation of the existing work · No new analysis')
        st.write('Bu çalışma bir formülle başlamadı. Önce hasta dosyalarının ne anlattığını, hangi kayıtların aynı kişiye ait olduğunu ve hangi sorulara güvenle cevap verebileceğimizi anlamamız gerekiyordu. Burada o yolculuğu; veriyi, modeli, hesabı ve hâlâ eksik olanları adım adım anlatıyoruz.' if tr else
                 'From actual records to the model, manual calculations and limits of the evidence. Read the complete guide on this page.')
        chapters = [b for b in blocks if b['type'] == 'chapter']
        links = ''.join(f'<li><a href="#guide-{b["number"]}">{b["number"]} · {escape(b["text"])}</a></li>' for b in chapters if b['number'])
        st.html('<nav id="guide-contents" class="guide-toc" aria-label="'+('İçindekiler' if tr else 'Contents')+'"><strong>'+('İçindekiler' if tr else 'Contents')+'</strong><ol style="list-style:none;padding:0">'+links+'</ol></nav>')
        def back_to_contents(number):
            label = 'İçindekilere dön' if tr else 'Back to contents'
            st.html(f'<a class="guide-back" data-guide-section="{number}" href="#guide-contents">↑ {label}</a>')

        math_index=0
        current_chapter=None
        for block in blocks:
            kind = block['type']
            if kind == 'chapter':
                if current_chapter is not None:
                    if current_chapter == 17:
                        render_learning_demo(lang)
                    back_to_contents(current_chapter)
                current_chapter=block['number']
                number = block['number']
                title = (f'{number} · ' if number else '') + block['text']
                st.html(f'<h2 id="guide-{number}">{escape(title)}</h2>')
            elif kind == 'heading':
                st.subheader(block['text'])
            elif kind == 'paragraph':
                st.markdown(block['text'].replace('\n','\n\n'))
            elif kind == 'note':
                st.info(block['text'])
            elif kind == 'math':
                guide_latex(block['text'],math_index,block.get('mobile_steps'))
                math_index+=1
            elif kind == 'table':
                headers = ''.join('<th>'+escape(str(v))+'</th>' for v in block['headers'])
                rows = ''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in block['rows'])
                st.html('<div class="guide-table"><table><thead><tr>'+headers+'</tr></thead><tbody>'+rows+'</tbody></table></div>')
            elif kind == 'link':
                st.markdown(f'[{block["text"]}]({block["url"]})')
        back_to_contents(current_chapter)
        st.divider()
        st.caption('PDF’lerde giriş ile 1–19. bölümlerin metni ve formülleri var. Öğrenme deneyini ise bu sayfada çalıştırabilir veya PDF’deki bağlantıdan açabilirsiniz.' if tr else
                   'The PDFs contain the text and formulas of the introduction and chapters 1–19. Run the learning experiment on this page or open it through the link in the PDF.')
        left,right=st.columns(2)
        for column,language,label in [(left,'TR','Türkçe Model Rehberi · PDF'),(right,'EN','English Model Guide · PDF')]:
            pdf = ASSETS / f'BRCA_Model_Guide_{language}.pdf'
            column.download_button(label,pdf.read_bytes(),file_name=pdf.name,mime='application/pdf',key='guide_pdf_'+language,width='stretch')

        st.html(NAV_SCRIPT, unsafe_allow_javascript=True)
