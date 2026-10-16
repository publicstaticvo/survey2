"""Verify synchronized labels, field positions, sort order, and preserved data."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'survey_eval/golden/review_analyze_llm'
OUTPUT = BASE / 'concern_action_classification'
SEVERITIES = ['Critical', 'Major', 'Serious', 'Limited', 'Negligible']


def read(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def verify():
    digest = hashlib.sha256((OUTPUT / 'prompt_v4.txt').read_text(encoding='utf-8').encode()).hexdigest()
    labels = {r['issue_id']: r for r in read(OUTPUT / 'labels.jsonl')}
    canonical = read(BASE / 'evidence_judgment_llm_input_complete.jsonl')
    assert len(canonical) == len({r['issue_id'] for r in canonical}) == 4051
    paths = [BASE / 'evidence_judgment_llm_input_complete.jsonl']
    paths += list((BASE / 'prepared_reviewer_concerns').glob('*.jsonl'))
    paths += list((ROOT / 'triage/test_inputs/human_testset_golden').glob('*.jsonl'))
    manifest = []
    ignored = {'is_reviewer_concern', 'concern_type', 'severity', 'concern_classification_reason'}
    for path in paths:
        rows = read(path)
        backup = OUTPUT / 'backups' / path.relative_to(ROOT)
        original = {r['issue_id']: r for r in read(backup)}
        assert len(rows) == len(original)
        assert rows == sorted(rows, key=lambda r: (r['paper_file'], r['paper_id'], SEVERITIES.index(r['severity']), r['concern_type']))
        for row in rows:
            label = labels[row['issue_id']]
            assert label['prompt_sha256'] == digest
            assert (row['concern_type'], row['severity'], row['concern_classification_reason']) == (label['category'], label['severity'], label['reason'])
            assert 'is_reviewer_concern' not in row
            keys = list(row)
            old = original[row['issue_id']]
            assert keys.index('severity') == keys.index('concern_type') + 1
            assert keys.index('concern_type') == list(old).index('is_reviewer_concern')
            assert {k: v for k, v in row.items() if k not in ignored} == {k: v for k, v in old.items() if k not in ignored}
        manifest.append({'path': str(path.relative_to(ROOT)), 'records': len(rows), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    result = {'records': len(canonical), 'files': manifest, 'prompt_sha256': digest, 'category_counts': dict(Counter(r['concern_type'] for r in canonical)), 'severity_counts': dict(Counter(r['severity'] for r in canonical)), 'verified': True}
    (OUTPUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    verify()
