---
name: survey-review
description: Evaluate literature surveys through existing and justified expected knowledge contributions, audit their scientific reasoning against publication-time scholarly evidence, and organize strengths, weaknesses and overall academic quality by substantive impact.
---

# Survey review

Evaluate **overall academic quality**, using reliable and useful cross-study synthesis as the main investigative lens. Preserve ProReviewer's active reading, persistent ReviewLog and review format. Contributions can include maps, distinctions, explanations, taxonomies, evidence assessments and research directions; useful synthesis need not be globally novel. Do not equate quality with a contribution count or exhaustive flaw detection.

## Start and output contract

Invoke `$survey-review "<absolute paper path>"` in Codex or `/survey-review "<absolute paper path>"` in Claude Code. Resolve `scripts/review_cli.py` relative to this skill. Install `requirements.txt` if needed. PDF, Markdown, text, LaTeX and LaTeX project directories are supported.

```text
python <skill>/scripts/review_cli.py init "P:/papers/Survey Title.pdf" --publication-date 2025-03-14 --date-basis "User supplied" --conference iclr
```

**Every new run directory is `review_{input filename without its final extension}`**, e.g. `review_Survey Title`. Preserve spaces, Unicode and the full stem; replace Windows-invalid characters with `_` and trim trailing dots/spaces. For project-directory input use its directory name. `--dir <parent>/review_<stem>` may change the parent, never the basename. Reuse an existing run with subsequent commands; initialize a separate parent for a new sample. No truncation, added run suffixes or overwriting nonempty runs.

Use only these final artifact names: `paper.md`, `input_manifest.json`, `review_log.json`, `review.md`, `audit_summary.md`, and optional `steps.jsonl` / `steps.md`. Keep request payloads in `inputs/<kind>_<id-or-new>.json` and downloaded source files in `sources/<E-id>.<ext>`; create these subdirectories only when needed. Do not create alternate final reports. The CLI fixes the run basename and exported review filename.

Before investigation read [state-and-cli.md](references/state-and-cli.md) for commands and [contribution-investigation.md](references/contribution-investigation.md) for discovery, audit and impact decisions.

## Temporal and evidence boundary

The exact input PDF is authoritative. Confirm its evaluated version, publication/release/submission cutoff and the basis using `context` before external evaluation. Metadata pages may establish identity/dates; file timestamps and the newest cited year do not. If only a year/month is established, use its earliest day conservatively and record uncertainty. If unresolved, continue internal reading but request the missing context before a historically grounded final judgment.

Use substantive evidence from source versions available **on or before the cutoff**. Exclude later discoveries, revised contents, hindsight, citation counts and post-cutoff model memory. Date filters alone do not verify source versions. Search snippets, inaccessible text and undated versions remain provisional. Use the host's available scholarly web/page/PDF tools with adaptive, question-driven searches; no mandatory API keys, providers or fixed keyword templates. Record actual searches, failures, access limits and budget. Never read previous reviews, official reviews or development-case diagnoses as answers.

## Working loop

1. Initialize and read the whole paper, mapping its goals, type, scope, central promises and distributed useful contributions. Inspect original figures/tables when extraction is uncertain. Persist C/Q/N notes and K contributions during reading; update existing records rather than duplicating them.
2. Discover expected contributions through **both manuscript and independent field/reader routes**. In the latter, investigate cutoff-admissible topic issues beyond checking the author's claims, then form source-grounded questions and possible synthesis responses. Screen scope, importance and feasibility before checking the full paper for presence. Record D outcomes including satisfied, optional, out-of-scope, insufficient or limited discovery; promote justified candidates to X. No quotas or compulsory missing contributions.
3. Prioritize investigations that could change a consequential assessment. Audit source facts, comparability conditions, cross-study inference, the actual synthesis and its scholarly use. Challenge important inferences when there is a plausible alternative, counterexample or scope problem; check the author's existing response, seek supporting and contrary evidence, and record the investigation and verdict in A. Do not turn an unanswered reviewer guess into a defect or the agent's newly supplied synthesis into the paper's contribution.
4. Assess K correctness, relative increment and value **separately, each with reasons**. Tie value to the actual synthesis, a scholarly use, why it helps and its conditions. State search limits for increment judgments. For X, establish reasonable necessity, inspect the whole manuscript including caveats/appendices, and distinguish absent from partial, qualified or already supplied. Unknown is not poor quality.
5. Record material positive and negative I findings: evidence, affected K/X or justified scholarly use/independent quality condition, direction, extent, reasoning, overlap and uncertainty. Preserve independent serious problems that directly affect trust or use without forcing them into K. Do not count findings, average contribution labels or invent repaired-paper scores.
6. After each investigation, use `step` to record target, priority, actual action, finding and state operations. Before closing, account for section coverage, unfinished challenges and external-discovery/search/budget limits. These are agent-written records, not automatically intercepted tool events.
7. Write summary, strengths, weaknesses, questions and useful comments through `outline` / `point`. Give positive findings the same evidential care as criticisms. Use `judgment` to explain reliable contributions, decisive limits, remaining value, dependencies, overlapping roots and why the conference rating category fits relative to adjacent categories. Cite the material I records; use `outline` for the score, or leave it unset with an explicit inability-to-judge explanation.
8. Run `audit`, fix errors, then `finalize`. Inspect `review.md` and `audit_summary.md` for faithful evidence, complete links and temporal leakage. Structural checks do not establish semantic support, discovery recall or scholarly validity. Return the review and run-directory paths.

This version does not add an exhaustive hallucination/format scanner, paper rewriting, counterfactual experiments, a large contribution graph or multiagent machinery. Incorporate consequential problems actually found; report the investigation's limits.
