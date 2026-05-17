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
3. Preserve textbook keywords and key sentences. Rewrite long textbook prose into concise, layered, exam-friendly points without changing meaning.
4. Mark all past-exam knowledge points as 一级. If past-exam content is missing, locate it in the textbook, add it as正文, and mark it 一级.
5. Treat screenshot examples as formatting examples, not as new正文规则 unless the leader confirms.
6. For PDF/OCR/image-heavy materials, also use `intern-agent-pdf-ocr-batch`: process screenshots in small batches and keep durable local notes.
7. When turning a new project PDF into reusable agent knowledge, create or update a dedicated skill: keep the operational workflow in `SKILL.md`, put detailed extracted rules in `references/`, and record the source PDF path so future agents read the skill first and consult the PDF only for detail checks.
8. Before finalizing, check: title levels, page references, importance levels, true-question markers, tips, supplement boxes, punctuation, line spacing, page numbers, catalog, chapter page breaks, typos, and cross-page tips/supplements.

## Reporting

When reporting to a manager or the user, include:

- Materials checked and any missing inputs.
- Changes made by category: add/delete/degrade/upgrade/rewrite/format.
- Uncertainties and conflicts requiring leader confirmation.
- Validation performed against the requirements reference.
