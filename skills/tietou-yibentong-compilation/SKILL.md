---
name: tietou-yibentong-compilation
description: Use whenever an intern agent works on 铁头一本通, psychology考研 course materials, 347应用心理学, 312心理学, 一本通编制、改写、审核、真题标注、重点层级、tips、补充内容、格式排版, or needs to follow the 铁头《一本通编制要求及细则》.
---

# Tietou Yibentong Compilation

Use this skill for all 铁头一本通 compilation, rewriting, review, and manager assignment work. The user is the leader; when these rules conflict with a new user instruction, project material, or subject-matter judgment, stop and ask the leader to confirm.

## Required References

Read [requirements.md](references/requirements.md) before producing or reviewing 一本通 content. Keep this SKILL.md loaded for workflow discipline; use the reference for detailed rules.

The original source PDF is stored in the `agiamason/tietou` project repository at `docs/yibentong/一本通编制要求及细则.pdf`. Start from this skill and its distilled reference; open the PDF only when exact original wording, screenshots, or formatting examples are needed. If the PDF is image-heavy, use `intern-agent-pdf-ocr-batch` and inspect it in small batches.

For cover, catalog, page-number formatting, Tips visual style, table style, fonts, spacing, and A4 print layout, follow the user-provided human sample `27深大普心一本通（最新版）(1).docx` when available.

Important: 一本通 files in HF are format references only unless the leader explicitly assigns a content review task. Do not copy, imitate, learn, or borrow their正文内容、层级判断、真题标注、Tips内容、语言表述, or content-selection decisions. The leader has confirmed those files may contain content problems. For new compilation, content authority is the assigned textbook, target-school official outline, target-school true questions, and traceable published教材/文献 only. Use the 深大普心一本通 sample as the formatting standard, not as a content standard.

## Non-Negotiable Workflow

1. Confirm the source set: 铁头一本通 draft or textbook as 主体材料, official/e-textbook reference, target院校官方考纲, target院校历年真题, and optional 312/泛347真题库.
2. Separate source types in notes and outputs: textbook/source rules, external-material comparison, past-exam evidence, tips/examples, supplementary content, and formatting requirements.
3. For a new textbook-based 一本通, keep the textbook chapter order, but compile as an exam-facing 考点筛选稿, not a full textbook compression. Delete or heavily compress background narration, transitions, low-yield examples, policy discussion, and long descriptive history unless they are directly examinable.
4. Preserve textbook keywords and key sentences after screening. Rebuild them into answer-like layers: category/person/event -> core contribution/definition -> necessary examples/details. Each layer should be a memorisable scoring point.
5. Before drafting, build a chapter evidence table and exam profile: knowledge point, textbook page, outline coverage, target-school true-question evidence, auxiliary 312/泛347 evidence, possible question type, suggested level, Tips/visual decision, and uncertainty. Split mixed target-school papers by subject and map only relevant questions to the smallest substantive textbook point. Evidence tables are internal/review artifacts; do not paste evidence-rationale or process reminders such as “无真题支撑、了解即可、细节了解即可” into the student-facing正文.
6. Mark all target-school past-exam knowledge points as 一级. If past-exam content is missing, locate it in the textbook, add it as正文, and mark it 一级. Do not mark a title as true-question evidence merely because the same person or word appears in an unrelated true question.
7. Use official exam outlines for importance, not chapter ordering. Outline items are usually broad and may cover multiple textbook chapters; split each outline-covered cluster into core points, supporting points, and background points before assigning 一级/二级/三级.
8. Treat screenshot examples as formatting examples, not as new正文规则 unless the leader confirms.
9. For PDF/OCR/image-heavy materials, also use `intern-agent-pdf-ocr-batch`: process screenshots in small batches and keep durable local notes.
10. When turning a new project PDF into reusable agent knowledge, create or update a dedicated skill: keep the operational workflow in `SKILL.md`, put detailed extracted rules in `references/`, and record the source PDF path so future agents read the skill first and consult the PDF only for detail checks.
11. Run a self-check before delivery: source fidelity, evidence mapping, level logic, core正文 compilation quality, wording concision, bold/underline extraction, Tips priority, visual/table gate, supplement sources, A4 print layout, and unresolved assumptions.
12. Deliver two files by default: a self-checked student-facing finished DOCX, and a manager review XLSX that makes the leader's audit fast. The review workbook's main sheet should focus on 强二级候选是否升为一级/保留二级 for leader audit; supporting sheets may include evidence mapping, Tips/visual/supplement decisions, deletions/compressions, self-check results, and open confirmations. Do not make the main audit experience a flat dump of every level.

## Manager-Worker-Reviewer Collaboration

Use this workflow whenever the project has `tietou_manager`, `tietou_worker1`, `tietou_worker2`, and `tietou_reviewer` available for 一本通 or other 铁头资料 tasks.

### Communication Rules

- `tietou_manager` is the only agent that communicates with the leader/user. Workers and reviewer report only to `tietou_manager` and follow manager assignments.
- Workers must not ask the leader directly for clarification. They should report blockers, assumptions, and missing inputs to `tietou_manager`.
- `tietou_reviewer` does not command workers directly. It reports findings and verdicts to `tietou_manager`; the manager decides and assigns rework.
- Use the collaboration CLI for handoffs. If `lite-agent` is not on `PATH`, try `/home/yileiyang/multi_agent/.venv/bin/lite-agent` before falling back. Record any CLI/PATH failure in the task notes and this skill when it affects the workflow.

### Role Responsibilities

- `tietou_manager`: understand the leader's request, clarify missing inputs when truly needed, split work into concrete subtasks, assign ownership to workers, route each meaningful worker output through reviewer, decide rework, integrate branches/artifacts, run final checks, push to GitHub, and report to the leader.
- `tietou_worker1` / `tietou_worker2`: execute assigned bounded tasks only, read this skill and `references/requirements.md` before working, respect the assigned branch/file scope, produce the requested artifact, self-check against the task brief, remove non-deliverable temporary files before reporting, commit changes on the assigned branch when code/file work is requested, and report deliverables plus assumptions/risks to the manager.
- `tietou_reviewer`: independently check worker outputs and the final integrated result against this skill, `references/requirements.md`, the manager's assignment, source materials, and produced artifacts. Report findings first, with evidence and a verdict: `PASS`, `PASS WITH RISKS`, `NEEDS REWORK`, or `BLOCKED`.

### Task Flow

1. Manager creates a work plan: source materials, target deliverables, chapter/section scope, expected output files, branch plan, file ownership, review checkpoints, and acceptance criteria.
2. Manager splits work so worker branches have disjoint or clearly bounded write sets. Typical split examples: source extraction/evidence table, separate chapter sections, Tips/visual assets, DOCX generation, review XLSX, or formatting pass.
3. Manager assigns tasks to `tietou_worker1` and/or `tietou_worker2` with explicit instructions: branch name, files/modules owned, materials to read, required skills, output format, self-check checklist, and reporting format. Remind workers they are not alone in the repo and must not revert others' work.
4. Each worker works on its assigned branch when file edits are required. Use clear branch names such as `worker1/<task-slug>` and `worker2/<task-slug>` unless the manager specifies another convention. Use `python3` for project task scripts in this environment; do not assume `python` exists.
5. After each meaningful worker milestone, manager asks `tietou_reviewer` to review that worker's branch/artifacts before integration. For 一本通, checkpoints should normally include at least: evidence/level table, first compiled draft, Tips/visual/supplement decisions, generated DOCX/XLSX, and final self-check.
6. Reviewer returns findings with evidence and a verdict. If the verdict is `NEEDS REWORK` or `BLOCKED`, manager sends precise rework instructions to the responsible worker and repeats review after revision. Do not merge work with unresolved blocker/high findings.
7. Once reviewed worker branches pass, manager integrates them in the manager repo, resolves conflicts conservatively, and preserves each worker's accepted changes.
8. Manager sends the integrated result to `tietou_reviewer` for final review before pushing. The final review must cover the combined artifact, not only individual worker outputs.
9. If final review passes, manager pushes to GitHub and reports to the leader with: pushed commit/branch, deliverables, review status, 强二级/待确认 items, and any residual risks. If final review fails, manager assigns rework before reporting completion.

### Worker Stall Or Artifact Failure

- If a worker does not produce the requested artifact in a reasonable time, leaves unrelated temporary files, or cannot be reached through the collaboration CLI, the manager records the issue in the task record and sends one explicit cleanup/finish instruction through `lite-agent assign` when available.
- If the worker still cannot provide a usable artifact and the task can continue without risking correctness, the manager may complete the blocked portion directly as a documented fallback, then must route the manager-produced artifact through `tietou_reviewer` before pushing or reporting completion.
- Do not integrate worker branches containing placeholder files such as `test.tmp`, half-written outputs, credential material, or files outside the assigned scope. Ask for cleanup/rework or ignore the branch and document why.
- Before running `commit_step.py`, check `git status --short` and make sure unrelated generated outputs are ignored, moved out of the repo, or intentionally staged. The helper runs `git add -A`, so unignored old artifacts can be committed accidentally.

### HuggingFace Material Library Workflow

Use this when organizing HF materials for future 一本通 compilation.

- Preferred top-level taxonomy:
  - `院校资料库/347应用心理专硕/<院校>/教材/<科目>/...`
  - `院校资料库/347应用心理专硕/<院校>/考纲/[年份]/...`
  - `院校资料库/347应用心理专硕/<院校>/真题/<年份或范围>/...`
  - `院校资料库/347应用心理专硕/<院校>/一本通/<科目>/...`
  - `院校资料库/347应用心理专硕/<院校>/报考信息/...` for non-outline background information.
  - `公共题库/312心理学统考/...` for 312 auxiliary true-question materials.
  - `公共题库/347应用心理专硕/...` for cross-school 347 auxiliary true-question materials.
  - `编制规范/一本通编制要求/...` for compilation standards.
  - `索引/资料目录.tsv` and `索引/清理记录.md` for retrieval and audit.
- Do not mix public 312/泛347 question banks into target-school true-question folders. Public banks are auxiliary evidence only.
- Remove upload noise such as `.DS_Store`; add `.gitignore` rules to prevent reintroduction.
- Delete duplicate legacy paths only when the same content remains in the canonical path, preferably verified by identical LFS object ids or another exact identity check. Record duplicate removals in `索引/清理记录.md` or the manager review artifact.
- Do not download large LFS files for a path-only organization task unless content inspection is actually required. Use filenames, LFS pointers, and directory context first.
- For private HF datasets, use cached HF token auth without printing or committing secrets. A temporary `GIT_ASKPASS` script is acceptable only if it reads the token from the local cache, is stored outside committed paths, and is removed immediately after use.
- Validate before push: pre/post file counts, `.DS_Store` count, unique LFS object id comparison, `git status`, root taxonomy listing, and index readability.

### Review Gates For 一本通

- Evidence gate: relevant true questions are subject-filtered and mapped, official outline coverage is interpreted correctly, and 强二级 candidates are listed.
- Content gate: the正文 is the best attainable compiled version under current materials, not just a compliant draft.
- Annotation gate: importance levels, true-question markers, 一级题型提示, bold keywords, and underlined key phrases follow the rules.
- Tips/visual gate: Tips follow priority, visuals/tables serve appropriate importance levels, and supplement sources are traceable published textbooks or academic literature.
- Format gate: Tips, tables, cover, catalog, fonts, logo/label placement, border/background color, and page layout match the 深大普心一本通 formatting sample as closely as the DOCX toolchain allows. Headings must not be orphaned at page bottoms; headings and their first正文 paragraph should stay together, and Tips/tables should not be split awkwardly across pages.
- Delivery gate: finished DOCX and manager review XLSX exist, self-check is complete, A4 black-and-white layout risks are checked, and unresolved assumptions are visible in the review file.

## Exam-Facing Compilation Guardrails

- 一本通 is not 速背, but it must still be much shorter than the textbook. If the result reads like a cleaned textbook summary, cut harder.
- The正文 is the core product. Self-check whether the compiled正文 is genuinely the best attainable version under the current materials and rules, not merely a minimally compliant draft: content selection, hierarchy, wording, memorisability, answer usability, and exam-facing compression should all be deliberately optimized.
- The default unit is a testable point, not a paragraph. Prefer numbered and nested points over prose.
- Level annotations are local to the specific knowledge point and describe estimated exam frequency/probability: 一级 is high-frequency and very likely, 二级 is medium-frequency and reasonably likely, and 三级 is low-frequency but still testable if the paper asks a偏、怪、难, or edge-scope question. A broad outline item may make a cluster important, but it does not automatically make every subtopic 一级.
- Treat official-outline coverage as cluster-level evidence. A covered cluster is important, but only its core definitions, classifications, theories, formulas, procedures, representative tests/scales, and high-yield comparisons should usually become 一级. Other outline-covered points should be at least 二级/强二级, except 中国/中国古代/我国发展史等中国背景类内容 can be 三级 when no target-school true-question evidence supports them.
- Treat 中国/中国古代/我国历史发展 content as non-core when there is no target-school true-question evidence. Compress, downgrade, or delete by examability; upgrade only exact true-question points to 一级.
- Treat 强二级 as a manual-review subset of 二级: points close to 一级 but lacking decisive evidence. Keep them as 二级 in the finished正文 unless instructed otherwise, and list them separately only in the manager review file with the upgrade reason and possible question type.
- Use 312 and 泛347真题 as auxiliary examability evidence. They can reveal common question forms and raise a point to 强二级, but they do not override target-school true questions, official outline, or textbook structure.
- Let likely question type shape the writing unit: term explanations need definition plus features; short answers need numbered scoring points; essays/material questions need logic chains and application conditions; choice/judgment points need exact people, years, names, boundaries, and misconceptions.
- Constrain question-type hints by the target school's observed true-question profile. Before adding any non-true-question question-type hint, build a target-school question-type inventory from the provided years and choose only among types the school has actually used for this subject/paper. Do not mark absent forms such as `案例分析`、`实验设计`、`材料分析` when the target school has never tested them. If a knowledge point naturally supports an absent type, record it only in the manager review file as external examability, not in the finished正文.
- Lower-level titles may be more important than their parent when a specific subtopic is high-yield or真题-covered. Mark the exception at the lower title.
- Actively identify同类概念、相似概念、易混概念, and add comparison tables, flowcharts, or simple visual summaries when they improve learning. Typical cases include similar terms, adjacent theories, scale/test variants, historical figures with overlapping contributions, and paired methods such as 个别测验 vs 团体测验.
- Gate comparison tables and visuals by importance: they should normally serve at least one 一级 point. 二级 points may appear as supporting comparisons, and 三级 points may appear only when needed to clarify the 一级/二级 distinction; do not create standalone tables or visuals for pure 三级 content.
- Put summary visuals and comparison tables in `铁头tips` blocks at the relevant knowledge point, not as standalone正文 sections.
- Design visuals for black-and-white printing: use high contrast, larger type, thick lines/arrows, and do not rely on color to encode meaning.
- Lay out for A4 black-and-white double-sided printing: avoid orphan headings at page bottoms and avoid splitting images, tables, tips, or supplement boxes across pages when generating DOCX/PDF.
- Keywords and key phrases must be deliberately separated: bold isolated terms, names, theories, scales, methods, indexes, years, and fixed expressions; underline answer-bearing phrases, clauses, or short sentences. The underlined unit can be a sentence fragment, not necessarily a complete sentence. The selected bold/underline text should be enough to reconstruct the paragraph's core content.
- Do not over-bold full clauses that function as answer statements. If the marked unit is a definition, judgment, boundary, cause-effect relation, or scoring phrase, underline it; reserve bold for terms and fixed labels. During self-check, read only the bold/underlined fragments and verify they reconstruct the core answer without noise.
- Tips are selective, not mandatory for every knowledge point. Priority order: textbook experiments/small demonstrations first and required when present; then supplementary content for important or target-school-tested points absent from the main textbook, with source textbook/page; then life-close examples only for genuinely hard-to-understand 一级/二级 points. Avoid tips for ordinary 三级 points and skip examples that would be forced or harder than the concept.
- Student-facing正文 must not include manager-facing rationale or process reminders, such as “本部分无真题支撑”“正文保留主线即可”“了解即可”“细节了解即可” as explanatory process language. If a 三级 point needs a learning signal, express it through the level tag and concise content selection, not through editor commentary.
- Supplementary content should be presented through a Tips-style block. Start with `补充内容：xxxx`, cite the source textbook and page when available, then edit according to 一本通 rules: layered structure, concise wording, bold keywords, and underlined key phrases. Supplement sources must be published textbooks or academic literature with traceable出处; do not use online文库、咨询号、unverified web summaries, or unsourced notes.
- Finished products should include question-type hints for 一级 points. For true-question 一级 points, use the actual target-school true-question type; for non-true-question 一级 points, use the agent's judged likely type within the target school's observed question-type boundary. 二级/三级 likely types go only in the manager review file. Use separate brackets after true-question markers, such as `【20、23年真题】【选择/名词解释】`.
- Keep a decision log for Tips, visuals, tables, and supplements. Record why each was added, and record why obvious candidates were skipped when the choice may need leader review.

## Reporting

When reporting to a manager or the user, include:

- Materials checked and any missing inputs.
- Target-school exam profile: relevant subject questions, question types, and mapped knowledge points.
- Changes made by category: add/delete/degrade/upgrade/rewrite/format.
- Strong 二级 review list: knowledge point, location/page, reason, likely question type, and whether it is a candidate for 一级.
- Self-check product file path and manager review file path.
- Tips/visual/supplement decision summary and any skipped-but-borderline candidates.
- Auxiliary evidence used: 312 or 泛347真题 evidence, if provided, and how it affected examability or question-type judgment.
- Uncertainties and conflicts requiring leader confirmation.
- Validation performed against the requirements reference.
