---
name: survey-review
description: Evaluate a literature survey's overall academic quality through its actual and justified expected synthesis contributions. Investigate source fidelity, cross-study reasoning, relative increment and scholarly value, then write an evidence-linked review. Use when asked to review a literature survey or assess its scholarly contributions.
---

# Survey Review  -  Contribution Investigation (v2a)

## Overview

Evaluate **overall academic quality**, using the survey's reliable and useful synthesis contributions as the main investigative lens. A contribution is an understanding the manuscript actually supplies through organizing, connecting, comparing, explaining or assessing studies. It may be a map, taxonomy, explanation, evidence assessment or research direction. Useful synthesis need not be globally novel.

The ReviewLog drives the investigation. Identify a contribution or grounded uncertainty, decide what evidence could settle it, investigate, update the log, then choose the next target. A positive finding needs the same evidence discipline as a criticism.

## Before starting

Resolve `<skill>` to this skill's directory. Use `python <skill>/scripts/review_cli.py`; install its requirements if needed. Read [state-and-cli.md](references/state-and-cli.md) before writing records. Read [contribution-investigation.md](references/contribution-investigation.md) before the first investigation; return to its relevant branch when the target changes.

Use the supplied PDF as authoritative; inspect figures/tables in the PDF when extraction is uncertain. Confirm the publication/submission cutoff and evaluated version. Set the review task and any requested rating scale before investigation; a research proxy scale is not the paper's actual venue decision. If no score is requested, retain a qualitative overall judgment. An unavailable venue scale alone does not invalidate qualitative evaluation.

Use sources available by the cutoff. Verify external versions and substantive passages, not only search results. Use the host's available web, scholarly-page and PDF tools with adaptive questions; no mandatory API key or fixed search template. Do not read earlier reviews or case diagnoses as answers. If project context already exposed them, report that limitation.

## Workflow

### 1. Initialize

```text
python <skill>/scripts/review_cli.py init "<absolute paper path>" --publication-date YYYY-MM-DD --date-basis "Basis actually established" --conference iclr
```

`--conference` selects a supported scoring interface, not the manuscript's actual venue. Use the task's specified scale; if none is specified, do not infer a scientific quality scale from the default. Use the optional `context` operation to record the exact version and date uncertainty. If the cutoff is missing, continue internal reading and obtain it before a historically grounded final judgment.

Save the output path printed by init. Pass `--dir <run>` **before every subsequent command**. The run basename is `review_{input filename without its final extension}`; preserve the full stem, spaces and Unicode, replacing Windows-invalid characters. For a project directory use its directory name. To repeat a sample, choose another parent, not a suffix or an overwrite.

### 2. Establish the initial agenda

1. Read the abstract, introduction, contribution statements and section/figure/table outline.
2. Create `inputs/run_context.md` for the task, manuscript scope/use, coverage inventory and pending agenda, following state-and-cli.md. These are run metadata, not additional review-record types or final evidence. Inventory the main text, figures/tables and appendices as `not_visited`; set `visited_processed` only after substantive reading and a recorded assessment consequence, or `unavailable` with actual access attempts. A step/log entry alone never proves coverage.
3. Create K records for **candidate contributions actually indicated in the manuscript**, with locations and three statuses `unchecked`. A title or author novelty assertion alone is not verification.
4. Put a relevant author's local assertion in its K/A inference with the original E passage. Keep unscreened leads or questions without an identifiable contribution target in the run agenda until investigated; they are not findings or omissions.
5. Start manuscript-route D discovery from the promises. If scope or a possible contribution is unclear, record the uncertainty rather than inventing an expectation.
6. Record this actual reading and the resulting IDs with `step`.

**Done:** scope and initial candidates are recorded, every in-scope section/item has an inventory row, and the next unsettled target can be named. Initial orientation does not count as processing every section. Do not read the entire paper first and reconstruct an apparently active log afterward.

### 3. Investigation loop

Repeat the following sequence. Each iteration investigates one question or tightly coupled inference; it may read several related locations and update multiple records.

**a. Consult the log.**

```text
python <skill>/scripts/review_cli.py --dir <run> show --detailed
```

Construct the pending agenda from:

- K: an unchecked correctness, increment or value judgment; unsupported identity as a contribution; a new counterexample or dependency.
- D: a screened candidate not yet passed to X, or a closed route with an explicit new investigation opportunity. Unperformed routes and unscreened thoughts stay in the run agenda; rejected/satisfied/limited records are not pending merely because retained.
- X: unchecked rationality/presence, incomplete manuscript search, or missing grounds for importance.
- A: an unresolved audit with an actionable next step, missing author response, or new evidence requiring revision. Distinguish not-started work, evidence-limited work and unresolved conflict using the action table in state-and-cli.md; do not repeatedly schedule a parked blocked audit.
- I: an uncertain effect with a concrete unperformed test, unclear remaining value, or overlapping findings needing reconciliation; closed inconclusive/withdrawn effects reopen only on a stated trigger.
- Run metadata: pending leads/questions and unvisited sections; parked access limits reopen only on a specific new opportunity.

Read `inputs/run_context.md` alongside `show`; the CLI does not load that file, generate the agenda or choose a target automatically. A completed investigation with an explicit `unknown` is different from `unchecked` work not performed.

**b. Pick the highest-priority target.**

Choose by the following principles, in order, explaining the choice rather than assigning invented numerical priority scores:

1. **Protect against a possible reversal.** Investigate a plausible source error, contradiction or counterexample that could invalidate a central synthesis before a routine detail. "Possible" must have a concrete basis; a bare suspicion does not outrank established work.
2. **Resolve shared premises before dependent claims.** If the same definition/source/comparison supports several material K records, inspect it before separately checking each downstream application. Shared dependency raises priority only when resolving it could change multiple consequential judgments; sharedness alone is not urgency.
3. **Do not systematically postpone positive value.** If a main positive contribution could materially change the overall assessment and its evidence is accessible, investigate it before peripheral concerns. A credible high-value positive can outrank a weak, low-impact suspected contradiction.
4. Investigate a missing discovery route or unvisited section that could change a main conclusion; then a screened X whose necessity/presence could materially affect use.
5. Complete remaining consequential questions, overlap checks and lower-impact coverage.

Centrality, uncertainty and decision relevance are separate priority considerations: none can substitute for either of the others. A central item may still be low priority when its uncertainty cannot change a decision, and a decision-relevant item may not be central.

**Conflict examples.** If a grounded citation/definition error could invalidate the central synthesis and also underlies three K records, test that common premise first, even when a major positive contribution awaits investigation. If an unverified positive map may be the paper's main value while a speculative contradiction concerns one peripheral example, verify the map first and leave the low-basis suspicion pending. If neither target has that priority-1 reversal risk but both are central and each can change the same rating category, choose the one with the more discriminating, accessible evidence; then reconsider priority immediately after the result.

Within a class, choose the target whose resolution could most change the assessment, then the one with accessible discriminating evidence. Do not investigate only weaknesses or repeatedly revisit a blocked source while other productive work remains.

**c. State the target and evidence plan before reading.**

Name the existing target ID or unnumbered agenda question, the proposed interpretation and any plausible alternative, and where discriminating evidence should be found. Examples: "K2's efficiency comparison: inspect the summary table, cost definitions and cited experiments"; "field discovery: inspect independent pre-cutoff accounts before deciding whether the survey owes a particular synthesis." Do not assign an ID or verdict to an unscreened lead merely to name the target.

**d. Gather evidence using the appropriate branch.**

| Target | Action | Record when evidence is obtained |
|---|---|---|
| Existing contribution K | Read its actual synthesis, supporting studies and comparison/inference conditions; inspect qualifications elsewhere | E; A for a consequential inference; update K |
| Expected-contribution discovery D | Investigate manuscript promises or independent field issues, then screen scope, importance, grounds and feasible response | S/E; update D; create X only after screening |
| Expected contribution X | Test reasonable necessity, search the full manuscript for the expected understanding and equivalent responses | E; checked locations; update X and its D |
| Unsettled audit A | Test the inference and grounded rival, inspect the author's response, gather support and counterevidence | E/S; revise A and affected K/X |
| Impact I | Determine what the established finding changes about the synthesis/use and what remains valid | Update I; reconcile overlap; revise affected assessments |
| Coverage or a pending lead in the run agenda | Read the specified location or remaining section; check the PDF where needed | Update run metadata; create/update K/D/A/E/I only if their definition is met |

For external work, record S **after an actual search/access attempt**, including failure. Create E for passages actually inspected. Metadata can establish identity/date; an abstract cannot verify unobserved experimental methods. A failed search produces an access limit, not a paper defect.

Before external searching, source retrieval or version checking, read [external-investigation.md](references/external-investigation.md) and use its trigger/goal table and ordered protocol. Correctness, relative increment and value require different discriminating evidence. The publication cutoff remains unchanged across searches; later evidence cannot settle a historical quality claim.

**e. Update the log from evidence.**

Write E/S first, then the analytical records that reference them. Create A as `unresolved` when an inference needs investigation; update its existing ID when resolved. Update only judgments the evidence warrants. Recheck affected K/X and I when a premise changes. A record may be created and settled in the same iteration only if the actual evidence was inspected in that iteration.

For a qualified inference, check whether the manuscript **already expresses the qualification where it makes the claim**. If so, the condition can be part of a sound contribution, with no weakness. If the abstract/table/conclusion exceeds the available support, identify that precise gap. An explicit limitation somewhere does not automatically repair every stronger formulation.

**f. Record the completed iteration.**

```text
python <skill>/scripts/review_cli.py --dir <run> step --target "K1,A1" --why "What could change and why now" --action "Actual sections, source versions, searches or calculations inspected" --found "What was observed; conclusion and remaining uncertainty" --ops "put evidence E1; put audit A1; put contribution K1"
```

Use one `step` for each actual investigation iteration, after reading and updates. `--ops` is semicolon-separated. Steps are agent-written reports, not automatically captured tool calls. Record failures as failures. Do not replace the whole investigation with one retrospective "read everything" step.

**g. Add new discoveries and return to a.**

Reading for one target may expose another contribution, contradiction or grounded expectation. Record it while its location is available, then prioritize it against the existing agenda. If it repeats an existing issue, update that ID.

**Iteration completion:** the stated question has either been tested and updated, or an actual failed/blocked attempt and its next action/stop reason has been recorded; newly affected dependencies and coverage are updated, and the step is written. Then re-sort the active agenda after every iteration. A completed iteration need not settle the question; merely choosing a new status does not complete an investigation.

### 4. Exit conditions

Before writing the review, verify each condition against the log:

1. Every main-text section, relevant figure/table and appendix has been read and processed or explicitly marked unavailable/still not_visited with its possible assessment effect and actual access/budget constraint. Process accessible unvisited sections unless an actual constraint prevents it; unread content remains a coverage limit, not completed coverage.
2. Each K used as a main positive/negative reason has separate correctness, relative increment and value reasons, manuscript evidence, and an audit of its consequential inference. Unknowns are stated as unknowns.
3. Both discovery routes are accounted for. A limited attempt records actual searches/access bounds; a `no_candidate` result states what was inspected. Neither implies exhaustive absence of expected contributions.
4. Each omission used as a weakness has a justified X, a screening D, a full-manuscript presence check, and a material impact. Optional or insufficiently grounded expectations remain outside weaknesses.
5. Every consequential A is settled or explicitly unresolved with a reason. An unresolved suspicion is not an established negative finding.
6. I records distinguish affected understanding, use, remaining value and shared causes. Positive and negative findings have both been examined.
7. Remaining agenda items are resolved, closed with reasons, or parked with actual limits and reopening conditions; disclose material coverage limits in the final judgment. Access failure does not become a confirmed absence. There is no requirement to pretend every uncertainty was resolved.

Coverage is complete only when each relevant section, figure/table and appendix was actually read and processed as defined in Step 2. For each row, the coverage note must state the substantive point examined and the assessment consequence (record update, new question/contribution, or why none is needed). A citation in steps, a mention in another log record, or a checked box without a processing account does not count. This checks access and processing, not that the resulting interpretation is correct. Mark inaccessible items and the plausible effect; do not silently count them covered.

If remaining uncertainty could change the overall judgment, investigate if feasible and then disclose it in the overall reasoning. Follow ProReviewer's ordinary score practice: compare the balanced merits and weaknesses with the already selected scale and explain the chosen category. Do not invent an additional numerical sufficiency threshold or arithmetic rule. An `unknown` field does not automatically prevent a score, and a completed log does not automatically justify one. The reviewer - not the structural validator - decides whether the established reasons support a category; when they do not, leave it unset and state why.

### 5. Build the review

Use `outline` for the summary and optional score; use `point` for one strength, weakness, question or comment per call. Use `judgment` for the overall argument. See the exact commands and payloads in [state-and-cli.md](references/state-and-cli.md#operating-the-log).

- Summary: what understanding the survey supplies and its scope.
- Strengths: verified positive contributions, their specific scholarly use and evidence.
- Weaknesses: established errors/limits or justified omissions, their locations and material effects. State what remains valid.
- Questions: specific unsettled matters the authors could clarify; do not present them as established defects.
- Comments: useful minor suggestions and scope/access qualifications.
- Overall: reliable contributions, decisive limits, overlap/dependencies, remaining value and uncertainty. Explain the weighting in prose, not counts or averages of labels.

Keep the task fixed. If a numerical scale was specified, explain why the category fits relative to adjacent categories, using established I records. If the task is qualitative, leave the score unset and state "qualitative review requested" in limitations. If a requested score is withheld, identify the judgment-relevant unknown. Do not switch tasks merely because the PDF names another venue.

For an incidental general academic issue found while checking a contribution, ask whether it changes an identified K/X, the evidence chain, or a specific trust/communication condition needed for scholarly use. If yes, create/update the relevant K/X/A/E and I. If it does not attach to a contribution but materially affects trust or use, record it under `I.independent_quality` with evidence and effect. If it is a minor issue without such an effect, do not expand scope into general proofreading. Note any repeated unattached material issue in coverage/limitations so a later study can estimate how often the contribution-centered lens misses it; do not infer a rate from four development cases.

### 6. Audit, finalize and inspect

```text
python <skill>/scripts/review_cli.py --dir <run> audit
python <skill>/scripts/review_cli.py --dir <run> finalize
```

Resolve structural errors using actual evidence or revised claims. Inspect `review.md` and `audit_summary.md`: every point's links must reach the intended records; cited evidence must be visible; there must be no unexplained empty Evidence section, duplicate penalty or stronger conclusion than its sources support. The current renderer may leave an empty legacy Evidence heading while exporting records later; report that output defect rather than treating it as absent evidence. Structural audit is not semantic validation.

Return `review.md` and its run path. Fixed artifacts: `paper.md`, `input_manifest.json`, `review_log.json`, `review.md`, `audit_summary.md`, `steps.jsonl` and `steps.md`; run metadata uses `inputs/run_context.md`. In v2a the step files are required by this procedure, although the CLI still treats them as optional. Payloads use `inputs/<kind>_<id-or-new>.json`; downloaded sources use `sources/<E-id>.<ext>`. Keep the original paper/text unchanged.

## The ReviewLog at a glance

| ID / name | Object | Creation rule |
|---|---|---|
| K  -  existing contribution | Understanding the evaluated manuscript actually supplies | Create from located manuscript content; evaluate separately on correctness/increment/value |
| D  -  discovery and screening | How a possible expectation was found and screened | Create for a real manuscript/field investigation, retaining rejected and limited outcomes |
| X  -  expected contribution | A particular reasonable synthesis the survey may owe | Create from a grounded candidate D; missingness remains unchecked |
| A  -  inference audit | Whether one consequential inference for K/X is warranted | Create when its premises, comparison or reasoning need investigation |
| I  -  impact account | What an evidenced finding changes about contribution/use/overall assessment | Create after a substantive finding, or keep uncertain while investigating |
| E  -  source evidence | A located passage from the manuscript or an external source | Create from inspected text, with eligibility/status and purpose |
| S  -  search/access attempt | What external retrieval was actually attempted and its outcome | Create after an attempt; success is retrieval, not a scientific verdict |

These seven are the complete review-record taxonomy for new v2a work. Task/coverage/agenda metadata and chronological steps manage execution; they have no evidence IDs and do not independently support review findings. Full definitions, fields, transitions and boundary examples are in [state-and-cli.md](references/state-and-cli.md). Do not create all record types for every issue.

