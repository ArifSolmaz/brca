"""Read-only web edition of the existing bilingual Model Guide."""
import json
from html import escape
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).resolve().parent / 'assets/model_details'

STYLE = '''<style>
.st-key-model_guide_body{max-width:1000px;margin:auto;line-height:1.7}
.st-key-model_guide_body h2{margin-top:2rem;scroll-margin-top:5rem}
.st-key-model_guide_body [data-testid=stMarkdownContainer]:has(.katex-display){overflow:visible!important}
.st-key-model_guide_body .katex-display{overflow-x:auto!important;overflow-y:hidden!important;padding:1em .2em!important;margin:.4em 0!important}
.st-key-model_guide_body .guide-table{overflow-x:auto;margin:.8rem 0}
.st-key-model_guide_body table{width:100%;border-collapse:collapse}
.st-key-model_guide_body th,.st-key-model_guide_body td{text-align:left;padding:.6rem;border-bottom:1px solid #dce1e8;vertical-align:top}
.st-key-model_guide_body .guide-toc{padding:1rem 1.5rem;background:#f0edf8;border-radius:12px}
@media(max-width:700px){.st-key-model_guide_body .katex{font-size:14px}.st-key-model_guide_body td,.st-key-model_guide_body th{padding:.4rem}}
</style>'''


def render_model_guide(lang='tr'):
    tr = lang == 'tr'
    blocks = json.loads((ASSETS / f'model_guide_{lang}.json').read_text())
    st.html(STYLE)
    with st.container(key='model_guide_body'):
        st.title('Model rehberi' if tr else 'Model guide')
        st.caption('3 Kasım 2026 · Mevcut çalışmanın anlatımı · Yeni analiz yapılmadı' if tr else
                   '3 November 2026 · Explanation of the existing work · No new analysis')
        st.write('Gerçek kayıtlardan modele, elle hesaplamalara ve kanıtın sınırlarına. Rehberin tamamını bu sayfada okuyabilirsiniz.' if tr else
                 'From actual records to the model, manual calculations and limits of the evidence. Read the complete guide on this page.')
        chapters = [b for b in blocks if b['type'] == 'chapter']
        links = ''.join(f'<li><a href="#guide-{b["number"]}">{b["number"]} · {escape(b["text"])}</a></li>' for b in chapters if b['number'])
        st.html('<nav class="guide-toc" aria-label="'+('İçindekiler' if tr else 'Contents')+'"><strong>'+('İçindekiler' if tr else 'Contents')+'</strong><ol style="list-style:none;padding:0">'+links+'</ol></nav>')
        for block in blocks:
            kind = block['type']
            if kind == 'chapter':
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
                st.latex(block['text'])
            elif kind == 'table':
                headers = ''.join('<th>'+escape(str(v))+'</th>' for v in block['headers'])
                rows = ''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in block['rows'])
                st.html('<div class="guide-table"><table><thead><tr>'+headers+'</tr></thead><tbody>'+rows+'</tbody></table></div>')
            elif kind == 'link':
                st.markdown(f'[{block["text"]}]({block["url"]})')
        st.divider()
        left,right=st.columns(2)
        for column,language,label in [(left,'TR','Türkçe Model Rehberi · PDF'),(right,'EN','English Model Guide · PDF')]:
            pdf = ASSETS / f'BRCA_Model_Guide_{language}.pdf'
            column.download_button(label,pdf.read_bytes(),file_name=pdf.name,mime='application/pdf',key='guide_pdf_'+language,width='stretch')
