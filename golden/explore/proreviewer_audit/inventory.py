"""Reproduce structural checks; semantic judgments are in report.md."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
out = []
for folder in sorted((ROOT / 'proreviewer-cc').iterdir()):
    log = json.loads((folder / 'review_log.json').read_text(encoding='utf-8'))
    outline = log['review_outline']
    namespaces = {k: {x['id']: x for x in log[k]} for k in ('claims', 'questions', 'notes')}
    points = []
    for section in ('strengths', 'weaknesses', 'questions'):
        for i, point in enumerate(outline.get(section, []), 1):
            refs = {k: point.get('related_' + k, point.get(k, [])) for k in namespaces}
            points.append({
                'id': section[0].upper() + str(i), 'section': section,
                'text': point.get('text', point.get('content')),
                'refs': refs, 'has_refs': any(refs.values()),
                'wrong_namespace_or_missing': [
                    {'namespace': k, 'id': ref} for k, ids in refs.items()
                    for ref in ids if ref not in namespaces[k]
                ],
            })
    steps = [json.loads(x) for x in (folder / 'steps.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    out.append({
        'paper_id': folder.name.split('_')[1], 'source_folder': str(folder),
        'conference': log.get('conference'), 'score': outline.get('overall_score'),
        'outline_keys': list(outline), 'points': points,
        'unsettled_claims': [x['id'] for x in log['claims'] if x['status'] == 'to_be_verified'],
        'unsettled_questions': [x['id'] for x in log['questions'] if x['status'] != 'resolved'],
        'recorded_steps': len(steps),
    })
target = Path(__file__).with_name('inventory.json')
target.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps([{k: v for k, v in x.items() if k not in ('points', 'source_folder')} | {
    'points': len(x['points']), 'with_refs': sum(p['has_refs'] for p in x['points']),
    'bad_typed_refs': sum(len(p['wrong_namespace_or_missing']) for p in x['points'])
} for x in out], ensure_ascii=False, indent=2))
