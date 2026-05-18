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

1. Confirm the source set: 铁头一本通 draft or textbook as 主体材料, official/e-textbook reference, strong external materials, and target院校历年真题.
2. Separate source types in notes and outputs: textbook/source rules, external-material comparison, past-exam evidence, tips/examples, supplementary content, and formatting requirements.
3. For a new textbook-based 一本通, keep the textbook chapter order, but compile as an exam-facing 考点筛选稿, not a full textbook compression. Delete or heavily compress background narration, transitions, low-yield examples, policy discussion, and long descriptive history unless they are directly examinable.
4. Preserve textbook keywords and key sentences after screening. Rebuild them into answer-like layers: category/person/event -> core contribution/definition -> necessary examples/details. Each layer should be a memorisable scoring point.
5. Mark all past-exam knowledge points as 一级. If past-exam content is missing, locate it in the textbook, add it as正文, and mark it 一级. Do not mark a title as true-question evidence merely because the same person or word appears in an unrelated true question.
6. Use official exam outlines for importance, not chapter ordering. Outline items are usually broad and may cover multiple textbook chapters; they identify important knowledge clusters, while the 一本通 structure still follows the textbook.
7. Treat screenshot examples as formatting examples, not as new正文规则 unless the leader confirms.
8. For PDF/OCR/image-heavy materials, also use `intern-agent-pdf-ocr-batch`: process screenshots in small batches and keep durable local notes.
9. When turning a new project PDF into reusable agent knowledge, create or update a dedicated skill: keep the operational workflow in `SKILL.md`, put detailed extracted rules in `references/`, and record the source PDF path so future agents read the skill first and consult the PDF only for detail checks.
10. Before finalizing, check: title levels, page references, importance levels, true-question markers, tips, supplement boxes, punctuation, line spacing, page numbers, catalog, chapter page breaks, typos, and cross-page tips/supplements.

## Exam-Facing Compilation Guardrails

- 一本通 is not 速背, but it must still be much shorter than the textbook. If the result reads like a cleaned textbook summary, cut harder.
- The default unit is a testable point, not a paragraph. Prefer numbered and nested points over prose.
- Level annotations are local to the specific knowledge point. A broad outline item may make a cluster important, but it does not automatically make every subtopic 一级.
- Lower-level titles may be more important than their parent when a specific subtopic is high-yield or真题-covered. Mark the exception at the lower title.
- Tips are optional. Use them for abstract concepts, confusing comparisons, calculations,量表, or examples that aid understanding; do not force Tips into historical or straightforward factual sections.

## Reporting

When reporting to a manager or the user, include:

- Materials checked and any missing inputs.
- Changes made by category: add/delete/degrade/upgrade/rewrite/format.
- Uncertainties and conflicts requiring leader confirmation.
- Validation performed against the requirements reference.
