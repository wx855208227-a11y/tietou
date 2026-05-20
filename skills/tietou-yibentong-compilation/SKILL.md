---
name: tietou-yibentong-compilation
description: Use whenever an intern agent works on 铁头一本通, psychology考研 course materials, 347应用心理学, 312心理学, 一本通编制、改写、审核、真题标注、重点层级、tips、补充内容、格式排版, or needs to follow the 铁头《一本通编制要求及细则》.
---

# Tietou Yibentong Compilation

Use this skill for all 铁头一本通 compilation, rewriting, review, and manager assignment work. The user is the leader; when these rules conflict with a new user instruction, project material, or subject-matter judgment, stop and ask the leader to confirm.

## Required References

Read [requirements.md](references/requirements.md) before producing or reviewing 一本通 content. Keep this SKILL.md loaded for workflow discipline; use the reference for detailed rules.

The original source PDF is stored in the `agiamason/tietou` project repository at `docs/yibentong/一本通编制要求及细则.pdf`. Start from this skill and its distilled reference; open the PDF only when exact original wording, screenshots, or formatting examples are needed. If the PDF is image-heavy, use `intern-agent-pdf-ocr-batch` and inspect it in small batches.

## Non-Negotiable Workflow

1. Confirm the source set: 铁头一本通 draft or textbook as 主体材料, official/e-textbook reference, target院校官方考纲, target院校历年真题, and optional 312/泛347真题库.
2. Separate source types in notes and outputs: textbook/source rules, external-material comparison, past-exam evidence, tips/examples, supplementary content, and formatting requirements.
3. For a new textbook-based 一本通, keep the textbook chapter order, but compile as an exam-facing 考点筛选稿, not a full textbook compression. Delete or heavily compress background narration, transitions, low-yield examples, policy discussion, and long descriptive history unless they are directly examinable.
4. Preserve textbook keywords and key sentences after screening. Rebuild them into answer-like layers: category/person/event -> core contribution/definition -> necessary examples/details. Each layer should be a memorisable scoring point.
5. Before assigning importance, build an exam evidence profile: split mixed target-school papers by subject, identify the relevant subject questions, record question types, map questions to textbook knowledge points, and separate direct target-school evidence from auxiliary 312/泛347 evidence.
6. Mark all target-school past-exam knowledge points as 一级. If past-exam content is missing, locate it in the textbook, add it as正文, and mark it 一级. Do not mark a title as true-question evidence merely because the same person or word appears in an unrelated true question.
7. Use official exam outlines for importance, not chapter ordering. Outline items are usually broad and may cover multiple textbook chapters; split each outline-covered cluster into core points, supporting points, and background points before assigning 一级/二级/三级.
8. Treat screenshot examples as formatting examples, not as new正文规则 unless the leader confirms.
9. For PDF/OCR/image-heavy materials, also use `intern-agent-pdf-ocr-batch`: process screenshots in small batches and keep durable local notes.
10. When turning a new project PDF into reusable agent knowledge, create or update a dedicated skill: keep the operational workflow in `SKILL.md`, put detailed extracted rules in `references/`, and record the source PDF path so future agents read the skill first and consult the PDF only for detail checks.
11. Before finalizing, check: title levels, page references, importance levels, true-question markers, tips, supplement boxes, punctuation, line spacing, page numbers, catalog, chapter page breaks, typos, and cross-page tips/supplements.

## Exam-Facing Compilation Guardrails

- 一本通 is not 速背, but it must still be much shorter than the textbook. If the result reads like a cleaned textbook summary, cut harder.
- The default unit is a testable point, not a paragraph. Prefer numbered and nested points over prose.
- Level annotations are local to the specific knowledge point and describe estimated exam frequency/probability: 一级 is high-frequency and very likely, 二级 is medium-frequency and reasonably likely, and 三级 is low-frequency but still testable if the paper asks a偏、怪、难, or edge-scope question. A broad outline item may make a cluster important, but it does not automatically make every subtopic 一级.
- Treat official-outline coverage as cluster-level evidence. A covered cluster is important, but only its core definitions, classifications, theories, formulas, procedures, representative tests/scales, and high-yield comparisons should usually become 一级; supporting points become 二级/强二级; background details usually stay 三级 or are compressed.
- Treat 中国/中国古代/我国历史发展 content as non-core when there is no target-school true-question evidence. Compress, downgrade, or delete by examability; upgrade only exact true-question points to 一级.
- Treat 强二级 as a manual-review subset of 二级: points close to 一级 but lacking decisive evidence. Keep them as 二级 in正文 unless instructed otherwise, and list them separately in the delivery notes with the upgrade reason and possible question type.
- Use 312 and 泛347真题 as auxiliary examability evidence. They can reveal common question forms and raise a point to 强二级, but they do not override target-school true questions, official outline, or textbook structure.
- Lower-level titles may be more important than their parent when a specific subtopic is high-yield or真题-covered. Mark the exception at the lower title.
- Actively identify同类概念、相似概念、易混概念, and add comparison tables, flowcharts, or simple visual summaries when they improve learning. Typical cases include similar terms, adjacent theories, scale/test variants, historical figures with overlapping contributions, and paired methods such as 个别测验 vs 团体测验.
- Gate comparison tables and visuals by importance: they should normally serve at least one 一级 point. 二级 points may appear as supporting comparisons, and 三级 points may appear only when needed to clarify the 一级/二级 distinction; do not create standalone tables or visuals for pure 三级 content.
- Put summary visuals and comparison tables in `铁头tips` blocks at the relevant knowledge point, not as standalone正文 sections.
- Design visuals for black-and-white printing: use high contrast, larger type, thick lines/arrows, and do not rely on color to encode meaning.
- Lay out for A4 black-and-white double-sided printing: avoid orphan headings at page bottoms and avoid splitting images, tables, tips, or supplement boxes across pages when generating DOCX/PDF.
- Keywords and key phrases must be deliberately separated: bold isolated terms, names, theories, scales, methods, indexes, years, and fixed expressions; underline answer-bearing phrases, clauses, or short sentences. The underlined unit can be a sentence fragment, not necessarily a complete sentence. The selected bold/underline text should be enough to reconstruct the paragraph's core content.
- Tips must be standard and should accompany each knowledge point: adapt textbook experiments first; otherwise give concrete, life-close examples beginning with `例如`. Use vivid, life-close, memorable examples when no experiment exists. Do not use Tips for真题提醒, answer strategy, broad summaries, or generic chapter comments.
- Supplementary content should also be presented through a Tips-style block when the leader requests this style. Start with `补充内容：xxxx`, then edit the supplementary content according to 一本通 rules: layered structure, concise wording, bold keywords, and underlined key phrases.

## Reporting

When reporting to a manager or the user, include:

- Materials checked and any missing inputs.
- Target-school exam profile: relevant subject questions, question types, and mapped knowledge points.
- Changes made by category: add/delete/degrade/upgrade/rewrite/format.
- Strong 二级 review list: knowledge point, location/page, reason, likely question type, and whether it is a candidate for 一级.
- Auxiliary evidence used: 312 or 泛347真题 evidence, if provided, and how it affected examability or question-type judgment.
- Uncertainties and conflicts requiring leader confirmation.
- Validation performed against the requirements reference.
