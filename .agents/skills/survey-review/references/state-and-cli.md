# State and CLI

Use `python <skill>/scripts/review_cli.py`. After initialization, pass `--dir <run>` **before** the command. Python requirements are in `requirements.txt`. State persists in `review_log.json`.

## Lifecycle and fixed names

```text
init "Survey Title.pdf" --publication-date 2025-03-14 --date-basis "User specified" --conference iclr
--dir "review_Survey Title" show --detailed
--dir "review_Survey Title" audit
--dir "review_Survey Title" finalize
--dir "review_Survey Title" export --no-evidence
```

The run basename must be `review_{input stem}`, with spaces/Unicode/full stem preserved and Windows-invalid characters replaced. `init --dir` can choose another parent only; a nonempty directory and `--force` are rejected. A project-directory input uses its directory name. All later commands can still access old run paths; old logs remain schema v1 and are not silently migrated.

Final files: `paper.md`, `input_manifest.json`, `review_log.json`, `review.md`, `audit_summary.md`; optional `steps.jsonl` / `steps.md`. Export cannot rename `review.md`. Use `inputs/<kind>_<id-or-new>.json` for request payloads and `sources/<E-id>.<ext>` for downloaded texts. Do not alter `paper.md` to repair extraction; inspect the PDF and retain uncertainty.

## Persistent operations

Create UTF-8 JSON using a file-writing tool, then pass `--file <path>` to avoid shell quoting issues. `put <kind>` creates an ID when `id` is omitted; including an existing ID updates only the supplied fields. Arbitrary new IDs are rejected. K/X exact text duplicates (ignoring case/whitespace) are rejected; use the existing ID. Review semantically overlapping records before adding new ones; merge only after establishing equivalence and updating references.

```text
--dir <run> context --file <run>/inputs/context_new.json
--dir <run> put contribution --file <run>/inputs/contribution_new.json
--dir <run> put discovery --file <run>/inputs/discovery_new.json
--dir <run> put audit --file <run>/inputs/audit_new.json
--dir <run> put impact --file <run>/inputs/impact_new.json
--dir <run> point --section strengths --file <run>/inputs/point_new.json
--dir <run> judgment --file <run>/inputs/judgment_new.json
```

Other `put` kinds: `expectation`, `evidence`, `search`. `show` displays all records. There is no delete/automatic semantic merge command.

| Kind / ID | Required fields | Additional fields |
| --- | --- | --- |
| contribution / K | statement, paper_locations | baseline_or_prior, evidence_ids, counter_evidence_ids, dependencies (K), centrality, correctness_status, increment_status, significance_status, correctness_reason, increment_reason, significance_reason, reason, uncertainty |
| expectation / X | expectation, origins, basis_evidence_ids, scope | discovery_ids (D), necessity, impact_hypothesis, tier, independence_reason, search_ids, evidence_ids, counter_evidence_ids, presence_status, rationality_status, missing_status, checked_locations, uncertainty, next_question |
| discovery / D | route, disposition, reason | question, basis_evidence_ids (E), search_ids, scope_and_use, possible_synthesis, checked_locations, uncertainty |
| audit / A | target (K/X), inference, author_response, investigation, verdict, reason | challenge, challenge_basis, evidence_ids, counter_evidence_ids, search_ids, uncertainty |
| impact / I | finding, evidence_refs, direction, extent, reason | target_refs (K/X), scholarly_use, independent_quality, counter_evidence_ids, overlaps (I), status, uncertainty |
| evidence / E | location, excerpt, purpose | kind, title, authors, doi, url, version, available_date, date_basis, status, search_ids, accessed_at |
| search / S | query, query_target, tool, status | mode, urls, failure_reason, executed_at |

Reference lists default empty. K's three statuses default `unchecked`; analytical statuses describe judgments rather than numerical weights. S/E timestamps default to current UTC when added. Search records are agent-reported actual actions, not automatic tool capture.

Fixed values:
- D route: `manuscript|field`; disposition: `candidate|satisfied|optional|out_of_scope|insufficient|no_candidate|limited`.
- A verdict: `supported|qualified|misrepresented_source|invalid_inference|hypothesis|unresolved|not_warranted`. A challenge requires `challenge_basis`.
- I direction: `supports|enhances|qualifies|weakens|blocks|unknown`; extent: `local|main|distributed|unknown`; status: `established|uncertain` (default uncertain). Supply a K/X target, justified scholarly use or independent quality condition.
- X origins: list drawn from `A|B|C|D` (see investigation reference); tier: `exploratory|decision_relevant` (default exploratory). Decision-relevant X requires grounded `independence_reason`, not a quota of source IDs.
- E kind: `paper|external` (default paper); status: `verified|partial|not_accessible|provider_error|excluded` (default partial).

Example A; source E1 and target K1 must already exist:

```json
{"target":"K1","inference":"Comparison conditions support the proposed distinction","challenge":"Could different evaluation conditions explain it?","challenge_basis":"The compared studies use different populations","evidence_ids":["E1"],"counter_evidence_ids":[],"author_response":"Paper qualifies the comparison in section 4","investigation":"Read section 4 and source methods; record actual sources here","verdict":"qualified","reason":"Distinction holds within the stated conditions","uncertainty":"Coverage outside those conditions remains unknown"}
```

Example I:

```json
{"finding":"A conditional comparison remains useful","target_refs":["K1"],"evidence_refs":["A1"],"direction":"supports","extent":"main","reason":"The scoped distinction helps choose methods with matching assumptions","status":"established","overlaps":[]}
```

## Evidence, judgment and completion

`context` accepts `publication_date` (ISO YYYY-MM-DD), `date_basis`, `version`, `date_uncertainty`. Init records the source path/hash and extracted-text hash. Unknown dates permit internal work; finalization needs a confirmed cutoff and basis.

Verified E needs an actual location and contiguous excerpt. Paper excerpts must match `paper.md` ignoring whitespace; `p. N` is checked against PDF page markers. External E additionally requires URL, version, availability date ≤ cutoff and date basis. Partial/excluded sources stay in the working log; they cannot substantiate final review claims. The validator does not retrieve external text or establish that metadata, excerpts or semantic support are true.

`point` payload: `{"text":"Finding and why it matters","evidence_refs":["I1"]}`; sections are strengths, weaknesses, questions, comments. C/Q/N may also be referenced. Every point needs existing references.

`judgment` payload: `{"reason":"Reliable value, decisive limits, overlap and remaining use","refs":["I1"],"scale_reason":"Why the chosen rating category fits relative to neighboring categories","limitations":"Coverage, failed access, unresolved questions and budget limits"}`. Record the score separately through `outline`; if judgment is blocked, leave it unset and explain why.

V2 completion requires both discovery routes to be accounted for, including limited/no-candidate outcomes; an impact-based overall rationale; separate reasons and an inference audit for decisive K; discovery/screening grounds and whole-paper absence checks for decisive X. Unresolved challenges/impacts cannot be decisive quality findings. The review follows indirect references to reject ineligible external evidence. No-score reports can document inability to judge without declaring unresolved findings established. Checks establish structure, not scholarly validity.

`finalize` / `export` write `review.md` and a compact `audit_summary.md` covering K's three judgments, D screening, X presence, A challenges/verdicts, I influence, uncertainty and coverage. The review appendix contains cited records and their dependencies; exploratory records remain in the full log/audit summary.

## Original ProReviewer interface

C/Q/N and conference scales are retained. Use command `--help` for full inherited syntax.

```text
--dir <run> add_claim --text "Authors' synthesis claim" --section "section 3, p. 5" --claim_type synthesis
--dir <run> update_claim --id C1 --status supported --reason "Verification" --cross_refs "section 4"
--dir <run> add_question --text "Which conditions apply?" --section "section 3" --related_claims C1
--dir <run> resolve_question --id Q1 --answer "Scoped answer" --sections "section 4"
--dir <run> add_note --text "Observation" --section "section 2" --tag synthesis
--dir <run> step --target "K1,A1" --why "Central inference" --action "Actual reading/search" --found "Evidence and outcome" --ops "put audit A1"
--dir <run> outline --section summary --content "Survey and contribution summary"
--dir <run> outline --section overall_score --content 6
--dir <run> set_conference acl
```
