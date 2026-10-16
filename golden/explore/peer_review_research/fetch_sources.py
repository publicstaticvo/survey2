"""Download public research PDFs and extract page-tagged text; no API credentials."""
from pathlib import Path
import json
import urllib.request
import fitz

ROOT = Path(__file__).resolve().parent
SOURCES = {
    'deepreviewer2': 'https://arxiv.org/pdf/2604.09590',
    'reviewgrounder': 'https://arxiv.org/pdf/2604.14261',
    'peer_review_survey': 'https://aclanthology.org/2026.acl-long.1504.pdf',
    'score_anchors': 'https://arxiv.org/pdf/2609.01905',
    'calibration_position': 'https://raw.githubusercontent.com/mlresearch/v306/gh-pages/assets/chen26hf/chen26hf.pdf',
    'merits_defects': 'https://arxiv.org/pdf/2509.19326',
    'reviewrl': 'https://arxiv.org/pdf/2508.10308',
    'deepreview': 'https://arxiv.org/pdf/2503.08569',
    'limitgen': 'https://arxiv.org/pdf/2507.02694',
    'metric_reliability': 'https://arxiv.org/pdf/2609.23264',
    'beyond_imitation': 'https://arxiv.org/pdf/2610.11087',
}

if __name__ == '__main__':
    records = []
    for name, url in SOURCES.items():
        dst = ROOT / (name + '.pdf')
        try:
            if not dst.exists():
                request = urllib.request.Request(url, headers={'User-Agent': 'ResearchLiteratureAudit/1.0'})
                with urllib.request.urlopen(request, timeout=45) as response:
                    data = response.read()
                if not data.startswith(b'%PDF'):
                    raise ValueError('Response is not a PDF')
                dst.write_bytes(data)
            doc = fitz.open(dst)
            (ROOT / (name + '.txt')).write_text('\n'.join(
                f'=== PAGE {i + 1} ===\n{page.get_text(sort=True)}' for i, page in enumerate(doc)
            ), encoding='utf-8')
            records.append({'name': name, 'url': url, 'pages': len(doc), 'status': 'ok'})
        except Exception as error:
            records.append({'name': name, 'url': url, 'status': 'error', 'error': str(error)})
        print(json.dumps(records[-1], ensure_ascii=False), flush=True)
    (ROOT / 'download_manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
