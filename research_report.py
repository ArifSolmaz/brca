"""Render a fixed report of existing results; no analysis or model execution."""
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).parent
REPORT = ROOT / 'evidence' / 'research_report_tr.json'
PDF = ROOT / 'output' / 'pdf' / 'BRCA_arastirma_raporu_TR.pdf'


def report_data():
    return json.loads(REPORT.read_text(encoding='utf-8'))


def report_html():
    d = report_data()
    e = escape
    references = {b['id']: b['url'] for p in d['pages'] for b in p['blocks'] if b['type'] == 'reference'}
    def content(text):
        result = e(text)
        for key, url in references.items():
            result = result.replace(f'[{key}]', f"<a href='{e(url)}' target='_blank' rel='noopener noreferrer'>[{key}]</a>")
        return result
    sections = []
    for page in d['pages']:
        parts = [f"<h2>{e(page['title'])}</h2>"]
        for b in page['blocks']:
            if b['type'] == 'reference':
                parts.append(f"<div class='ro-need'><p><b>[{e(b['id'])}] {e(b['citation'])}</b></p>"
                             f"<p><a href='{e(b['url'])}' target='_blank' rel='noopener noreferrer'>"
                             f"{e(b['url'])}</a></p><p>{e(b['note'])}</p></div>")
            elif b['type'] in ('p', 'callout'):
                cls = " class='ro-notice'" if b['type'] == 'callout' else ''
                parts.append(f"<p{cls}>{content(b['text'])}</p>")
            else:
                headers = b.get('headers', ['Seçim aşaması', 'Açıklama'])
                head = ''.join(f"<th scope='col'>{e(x)}</th>" for x in headers)
                rows = ''.join('<tr>' + ''.join(f'<td>{content(x)}</td>' for x in row) + '</tr>' for row in b['rows'])
                parts.append(f"<div class='ro-table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>")
        sections.append('<section>' + ''.join(parts) + '</section>')
    return (f"<article class='research-overview' id='arastirma-rapor-metni'><h1>{e(d['title'])}</h1>"
            f"<p class='ro-lead'>{e(d['subtitle'])}</p><p class='ro-muted'>Rapor: {e(d['prepared'])} · "
            f"Sonuçların kesim tarihi: {e(d['evidence_date'])} · Sürüm {e(d['version'])}</p>"
            f"<p class='ro-notice'>{e(d['scope'])}</p>" + ''.join(sections) + '</article>')
