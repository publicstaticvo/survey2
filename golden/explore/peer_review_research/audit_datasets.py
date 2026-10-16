"""Read-only audit of released datasets; writes reproducible research summaries."""
import collections
import hashlib
import json
import re
from pathlib import Path

BASE = Path('P:/AI4S')
OUT = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def jsonl(path):
    with path.open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.strip()]

def main():
    arena = BASE / 'LitReview-Arena'
    votes = jsonl(arena / 'data/expert_outcomes.jsonl')
    dims = ['D1', 'D2', 'D3', 'D4', 'D5']
    patterns = collections.defaultdict(collections.Counter)
    samples = []
    majority = collections.Counter()
    for row in votes:
        values = row['outcomes']
        key = tuple(values[d] for d in dims[:4])
        patterns[key][values['D5']] += 1
        ab = collections.Counter(values[d] for d in dims[:4] if values[d] in ['A', 'B'])
        if ab['A'] != ab['B'] and values['D5'] in ['A', 'B']:
            winner = 'A' if ab['A'] > ab['B'] else 'B'
            majority['eligible'] += 1
            majority['agreement' if winner == values['D5'] else 'disagreement'] += 1
            if winner != values['D5'] and len(samples) < 8:
                samples.append(row)
    inconsistent = [{'D1_D4': list(k), 'D5_counts': dict(v)} for k, v in patterns.items() if len(v) > 1]
    caches = {}
    for name in ['litjudge_context_cache.jsonl', 'litjudge_context_cache_mmr.jsonl']:
        rows = jsonl(arena / 'data/evaluator' / name)
        caches[name] = {'rows': len(rows), 'keys': list(rows[0]),
                        'mean_context_chars': sum(len(x.get('context', '')) for x in rows) / len(rows),
                        'first_context_head': rows[0].get('context', '')[:1100],
                        'first_context_tail': rows[0].get('context', '')[-2600:]}
    result = {'arena': {'votes': len(votes), 'unique_battles': len({r['battle_id'] for r in votes}),
              'annotators': len({r['annotator_id'] for r in votes}),
              'dimension_counts': {d: dict(collections.Counter(r['outcomes'][d] for r in votes)) for d in dims},
              'majority_comparison': dict(majority), 'conflicting_patterns': inconsistent,
              'samples': samples, 'caches': caches,
              'battles_exists': (arena / 'data/battles.jsonl').exists()}}
    survey = BASE / 'SurveyReview/v1.1/data/v1.1-paper'
    raw_all = []
    grouped_all = []
    result['surveyreview'] = {}
    for split in ['train', 'test']:
        raw = read(survey / 'raw' / f'{split}_samples.json')
        grouped = read(survey / split / f'grouped_{split}set.json')
        raw_all.extend(raw)
        grouped_all.extend(grouped)
        result['surveyreview'][split] = {
            'raw_rows': len(raw), 'grouped_rows': len(grouped),
            'raw_sources': dict(collections.Counter(x.get('source') for x in raw)),
            'raw_scores': {d: dict(collections.Counter(str(y['score']) for x in raw for y in x['result'] if y['dimension'] == d)) for d in ['Readability', 'Criticalness', 'Comprehensiveness', 'Structure']},
            'grouped_scores': {d: dict(collections.Counter(str(y['score']) for x in grouped for y in x['result'] if y['dimension'] == d)) for d in ['Readability', 'Criticalness', 'Comprehensiveness', 'Structure']},
            'all_zero_raw': sum(all(y['score'] == 0 for y in x['result']) for x in raw),
        }
    titles = collections.defaultdict(list)
    for row in raw_all:
        titles[row['paper_title']].append(row)
    mixed = []
    for row in grouped_all:
        for item in row['result']:
            score_set = {y['score'] for x in titles[row['paper_title']] for y in x['result'] if y['dimension'] == item['dimension'] and y['score'] not in [0, -3]}
            if any(x < 0 for x in score_set) and any(x > 0 for x in score_set):
                mixed.append({'uid': row['uid'], 'title': row['paper_title'], 'dimension': item['dimension'], 'raw_nonzero_scores': sorted(score_set), 'grouped_score': item['score'], 'grouped_reasons': item['reasons']})
    result['surveyreview']['mixed_sign_paper_dimensions'] = len(mixed)
    result['surveyreview']['mixed_sign_samples'] = mixed[:8]
    result['surveyreview']['raw_samples'] = [raw_all[0]] + [x for x in raw_all if any(y['score'] > 0 for y in x['result']) and any(y['score'] < 0 for y in x['result'])][:3]
    result['surveyreview']['grouped_first_test'] = read(survey / 'test/grouped_testset.json')[0]
    a = {x['paper_title'] for x in read(survey / 'train/grouped_trainset.json')}
    b = {x['paper_title'] for x in read(survey / 'test/grouped_testset.json')}
    result['surveyreview']['train_test_title_overlap'] = sorted(a & b)
    result['surveyreview']['unique_raw_titles'] = len(titles)
    result['surveyreview']['v1_label_files_identical'] = {str(p.relative_to(survey)): hashlib.sha256(p.read_bytes()).hexdigest() == hashlib.sha256((BASE / 'SurveyReview/v1.0/data/v1.0-paper' / p.relative_to(survey)).read_bytes()).hexdigest() for p in list((survey / 'raw').glob('*.json')) + list((survey / 'test').glob('*.json')) + list((survey / 'train').glob('*.json'))}
    (OUT / 'dataset_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: {a:b for a,b in v.items() if a not in ['caches','samples','raw_samples','grouped_first_test','mixed_sign_samples','conflicting_patterns']} for k,v in result.items()}, ensure_ascii=False, indent=2))
    print('conflicting D1-D4 patterns:', len(inconsistent))

if __name__ == '__main__':
    main()
