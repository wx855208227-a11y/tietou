# Revise ECNU measurement yibentong feedback

- task_id: task-20260525-134242-155337-revise-ecnu-measurement-yibentong-feedback
- branch: work/20260525-134241-264636-revise-ecnu-measurement-yibentong-feedback
- branch_slug: work__20260525-134241-264636-revise-ecnu-measurement-yibentong-feedback
- created_utc: 2026-05-25T13:42:42Z
- status: active

## Description
用户反馈华东347测量心理学一本通第1-2章存在格式和内容问题：tips样式、字体、logo、底框颜色、表格格式、标题正文跨页；关键词关键句划分不准；正文出现编制说明式提示语；审核表应聚焦强二级升降级审核而非罗列所有等级；HF资料库中的一本通只能借鉴格式，不能借鉴/学习内容，格式标准以深大普心一本通为准。需要更新本地和repo skill，并返工DOCX/XLSX后通过manager-worker-reviewer流程发送文件。

## Review Brief
### Original Request
用户反馈华东347测量心理学一本通第1-2章存在格式和内容问题：tips样式、字体、logo、底框颜色、表格格式、标题正文跨页；关键词关键句划分不准；正文出现编制说明式提示语；审核表应聚焦强二级升降级审核而非罗列所有等级；HF资料库中的一本通只能借鉴格式，不能借鉴/学习内容，格式标准以深大普心一本通为准。需要更新本地和repo skill，并返工DOCX/XLSX后通过manager-worker-reviewer流程发送文件。

### Assigned Scope
- Update local and repo 一本通 skills so future agents treat HF 一本通 as format-only references, with 深大普心一本通 as the formatting standard.
- Revise 华东347《测量心理学》一本通第1-2章 deliverables after user feedback.
- Fix student DOCX format: Tips style/logo/border/fill/font, table style/font/readability, A4 black-and-white layout, and heading/body cross-page risks.
- Fix student DOCX content: remove manager-facing rationale from正文, improve keyword vs key-phrase marking, and avoid borrowing content from HF 一本通.
- Fix review XLSX: make the main audit sheet focus on 强二级 candidates and upgrade/keep decisions, with supporting evidence/self-check sheets as needed.
- Follow manager-worker-reviewer flow; only tietou_manager communicates with the leader.

### Deliverables
- Updated local Codex skill: `/home/yileiyang/.codex/skills/tietou-yibentong-compilation/`.
- Updated repo skill files under `skills/tietou-yibentong-compilation/`.
- Revised student-facing DOCX in `deliverables/ecnu-measurement-ch1-2/`.
- Revised manager review XLSX in `deliverables/ecnu-measurement-ch1-2/` with 强二级复核 as main sheet.
- Source/style extraction notes and validation notes under `analysis/ecnu-measurement-ch1-2/` if useful.

### Validation Plan
- Inspect 深大普心一本通 formatting structurally; use it only for format, not content.
- Validate DOCX/XLSX zip integrity and readability.
- Programmatically check student DOCX does not contain editor/process phrases such as `无真题支撑`, `正文保留主线`, `细节了解即可`, `不展开背诵`.
- Programmatically check review XLSX first sheet is 强二级-focused and includes confirmation columns.
- Ask `tietou_reviewer` to review worker outputs and final integrated deliverables against the updated skill.
- Run `git diff --check`, keep worktree clean, commit and push after meaningful steps.

### Constraints And Non-Goals
- Do not use HF 一本通 content as a source for正文, level decisions, Tips content, or wording.
- Do not introduce unsupported textbook claims or unsourced supplementary content.
- Do not let workers communicate with the leader; they report only to manager.
- Keep scope to fixing 第1-2章 deliverables and skill updates from this feedback.

### Claimed Output
- Updated local Codex skill and repo skill to make HF 一本通 format-only, forbid正文过程语 including `了解即可`, require 深大普心样式 for Tips/table formatting, and focus manager audit on 强二级 decisions.
- Regenerated `deliverables/ecnu-measurement-ch1-2/华东347测量心理学一本通_第1-2章_自检版.docx`.
- Regenerated `deliverables/ecnu-measurement-ch1-2/华东347测量心理学一本通_第1-2章_审核表.xlsx` with first sheet `强二级复核`.
- Updated `scripts/generate_ecnu_measurement_ch1_2.py` so Tips use an embedded upper-left `铁头 tips` ribbon image, light-blue body block, centered title, fixed tables, keep-with-next headings, and row non-splitting controls.

### Artifacts And Evidence
- Generated artifacts: DOCX, XLSX, and `编制说明_第1-2章.md` under `deliverables/ecnu-measurement-ch1-2/`.
- Validation: `unzip -t` passed for DOCX and XLSX; `git diff --check` passed.
- Student DOCX phrase check: no `无真题支撑`, `正文保留主线`, `细节了解即可`, `了解即可`, `后续章节再展开`, `本章先掌握`, `不展开背诵`, `无华东`, `暂无华东`, `二级/强二级`, or `既有人工一本通样例`.
- Review XLSX check: sheets are `强二级复核`, `证据映射`, `自检`; main sheet has 8 强二级 candidates, 11 columns, and `主管确认` column.
- DOCX OOXML check: headings have keep-next/keep-lines; tables include fixed layout and non-splitting rows; Tips contain embedded ribbon image and blue body table.
- Residual limitation: no local LibreOffice/Word renderer is available, so visual pagination can only be checked through OOXML controls and later Word inspection.

## Steps
- 2026-05-25T13:42:42Z: task created
- 2026-05-25T13:45:31Z: Record yibentong feedback rules
  - pushed_commit: ec3fab1
- 2026-05-25T13:50:51Z: Revise ECNU measurement yibentong format and audit files
  - pushed_commit: d413714
- 2026-05-25T14:01:30Z: Revise ECNU measurement chapters after feedback
  - pushed_commit: 7c98e61
- 2026-05-25T14:09:00Z: Remove remaining process-wording conflicts from yibentong skills and complete task evidence notes
- 2026-05-25T14:06:09Z: Clean yibentong process wording rules
