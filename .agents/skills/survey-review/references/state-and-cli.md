# State and CLI

Use `python <skill>/scripts/review_cli.py`. Pass `--dir <run>` before every command after initialization. State changes persist in `review_log.json`.

## ProReviewer-compatible operations

```text
init paper.pdf --dir <run> --publication-date 2025-03-14 --date-basis "User specified" --conference iclr
--dir <run> add_claim --text "Authors' synthesis claim" --section "§3, p. 5" --claim_type synthesis
--dir <run> update_claim --id C1 --status supported --reason "What verifies it" --cross_refs "§4,Table 2"
--dir <run> add_question --text "Does this synthesis address the conflicting finding?" --section "§3" --related_claims C1
--dir <run> resolve_question --id Q1 --answer "Finding with evidence" --sections "§4,Appendix A"
--dir <run> add_note --text "Observation with precise paper location" --section "§2" --tag synthesis
--dir <run> step --target "K1,Q1" --why "Central unresolved inference" --action "Read §4 and external source" --found "Observed evidence" --ops "update_claim C1; put contribution K1"
--dir <run> outline --section strengths --content "Specific finding and significance" --claims C1 --notes N1
--dir <run> outline --section summary --content "Survey and contribution summary"
--dir <run> outline --section overall_score --content 6
--dir <run> show --detailed
--dir <run> set_conference acl
--dir <run> audit
--dir <run> finalize
```

The original C/Q/N types and rating scales are preserved. CLI `--help` lists inherited commands; `put --help`, `context --help`, `point --help`, `judgment --help` describe the additions. An unresolved question is uncertainty, not proof of a weakness.

## Extended records

Write UTF-8 JSON with a file-writing tool, then pass `--file <path>`; this avoids shell quoting problems. To create, omit `id`; CLI assigns E/K/X/S IDs. To update, include an existing `id`; the provided fields are merged into that record. `show` includes all extended records. Source references should use E IDs; K/X identify analysis, S actual searches, C/Q/N original ProReviewer entries.

```text
--dir <run> context --file context.json
--dir <run> put evidence --file evidence.json
--dir <run> put contribution --file contribution.json
--dir <run> put expectation --file expectation.json
--dir <run> put search --file search.json
--dir <run> point --section weaknesses --file point.json
--dir <run> judgment --file judgment.json
```

`context.json`: `{"publication_date":"2025-03-14","date_basis":"Publisher/version-history URL and observation","version":"arXiv v1 / submitted PDF","date_uncertainty":""}`. Dates use full ISO `YYYY-MM-DD`. Input path/fingerprint are recorded at init. If no date is known, init succeeds and external evidence stays provisional; finalization requires confirmed time context.

E example (paper):

```json
{"kind":"paper","location":"p. 5, §3","excerpt":"Exact contiguous source passage","purpose":"Basis for K1","status":"verified"}
```

E example (external):

```json
{"kind":"external","title":"Prior study","authors":["A. Author"],"doi":"10.example/id","url":"https://example.org/paper-v1.pdf","version":"v1","available_date":"2024-06-01","date_basis":"Version-history URL identifying v1 and its date","location":"p. 7, Table 2","excerpt":"Exact source passage","purpose":"Checks the comparison underlying K1","status":"verified","search_ids":["S1"]}
```

Evidence status is `verified`, `partial`, `not_accessible`, `provider_error`, or `excluded`. Store later sources as excluded when useful for audit, but do not use their substantive contents in the historical review. Undated/partial sources remain provisional. `verified` external evidence requires a URL, version, date basis, nonempty location/excerpt, and availability no later than the target cutoff. The CLI checks date consistency, not the truth of metadata or semantic support. Verified paper excerpts must match `paper.md` ignoring whitespace; a `p. N` location is checked against that PDF page. Inspect the PDF to resolve extraction errors, keeping an appropriate uncertainty status.

K example:

```json
{"statement":"What synthesized understanding is provided","paper_locations":["§3, p. 5","Table 2"],"baseline_or_prior":"What earlier accounts provided","evidence_ids":["E1","E2"],"correctness_status":"supported","increment_status":"supported","significance_status":"important","centrality":"core","dependencies":[],"counter_evidence_ids":[],"reason":"Why each judgment follows from the sources","uncertainty":"Remaining limitations"}
```

X example:

```json
{"expectation":"A relationship needed for the promised comparison","origins":["A","B"],"basis_evidence_ids":["E1","K1"],"scope":"Why within this survey's chosen task","necessity":"core","impact_hypothesis":"Which central inference is limited","tier":"decision_relevant","independence_reason":"How the grounds differ","search_ids":["S1"],"evidence_ids":[],"presence_status":"absent","rationality_status":"reasonable","missing_status":"confirmed","checked_locations":["§3","§4","Appendix A"],"counter_evidence_ids":[],"uncertainty":"","next_question":""}
```

Analytical status fields are descriptive judgments with defaults `unchecked`/`unknown`; give specific reasons. E status, X tier and origins have fixed allowed values. The CLI verifies references and records independence explanations, while the agent establishes whether the grounds are independent, reasonable and sufficient.

S example:

```json
{"query":"Actual query sent","query_target":"Check the comparison in K1","tool":"Host web search","mode":"live","urls":["https://example.org/paper"],"status":"success","failure_reason":""}
```

Timestamps are recorded when S/E records are added unless supplied. These are self-reported records, not a tool-event interception system.

Point example: `{"text":"Specific positive or negative finding, with why it matters","evidence_refs":["K1","E1"]}`. Valid sections are strengths, weaknesses, questions and comments. C/Q/N can also be used in `evidence_refs`. Every point needs existing evidence IDs. Use `outline` for the summary and numeric conference score.

Judgment example: `{"reason":"How the decisive positive/negative findings support the score, accounting for centrality and dependence","refs":["K1","X1"],"limitations":"Access/budget/uncertainty limits"}`. Set an overall score separately via `outline`; if a score cannot be justified, leave it unset and explain why in `limitations`. Exploratory X records cannot be decisive overall references. Finalization follows indirect K/X evidence links to reject ineligible external evidence.

`finalize` and `export` check the complete review, temporal metadata, evidence IDs, excerpt locations and input manifest before writing `review.md`. The evidence appendix includes the persistent records; overall reasoning is explicit rather than a numerical aggregation. Semantic support, completeness of search and domain judgments still need agent and human verification.
