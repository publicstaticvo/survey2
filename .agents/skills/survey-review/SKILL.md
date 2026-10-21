---
name: survey-review
description: Review literature surveys through their existing and justified expected knowledge contributions, investigate scholarly sources as of publication, and produce a ProReviewer-style evidence-grounded review and overall judgment.
---

# Survey review

Review a literature survey with knowledge contribution as the main investigative lens. Follow ProReviewer's active reading and persistent ReviewLog approach, producing summary, strengths, weaknesses, questions, comments when useful, and an overall score with an explicit rationale. Explain the scope of the judgment and how the evidence warrants it.

Knowledge contribution is a useful synthesis of existing research: relationships, distinctions, explanations, conditions, taxonomies, evidence maps, resolution of conflicting findings, or supported research directions. Assess correctness, what it adds relative to prior knowledge, and its significance for this survey's goals at publication. A useful synthesis need not be a world-first finding.

## Invocation and time context

Use `scripts/review_cli.py` relative to this SKILL.md; resolve an absolute script path before executing commands. Python requires `pydantic>=2,<3` and `PyMuPDF` for PDF input. The CLI also accepts Markdown, text, LaTeX, and LaTeX project directories through the original ProReviewer converter.

```text
$survey-review "P:/papers/survey.pdf" --publication-date 2025-03-14
$survey-review "P:/papers/survey.pdf"
```

Use `$survey-review` in Codex and `/survey-review` in Claude Code, from this project.

Initialize using the provided date and conference (default is ProReviewer's ICLR scale):

```text
python <skill>/scripts/review_cli.py init "paper.pdf" --dir "review_survey" --publication-date 2025-03-14 --date-basis "User supplied publication date" --version "submitted PDF" --conference iclr
```

**Evaluate with information available on or before the paper's publication cutoff. Do not use information published after that date to judge correctness, prior art, significance, missing contributions, or overall quality.** This includes later discoveries, later reviews, hindsight about research impact, and later versions of earlier papers. Model memory about post-cutoff developments is also inadmissible. A search date filter alone does not establish admissibility.

When only a PDF is provided, initialize without a date, identify the exact manuscript from its front matter, then verify its publication/release date using the paper or an authoritative version history. Write the date and its source using `context` before external evaluative investigation. For an unpublished submission, use a verified release/submission date for that evaluated version. Keep target version and date basis explicit. PDF file creation/modification timestamps and the newest year in the bibliography are not publication dates.

If only a year/month is verifiable, record the uncertainty and use the earliest day of that interval as a conservative cutoff, explicitly marking this choice; retain time-ambiguous sources as uncertain. If the date cannot be established, continue internal investigation, report the missing temporal context, and request clarification rather than fabricate a date or finalize a historically grounded judgment. A PDF revised after its claimed cutoff needs an explicit version/date resolution before finalizing.

Retrieval may happen today, but admissible substantive evidence must be from a version publicly available by the cutoff. Modern catalog pages may establish identity/version metadata; their later commentary, citation counts, rankings, and retrospective assessments cannot support a historical quality judgment.

## Working loop

Read [references/state-and-cli.md](references/state-and-cli.md) for state operations and [references/contribution-investigation.md](references/contribution-investigation.md) for the two investigation directions.

1. Initialize, confirm the temporal context, and map the paper's structure and central promises. Use the exact input PDF as authoritative; record uncertainty caused by extraction and inspect original figures/tables when needed.
2. Log author claims, questions, observations, candidate contributions, and candidate expectations as they arise. Keep the ReviewLog as working state, updated during reading. Each targeted read may reveal new contributions or issues beyond the original agenda.
3. Consult unsettled records and choose the investigation most likely to clarify a central contribution or change the overall judgment. Examine the paper's synthesis and its supporting sources; use the host agent's available web search and page/PDF tools for question-driven scholarly investigation. Decide queries and follow-up paths from evidence rather than fixed keyword templates. Record actual searches and failures; respect any user-specified global budget.
4. Verify the specific external source version, availability date, location, and excerpt before using it. Store search snippets and inaccessible/undated sources as partial or uncertain. Seek contrary evidence on consequential disputes. Search failure is not evidence that prior work is absent. Record counterevidence and unresolved alternatives.
5. Update existing-contribution correctness, increment, and significance separately. For expected contributions, first discover candidates, then assess grounds/scope/necessity, then inspect the full manuscript for their presence. Distinguish consequential deficiencies from optional improvements.
6. Record a `step` after each investigation: target, reason for priority, actual reading/search, findings, and resulting operations. These are agent-written investigation records, not an automatic capture of every tool event. Check every section before closing; identify budget or access limits explicitly and preserve unresolved questions as uncertainty.
7. Build the review using the original `outline` interface or `point` for extended evidence references. Substantiate positive as well as negative judgments. Explain why each point matters and identify actionable implications. Other grounded observations can be recorded through claims/questions/notes and included where relevant.
8. Set the conference-scaled `overall_score` with `outline`; use `judgment` to record the decisive evidence and explain how positive and negative findings jointly support the overall conclusion. Discuss centrality, overlapping contributions, dependencies, and limitations instead of counting points. Unknown is not poor quality. If key evidence prevents a score, leave it unset and explain the limit.
9. Run `audit`, correct errors, then `finalize`. Inspect the exported review for evidence support and temporal leakage; validators establish structural/date consistency, not scholarly truth. Return the review and output paths.

The output includes `paper.md`, `input_manifest.json`, `review_log.json`, `review.md`, and, when recorded, `steps.jsonl` / `steps.md`. Maintain ProReviewer's review format and conference rating scale; the methodological change is the knowledge-contribution investigation and its evidence state.
