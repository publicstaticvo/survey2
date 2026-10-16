"""Resumeable AsyncChat classification with a manually audited pilot gate."""
import argparse
import asyncio
import hashlib
import json
import logging
import random
import sys
import shutil
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from survey_eval.agent.tools.utility.llmclient import AsyncChat
from survey_eval.agent.tools.utility.tool_config import LLMServerInfo
from survey_eval.agent.tools.utility.request_utils import SessionManager

PROMPT = """### Task
Classify the focal reviewer evidence in its original review context. Return exactly one category, one severity, and an explanatory reason. Classify the actual request, not the automatically extracted issue description. The source field is context, never a category or severity shortcut. Optional suggestions can still be actionable concerns. A question can implicitly identify a deficiency. Do not invent defects or infer severity from the review's recommendation or rating. Context may resolve the focal evidence's meaning, but never substitute a different request elsewhere in the review. If the focal evidence discusses benchmarking, do not classify an adjacent future-directions request instead.

### Categories and exclusive decision procedure
Identify the focal request's primary response action. Use the following ordered decisions to resolve overlap, considering what would actually satisfy the reviewer:
1. CORRECT: a stated or suspected factual, logical, numerical, or internal consistency error needs correction. Example: 'Does this definition contradict Section 3?' Use this for alleged wrongness, not merely missing support. Doubt about the truth of a statement, including a question mark challenging its accuracy, belongs here even without an explicit correction demand. A redundant table column or undesirable organization alone is REVISE, not a logical error.
2. SUBSTANTIATE: an existing substantive claim needs justification, empirical testing, evidence, or an explicit derivation. Example: 'Provide evidence for the claim that A outperforms B.' Adding an experiment to test an existing claim belongs here, not ADD. An unsupported claim is not automatically an incorrect claim. Merely asking for comparative experiments without identifying an existing claim to verify is ADD; do not invent a comparative claim.
3. ADD: add an absent topic, reference, comparison, discussion, result, or component rather than substantiate a particular existing claim. Example: 'Include the omitted literature on robustness.' New analysis intended to fill absent coverage belongs here.
4. REVISE: reorganize, reword, shorten, remove, relocate, or improve the presentation of existing content. Example: 'Move the definitions before the taxonomy.' Requests to change a title remain actionable even when optional. Correcting a substantive error takes precedence over rewriting.
5. CLARIFY: explain an existing choice, meaning, or procedure without demanding new substantive evidence or content. Example: 'Explain how the reported search was conducted.' If the review requests a missing search protocol, use ADD; if it asks to explain an already described protocol, use CLARIFY. Merely asking why an established choice was made is CLARIFY unless support for its validity is explicitly sought.
6. ASSESSMENT: a negative evaluation of value, depth, novelty, suitability, or quality without a sufficiently identifiable response action. Example: 'The contribution is too incremental.' If an actionable request is explicit, use its category above.
7. INQUIRY: information-seeking, neutral commentary, or a hypothetical improvement expressly disclaimed as a current deficiency or request. Example: 'Out of curiosity, have you explored this application?' A question implying a missing explanation or a suspected error instead takes the appropriate category above. Praise and explicit statements that no weakness is identified also belong here when erroneously extracted as concerns. Questions about an unexplained organizational choice are CLARIFY; requests for examples illustrating a definition are ADD; questions asking for comparison between surveyed methods or metrics are ADD. None requires an explicit statement of deficiency. Reserve INQUIRY for genuinely neutral questions, not all politely worded requests.
For multiple actions within the focal evidence choose the action addressing its central concern; use the ordered decisions only when centrality does not resolve the tie. Explain the boundary decision in the reason.

### Severity
Negligible: a cosmetic or optional issue with virtually no effect on the main information, conclusions, or usability. INQUIRY always has Negligible severity because no defect is alleged; this is a storage convention, not a claim of a minor defect.
Limited: a localized issue with limited impact on the survey's main information, conclusions, or usability.
Serious: an issue affecting important content, evidence reliability, coverage, or assessment of key conclusions, without undermining the survey as a whole.
Major: a fundamental issue substantially undermining the reliability, core conclusions, or essential functionality of the survey.
Critical: a demonstrated fatal validity or integrity defect making the central work unusable without replacing its foundation, such as pervasive fabricated sources supporting the central conclusions. Strong criticism or rejection alone is not Critical. Use Major rather than Critical absent explicit contextual grounds for this extreme impact.
Infer impact only from the focal evidence and context, not from field names, forceful wording, or the number of other criticisms. State what is affected and why that supports the selected severity. Do not equate all missing citations with Serious or all questions with Limited. Politeness ('might', 'could', 'would be nice') does not imply negligible impact. A missing important family of methods is at least Limited even if politely suggested. Conversely do not invent centrality or high impact when context gives none.

### Output
Return a JSON object with exactly three fields: category (one category above), severity (one severity above), reason (a nonempty English explanation).
"""
PROMPT += """
### Boundary checks before answering
An indirect request is still actionable: 'How does this definition account for regional norms? Could examples illustrate it?' requires ADD, whereas 'Why did you organize this existing taxonomy differently?' requires CLARIFY. A Questions heading never makes these INQUIRY. When a definition already exists later, bringing it to first use is REVISE, not CLARIFY. A parenthetical question mark inserted by the reviewer to challenge an assertion is not manuscript punctuation to delete: assess the suspected substantive error as CORRECT even under a style heading.
Choose Serious when the context identifies a missing core technical foundation, an entire important modality lacking substantive treatment, or missing analysis that prevents the central recommendations from being actionable. Serious does not require invalidating the survey or its conclusions. Choose Limited for localized additions without that important-content impact. Isolated duplicate words and minor terminology substitutions are Negligible; reorganization needed for comprehension can be Limited. In the reason identify the specific impact, rather than merely saying that the issue is localized.
"""
PROMPT += """
### Final consistency checks
REVISE changes existing material without supplying missing substantive analysis: supplying mathematical foundations or a new critical benchmark analysis is ADD, even if it improves an existing section. If an acronym is already explained but appears before its explanation, relocating that explanation is REVISE. SUBSTANTIATE requires an identifiable existing assertion whose support is challenged; asking to cover how a concept applies to another task is ADD unless such an assertion is actually stated. Do not invent a claim to justify SUBSTANTIATE.
Severity concerns important information and usability, not just validity. An omission can be Serious even when the overall conclusions remain valid: absent mathematical foundations of the central subject, missing analysis of a whole major modality, or absent cross-method analysis needed to turn an inventory into a useful survey are examples. When context explicitly explains that recommendations are not actionable, requested concrete guidance can be Serious. Negligible is restricted to cosmetic changes or explicitly optional improvements without meaningful information impact; a disputed substantive assertion is normally at least Limited. After drafting the reason, ensure the category and severity agree with these definitions rather than using 'does not invalidate the survey' as a reason for Limited.
"""
PROMPT_VERSION = 'v4'
TYPES = ['CLARIFY', 'ADD', 'SUBSTANTIATE', 'CORRECT', 'REVISE', 'ASSESSMENT', 'INQUIRY']
SEVERITIES = ['Critical', 'Major', 'Serious', 'Limited', 'Negligible']
SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['category', 'severity', 'reason'], 'properties': {'category': {'enum': TYPES}, 'severity': {'enum': SEVERITIES}, 'reason': {'type': 'string', 'minLength': 1}}}


class ConcernChat(AsyncChat):
    def _availability(self, response, context):
        response = response.strip()
        if response.startswith('```') and response.endswith('```'):
            response = response.split('\n', 1)[1].rsplit('```', 1)[0].strip()
        value = json.loads(response)
        jsonschema.validate(value, SCHEMA)
        assert value['category'] != 'INQUIRY' or value['severity'] == 'Negligible'
        return value


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def source(row):
    path = ROOT / 'survey_eval' / Path(row['paper_file'].replace('\\', '/'))
    if not path.exists():
        path = ROOT / 'survey_eval/golden/pdf_content' / path.name
    paper = json.loads(path.read_text(encoding='utf-8'))
    matches = [r for r in paper['reviews'] if r['review_id'] == row['review_id']]
    assert len(matches) == 1, row['issue_id']
    review = matches[0]
    content = review.get('content', {})
    field = content.get(row['raw_source_field']) if isinstance(content, dict) else None
    if isinstance(field, dict):
        field = field.get('value')
    text = field if isinstance(field, str) and field.strip() else review['text']
    return {'evidence': row['evidence'], 'raw_source_field': row['raw_source_field'], 'official_review_context': text}


def save(path, rows):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    temporary.replace(path)


async def run(args):
    base = ROOT / 'survey_eval/golden/review_analyze_llm'
    rows = read(base / 'evidence_judgment_llm_input_complete.jsonl')
    assert len(rows) == 4051 and len({r['issue_id'] for r in rows}) == 4051
    output = base / 'concern_action_classification'
    output.mkdir(exist_ok=True)
    (output / f'prompt_{PROMPT_VERSION}.txt').write_text(PROMPT, encoding='utf-8')
    cache_path = output / 'labels.jsonl'
    cache = {r['issue_id']: r for r in read(cache_path)} if cache_path.exists() else {}
    digest = hashlib.sha256(PROMPT.encode()).hexdigest()
    selected = random.Random(42).sample(sorted(rows, key=lambda r: r['issue_id']), 40) if args.pilot else rows
    client = ConcernChat(LLMServerInfo(base_url='https://uni-api.cstcloud.cn', model='deepseek-v4-flash'), {'temperature': 0, 'response_format': {'type': 'json_object'}})
    client.timeout = 120
    queue = asyncio.Queue()
    for row in selected:
        if row['issue_id'] not in cache or cache[row['issue_id']].get('prompt_sha256') != digest:
            queue.put_nowait(row)

    async def worker():
        while not queue.empty():
            row = queue.get_nowait()
            try:
                context = source(row)
                result = await asyncio.wait_for(client.call(messages=[{'role': 'system', 'content': PROMPT}, {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)}]), timeout=660)
                record = {'issue_id': row['issue_id'], **result, 'prompt_sha256': digest}
                cache[row['issue_id']] = record
                with cache_path.open('a', encoding='utf-8') as handle:
                    handle.write(json.dumps(record, ensure_ascii=False) + '\n')
                completed = sum(r.get('prompt_sha256') == digest for r in cache.values())
                print(f"Completed {completed}/4051: {row['issue_id']}", flush=True)
            except Exception as exc:
                logging.exception('Classification failed for %s', row['issue_id'])
                with (output / 'errors.jsonl').open('a', encoding='utf-8') as handle:
                    handle.write(json.dumps({'issue_id': row['issue_id'], 'error': str(exc)}) + '\n')
            finally:
                queue.task_done()

    await SessionManager.init()
    try:
        await asyncio.gather(*(worker() for _ in range(args.workers)))
    finally:
        await SessionManager.close()
    if args.pilot:
        save(output / f'pilot_{PROMPT_VERSION}.jsonl', [{**source(r), 'issue_id': r['issue_id'], 'prediction': cache.get(r['issue_id'])} for r in selected])
        return
    assert all(r['issue_id'] in cache and cache[r['issue_id']]['prompt_sha256'] == digest for r in rows), 'Incomplete labels; rerun to resume.'
    destinations = [base / 'evidence_judgment_llm_input_complete.jsonl']
    destinations += list((base / 'prepared_reviewer_concerns').glob('*.jsonl'))
    destinations += list((ROOT / 'triage/test_inputs/human_testset_golden').glob('*.jsonl'))
    destinations += list((base / 'manual_reannotation_by_lj').glob('*.jsonl'))
    for path in destinations:
        existing = read(path)
        if not existing or not all(r.get('issue_id') in cache for r in existing):
            continue
        if not all('is_reviewer_concern' in r or 'concern_type' in r for r in existing):
            continue
        updated = []
        backup = output / 'backups' / path.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(path, backup)
        for row in existing:
            label = cache[row['issue_id']]
            result = {}
            inserted = False
            for key, value in row.items():
                if key in ('severity', 'concern_classification_reason'):
                    continue
                if key in ('is_reviewer_concern', 'concern_type'):
                    result.update(concern_type=label['category'], severity=label['severity'])
                    inserted = True
                else:
                    result[key] = value
            if not inserted:
                result.update(concern_type=label['category'], severity=label['severity'])
            result['concern_classification_reason'] = label['reason']
            updated.append(result)
        updated.sort(key=lambda r: (r['paper_file'], r['paper_id'], SEVERITIES.index(r['severity']), r['concern_type']))
        save(path, updated)
        verified = read(path)
        assert verified == updated
        originals = {r['issue_id']: r for r in existing}
        ignored = {'is_reviewer_concern', 'concern_type', 'severity', 'concern_classification_reason'}
        for row in verified:
            original = originals[row['issue_id']]
            assert {k: v for k, v in row.items() if k not in ignored} == {k: v for k, v in original.items() if k not in ignored}
            keys = list(row)
            assert keys.index('severity') == keys.index('concern_type') + 1
            original_keys = list(original)
            old_key = 'is_reviewer_concern' if 'is_reviewer_concern' in original else 'concern_type'
            assert keys.index('concern_type') == original_keys.index(old_key)
        print(f'Updated {path}: {len(updated)}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--workers', type=int, default=12)
    asyncio.run(run(parser.parse_args()))
