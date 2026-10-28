---
name: tietou-yibentong-compilation
description: Use whenever an intern agent works on 铁头一本通, psychology考研 course materials, 347应用心理学, 312心理学, 一本通编制、改写、审核、真题标注、重点层级、tips、补充内容、格式排版, or needs to follow the 铁头《一本通编制要求及细则》.
---

# Tietou Yibentong Compilation

Use this skill for all 铁头一本通 compilation, rewriting, review, and manager assignment work. The user is the leader; when these rules conflict with a new user instruction, project material, or subject-matter judgment, stop and ask the leader to confirm.

## Required References

Read [requirements.md](references/requirements.md) before producing or reviewing 一本通 content. Keep this SKILL.md loaded for workflow discipline; use the reference for detailed rules.

The original source PDF is stored in the `agiamason/tietou` project repository at `docs/yibentong/一本通编制要求及细则.pdf`. Start from this skill and its distilled reference; open the PDF only when exact original wording, screenshots, or formatting examples are needed. If the PDF is image-heavy, use `intern-agent-pdf-ocr-batch` and inspect it in small batches.

For cover, catalog, and page-number formatting, follow the user-provided human sample `27深大普心一本通（最新版）(1).docx` when available.

## Non-Negotiable Workflow

1. Confirm the source set: 铁头一本通 draft or textbook as 主体材料, official/e-textbook reference, target院校官方考纲, target院校历年真题, and optional 312/泛347真题库.
2. Separate source types in notes and outputs: textbook/source rules, external-material comparison, past-exam evidence, tips/examples, supplementary content, and formatting requirements.
3. For a new textbook-based 一本通, keep the textbook chapter order, but compile as an exam-facing 考点筛选稿, not a full textbook compression. Delete or heavily compress background narration, transitions, low-yield examples, policy discussion, and long descriptive history unless they are directly examinable.
4. Preserve textbook keywords and key sentences after screening. Rebuild them into answer-like layers: category/person/event -> core contribution/definition -> necessary examples/details. Each layer should be a memorisable scoring point.
5. Before drafting, build a chapter evidence table and exam profile: knowledge point, textbook page, outline coverage, target-school true-question evidence, auxiliary 312/泛347 evidence, possible question type, suggested level, Tips/visual decision, and uncertainty. Split mixed target-school papers by subject and map only relevant questions to the smallest substantive textbook point.
6. Use past-exam type and answer demand, not mere appearance, to assign levels. A target-school subjective question normally makes the exact answer point 一级; a target-school objective question is normally 二级 unless repetition, centrality, and subjective-question transfer justify 强二级/一级. If tested content is missing, add it from the textbook or a traceable supplement. Never infer a true-question hit from a shared word alone.
7. Use official exam outlines for importance, not chapter ordering. Build a line-by-line coverage matrix and cover every outline item substantively. Split broad items across the relevant textbook chapters and assign levels locally; outline coverage does not make every subpoint 一级.
8. Treat screenshot examples as formatting examples, not as new正文规则 unless the leader confirms.
9. For PDF/OCR/image-heavy materials, also use `intern-agent-pdf-ocr-batch`: process screenshots in small batches and keep durable local notes.
10. When turning a new project PDF into reusable agent knowledge, create or update a dedicated skill: keep the operational workflow in `SKILL.md`, put detailed extracted rules in `references/`, and record the source PDF path so future agents read the skill first and consult the PDF only for detail checks.
11. Run a self-check before delivery: source fidelity, evidence mapping, level logic, core正文 compilation quality, wording concision, bold/underline extraction, Tips priority, visual/table gate, supplement sources, A4 print layout, and unresolved assumptions.
12. Deliver two files by default: a self-checked student-facing finished DOCX, and a manager review XLSX that makes the leader's audit fast. The review file should list evidence mapping, level decisions, 强二级 candidates, Tips/visual/supplement decisions, deletions/compressions, self-check results, and open confirmations.

## Manager-Worker-Reviewer Collaboration

Use this workflow whenever the project has `tietou_manager`, `tietou_worker1`, `tietou_worker2`, and `tietou_reviewer` available for 一本通 or other 铁头资料 tasks.

### Communication Rules

- `tietou_manager` is the only agent that communicates with the leader/user. Workers and reviewer report only to `tietou_manager` and follow manager assignments.
- Workers must not ask the leader directly for clarification. They should report blockers, assumptions, and missing inputs to `tietou_manager`.
- `tietou_reviewer` does not command workers directly. It reports findings and verdicts to `tietou_manager`; the manager decides and assigns rework.

### Role Responsibilities

- `tietou_manager`: understand the leader's request, clarify missing inputs when truly needed, split work into concrete subtasks, assign ownership to workers, route each meaningful worker output through reviewer, decide rework, integrate branches/artifacts, run final checks, push to GitHub, and report to the leader.
- `tietou_worker1` / `tietou_worker2`: execute assigned bounded tasks only, read this skill and `references/requirements.md` before working, respect the assigned branch/file scope, produce the requested artifact, self-check against the task brief, commit changes on the assigned branch when code/file work is requested, and report deliverables plus assumptions/risks to the manager.
- `tietou_reviewer`: independently check worker outputs and the final integrated result against this skill, `references/requirements.md`, the manager's assignment, source materials, and produced artifacts. Report findings first, with evidence and a verdict: `PASS`, `PASS WITH RISKS`, `NEEDS REWORK`, or `BLOCKED`.

### Task Flow

1. Manager creates a work plan: source materials, target deliverables, chapter/section scope, expected output files, branch plan, file ownership, review checkpoints, and acceptance criteria.
2. Manager splits work so worker branches have disjoint or clearly bounded write sets. Typical split examples: source extraction/evidence table, separate chapter sections, Tips/visual assets, DOCX generation, review XLSX, or formatting pass.
3. Manager assigns tasks to `tietou_worker1` and/or `tietou_worker2` with explicit instructions: branch name, files/modules owned, materials to read, required skills, output format, self-check checklist, and reporting format. Remind workers they are not alone in the repo and must not revert others' work.
4. Each worker works on its assigned branch when file edits are required. Use clear branch names such as `worker1/<task-slug>` and `worker2/<task-slug>` unless the manager specifies another convention.
5. After each meaningful worker milestone, manager asks `tietou_reviewer` to review that worker's branch/artifacts before integration. For 一本通, checkpoints should normally include at least: evidence/level table, first compiled draft, Tips/visual/supplement decisions, generated DOCX/XLSX, and final self-check.
6. Reviewer returns findings with evidence and a verdict. If the verdict is `NEEDS REWORK` or `BLOCKED`, manager sends precise rework instructions to the responsible worker and repeats review after revision. Do not merge work with unresolved blocker/high findings.
7. Once reviewed worker branches pass, manager integrates them in the manager repo, resolves conflicts conservatively, and preserves each worker's accepted changes.
8. Manager sends the integrated result to `tietou_reviewer` for final review before pushing. The final review must cover the combined artifact, not only individual worker outputs.
9. If final review passes, manager pushes to GitHub and reports to the leader with: pushed commit/branch, deliverables, review status, 强二级/待确认 items, and any residual risks. If final review fails, manager assigns rework before reporting completion.

### Review Gates For 一本通

- Evidence gate: relevant true questions are subject-filtered and mapped, official outline coverage is interpreted correctly, and 强二级 candidates are listed.
- Content gate: the正文 is the best attainable compiled version under current materials, not just a compliant draft.
- Annotation gate: importance levels, true-question markers, 一级题型提示, bold keywords, and underlined key phrases follow the rules.
- Tips/visual gate: Tips follow priority, visuals/tables serve appropriate importance levels, and supplement sources are traceable published textbooks or academic literature.
- Delivery gate: finished DOCX and manager review XLSX exist, self-check is complete, A4 black-and-white layout risks are checked, and unresolved assumptions are visible in the review file.

## Exam-Facing Compilation Guardrails

- 一本通 is not 速背, but it must still be much shorter than the textbook. If the result reads like a cleaned textbook summary, cut harder.
- The正文 is the core product. Self-check whether the compiled正文 is genuinely the best attainable version under the current materials and rules, not merely a minimally compliant draft: content selection, hierarchy, wording, memorisability, answer usability, and exam-facing compression should all be deliberately optimized.
- The default unit is a testable point, not a paragraph. Prefer numbered and nested points over prose.
- Level annotations describe the required preparation mode as well as probability: 一级 is an output-level point prepared as a complete subjective answer and must be memorised; 二级 is a recognition-level point, usually prepared for the target school's objective forms; 三级 is a low-probability point retained for minimal recognition and cold-topic protection.
- Treat official-outline coverage as cluster-level evidence. A covered cluster is important, but only its core definitions, classifications, theories, formulas, procedures, representative tests/scales, and high-yield comparisons should usually become 一级. Other outline-covered points should be at least 二级/强二级, except 中国/中国古代/我国发展史等中国背景类内容 can be 三级 when no target-school true-question evidence supports them.
- Treat 中国/中国古代/我国历史发展 content as non-core when there is no target-school subjective-question evidence. Compress or downgrade by examability. If it is explicitly outline-covered, retain minimum substantive coverage even when marked 三级.
- Treat 强二级 as a manual-review subset of 二级: points close to 一级 but lacking decisive evidence. Keep them as 二级 in the finished正文 unless instructed otherwise, and list them separately only in the manager review file with the upgrade reason and possible question type.
- Use 312 and 泛347真题 as auxiliary examability evidence. They can reveal common question forms and raise a point to 强二级, but they do not override target-school true questions, official outline, or textbook structure.
- Let likely question type shape the writing unit: term explanations need definition plus features; short answers need numbered scoring points; essays/material questions need logic chains and application conditions; choice/judgment points need exact people, years, names, boundaries, and misconceptions.
- Lower-level titles may be more important than their parent when a specific subtopic is high-yield or真题-covered. Mark the exception at the lower title.
- Actively identify同类概念、相似概念、易混概念, and add comparison tables, flowcharts, or simple visual summaries when they improve learning. Typical cases include similar terms, adjacent theories, scale/test variants, historical figures with overlapping contributions, and paired methods such as 个别测验 vs 团体测验.
- Gate comparison tables and visuals by importance: they should normally serve at least one 一级 point. 二级 points may appear as supporting comparisons, and 三级 points may appear only when needed to clarify the 一级/二级 distinction; do not create standalone tables or visuals for pure 三级 content.
- Put summary visuals and comparison tables in `铁头tips` blocks at the relevant knowledge point, not as standalone正文 sections.
- Design visuals for black-and-white printing: use high contrast, larger type, thick lines/arrows, and do not rely on color to encode meaning.
- Lay out for A4 black-and-white double-sided printing: avoid orphan headings at page bottoms and avoid splitting images, tables, tips, or supplement boxes across pages when generating DOCX/PDF.
- Keywords and key phrases must be deliberately separated: bold isolated terms, names, theories, scales, methods, indexes, years, and fixed expressions; underline answer-bearing phrases, clauses, or short sentences. The underlined unit can be a sentence fragment, not necessarily a complete sentence. The selected bold/underline text should be enough to reconstruct the paragraph's core content.
- Tips are selective, not mandatory for every knowledge point. Priority order: textbook experiments/small demonstrations first and required when present; then supplementary content for important or target-school-tested points absent from the main textbook, with source textbook/page; then life-close examples only for genuinely hard-to-understand 一级/二级 points. Avoid tips for ordinary 三级 points and skip examples that would be forced or harder than the concept.
- Supplementary content should be presented through a Tips-style block. Start with `补充内容：xxxx`, cite the source textbook and page when available, then edit according to 一本通 rules: layered structure, concise wording, bold keywords, and underlined key phrases. Supplement sources must be published textbooks or academic literature with traceable出处; do not use online文库、咨询号、unverified web summaries, or unsourced notes.
- Give every knowledge item a local level marker. Add true-question years/types only when substantively verified. For points that should only be prepared for the target school's objective form, retain the established student-facing `选择题考点` annotation; do not inflate them into subjective-answer units. Use separate brackets after verified true-question markers, such as `【20、23年真题】【选择/名词解释】`.
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
