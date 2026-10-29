---
name: survey-review
description: Evaluate a literature survey's overall academic quality through actual knowledge results and justified expected knowledge results. Use when asked to review a literature survey or assess its scholarly quality.
---

# Survey Review

## Task

Evaluate the survey's overall academic quality through the knowledge results it provides and the knowledge results its stated scope gives readers sufficient reason to expect.

A **candidate knowledge unit** is one concrete understanding or organization of a research area that the survey actually expresses. It must have concrete content, a stated range and location, and independent checking significance. It may be a cross-study synthesis, comparison, explanation, assessment, classification, evidence distribution, limitation diagnosis or research suggestion.

The required assessment dimensions are separate:

- **Knowledge-increment identification:** whether the manuscript actually forms a concrete, separately checkable survey-level understanding or organization that could be a knowledge increment, rather than only presenting background or repeating an individual source.
- **Correctness:** whether the source facts, comparison conditions and reasoning support the candidate at its stated scope.
- **Relative novelty:** what was already expressed by identifiable work available by the evaluation cutoff, and what this survey adds, clarifies, connects or makes useful.
- **Scholarly value:** what understanding, judgment or research use the candidate supports, under what conditions.

Knowledge-increment identification answers only whether this candidate is a review-level result that could add knowledge. It does not decide whether the result is correct, whether a prior survey already expressed it, or whether it is valuable. Assess correctness, relative novelty and scholarly value independently. A candidate may qualify while being incorrect, already familiar or low-value; a useful result may also be familiar.

An **expected knowledge item** is a concrete understanding or organization that the target reader has good reason to expect from the survey's title, abstract, stated scope, promises or established field evidence. An expectation is not automatically an omission. It becomes a negative review reason only when its rationale is supported, its presence has been checked across the paper, and the missing part has a material effect.

The final review must contain evidence-linked strengths, weaknesses, questions, comments, and overall_score when a rating scale is requested. Overall reasoning must explain how established positive and negative findings affect scholarly use. Do not average labels or count findings.

## Read the references

Resolve the skill directory before starting. Before writing records, read:

1. references/state-and-cli.md for record definitions, fields, statuses, command syntax and structural checks.
2. references/contribution-investigation.md for candidate extraction, expected knowledge discovery, assessment branches and overall reasoning.
3. references/external-investigation.md before any external search, source retrieval or version check.

Use the supplied PDF as the authoritative manuscript. When parsed text or JSON differs from the PDF, inspect the PDF and cite the PDF location. Keep the publication/version cutoff fixed throughout the run. External search uses the host's available tools; no API key or fixed keyword template is required.

## Run setup

Use the supplied script and keep every run in a folder named review_<paper filename without its final extension>. Preserve the full input stem, including meaningful spaces or Unicode, after replacing Windows-invalid path characters. Use a different parent directory for a new run; do not overwrite an existing run.

~~~
python <skill>/scripts/review_cli.py init "<absolute paper path>" --output-parent "<existing run parent>" --publication-date YYYY-MM-DD --date-basis "basis actually established" --conference iclr
~~~

The conference argument selects the rating interface. It does not establish the manuscript's venue or scientific quality. If no score is requested, leave the score unset and write a qualitative overall judgment.

The output parent must already exist. Omit `--output-parent` to place the run beside the manuscript. Initialization fails if the target run folder already exists. Save the printed run path and pass it before every later command.

## Initial reading

1. Read the abstract, introduction, stated promises, section/figure/table outline and conclusion.
2. Create inputs/run_context.md with the task, manuscript scope/use, cutoff and a coverage inventory. Mark each in-scope section, figure, table and appendix not_visited.
3. Read the full manuscript in section order, including result analyses, discussion, conclusion, figures, tables and appendices.
4. Extract every candidate knowledge unit that meets the three definition conditions. Do not use the explicit contribution list as the extraction boundary.
5. Record each candidate's exact wording, range, PDF location, result form, relation to existing knowledge and split/merge reason.
6. Record explicit author contribution statements separately as promises and link them to the candidate results they claim to deliver.
7. Start expected-knowledge discovery from the stated promises and the two routes in contribution-investigation.md.
8. Record the actual reading and created record IDs with step.

Reading the abstract or creating a step does not mark the full paper processed. A coverage row becomes processed only after substantive reading and a recorded assessment consequence, newly created question/contribution, or a stated reason that no record is required.

## Investigation loop

Repeat until the exit conditions in contribution-investigation.md are satisfied:

1. Run show --detailed and read inputs/run_context.md.
2. Build the pending agenda from unassessed candidate dimensions, unscreened expected items, unresolved assessments, incomplete full-paper presence checks, uncertain impacts, unvisited sections and actionable investigation questions.
3. Choose the highest-priority target. Protect against a plausible reversal of a central result, resolve shared consequential premises, investigate material positive results, then address expected items and lower-impact coverage. Centrality, uncertainty and decision relevance are separate considerations and cannot replace one another.
4. State the target, proposed interpretation, plausible alternative and evidence plan before reading.
5. Execute the relevant internal or external investigation branch.
6. Add source evidence after inspecting the source. Record external search attempts separately. Update only the assessments warranted by the evidence.
7. Check newly read material for additional candidates, expectations, contradictions and dependencies.
8. Record one completed iteration with step, then re-sort the agenda.

Use the CLI commands exactly as defined in state-and-cli.md. A record may be created and assessed in one iteration only when the evidence was actually inspected in that iteration. A failed access attempt produces a bounded unknown; it does not prove absence or a manuscript defect.

## Final review

Before finalizing, verify that:

- every relevant manuscript section, figure, table and appendix was processed or marked unavailable with actual access attempts and possible assessment effect;
- every candidate used in a positive or negative review reason has separate knowledge-increment identification, correctness, relative novelty and value decisions, with explicit skip reasons where a dimension is not applicable;
- both expected-knowledge discovery routes were accounted for;
- every omission used as a weakness has a justified expected item, a full-paper presence check and a material impact;
- every consequential assessment is settled or explicitly unresolved with evidence limits;
- overall impact records distinguish finding, materiality and rating effect, and shared causes are not counted repeatedly;
- the final review cites only records that exist and reflects the fixed task and scale.

Then run:

~~~
python <skill>/scripts/review_cli.py --dir <run> validate
python <skill>/scripts/review_cli.py --dir <run> finalize
~~~

The CLI integration checks use the supplied 001 manuscript PDF and run with:

~~~
python -m unittest discover -s <skill>/tests -v
~~~

Inspect review.md, audit_summary.md, review_log.json and steps.jsonl. Report empty evidence sections, broken links, duplicate points, unsupported conclusions and coverage gaps. Structural validation cannot decide whether a scholarly judgment is correct.

Return the final review.md path and the run directory.
