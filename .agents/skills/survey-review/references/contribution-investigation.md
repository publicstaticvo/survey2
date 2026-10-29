# Knowledge-result investigation

本文件规定候选知识单元、预期知识项、来源证据、评估记录和整体影响记录的操作分支。每个分支先给出操作卡片，再给出需要深入阅读的判断规则。

## 1. Extract candidate knowledge units

| Field | Operating rule |
|---|---|
| Trigger | A passage, table, figure, appendix or distributed argument expresses an understanding or organization of the research area. |
| Input | The actual PDF location, manuscript purpose and surrounding text. |
| Actions | Read the complete local argument; state the result, range and source locations; split only when support, status or scholarly effect can differ. |
| Output | Create or update one candidate knowledge unit with a stable K identifier. |
| Done when | The unit has concrete content, range, location and independent checking significance. |
| Do not conclude | A contribution statement, a single-study restatement or a list of references alone proves a knowledge increment. |

Read beyond the abstract and explicit contribution list. Inspect result analyses, thematic sections, tables, figures, discussion, conclusion and appendices. Extract:

- an overall synthesis when it has its own concrete scope and a reader can check it separately;
- the quantitative or qualitative patterns that support the overall synthesis;
- concept definitions and cross-study comparisons;
- distributions of methods, motivations, stakeholders, limitations or evaluation practices;
- scenario-dependent interpretations and boundary conditions;
- research directions and practical recommendations when they express a specific proposed understanding or organization.

A high-level result and its independently checkable supporting results can both be candidates. Link them through related knowledge IDs. Do not remove a lower-level result merely because it supports a higher-level result.

For every candidate, separately decide whether it is a **possible knowledge increment**. Set `possible_increment` only when the manuscript forms a concrete, scoped, independently checkable survey-level understanding or organization. Use `not_increment` for context-only material, an individual study restated without cross-study synthesis, or a list without an expressed relation or organizing rule. Use `unknown` only after a recorded check cannot resolve the distinction. This decision separates a review-level result from background material; it does not compare the result with prior surveys, validate its reasoning, or rate its value. Record those judgments under relative novelty, correctness and scholarly value.

Keep source facts in source evidence unless the survey turns them into a field-level understanding. A sentence such as “Study A reports X” is evidence for a synthesis; a statement such as “the field is dominated by method proposals” is a candidate result and requires its own evidence.

Record the manuscript wording before explaining it. Separate author text, source findings and reviewer reconstruction. Preserve qualifications, quantities, populations, dates and conditions. If two parts can change independently, split them; if splitting destroys the relation that makes the result meaningful, keep one compound unit and explain the relation.

After extraction, set knowledge relation and result form. This classification is descriptive and routes later checks; it does not establish quality.

## 2. Discover expected knowledge items

| Field | Operating rule |
|---|---|
| Trigger | The survey promise or field evidence gives a reader a concrete reason to expect another synthesis or organization. |
| Input | Survey title, abstract, declared scope/use, current candidate units and actual independent field material. |
| Actions | Form a specific expected result; record its route, trigger and rationale; apply the five screening conditions. |
| Output | Create or update one expected knowledge item with status pending, confirmed, rejected or insufficient. |
| Done when | The route has been investigated and the expectation is confirmed, rejected, insufficient or explicitly limited. |
| Do not conclude | A reader preference, a search failure or the existence of a related paper alone establishes an omission. |

### Ordinary-reader route

1. Read only the title and abstract.
2. List the problem, organization, findings and use the survey explicitly promises.
3. Formulate the concrete understanding a reader needs to interpret or use those promises.
4. Record the exact title/abstract trigger and create an expected knowledge item.
5. Search the full manuscript for an equivalent response later; do not decide omission from the abstract alone.

This route captures needs induced by the manuscript's own stated purpose. It does not require the reader to know every field dispute.

### Senior-reader route

1. Read the full manuscript and identify central candidate results, classifications, comparisons and recommendations.
2. Use cited work and adaptive external search to identify conditions, conflicts, alternative explanations or missing relations that could change those results.
3. State the concrete synthesis that would resolve the identified issue and explain how it fits the survey's scope and use.
4. Record the field passage or source relation that triggered the expectation. A role label or longer prompt is not evidence of senior expertise.
5. If no domain evidence and no concrete expected result can be given, keep the item pending or insufficient.

### Screening conditions

An expected item becomes confirmed only when all five conditions have an evidence-bounded answer:

1. **Specific result:** it is a concrete synthesis or organization, not “more depth”.
2. **Scope fit:** it belongs to the survey's declared range or actual coverage.
3. **Grounded trigger:** an ordinary-reader promise or a senior-reader field relation supports it.
4. **Scholarly use:** its absence would affect understanding, comparison, judgment or research selection.
5. **Feasible response:** literature available by the cutoff could support a survey response without requiring an unrelated new experiment.

If a necessary condition is unknown, keep rationality pending or insufficient. Do not convert an unresolved expectation into a weakness.

## 3. Check expected knowledge presence

| Field | Operating rule |
|---|---|
| Trigger | An expected knowledge item has been discovered and its rationale is ready for a full-paper check. |
| Input | The item, its trigger evidence, cutoff and a whole-paper search plan. |
| Actions | Search for equivalent answers across the manuscript; inspect definitions, tables, discussion, limitations and appendices; record partial answers and counterevidence. |
| Output | Update the item's rationality and presence independently; create or update an impact record only for an established effect. |
| Done when | Rationality and presence each have a reasoned state and the checked locations are recorded. |
| Do not conclude | An absent phrase is not an absent synthesis; an expected item is not an automatic penalty. |

Search for meaning, not a keyword. A distributed answer can satisfy an expectation if its relations and conditions are explicit enough for the target use. A citation alone may be background rather than synthesis; inspect its role.

Use these presence states:

- present: the expected result is supplied at the required scope;
- partial: a material component is missing but some useful answer exists;
- absent: the confirmed expectation has no adequate answer;
- unknown: relevant locations or evidence could not be inspected.

Only confirmed rationality combined with partial or absent presence can create a negative omission finding. Explain what remains valid and what reader use is affected.

## 4. Audit correctness and scientific reasoning

| Step | What to do | Do not infer directly |
|---|---|---|
| Reconstruct | Rebuild source facts, comparison conditions, inference and survey conclusion. | A reviewer reconstruction is not automatically the author's argument. |
| Verify | Check decisive source passages, definitions, quantities and conditions. | A title, abstract or citation cannot replace decisive evidence. |
| Test | Check viable counterexamples, competing explanations and author qualifications. | Do not manufacture opposition to create a weakness. |
| Adjudicate | Update the assessment record and propagate only established effects to related knowledge or expectations. | A qualified result does not automatically make the paper defective. |
| Assess impact | Decide what changes for overall understanding and scholarly use. | A local issue does not automatically lower overall quality. |

| Field | Operating rule |
|---|---|
| Trigger | A consequential candidate or expectation relies on a factual, comparative, causal, mechanistic or scope inference. |
| Input | The stated result, its premises, comparison conditions and plausible alternatives. |
| Actions | Reconstruct, verify, test, adjudicate and assess impact; record support and contrary evidence. |
| Output | One bounded assessment record and justified updates to affected records. |
| Done when | The inference is supported, qualified, invalid, misrepresented, or explicitly unresolved. |
| Do not conclude | A refuted challenge is not a weakness; an unresolved audit is not a negative fact. |

Use an assessment record even for confirmation. For each inference:

1. Separate explicit links, fair implicit reconstruction and unsupported jumps.
2. Read the decisive source version. If access fails, record the affected component as unknown.
3. Check comparability: population, data, metrics, baselines, resource accounting, intervention and scope as applicable.
4. State a rival explanation or counterexample only when a concrete fact or logical condition makes it plausible.
5. Inspect definitions, discussion, limitations, appendices, abstract and conclusion for author qualifications. A caveat repairs a strong claim only when it actually covers that claim.
6. Distinguish supported, qualified, invalid and unknown. Record whether a challenge was sustained, answered by an adequate qualification, investigated but unresolved, or refuted by evidence.
7. Propagate only the established result. Withdraw downstream effects when later evidence refutes the challenge.

An unconnected middle step may create a comprehension difficulty; it becomes a scientific concern only when the missing connection changes the stated result, scope or scholarly use.

## 5. Assess relative novelty

| Field | Operating rule |
|---|---|
| Trigger | A candidate is identified as a knowledge result and a comparison with prior understanding is needed. |
| Input | The candidate's exact output, its scope and identifiable pre-cutoff accounts. |
| Actions | Retrieve close prior accounts; compare actual synthesis, relations, conditions and guidance; record overlap and remaining difference. |
| Output | Update the candidate's novelty status and create an assessment record. |
| Done when | A source-grounded comparison exists, or bounded search limits leave the comparison unknown. |
| Do not conclude | Search failure does not prove novelty; topical overlap does not prove duplication. |

Compare the understanding, not just the title or taxonomy name. A result can add value through clarification, integration, correction or usable organization without presenting a new scientific discovery. Record prior match, partial overlap, no match within search or unknown. Each state must describe inspected accounts and bounded search limits.

If later evidence identifies a direct prior account, add the source evidence and reopen the novelty assessment. Keep the original cutoff and search history.

## 6. Assess scholarly value

| Field | Operating rule |
|---|---|
| Trigger | The candidate's actual output and correctness boundaries are understood enough to discuss use. |
| Input | What the candidate supplies, its conditions, survey scope and target use. |
| Actions | Name the output, identify a concrete scholarly use, test whether the output supports it, and weigh limitations and contrary evidence. |
| Output | Update value assessment and create or update impact when material value is established. |
| Done when | Output → use → reason → conditions is explicit, or value remains bounded unknown. |
| Do not conclude | Novelty, source count, candidate count or author confidence alone proves value. |

Use a specific output such as “distinguishes evidence for task performance from evidence for an internal mechanism”, rather than “comprehensive overview”. Then explain:

1. which reader understanding, comparison, judgment or research choice it supports;
2. why this result supports that use;
3. which conditions and limitations restrict the use;
4. whether the result remains useful when a dependent explanation is qualified;
5. whether the claim is reasoned potential utility, demonstrated use or expert consensus.

An independent user study is not required for every bounded value judgment. A broad impact claim requires stronger external support than a conditional use argument.

## 7. Connect findings to overall judgment

| Field | Operating rule |
|---|---|
| Trigger | Candidate and expected results have individual assessment records and may affect the overall review. |
| Input | Established and contrary evidence, unresolved limits, fixed task and rating scale. |
| Actions | Separate finding from impact; group common causes; inspect surviving support; weigh positive and negative material evidence. |
| Output | Nonduplicated impact records, review points and one prose overall rationale. |
| Done when | The rationale explains what changes for scholarly use and why the chosen category or qualitative judgment follows. |
| Do not conclude | Do not average labels, count records or convert an access issue directly into a penalty. |

For each impact:

1. State exactly what the evidence establishes and at what scope.
2. State which synthesis, conclusion, evidence base or scholarly use changes.
3. Record what remains valid.
4. Link repeated manifestations of one cause through overlaps.
5. Withdraw impacts whose underlying assessment is refuted.
6. Relate the balanced material findings to the fixed task and scale in prose.

Extent describes affected range; it does not encode severity. A confirmed error can have a local effect. A reliable positive result can have a main effect without being globally novel. Unknown may still permit a rating when the reviewer explains why it cannot change the selected category; an unknown that could change the category and has a feasible discriminating action remains pending.

## 8. General quality issues encountered during contribution work

When a numerical, source, consistency or writing issue appears, first test whether it changes a candidate's premise, synthesis, scope or scholarly use. If it does, attach the issue to the relevant evidence, assessment and impact. A minor typo that leaves the interpretation intact need not affect the overall judgment.

If a serious issue affects scholarly trust or use independently of a candidate, retain its source evidence and record an independent-quality impact with a direct factual and materiality argument. An untested suspicion stays in the agenda. Do not create a new candidate solely to house an unrelated general defect.
