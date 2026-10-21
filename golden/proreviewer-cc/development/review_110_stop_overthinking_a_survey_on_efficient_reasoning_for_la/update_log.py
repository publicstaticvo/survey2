import json

with open('review_log.json', 'r', encoding='utf-8') as f:
    log = json.load(f)

# Update C1 to supported
for i, c in enumerate(log.get('claims', [])):
    if c['id'] == 'C1':
        log['claims'][i]['status'] = 'supported'
        log['claims'][i]['reason'] = 'Paper explicitly claims first structured survey. ~124 references cited. Paper acknowledges lack of standardized benchmarks as limitation.'
        log['claims'][i]['cross_refs'] = 'Abstract, Conclusion, 8.2'
        break

# Update C3 and C4 to supported
for i, c in enumerate(log.get('claims', [])):
    if c['id'] == 'C3':
        log['claims'][i]['status'] = 'supported'
        log['claims'][i]['reason'] = 'Three categories confirmed throughout paper structure'
        log['claims'][i]['cross_refs'] = '3, 4, 5'
    if c['id'] == 'C4':
        log['claims'][i]['status'] = 'supported'
        log['claims'][i]['reason'] = 'Definition confirmed in 2.3 with examples showing overthinking'
        log['claims'][i]['cross_refs'] = '2.3'

# Update questions
for i, q in enumerate(log.get('questions', [])):
    if q['id'] == 'Q1':
        log['questions'][i]['status'] = 'resolved'
        log['questions'][i]['answer'] = 'Paper discusses RL vs SFT in 8.2: RL is creative but unpredictable/expensive; SFT is stable but requires dataset construction. Combining both suggested as promising.'
        log['questions'][i]['sections'] = '8.2'
    if q['id'] == 'Q2':
        log['questions'][i]['status'] = 'resolved'
        log['questions'][i]['answer'] = '~124 references cited. Coverage is broad but lacks standardized comparison leaderboard.'
        log['questions'][i]['sections'] = '8.2'
    if q['id'] == 'Q3':
        log['questions'][i]['status'] = 'resolved'
        log['questions'][i]['answer'] = 'Yes, 8.2 covers safety-efficiency tradeoff. H-CoT attacks exploit longer reasoning. RL-based length control proposed.'
        log['questions'][i]['sections'] = '8.2'
    if q['id'] == 'Q4':
        log['questions'][i]['status'] = 'resolved'
        log['questions'][i]['answer'] = 'No standardized leaderboard exists. 8.2 acknowledges challenges: varying architectures, inconsistent datasets.'
        log['questions'][i]['sections'] = '8.2'

with open('review_log.json', 'w', encoding='utf-8') as f:
    json.dump(log, f, indent=2, ensure_ascii=False)

print('Updated claims and questions')