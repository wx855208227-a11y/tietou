# SZU general psychology chapter 1 decision ledger

- task_id: task-20261030-072810-635354-szu-general-psychology-chapter-1-decision-ledger
- branch: worker1/szu-general-psychology-ch01-ledger
- branch_slug: worker1__szu-general-psychology-ch01-ledger
- created_utc: 2026-10-30T07:28:10Z
- status: active

## Description
Task task-20261028-083259-728941-task-20261028-083259: based on approved origin/work/20261028-szu-general-psychology-remake, create only outputs/szu-347/general-psychology/remake/pilot/chapter01_decision_ledger.tsv; verify textbook titles, terminology, and printed pages directly against original PDF; map official outline and SZU evidence IDs; do not use other yibentong as content source or write DOCX; validate schema, empty fields, evidence IDs, sequence, and chapter-one outline coverage.

## Review Brief
### Original Request
Task task-20261028-083259-728941-task-20261028-083259: based on approved origin/work/20261028-szu-general-psychology-remake, create only outputs/szu-347/general-psychology/remake/pilot/chapter01_decision_ledger.tsv; verify textbook titles, terminology, and printed pages directly against original PDF; map official outline and SZU evidence IDs; do not use other yibentong as content source or write DOCX; validate schema, empty fields, evidence IDs, sequence, and chapter-one outline coverage.

### Assigned Scope
- 基于已审核分支 `origin/work/20261028-szu-general-psychology-remake` 的证据层，只编制深圳大学347普通心理学第一章逐知识点决策账。
- 按彭聃龄《普通心理学》第6版第一章原始顺序覆盖61个条目；教材标题、术语和印刷页以原PDF页面为准，不按PDF偏移推算。
- 将官方考纲终端项 `GP-O01`、`GP-O02`、`GP-M01` 至 `GP-M09` 映射到条目，并仅在真题最小答案点实际命中时登记深大证据ID。
- 本次限定返工只处理证据传导、层级、题型、Tips筛选及任务记录完整性，不进入正文或DOCX生成。

### Deliverables
- 唯一业务产物：`outputs/szu-347/general-psychology/remake/pilot/chapter01_decision_ledger.tsv`，61行数据、15列。
- 管理记录：本任务记录及工作区 `tasks/worker1__szu-general-psychology-ch01-ledger/` 下的canonical镜像保持相同内容。
- TSV逐行包含教材顺序、原题名、印刷页、考纲映射、真题证据、层级理由、题型、底稿动作、答案维度、关键词、关键句、Tips/实验、补充来源状态、置信度和人工确认项。

### Validation Plan
- 用Python `csv` 按制表符解析，断言15列表头、61行数据、所有单元格非空、教材顺序唯一且递增。
- 将 `深大证据ID` 与 `evidence/question_evidence.tsv` 的证据ID集合比对；证据行题型必须等于所引真题真实题型集合（`单选`在成品规范化为`选择`）。
- 断言层级仅为一级/二级/三级，题型仅使用 `选择/判断/填空/名词解释/简答/论述/案例分析`，且不存在 `单选` 或旧标签 `案例`。
- 检查 `03.11`、`03.16` 不挂父题证据，`Q2020-E01` 只出现在观察法和实验法；检查 `04.10` 至 `04.14` 在GP-O02边界确认前均为三级。
- 检查第一章考纲ID集合完整覆盖 `GP-O01`、`GP-O02`、`GP-M01` 至 `GP-M09`；运行 `git diff --check`，并用 `rg` 确认两份任务记录没有模板占位词。
- 用 `sha256sum` 复核四项输入文件hash；用 `git status --short --branch` 与 `git log -1` 确认返工提交已推送且工作树干净。

### Constraints And Non-Goals
- 不写正文、DOCX、审核XLSX或渲染PDF，不扩展到第一章之外，不修改证据层已审核文件。
- 其他一本通不得作为内容来源；现有深大一本通仅用于登记“现有底稿动作”，教材正文、术语和页码仍以原PDF为准。
- 不把父题证据机械传导给下级细节；`Q2019-S01`只支撑主要方法及因果边界，`Q2020-E01`只支撑观察法和实验法优缺点。
- 未确认GP-O02是否覆盖当代研究取向前，不据此提升 `04.10` 至 `04.14`；不捏造真题、题型、教材页码或补充来源。
- Tips按“教材实验必做、正式来源必要补充其次、一级/二级难点生活例再次”筛选；人物介绍、时间轴、学术争鸣和仪器图不因教材存在自动采用。
- 不修改HF材料库或凭据，不覆盖其他工作者改动；业务输出限于指定TSV。

### Claimed Output
- 已按教材第一章顺序建立61条决策，教材题名和印刷页覆盖P2-P34，第一章考纲ID均有落点。
- 已删除 `03.11` 和 `03.16` 的父题式证据传导；观察法/实验法保留 `Q2020-E01`，并在层级理由中限定其只支撑优缺点。
- 有真题证据的条目只列真实题型；无真题条目按知识形态给出保守预测并在层级理由中注明预测依据，标签统一为 `选择` 和 `案例分析`。
- `04.10` 至 `04.14` 在GP-O02边界确认前统一保守为三级；争鸣、人物、时间轴和仪器图候选均明确“不采用”或给出保留理由。
- 当前产物是编制决策账，不宣称第一章正文、DOCX或补充教材核页已经完成。

### Artifacts And Evidence
- 业务产物：`outputs/szu-347/general-psychology/remake/pilot/chapter01_decision_ledger.tsv`；初始产物提交 `bb2e565`，任务记录提交 `d29a8d5`，返工提交由本记录 `Steps` 中的最新 `pushed_commit` 标识。
- 仓库证据输入：`outputs/szu-347/general-psychology/remake/evidence/question_evidence.tsv`、`outline_coverage.tsv`、`strong_secondary_review.tsv`、`baseline_audit.md`。
- 材料根路径：`/home/yileiyang/multi_agent/.work/workspaces/github.com/agiamason/tietou/agents/tietou_manager/analysis/hf_tietou_repo/`。
- 教材相对路径：`院校资料库/347应用心理专硕/深圳大学/教材/普通心理学/深大普通心理学_第6版_彭聃龄.pdf`；SHA-256 `b6804cf998157b1635e19126aa1a120cdad2f6a19e63a2805b80cea36b9585ff`。
- 考纲相对路径：`院校资料库/347应用心理专硕/深圳大学/考纲/2026/深圳大学2026年硕士研究生入学考试大纲.docx`；SHA-256 `4b3c4a8acfa9f06460ada2b9126501c42f63dde7f4c96f35a32afd76fa213882`。
- 真题相对路径：`院校资料库/347应用心理专硕/深圳大学/真题/汇总/深大初试真题册.docx`；SHA-256 `4f1bbc6972f4ba7d20ef8c4252a5bb55288a754d750526b5bc070a569240b21d`。
- 底稿相对路径：`院校资料库/347应用心理专硕/深圳大学/一本通/普通心理学/深大普通心理学一本通.docx`；仅用于动作判断；SHA-256 `506b7bc5e92bb0c067ec308d70e6c796646c0dc2ccdb533fa50b29dda5e6258f`。
- 验证命令：`python -`（使用 `csv.DictReader(..., delimiter='\\t')` 执行结构、空值、顺序、证据ID、真实题型、层级、Tips及考纲覆盖断言）、`sha256sum <四项材料路径>`、`rg -n <模板占位词正则> <两份任务记录>`、`git diff --check`、`git status --short --branch`。
- 风险：GP-O02与当代研究取向的映射边界仍需人工确认；GP-M02、GP-M03、GP-M04、GP-M08需正式研究方法/实验心理学来源核页；GP-M07正文应回第十四章核页，第一章只建索引；部分三级条目是否合并仍为成品编制决策。

## Steps
- 2026-10-30T07:28:10Z: task created
- 2026-10-30T07:50:43Z: Build chapter 1 decision ledger from source evidence
  - pushed_commit: bb2e565
- 2026-10-30T08:01:23Z: Refine chapter 1 evidence levels and task audit trail
