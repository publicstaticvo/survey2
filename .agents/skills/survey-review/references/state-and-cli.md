# ReviewLog：记录定义、状态与命令

## 1. 记录对象

先理解记录对象，再使用短名称。短名称只用于 JSON 的记录编号和命令实现。

### 候选知识单元（K）

记录综述正文实际表达的一项关于领域的理解或组织结果。K 是抽取时创建的候选，创建时不假设它正确、新颖或有价值。

必需字段：

| 字段 | 内容 |
|---|---|
| statement | 忠实复述综述形成的具体认识 |
| scope | 适用对象、条件和边界 |
| paper_locations | PDF 页码、章节、表格、图或附录位置 |
| result_form | synthesis、organization、both |
| knowledge_relation | background、single_source_summary、review_synthesis、unresolved |
| extraction_reason | 为什么它满足具体内容、范围出处和独立检查意义 |
| increment_identification_status | 候选是否构成可能的知识增量 |
| correctness_status | 正确性状态 |
| novelty_status | 相对新颖性状态 |
| value_status | 学术价值状态 |
| evidence_refs | 已创建的来源证据编号 |
| assessment_refs | 已创建的评估记录编号 |
| promise_refs | 关联的作者承诺位置，可为空 |
| related_knowledge_ids | 支撑或依赖的其他 K，可为空 |

**知识增量识别只回答一个窄问题：这项候选是否确实表达了具体、有限定、可单独检查的综述层面认识或组织结果，因而可能构成知识增量？**

该判断排除只承担背景说明的内容、单篇研究结果的转述，以及没有形成跨研究关系或组织规则的文献清单。它不评判候选是否正确，不比较其他综述是否已有同一结果，也不评判其学术价值。前者由正确性评估处理；与截止点前综述或研究的实质比较由相对新颖性评估处理；价值另行评估。因此，“可能构成知识增量”不等于正确、新颖、有价值三者的合并评分。

`knowledge_relation` 描述候选在当前稿件中的内容角色：`background` 表示用于交代背景；`single_source_summary` 表示主要转述单篇来源；`review_synthesis` 表示稿件形成了跨研究认识或组织结果；`unresolved` 表示依据尚不足以分类。该字段只是抽取分类，不代替知识增量识别状态，也不判断外部文献中是否已有相同结果。

| 状态 | 含义 |
|---|---|
| unchecked | 尚未检查是否确实形成候选知识增量 |
| possible_increment | 稿件形成了可单独检查的综述层面认识或组织结果；可能构成知识增量，但不代表正确、新颖或有价值 |
| not_increment | 证据表明它只是背景、单篇研究转述、未形成综合关系的文献清单或其他非综述层面结果 |
| unknown | 已调查但仍不能区分是否形成知识增量，并记录调查边界 |

正确性使用 unchecked、supported、qualified、invalid、unknown。相对新颖性使用 unchecked、prior_match、partial_overlap、no_match_within_search、unknown。价值使用 unchecked、meaningful、limited、not_established、unknown。后续证据可以重新打开任何已判断状态，旧状态和变更理由保留在 revision history 中。

### 预期知识项（X）

记录目标读者有依据期待综述提供的一项具体综合认识或组织结果。它与 K 使用同一候选生命周期：发现时创建一条记录，随后更新合理性和正文覆盖状态；不再设置一个独立的发现候选记录类型。

必需字段：

| 字段 | 内容 |
|---|---|
| expectation | 具体预期结果，不能写成“需要更多讨论” |
| route | ordinary_reader 或 senior_reader |
| trigger_locations | 标题、摘要、正文 K、作者承诺或外部资料位置 |
| trigger_reason | 为什么触发这项预期 |
| scope | 预期结果所属的综述范围 |
| scholarly_use | 缺少或提供该结果会影响什么理解、比较、判断或研究选择 |
| rationale | 支持预期具有内容责任的理由 |
| feasible_response | 截止点前资料如何支持综述回应 |
| rationality_status | pending、confirmed、rejected、insufficient |
| presence_status | unchecked、present、partial、absent、unknown |
| evidence_refs | 支撑触发、合理性或正文覆盖的来源证据 |
| search_refs | 相关检索事件 |
| related_knowledge_ids | 受该期待影响或用于检查的 K |

只有 rationality_status=confirmed 且 presence_status=absent 或 partial，才允许形成遗漏型 weakness。X 本身不代表论文存在缺陷。

### 来源证据（E）

记录实际查看过的论文内或外部来源材料。E 只能引用实际访问的版本和位置；搜索摘要只能支持身份发现，不能代替决定性正文证据。

字段：

| 字段 | 内容 |
|---|---|
| source_type | manuscript、paper、dataset、web_page 或其他实际类型 |
| source_identity | 标题、作者、标识符或输入文件 |
| version_date | 具体版本及可用日期 |
| location | 页码、章节、表格、图、段落或网页定位 |
| excerpt | 实际摘录或忠实概述 |
| role | support、counter、limit 或 context |
| evaluation_role | increment、correctness、novelty、value、expectation、impact |
| target_refs | 支持或限制的 K、X 或评估记录 |
| accessed_at | 实际访问时间 |
| cutoff_eligible | 是否满足评价截止点；未知时写 unknown |

### 评估记录（A）

A 是 Assessment 的简称，表示对一项 K 或 X 的一个维度作出的评估记录。A 不是搜索行为，不是所有中间推理步骤的容器，也不是整体影响记录。

字段：

| 字段 | 内容 |
|---|---|
| target_id | K 或 X 的编号 |
| dimension | increment_identification、correctness、novelty、value、rationality 或 presence |
| question | 当前要裁决的具体问题 |
| status | 该维度允许的结论状态 |
| reason | 从来源证据到结论的完整说明 |
| evidence_refs | 支持、限制和反驳证据编号 |
| counter_evidence_refs | 主动检查的相反证据编号 |
| unresolved | 尚未解决的替代解释、缺失步骤或访问限制 |
| cutoff | 使用的评价截止点 |

未调查使用 unchecked。已调查但不能裁决使用 unknown，并且必须有实际 E、S 或失败记录。新证据改变结论时更新同一评估目标并保留历史。

### 整体影响记录（I）

I 是 Impact 的简称，记录已经核实的发现对综述知识用途和整体判断的影响。I 不重新裁决 K 或 X。

字段：

| 字段 | 内容 |
|---|---|
| finding | 已核实的具体发现 |
| target_refs | 受影响的 K、X 或 A |
| evidence_refs | 证明发现和影响的证据 |
| direction | supports、qualifies、limits 或 harms |
| extent | local、supporting、main 或 independent_quality |
| effect | 对理解、比较、判断或研究使用的具体影响 |
| reason | 证据 → 前提/推理改变 → 学术使用改变 |
| status | established、uncertain 或 withdrawn |
| overlaps | 共同根因或重复表现的 I 编号 |
| uncertainty | 仍可能改变影响判断的未知事项 |

extent 只描述影响范围，不代表严重程度。多个表现来自同一根因时，通过 overlaps 关联并在整体理由中合并说明。

### 检索事件（S）

S 是 Search 的简称，记录实际执行的外部搜索或访问尝试。S 不是来源证据；命中并实际查看的材料必须另建 E。

字段：

| 字段 | 内容 |
|---|---|
| target_question | 本次检索要裁决的问题 |
| query | 实际使用的查询或 URL |
| tool | 实际使用的搜索或访问工具 |
| status | success、no_results、partial、failed |
| result_urls | 实际返回或访问的链接 |
| checked_source_refs | 实际查看后创建的 E 编号 |
| failure_reason | 失败、限制或无结果原因 |
| searched_at | 实际时间 |

没有结果不等于不存在前作或不存在预期知识。S 只说明搜索范围和执行结果。

## 2. 记录生命周期

所有记录都遵守以下生命周期：

1. **创建：**对象已经能够用具体内容和位置描述时创建。
2. **调查：**列出待裁决的问题和证据计划。
3. **更新：**实际查看材料后更新同一编号；新证据不覆盖旧历史。
4. **终结：**写入支持、拒绝、部分支持、未知或跳过理由。
5. **重新打开：**只有新证据、依赖变化或状态冲突才重新打开；无新触发时不重复调查。

CLI 不删除记录，不自动合并语义相近记录，不把未知字段当成已完成。

## 3. 状态与动作表

| 对象 | 当前状态 | 允许动作 | 完成条件 |
|---|---|---|---|
| 候选知识单元 | 新建或 unchecked | add_knowledge；update_knowledge；为每个维度运行 assess | 内容、范围、出处、拆分理由已记录；知识增量识别有结论，其他必评维度有结论或跳过理由 |
| 预期知识项 | pending 或 unchecked | add_expectation；update_expectation；先判断合理性，再检查全文覆盖 | rationality 和 presence 分别有结论；仅确认合理且缺失时进入遗漏影响 |
| 来源证据 | 新建 | add_evidence | 来源版本、精确位置、摘录、用途和截止点状态齐全 |
| 评估记录 | unchecked | assess 更新同一目标/维度 | 支持、有限支持、反证、证据不足或跳过理由有证据 |
| 整体影响记录 | 新建或 uncertain | add_impact；update_impact | 找到具体受影响结果、影响理由、共同根因和不确定性 |
| 检索事件 | 新建 | record_search | 查询、工具、状态、时间和失败原因均反映真实执行 |

优先级遵循：可能推翻中心结果的证据问题，能够改变多个重要判断的共享前提，可能显著改变总体判断的正面结果，预期知识覆盖，最后是低影响覆盖。中心性、不确定性和决策相关性分别记录，不能相互替代。

## 4. 命令

所有命令都从运行目录读取 review_log.json。创建命令接受 JSON 文件；更新命令只更新文件中出现的字段。命令失败返回非零状态，不写入部分状态。

### 初始化和查看

~~~
python <skill>/scripts/review_cli.py init "<paper>" --output-parent "<existing run parent>" --publication-date YYYY-MM-DD --date-basis "actual basis" --conference iclr
python <skill>/scripts/review_cli.py --dir <run> show --detailed
~~~

初始化生成 paper.md、input_manifest.json、review_log.json、inputs/ 和 sources/。`--output-parent` 必须指向已有目录；省略时使用论文所在目录。运行目录必须是 `review_<paper filename without final extension>`，目标目录存在时初始化失败，避免覆盖已有运行。

### 创建与更新记录

~~~
python <skill>/scripts/review_cli.py --dir <run> add_knowledge --file <payload.json>
python <skill>/scripts/review_cli.py --dir <run> update_knowledge --id K1 --file <patch.json>
python <skill>/scripts/review_cli.py --dir <run> add_expectation --file <payload.json>
python <skill>/scripts/review_cli.py --dir <run> update_expectation --id X1 --file <patch.json>
python <skill>/scripts/review_cli.py --dir <run> add_evidence --file <payload.json>
python <skill>/scripts/review_cli.py --dir <run> assess --file <payload.json>
python <skill>/scripts/review_cli.py --dir <run> record_search --file <payload.json>
python <skill>/scripts/review_cli.py --dir <run> add_impact --file <payload.json>
python <skill>/scripts/review_cli.py --dir <run> update_impact --id I1 --file <patch.json>
~~~

专属命令保持参数边界清楚：新增、更新、评估和检索行为不能通过一个任意 put 入口混在一起。内部实现可以共享 JSON 读取、ID 检查、引用检查和保存代码。

### 调查轨迹和最终评语

~~~
python <skill>/scripts/review_cli.py --dir <run> step --target "K1,A1" --why "why now" --action "actual reading/search" --found "actual result" --ops "add_evidence E1; assess A1"
python <skill>/scripts/review_cli.py --dir <run> point --section strengths --file <point.json>
python <skill>/scripts/review_cli.py --dir <run> outline --section summary --content "summary"
python <skill>/scripts/review_cli.py --dir <run> judgment --file <judgment.json>
python <skill>/scripts/review_cli.py --dir <run> validate
python <skill>/scripts/review_cli.py --dir <run> finalize
~~~

step 只记录已经完成的调查；计划不能写成已完成动作。point 每次写一个 strength、weakness、question 或 comment，并使用 evidence_refs 关联已存在的记录。judgment 保存 overall_reason、overall_refs、scale_reason 和 limitations。

## 5. 结构校验

validate 至少检查：

- 必需的运行上下文和文件是否存在；
- 每类记录的编号前缀、唯一性和 JSON 结构；
- 所有 evidence_refs、assessment_refs、target_refs、search_refs、overlaps 和 overall_refs 是否指向已存在记录；
- 更新目标是否存在；
- 评估状态是否属于该维度允许的集合；
- 每条 K 是否为四个维度分别记录结论或有理由的跳过；
- 每个 unknown 是否留有调查证据或具体未决理由；
- 未调查和已调查未知是否区分；
- 截止点字段和来源版本是否存在；
- 最终评语是否引用存在的记录。

结构校验不能裁决知识增量是否真实、正确性是否成立、相对新颖性是否充分或价值判断是否合理。

finalize 先运行完整校验。校验失败时不得写入或覆盖 review.md。成功后导出 review.md、Evidence appendix 和 audit_summary.md，并渲染 steps.md。
