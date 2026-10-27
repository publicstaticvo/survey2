# ReviewLog: definitions, states and operations

This file defines the persistent working state. Read it before creating records. The main workflow decides **when to act**; this file defines **what each record means and how to write it**. All commands use `python <skill>/scripts/review_cli.py`.

## Conventions

- A record is a revisable assessment, not a fact made true by its ID. References establish traceability; their semantic support still needs investigation.
- Create the record when its object becomes identifiable. Update the existing ID when evidence changes. K/X exact duplicates are rejected; semantic duplicates require reviewer inspection. There is no deletion or automatic semantic-merge command.
- Supply a UTF-8 JSON payload using a file-writing tool. `put <kind> --file <path>` creates the next ID when `id` is omitted; specifying an existing ID patches only supplied fields. Arbitrary IDs and unknown JSON fields are rejected. Omitted fields retain their values on update; a supplied list replaces that list.
- Required fields below mean required by the current model. "Assessment requirement" means additional semantic obligations of this procedure. Reference arrays default to `[]`, strings to `""` unless stated otherwise. Every record has an automatically assigned `id`.
- D/A/I routes/verdicts/statuses are already enumerated by the model. E statuses are checked by audit. **K/X states, centrality and S outcomes below are v2a vocabulary conventions; current code stores them as strings and does not fully enforce them.** Use these words in new runs; do not silently rewrite old runs.
- For an assessed dimension, `unchecked` means investigation not performed; a terminal `unknown` requires actual investigation that cannot settle the specified judgment. Record attempted actions, inspected evidence, the missing discriminating fact and why feasible further work stops. This does not redefine initialization defaults such as X.necessity=unknown or S.mode=unknown: those values alone never mean that an investigation was completed. Merely writing unknown is not completion. Unknown is neither zero quality nor necessarily immaterial to the overall judgment.

## K - Existing knowledge contribution

**Object:** one identifiable understanding supplied by the evaluated survey: a relation, distinction, classification, explanation, evidence assessment, research direction or useful integrated map. K describes the survey's output, not an isolated finding copied from a cited study or the reviewer's newly invented synthesis.

**Create when:** a located passage, table, figure or distributed argument indicates the contribution. A candidate can be recorded before verification. **Update when:** its interpretation, evidence, baseline, conditions or assessment changes. Split only if outputs have materially different support/use; keep common source dependencies explicit.

| Field | Type / default | Meaning and writing requirement |
|---|---|---|
| `statement` | required string | What understanding the manuscript supplies, including scope; avoid "excellent taxonomy" |
| `paper_locations` | required string array | Locations that actually express this synthesis; include pages/sections/tables |
| `baseline_or_prior` | string | Prior understanding/accounts actually compared; state not investigated before work, or explain bounded unknown after actual work |
| `evidence_ids` | E array | Source passages supporting identity and assessments; explain their roles in the reasons |
| `counter_evidence_ids` | E array | Contrary/qualifying passages; include the author's own relevant caveats |
| `dependencies` | K array | Contributions whose validity this contribution relies on, not every related topic |
| `centrality` | `unknown` | `main`: essential to the principal output; `supporting`: enables it; `peripheral`: limited local output; explain basis in `reason` |
| `correctness_status` | `unchecked` | Scientific/source and inferential validity; see states below |
| `increment_status` | `unchecked` | Relative added understanding against inspected prior accounts |
| `significance_status` | `unchecked` | Value for scholarly understanding/judgment/research; not citation popularity |
| `correctness_reason` | string | Facts, comparison conditions, inference and evidence; distinguish reconstruction from manuscript text |
| `increment_reason` | string | Specific prior comparison, added/duplicated understanding and search limits |
| `significance_reason` | string | Actual output -> scholarly use -> why useful -> conditions; distinguish potential from demonstrated benefit |
| `reason` | string | Identity, granularity/centrality rationale or shared context; does not replace the three reasons |
| `uncertainty` | string | Unverified portions and their possible effect |

| Assessment | Allowed v2a states | Meaning |
|---|---|---|
| Correctness | `unchecked`, `supported`, `qualified`, `unsupported`, `invalid`, `unknown` | Supported at the stated scope; supported only with specified conditions; insufficient manuscript support after checking; contradicted/invalidated by inspected evidence; or reviewer cannot settle it |
| Relative increment | `unchecked`, `substantial`, `moderate`, `limited`, `none_identified`, `unknown` | Qualitative extent of added understanding relative to named inspected accounts; `none_identified` requires an actual comparison, not failed retrieval |
| Value | `unchecked`, `high`, `meaningful`, `limited`, `none_identified`, `unknown` | Reasoned importance of the actual contribution for its scope/use, not a numerical score; weak/unsupported claims may still have potential but not established realized value |

Normal transition: `unchecked` -> evidence-based judgment or `unknown`; any judgment can be reopened when evidence changes. `qualified` does not by itself mean weakness: check whether the paper already states the conditions. `unsupported` describes an inspected support gap; use `unknown` if the reviewer could not inspect it.

## D - Discovery and screening of possible expectations

**Object:** one question investigated as a possible reasonable expectation, together with how it was discovered and screened. D records the discovery process and retains satisfied/rejected/limited outcomes. It is neither a missing contribution nor a criticism.

**Create when:** a manuscript promise/inference prerequisite or actual field investigation yields a question; also create a route-level record when investigation cannot proceed. Update the same D as screening/presence checks progress. A route-level limited/no-candidate D reports what was attempted, not an invented candidate.

| Field | Type / default | Meaning |
|---|---|---|
| `route` | required `manuscript` / `field` | From manuscript promises/prerequisites or independent topic evidence |
| `disposition` | required enum below | Current screening outcome |
| `reason` | required string | Why the outcome follows from evidence, scope, importance and feasibility |
| `question` | string | Concrete understanding the survey might owe, phrased as a question |
| `basis_evidence_ids` | E array | Actual origin evidence; source content and normative relevance are separate |
| `search_ids` | S array | Actual attempts that produced or limited discovery |
| `scope_and_use` | string | Why the question fits this survey and matters for scholarly use |
| `possible_synthesis` | string | Feasible synthesis of existing literature, not a demand for a new research project |
| `checked_locations` | string array | Manuscript locations checked for an existing/equivalent response |
| `uncertainty` | string | Unsettled source/necessity/presence/access issues |

| Disposition | Meaning / next action |
|---|---|
| `candidate` | Grounds, scope, importance and feasible response pass screening; create X to check the expectation, not to assert absence |
| `satisfied` | Manuscript provides an adequate response; cite locations and preserve contrary evidence |
| `optional` | Useful addition, but insufficient reason this survey owes it; suggestion rather than weakness |
| `out_of_scope` | Outside the survey's justified remit; explain the boundary |
| `insufficient` | Available grounds fail to establish the expectation or screening remains unsettled; no omission claim |
| `no_candidate` | Actual route investigation found no qualified candidate in the inspected scope; no exhaustive recall claim |
| `limited` | Access/budget/coverage prevented adequate discovery or screening; record actual attempts and the missing step |

There is no compulsory missing contribution. A candidate later found satisfied changes to `satisfied`; new evidence may revise any disposition. A fresh unscreened thought belongs in the run agenda until screening is actually attempted; do not use `insufficient` as a placeholder for unperformed screening. Insufficient is a completed negative/inconclusive screening outcome with actual grounds; limited is an investigated access/budget boundary. Neither automatically re-enters the agenda.

## X - Justified expected contribution

**Object:** a specific synthesis that this survey may reasonably be expected to supply, separately from whether it is present. X can end as satisfied; it does not mean defect. Create after D screening, and update rationality and presence independently.

| Field | Type / default | Meaning |
|---|---|---|
| `expectation` | required string | Concrete expected understanding, not "more depth" or a mandatory uncited paper |
| `origins` | required string array | v2a descriptive tags: `author_promise`, `inference_prerequisite`, `field_issue`, `reader_use`; tags, not record IDs |
| `basis_evidence_ids` | required E array by this protocol | Why the expectation arises; distinguish evidence of the issue from why this paper owes it |
| `scope` | required string | Topic/type/purpose boundaries making this expectation applicable |
| `discovery_ids` | D array | D records showing origin and screening |
| `necessity` | `unknown` | v2a: `required`, `useful_optional`, `out_of_scope`, `unknown` |
| `impact_hypothesis` | string | What important understanding/use might be lost; hypothesis until checked |
| `tier` | `exploratory` | `decision_relevant` only after necessity, presence and effect are established |
| `independence_reason` | string | Why grounds are credible and not merely the reviewer's preference or circular restatement |
| `search_ids` | S array | Discovery/presence/source searches relevant to the expectation |
| `evidence_ids` | E array | Passages supporting reasonable necessity or the assessed presence/absence |
| `counter_evidence_ids` | E array | Existing responses, caveats and evidence against necessity/absence |
| `presence_status` | `unchecked` | v2a: `unchecked`, `present`, `partial`, `absent`, `unknown` |
| `rationality_status` | `unchecked` | v2a: `unchecked`, `justified`, `optional`, `out_of_scope`, `unsupported`, `unknown` |
| `missing_status` | `unchecked` | v2a: `unchecked`, `confirmed`, `not_missing`, `unknown` |
| `checked_locations` | string array | Main text, tables/figures, limitations and appendices actually checked |
| `uncertainty` | string | Remaining scope/necessity/presence ambiguity |
| `next_question` | string | Next discriminating question while unsettled; empty when settled |

**Decision rule:** an omission may support a weakness only with `rationality_status=justified`, `necessity=required`, `presence_status=absent` (or a specified consequential gap in `partial`), `missing_status=confirmed`, `tier=decision_relevant`, a candidate D, whole-paper check and established negative I. For partial presence, "confirmed" means the exact unmet component is established; name the supplied part and remaining gap. Optional/out-of-scope/unsupported expectations remain exploratory and do not penalize quality.

At creation, necessity=unknown is an initial pending value while rationality/presence/missing assessments remain unchecked. After actual investigation, an unknown assessment must carry the attempted work and missing discriminator in uncertainty/next_question or linked step. Do not infer a terminal investigation outcome from the default necessity label.

All four screening questions are necessary for **the specific obligation being claimed**, but do not require certainty about every related detail. Unknown scope/obligation, material use, factual basis, feasible response, or presence blocks confirmation of that omission. Unknowns about a secondary mechanism, exact benefit magnitude or an optional example need not block a narrower established omission. State which prerequisite the uncertainty touches; restrict the claim accordingly rather than upgrading or rejecting the entire topic wholesale.

Transition: screened D -> exploratory X -> separate necessity/presence investigation -> decision-relevant X only if a material obligation and unmet part are verified. Satisfied X uses `present`/`not_missing`, with D changed to `satisfied`. New evidence can demote a previously accepted X; revise its I and review points too.

## A - Audit of an inference

**Object:** one consequential inferential unit for a K or X: what premises, comparison and reasoning warrant its conclusion. A can confirm a sound inference without inventing a challenge. It is not a general impression or the effect on overall quality.

**Create when:** a relevant inference is identified and needs checking; use `unresolved` if investigation is pending. Update that A as evidence is obtained. Each independent inference may have its own A; avoid a compulsory A per paragraph.

| Field | Type / default | Meaning |
|---|---|---|
| `target` | required string | Existing K/X ID being audited |
| `inference` | required string | Premises/comparison -> inferred conclusion; mark explicit text vs fair reconstruction |
| `author_response` | required string | Located caveats/responses; before checking write "Not yet checked," after a negative search state where checked |
| `investigation` | required string | Before work, `not_started:` plus pending action; after work, `performed:` plus actual reading, source checks, calculations/results. Never present a plan as completed work |
| `verdict` | required enum below | Current result |
| `reason` | required string | Why evidence licenses this verdict at the stated scope |
| `challenge` | string | Specific rival, counterexample or scope concern if one has grounds |
| `challenge_basis` | string | Observed fact or explicit logical reason making it plausible; required when challenge is nonempty |
| `evidence_ids` | E array | Passages inspected for the inference and finding |
| `counter_evidence_ids` | E array | Evidence against the current assessment, including contrary author qualifications |
| `search_ids` | S array | Actual external investigations |
| `uncertainty` | string | Remaining unverified premise/scope and possible consequences |

| Verdict | Meaning |
|---|---|
| `unresolved` | Investigation has not settled the inference; a question/limit, not a proved defect |
| `supported` | The specified inference is supported within its actual scope |
| `qualified` | Evidence supports a narrower/conditional conclusion; separately check how the paper expresses it |
| `misrepresented_source` | The survey's attribution or source description conflicts with inspected source text |
| `invalid_inference` | Identified premises/logic do not warrant the asserted conclusion; name the failing link |
| `hypothesis` | A plausible, clearly unestablished explanation; judge whether the paper appropriately labels it |
| `not_warranted` | The reviewer challenge has no adequate basis or is answered; do not carry it forward as a criticism |

`not_warranted` describes the challenge, not proof that all aspects of K are correct. A `qualified` result becomes a negative I only when the manuscript exceeds the support or loses a justified use. A correctly labeled hypothesis can be valuable without being a validated mechanism.

### Four outcomes for a previously raised challenge

| What happened | A update using existing enums | Downstream action |
|---|---|---|
| Challenge sustained by inspected evidence | invalid_inference/misrepresented_source, or qualified if the actual claim exceeds a supported condition; reason names the failing claim | Update K/X; create negative I only for established material effect, not merely a strong adjective |
| Manuscript qualification answers the challenge | not_warranted with reason `answered_by_author_qualification`; supported/hypothesis may be used for a separate sound inference, but do not leave the challenged allegation active | Record response locations; withdraw the specific allegation; no negative I from that allegation. Check stronger passages before claiming it was fully answered |
| Insufficient evidence to decide | unresolved, investigation performed with missing discriminator, attempts and stop/next-action reason | Keep question/limitation, not established weakness; I remains uncertain if effect depends on the unresolved fact |
| Counterevidence disproves the challenge | not_warranted with reason `refuted_by_counterevidence`, explicitly naming the earlier proposition rejected and contrary E | Preserve trajectory, retract that proposition, recompute affected K/X, mark dependent negative I withdrawn/uncertain, remove its decisive refs and final criticism |

Withdrawal does not delete audit history: preserve the former assessment and affected IDs in a timestamped input snapshot before overwriting them; after the canonical updates, the iteration step records the former assessment, new evidence, new verdict and affected IDs. Keep the original challenge text as a historical question in A but make its current rejection explicit; wording in the final review must follow the new verdict. Update all dependent records rather than merely adding a rebuttal note. See the outline-revision limitation below.

## I - Impact on contribution and overall judgment

**Object:** an evidence-backed account of what a finding changes about reliable understanding, scholarly use or an independent serious trust condition. I is neither a new evidence source nor a numerical weight or counterfactual repaired-paper score.

| Field | Type / default | Meaning |
|---|---|---|
| `finding` | required string | The actual positive/negative finding, not "K1 is important" |
| `evidence_refs` | required ID array | E/A/K/X and other existing records providing its support; include the actual audit where applicable |
| `direction` | required enum below | How the finding changes the assessment |
| `extent` | required enum below | What part of the survey is affected; not severity |
| `reason` | required string | Evidence -> affected understanding/conditions -> use/importance; what remains valid |
| `target_refs` | K/X array | Contributions/expectations materially affected |
| `scholarly_use` | string | Specific understanding, judgment or research use at issue |
| `independent_quality` | string | Serious trust/use issue without a forced K/X link, if actually encountered |
| `counter_evidence_ids` | E array | Evidence limiting or reversing this impact |
| `overlaps` | I array | Other effects sharing an underlying cause; avoid double counting |
| `status` | `uncertain` / `established` | Reviewer judgment supported by sufficient evidence, not empirical causal proof |
| `uncertainty` | string | Unsettled magnitude/scope, dependencies or access limits |

Directions: `supports` confirms reliable usefulness; `enhances` establishes additional value beyond the initial assessment; `qualifies` narrows conditions while preserving a contribution; `weakens` undermines an important component/use; `blocks` makes the specified conclusion/use unreliable or unavailable; `unknown` means effect unresolved. `qualifies` can describe a sound boundary, not an automatic penalty.

Extent: `local` affects one bounded part; `main` affects a principal contribution; `distributed` affects several parts or a shared dependency; `unknown` is unsettled. A main effect need not be fatal, and distributed is not automatically worse.

Transition: `uncertain` -> `established` after facts, link, conditions and counterevidence are checked. Revise/demote if a premise changes. Only established findings with non-unknown direction can decide the overall judgment. An unresolved A cannot become established impact merely through paraphrase.

Three questions must remain separate: **fact state** (E/A/X: what is established), **material severity** (I.reason: what reliability/use is lost or gained and how much remains), and **rating effect** (overall rationale: how all material reasons jointly fit the selected rubric). Extent is affected scope, not severity. Write severity in prose in I.reason using the actual consequence - bounded correction, loss of a comparison, failure of a central inference - rather than inventing a numeric field/weight. I is established by a justified link to a central conclusion, important synthesis/evidence or obtainable understanding; "K is novel, therefore high overall quality" is not such a link. Several I from one root may describe distinct effects, but the overall reasoning counts the common root once and explains any additional distinct loss/benefit.

## E - Source evidence

**Object:** a located contiguous passage actually inspected in the evaluated paper or an external source. It records what the source says, not whether the reviewer agrees with it.

| Field | Type / default | Meaning |
|---|---|---|
| `location` | required string | PDF page plus section/table/equation; webpage section or stable passage locator |
| `excerpt` | required string | Exact contiguous excerpt; put paraphrase/reasoning in analytical records |
| `purpose` | required string | What this passage establishes or challenges; not generic "support review" |
| `kind` | `paper` | `paper` for evaluated manuscript; `external` for other sources |
| `title` | string | Source identity |
| `authors` | string array | Available source authors; do not invent missing metadata |
| `doi` | string | DOI when present |
| `url` | string | Actual inspected source URL; required for verified external evidence |
| `version` | string | Exact inspected external version; required when verified external |
| `available_date` | date / null | Date this substantive version was available, ISO YYYY-MM-DD |
| `date_basis` | string | How version availability was established |
| `status` | `partial` | Status below; verified eligibility is also checked by audit |
| `search_ids` | S array | Retrieval provenance where applicable |
| `accessed_at` | string | Actual access time; CLI supplies current UTC when absent |

States: `partial` means incomplete identity/version/text/verification; `verified` means inspected passage and required eligibility are established; `not_accessible` means the source could not be read; `provider_error` means tool/provider failure; `excluded` means inadmissible version/date or otherwise excluded, with reason in `purpose`. Failed-source E may have an empty excerpt and access locator, but cannot ground a substantive final finding.

Paper verified excerpts must match paper.md ignoring whitespace; a claimed page is checked against page markers. Inspect extraction problems in the original PDF and keep the record partial rather than fabricating a matching quote. External verified E needs URL, version, location, excerpt, date basis and available_date <= cutoff. A metadata page can verify metadata only; use source text for scientific claims. Verified means admissible evidence, not that its conclusion is scientifically true or that it supports every attached judgment.

Keep partial/excluded E in the working log for retrieval limits. Do not leave an ineligible E in the support/counterevidence dependency chain of a final substantive point: the current validator follows those links and will reject the export. Represent the remaining limit in uncertainty/limitations; preserve the unsuccessful E/S in the working log. If that source is necessary to decide a claim, keep the claim unresolved rather than removing the link and pretending adequate support exists.

## S - Search or access attempt

**Object:** one external retrieval action, or tightly connected search/open chain with the same question and outcome. Record the actual query and results after acting; split actions if outcomes/provenance differ.

| Field | Type / default | Meaning |
|---|---|---|
| `query` | required string | Actual query, URL request or source lookup; no retrospectively invented search |
| `query_target` | required string | Which uncertainty this action was intended to resolve |
| `tool` | required string | Tool/provider actually used |
| `status` | required string | v2a: `success`, `partial`, `no_results`, `failed` |
| `mode` | `unknown` | v2a: `live`, `cache`, `unknown`; cache does not count as new live access |
| `urls` | string array | Returned/visited URLs relevant to the action |
| `failure_reason` | string | Actual failure or unresolved retrieval limitation |
| `executed_at` | string | Actual attempt time; CLI supplies current UTC if absent |

Success means retrieval succeeded, not that K/X/A was verified. `no_results` means a functioning search returned no useful result, not that the literature lacks it. `failed` means action/tool access failed, including denial before execution; state which. An attempt has no investigative lifecycle: a retry is a new S. Correct an incorrectly recorded outcome rather than rewriting history as a successful retry.

## Record lifecycle and permission to criticize

The definitions and fields above are complemented by this lifecycle table. "Closed" means removed from the active agenda for the current scope/budget, not scientifically proved or permanently immutable. Reopen only on new evidence, changed access/scope, or a specific discovered omission in the previous investigation. Rejected records remain available for audit and do not become recurring tasks.

| Record | Create / update trigger | Closing condition / permitted transition | May it support criticism by itself? / relationship |
|---|---|---|---|
| K | Located candidate synthesis; update when its identity, premises or assessments change | Each relevant dimension moves unchecked -> evidence-based result or justified unknown. If the candidate proves reviewer-invented, revise its statement/reason as rejected candidate, explain in step and close its agenda item, remove from final contribution claims; do not assert the paper has it | No: a low label is not evidence or impact. E/A establish the relevant defect, I establishes its material significance |
| D | A real discovery question or route attempt; update screening or coverage from actual work | Candidate -> X investigation (no duplicate screening task); satisfied/optional/out_of_scope/insufficient/no_candidate close after reasons; limited closes the blocked investigation after actual attempts. Unperformed screening stays pending in the run agenda, not a closed D | No: records the source and screening, not demonstrated obligation/absence; justified candidate can ground X |
| X | Candidate D establishes a concrete reasonable expectation; update rationality/presence separately | Unchecked components -> justified/present/partial/absent or justified unknown; rejected necessity closes without searching for every absent detail. Confirmed unmet necessary component may become decision_relevant; satisfied -> not_missing and D satisfied | Only as the omission finding after the stated necessity/presence gates; negative overall weight additionally needs I. X alone is never an automatic penalty |
| A | Consequential inference identified; update after evidence, author response or counterevidence | Not-started unresolved -> actual audit; settled verdict closes that inference. Investigated unresolved can pause only with actual limits/conflict and a stopping reason. Four challenge outcomes and their updates are specified below | An evidenced A can substantiate a bounded scientific criticism; its global importance is a separate I judgment. Unresolved or withdrawn challenge cannot substantiate weakness |
| I | An evidenced finding may change reliable synthesis/use; update when support, scope or overlap changes | Uncertain -> established when link is justified; may close uncertain after a bounded inconclusive investigation, with no decisive weight. Refuted premise -> uncertain + withdrawn reason, removed from decisive refs | Can express material impact only with eligible underlying records and reasoning; repeats of K or severity words are insufficient |
| E | A passage/source inspection; update missing verification details, not source history | Partial -> verified after required checks, or excluded/not_accessible/provider_error with actual reason. A changed source version is a new E, not replacement of old excerpt | No: excerpt is a factual premise, not a normative defect or quality weight. A demonstrated text contradiction still needs the inference stated |
| S | Actual external search/access attempt; correct recording errors only | The attempt ends success/partial/no_results/failed with outcome. Retry is new S; planned searches remain agenda items, not S | No: source discovery or failed retrieval does not prove correctness, novelty, obligation or absence |

### Action table for unsettled and closed work

| Observed state / condition | Next action | Completion condition | Allowed update / active agenda |
|---|---|---|---|
| K dimension unchecked | Run the matching correctness, increment or value branch | Discriminating evidence considered or actual access/budget limit identified | Assessed value or justified unknown; other unchecked dimensions remain pending |
| A unresolved, investigation not started | Identify the premise/alternative and inspect planned manuscript/source locations | At least the relevant inference and its evidence were actually examined | Resolved verdict or investigated unresolved; still active if a feasible next test remains |
| A unresolved, inspected evidence insufficient | Name missing fact, try a feasible alternative retrieval/inspection | Retrieval attempts and stop reason documented | Remains unresolved with evidence_limited reason; close/park only if no productive current action, reopen on changed access/evidence |
| A unresolved, evidence conflicts | Compare definitions/conditions/versions; target the observation that distinguishes accounts | Conflict resolved or its unresolved discriminator and investigation bounds recorded | Settled verdict, or conflict_unresolved with explicit parked reason; no negative factual conclusion from conflict alone |
| D candidate, X not created | Create X with screening grounds | X ID exists with pending presence/necessity work | Keep D candidate as provenance, queue X once |
| D rejected/satisfied/no_candidate after screening | No further action without a reopening trigger | Outcome and actual grounds/coverage recorded | Closed; retention is not a pending task |
| D limited after actual attempt | Report failed route and substantive consequence | S/step or other actual access evidence plus missing stage recorded | Closed as limited for this run; retry only on a stated new opportunity |
| X key necessity/presence unchecked | Investigate the missing prerequisite, not arbitrary extra detail | Gates below satisfied, rejected or genuinely unresolvable | Relevant states change; incidental uncertainty may remain without blocking |
| I uncertain | Test factual support separately from the impact link | Effect justified, withdrawn, or bounded investigation inconclusive | Established, or close uncertain with explicit reason; no decisive use while uncertain |
| Assessed unknown without actual actions/reason | Restore an unfinished assessment-status component to unchecked; if the field has no unchecked value, retain its default unknown and an explicit pending action | Evidence is investigated rather than merely relabeled | Pending, not closed unknown |
| Assessed unknown with actual actions, but a clear untried feasible discriminator | Add that specific next action | Test performed or actual constraint established | Remains pending; unknown wording does not excuse stopping early |
| Assessed unknown with documented bounded search and no productive current test | Preserve reason and possible overall effect | Actual work and limit auditable | Closed for this run, not automatically repeated; reopen only with new basis |

These process distinctions use existing `investigation`, `reason`, `uncertainty`, `next_question`, the run agenda and step text. They are not new CLI fields or verdict enums. For A, begin `investigation` with `not_started:` before work, or `performed:` plus actual actions afterward; explain `evidence_limited` or `conflict_unresolved` in uncertainty when relevant. Put a pending next action or a parked stop reason there. The method does not pretend that unknown proves sufficient scholarly inquiry.


## Choosing the right type

| What you have | Use | Boundary |
|---|---|---|
| "Authors say this method family improves efficiency" | E for the quoted assertion; K if synthesis, otherwise its role in an existing K/A | Author wording is not proof; no standalone local-claim class |
| "Does the cost table include training?" | Existing K/A uncertainty and next action; run agenda if not yet attached | Local uncertainty, not an established weakness |
| "This synthesis relates method families to evidence quality" | K | Must be supplied by the paper, not completed by reviewer |
| "Field sources expose a potentially important unresolved comparison" | D | Screen before expecting this survey to supply it |
| "This promised comparison reasonably requires compatible cost definitions" | X after candidate D | Reasonable obligation and presence investigated separately |
| "Compared studies count incompatible resources" | E passages + A | Inference result; still explain scope and author's response |
| "This prevents a general efficiency ranking but preserves the taxonomy" | I | Impact on understanding/use, not an independent data point |
| Search produced sources / hit network denial | S | Retrieval record, not scientific support |
| Exact inspected source passage | E | Quote/locator, not a judgment |
| Reading plan, coverage or an unscreened lead | Run metadata below | Execution information without evidence IDs; never an independent criticism |

## Run metadata and history: not additional review records

New v2a work uses exactly K/X/D/A/I/E/S as its review-record taxonomy. Maintain one small `inputs/run_context.md` with the host's file-edit tool for execution information that is not itself a review finding. The current CLI does not create, load, validate or render this file. Read it alongside `show`, update affected rows after each iteration, and preserve actual completed actions in the existing step files.

| Section in run_context.md | Minimal content | Update / closure |
|---|---|---|
| Task | Requested evaluation objective and scale or qualitative task; manuscript topic/type/scope/use; actual budget and prior-review exposure | Fix at initialization; record any explicit scope change. Cutoff/version remain authoritative in review_log.context, not a second editable date here |
| Coverage | Location; `not_visited`, `visited_processed` or `unavailable`; substantive content processed; assessment consequence or why none; related record IDs; actual limit | After actual reading/access. Unread stays not_visited; unavailable states attempted route and possible judgment effect. Neither counts as completed coverage |
| Agenda | Question or discovery route; existing target IDs if any; next action; pending/parked/closed; actual reason and reopening trigger if parked | Merge semantically repeated questions. If a target is identifiable, use its existing fields as canonical and retain only the action pointer here. On promotion to K/D/A or closure, record the outcome/IDs and stop requeuing |
| Access/trace limits | Actual tools/budget bounds and any available host-trace producer, session, format/path; known missing traces | Update from actual access events; raw host events remain separate from agent-reported steps |

These rows receive no new record prefix or citable finding ID. They organize work and disclose limits; final substantive strengths/weaknesses still require evidence-backed records among the seven. A source assertion belongs in E and its role in K/A; an attached question belongs in the target's uncertainty/next action. An established independent trust/use issue can use E and I.independent_quality without manufacturing K; an untested suspicion remains an agenda item.

The final review's `questions` section is an output section; use its `evidence_refs` to link the relevant records among the seven.

## Operating the log

### Initialize, context and view

```text
python <skill>/scripts/review_cli.py init "<paper.pdf>" --publication-date YYYY-MM-DD --date-basis "Actual basis" --conference iclr
python <skill>/scripts/review_cli.py --dir <run> context --file <run>/inputs/context_new.json
python <skill>/scripts/review_cli.py --dir <run> show --detailed
```

Context payload fields: `publication_date`, `date_basis`, `version`, `date_uncertainty`. Init also records original path/hash and extracted-text hash. Record evaluation scope, proxy scale if any and budget in `inputs/run_context.md`; there is no dedicated task-config command.

### Create or update the seven records

```text
python <skill>/scripts/review_cli.py --dir <run> put evidence --file <run>/inputs/evidence_new.json
python <skill>/scripts/review_cli.py --dir <run> put search --file <run>/inputs/search_new.json
python <skill>/scripts/review_cli.py --dir <run> put contribution --file <run>/inputs/contribution_new.json
python <skill>/scripts/review_cli.py --dir <run> put discovery --file <run>/inputs/discovery_new.json
python <skill>/scripts/review_cli.py --dir <run> put expectation --file <run>/inputs/expectation_new.json
python <skill>/scripts/review_cli.py --dir <run> put audit --file <run>/inputs/audit_new.json
python <skill>/scripts/review_cli.py --dir <run> put impact --file <run>/inputs/impact_new.json
```

Use the returned actual ID for subsequent references. Payload names may use their assigned IDs after creation. Reusing a `_new` payload file is allowed only after its content has actually been replaced with the next operation; preserve useful provenance when practical. Use `inputs/<kind>_<ID>.json` for patches.

Minimal candidate K payload (not final assessment):

```json
{"statement":"The survey organizes methods by their execution mechanism and relates each family to available evidence","paper_locations":["Section 3, pp. 5-7","Fig. 2"],"correctness_status":"unchecked","increment_status":"unchecked","significance_status":"unchecked","centrality":"main","reason":"The introduction identifies this organization as a principal output"}
```

Unresolved A payload, assuming K1 exists:

```json
{"target":"K1","inference":"The proposed organizing dimensions support the manuscript's stated comparison","author_response":"Not yet checked; inspect definitions, examples and limitations","investigation":"not_started: inspect the definition, examples and claimed use","verdict":"unresolved","reason":"Need to verify what the taxonomy claims before challenging overlaps"}
```

Patch after actual investigation (illustrative IDs must already exist; replace prose with actual evidence):

```json
{"id":"A1","evidence_ids":["E1","E2"],"author_response":"The taxonomy is explicitly complementary, not disjoint","investigation":"performed: read taxonomy definition, examples, table and limitations; found no exclusivity claim or demonstrated assignment conflict","verdict":"not_warranted","reason":"refuted_by_counterevidence: the challenge assumed exclusivity, whereas the inspected definition states complementary categories; no separate assignment conflict was established","uncertainty":"Other mapping errors were not exhaustively checked"}
```

This rejects the specific challenge. It does not by itself establish high value or global correctness for K1. No negative I follows merely from the rejected overlap objection.

### Payload shapes for the remaining types

The following are **syntax templates, not research evidence**. Replace bracketed values with actual inspected content, dates and URLs, and replace IDs with those returned in your run. Referenced records must already exist. Never persist these placeholders as verified findings. K and A shapes are illustrated above.

E, manuscript passage:

```json
{"kind":"paper","location":"p. 5, Section 3, Table 2","excerpt":"[Exact contiguous text actually inspected]","purpose":"[Which premise this establishes]","status":"partial"}
```

S, an actual unsuccessful attempt:

```json
{"query":"[Actual query or requested URL]","query_target":"[Question being investigated]","tool":"[Tool actually called]","mode":"live","status":"failed","urls":[],"failure_reason":"[Actual tool failure or denial]"}
```

D, a screened manuscript candidate:

```json
{"route":"manuscript","question":"[Concrete synthesis required by the located promise]","basis_evidence_ids":["E1"],"search_ids":[],"scope_and_use":"[Scope and material use]","possible_synthesis":"[Feasible response from available studies]","disposition":"candidate","reason":"[Why all four screening questions pass]","checked_locations":[],"uncertainty":"Presence not yet checked"}
```

X, created from that candidate but not yet an omission:

```json
{"expectation":"[Concrete expected understanding]","origins":["author_promise"],"basis_evidence_ids":["E1"],"scope":"[Justified survey remit]","discovery_ids":["D1"],"necessity":"required","independence_reason":"[Why the obligation is grounded rather than a preference]","tier":"exploratory","rationality_status":"justified","presence_status":"unchecked","missing_status":"unchecked","next_question":"Where does the manuscript supply an equivalent response?"}
```

I, only after finding and effect are checked:

```json
{"finding":"[Established positive or negative finding]","target_refs":["K1"],"evidence_refs":["A1","E1"],"scholarly_use":"[Specific use]","direction":"qualifies","extent":"main","reason":"[What changes about the contribution and why; what remains valid]","status":"established","overlaps":[],"uncertainty":"[Remaining bounded uncertainty]"}
```

For the I template, A1 must actually establish the stated qualification. The earlier `not_warranted` A example would not justify inventing such a negative effect; examples are alternative payload shapes, not an automatically valid chain.

### Run control and investigation trajectory

Create/update `inputs/run_context.md` with the host's file-edit tool using the sections above. No new CLI command is implied. After actual investigation and record updates, write the step:

```text
python <skill>/scripts/review_cli.py --dir <run> step --target "K1,A1" --why "Why this is next" --action "Actual inspected locations/tools" --found "Observed evidence and remaining uncertainty" --ops "put evidence E1; put audit A1"
```

Use `Section 3` for manuscript sections, not S (which also names search records). `Table 2`, `Fig. 3` and PDF page numbers are explicit locators. `step` is mandatory in this v2a procedure after each actual investigation, although optional in the inherited CLI.

### Review points and overall judgment

Point payload:

```json
{"text":"A specific finding, its manuscript location and why it matters","evidence_refs":["I1"]}
```

```text
python <skill>/scripts/review_cli.py --dir <run> point --section strengths --file <run>/inputs/point_new.json
```

Other sections: `weaknesses`, `questions`, `comments`. `point` appends; it does not update an earlier point. Draft only after investigation, and check for duplicates before adding. Place IDs in reference fields, not as handwritten evidence tags in text.

#### Outline-revision limitation

The inherited `point` and list-section `outline` commands append; updating A/I does **not** revise their old outline wording, and `finalize` is not a semantic withdrawal operation. Do not append a rebuttal while retaining the obsolete weakness. Normally finish adjudication before drafting points. If subsequent evidence reopens an already drafted finding:

1. Preserve the former verdict, affected A/K/X/I and outline text in an input snapshot before updating; update the canonical finding and its dependent impacts through existing `put` operations. Record the completed changes in the subsequent step, following the normal loop order.
2. Use the host's structured file-edit capability for this narrow maintenance case: read `review_log.json`, locate the exact obsolete item under `review_outline.strengths`, `weaknesses`, `questions` or `comments`, and save its before/after text and references, affected section/index, reason and time in `inputs/outline_revision_<unique-id>.json`. Preserve all unrelated fields/items and IDs. Then remove or replace that exact list item. This is an explicit file edit, **not an existing CLI replace/remove command**, and not permission to reconstruct the whole log. Do not edit the rendered review as the source of truth.
3. Reassess the overall reason/refs/scale reason using `judgment`, update the summary/score if their reasons changed, and record the maintenance operation in a new step. If a prior score can no longer be defended, explicitly set `review_outline.overall_score` to JSON null in the same tracked file edit; do not substitute an empty string or zero.
4. Reload through `show`, run `audit`, inspect the final reference chain and render again with `finalize`. Check that no withdrawn premise survives through another point or the overall reason. Old exported text is obsolete until regenerated.

A future minimal CLI replace/remove operation should encapsulate this tracked edit; it is a code change to implement, not a capability claimed by this proposal. Archive the before/after correction rather than deleting the evidence of the reviewer's mistake.

Judgment payload:

```json
{"reason":"Reliable contributions; decisive limits and why they matter; remaining value; dependencies and overlap; uncertainty","refs":["I1","I2"],"scale_reason":"Why the requested category fits relative to adjacent categories, or qualitative task with no numerical scale","limitations":"Actual access, coverage and unresolved judgment limits; if no score, explain whether qualitative task or inability to decide"}
```

```text
python <skill>/scripts/review_cli.py --dir <run> judgment --file <run>/inputs/judgment_new.json
python <skill>/scripts/review_cli.py --dir <run> outline --section summary --content "What understanding this survey provides"
python <skill>/scripts/review_cli.py --dir <run> outline --section overall_score --content 6
python <skill>/scripts/review_cli.py --dir <run> audit
python <skill>/scripts/review_cli.py --dir <run> finalize
```

The score command is optional and shown only for a task using that valid category. Supported interfaces are currently iclr/icml/neurips/acl/emnlp; use inherited `set_conference <name>` to inspect labels. These are bundled interfaces, not a claim that their labels match every historical review form. Existing structural checks may require an inability-to-judge/limitations explanation when no score is set; explicitly identify a requested qualitative task rather than inventing uncertainty.

### Files and completion

Final names: `review.md`, `audit_summary.md`; working files: `paper.md`, `input_manifest.json`, `review_log.json`, `steps.jsonl`, `steps.md`, `inputs/` and `sources/`. Every new run folder is `review_<full input stem>`; alternate parents separate repeats. Do not rename final review or alter the input text to make excerpts pass.

Run control metadata is fixed at `inputs/run_context.md`; it is maintained by the host file tool, with the four sections above, and is not another final review or CLI record payload.

`steps.jsonl` is the agent's reported investigation sequence. If the host can export raw tool events, retain them separately under `inputs/host_trace_<unique-id>.<format>` or reference their actual external path. Record producer, run/session identity, format and availability in `inputs/run_context.md`. Do not fabricate missing host traces or present an agent-authored step as a host-confirmed action. Coverage metadata and steps report what was processed; their existence alone does not independently demonstrate execution, understanding or correct assessment.

Audit validates IDs, basic structural completion, date eligibility and excerpt matching. It does not establish scientific correctness, expectation necessity, value, search recall or successful adherence to the investigation loop. Manually apply the workflow exit conditions and inspect rendered evidence links. The full log retains exploratory/rejected material; final review cites only the findings it actually uses.

