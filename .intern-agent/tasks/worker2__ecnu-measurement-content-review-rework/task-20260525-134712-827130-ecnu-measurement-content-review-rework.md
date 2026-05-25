# ECNU measurement content review rework

- task_id: task-20260525-134712-827130-ecnu-measurement-content-review-rework
- branch: worker2/ecnu-measurement-content-review-rework
- branch_slug: worker2__ecnu-measurement-content-review-rework
- created_utc: 2026-05-25T13:47:12Z
- status: complete

## Description
Manager task: inspect current ECNU measurement chapters 1-2 deliverables, scripts/generate_ecnu_measurement_ch1_2.py, and source notes. Identify exact student-facing process/rationale phrases to remove, bold-to-underline or missing key phrase markings, and redesign XLSX so the main sheet focuses on strong level-2 candidates and upgrade/keep decisions instead of listing all levels. Do not use HF 一本通 as content source. Output analysis/ecnu-measurement-ch1-2/worker2_content_review_rework.md, commit, push, and report to tietou_manager.

## Review Brief
### Original Request
Manager task: inspect current ECNU measurement chapters 1-2 deliverables, scripts/generate_ecnu_measurement_ch1_2.py, and source notes. Identify exact student-facing process/rationale phrases to remove, bold-to-underline or missing key phrase markings, and redesign XLSX so the main sheet focuses on strong level-2 candidates and upgrade/keep decisions instead of listing all levels. Do not use HF 一本通 as content source. Output analysis/ecnu-measurement-ch1-2/worker2_content_review_rework.md, commit, push, and report to tietou_manager.

### Assigned Scope
- Inspect current ECNU measurement chapters 1-2 deliverables, the generation script, and source notes on branch `worker2/ecnu-measurement-content-review-rework`.
- Produce a concrete content-review/rework checklist only; do not edit generated DOCX/XLSX content in this task.
- Focus on exact student-facing process/rationale phrases to remove, bold-to-underline or missing underline markings, and XLSX main-sheet redesign for strong level-2 review decisions.

### Deliverables
- `analysis/ecnu-measurement-ch1-2/worker2_content_review_rework.md`

### Validation Plan
- Confirm required markdown exists and contains sections for process/phrase cleanup, bold/underline rework, and XLSX redesign.
- Run `git diff --check` before commit.
- Confirm no HF clone or credential files were touched.

### Constraints And Non-Goals
- Do not use HF 一本通 as content source.
- Do not touch HF clone or credentials.
- Do not revert or overwrite other workers' edits.
- Do not contact the leader/user directly; report only to `tietou_manager`.

### Claimed Output
- Created `worker2_content_review_rework.md` with line-level cleanup items, marking changes, level sync notes, and a proposed workbook sheet/column redesign.

### Artifacts And Evidence
- Changed file: `analysis/ecnu-measurement-ch1-2/worker2_content_review_rework.md`.
- Validation: `git diff --check` passed; `rg` confirmed required sections/keywords in the new markdown.

## Steps
- 2026-05-25T13:47:12Z: task created
- 2026-05-25T13:53:51Z: completed - Add ECNU measurement content review rework
