# Compile ECNU measurement yibentong chapters 1-2

- task_id: task-20260524-203620-191784-compile-ecnu-measurement-yibentong-chapters-1-2
- branch: work/20260524-203619-117032-compile-ecnu-measurement-yibentong-chapters-1-2
- branch_slug: work__20260524-203619-117032-compile-ecnu-measurement-yibentong-chapters-1-2
- created_utc: 2026-05-24T20:36:20Z
- status: active

## Description
用户要求：编制华东师范大学347测量心理学一本通第一章和第二章，编好后发送文件。需要遵循一本通编制标准，使用华东测量教材、华东官方考纲、华东历年真题、已有人工一本通样例和必要的公共题库辅助判断。默认交付学生版DOCX和审核文件，并经过manager-worker-reviewer流程。

## Review Brief
### Original Request
用户要求：编制华东师范大学347测量心理学一本通第一章和第二章，编好后发送文件。需要遵循一本通编制标准，使用华东测量教材、华东官方考纲、华东历年真题、已有人工一本通样例和必要的公共题库辅助判断。默认交付学生版DOCX和审核文件，并经过manager-worker-reviewer流程。

### Assigned Scope
- Compile 华东师范大学 347 测量心理学一本通第 1 章和第 2 章.
- Use HF source materials: measurement textbook, official outline, ECNU true-question collection, existing ECNU measurement 一本通 sample, and optional public 312/347 question banks for auxiliary examability judgment.
- Follow the manager-worker-reviewer flow and deliver a student-facing DOCX plus a manager review file.

### Deliverables
- Student-facing DOCX for chapters 1-2.
- Manager review XLSX/MD containing evidence mapping, level decisions, strong 二级 candidates, Tips/visual/supplement decisions, and self-check.
- Source extraction notes sufficient for reviewer audit.

### Validation Plan
- Inventory and extract textbook/outline/true-question source content without bulk image loading.
- Worker self-check for evidence mapping and compiled正文 quality.
- Reviewer checkpoints for evidence table/draft and final DOCX/review file.
- Final manager check: file existence, no unrelated files staged, generated DOCX readable, review verdict PASS or documented risk.

### Constraints And Non-Goals
- Only `tietou_manager` communicates with the leader/user.
- Do not commit historical untracked `outputs/` artifacts; use a clean deliverables path for this task.
- Do not invent true-question evidence, textbook pages, or supplement sources.
- Do not use unsourced web materials for supplements.
- Keep the task scoped to chapters 1 and 2.

### Claimed Output
- TODO: fill when reporting completion.

### Artifacts And Evidence
- TODO: fill with changed files, commits, generated artifacts, logs, screenshots, or test output.

## Steps
- 2026-05-24T20:36:20Z: task created
- 2026-05-24T20:37:18Z: Set up ECNU measurement yibentong task
