# Rework HF taxonomy canonical paths

- task_id: task-20260525-193401-326316-rework-hf-taxonomy-canonical-paths
- branch: worker1/hf-taxonomy-plan
- branch_slug: worker1__hf-taxonomy-plan
- created_utc: 2026-05-25T19:34:01Z
- status: complete

## Description
Review result NEEDS REWORK for task-20260524-151757-705031-organize-huggingface-psychology-materials. Revise branch outputs only on worker1/hf-taxonomy-plan so taxonomy_proposal aligns with canonical HF taxonomy from yibentong skill: 院校资料库/347应用心理专硕/<院校>/教材|考纲|真题|一本通|报考信息, 公共题库/312心理学统考, 公共题库/347应用心理专硕, 编制规范/一本通编制要求, 索引/资料目录.tsv and 索引/清理记录.md. Update current top-level inventory accounting target paths, legacy 教材/考纲 mapping, optional shared textbook note only as 待确认/可选建议. Preserve no content inspection, no false dedupe, .DS_Store cleanup, ambiguity notes, school/public题库 separation. Validate TSV 5 columns, file_count sum=113, top-level coverage, git diff --check, clean status, push, report.

## Review Brief
### Original Request
Review result NEEDS REWORK for task-20260524-151757-705031-organize-huggingface-psychology-materials. Revise branch outputs only on worker1/hf-taxonomy-plan so taxonomy_proposal aligns with canonical HF taxonomy from yibentong skill: 院校资料库/347应用心理专硕/<院校>/教材|考纲|真题|一本通|报考信息, 公共题库/312心理学统考, 公共题库/347应用心理专硕, 编制规范/一本通编制要求, 索引/资料目录.tsv and 索引/清理记录.md. Update current top-level inventory accounting target paths, legacy 教材/考纲 mapping, optional shared textbook note only as 待确认/可选建议. Preserve no content inspection, no false dedupe, .DS_Store cleanup, ambiguity notes, school/public题库 separation. Validate TSV 5 columns, file_count sum=113, top-level coverage, git diff --check, clean status, push, report.

### Assigned Scope
- Rework only the branch output files for the HF psychology material taxonomy plan.
- Align the proposed final taxonomy and top-level inventory accounting with canonical paths: `院校资料库/347应用心理专硕/<院校>/教材|考纲|真题|一本通|报考信息`, `公共题库/312心理学统考`, `公共题库/347应用心理专硕`, `编制规范/一本通编制要求`, and `索引/资料目录.tsv` / `索引/清理记录.md`.
- Preserve path/filename-only classification, ambiguity flags, `.DS_Store` cleanup notes, and school vs public题库 separation.

### Deliverables
- Revised `outputs/hf-organization/taxonomy_proposal.md`.
- Targeted consistency updates to `outputs/hf-organization/school_material_summary.tsv` and `outputs/hf-organization/noise_and_duplicate_notes.md` where they referenced rejected numeric or migration-archive paths.

### Validation Plan
- TSV five-column check for `school_material_summary.tsv`.
- Confirm `file_count` sum remains 113.
- Confirm all current non-`.DS_Store` top-level inventory categories are represented in `taxonomy_proposal.md`.
- Run `git diff --check`.
- Confirm clean status after commit and push.

### Constraints And Non-Goals
- Do not edit the HF clone or credentials.
- Do not inspect content; classify by sanitized inventory path/filename only.
- Do not introduce numeric final top-level taxonomy names or a final `04_归档`/shared textbook-library top-level.
- Keep any shared textbook library idea under a clearly labeled optional/manager-confirmation section only.

### Claimed Output
- Replaced the final taxonomy with canonical Chinese top-level names and canonical school/public题库/index/specification paths.
- Updated top-level inventory accounting so legacy `教材/` and `考纲/` map first to `索引/清理记录.md`, then to relevant school paths only after confirmation.
- Kept shared textbook library as `待确认/可选建议`, not as final taxonomy.
- Updated notes that still pointed to numeric `03_题库辅助` or final migration archive paths.

### Artifacts And Evidence
- Changed files: `outputs/hf-organization/taxonomy_proposal.md`, `outputs/hf-organization/school_material_summary.tsv`, `outputs/hf-organization/noise_and_duplicate_notes.md`.
- Validation: TSV 5-column check returned `TSV_OK`; TSV file_count sum returned `113`; top-level coverage check returned `missing NONE`, `non_ds_total 113`, `ds_total 21`; `git diff --check` passed.
- Risks: all classification remains path/filename-only; duplicate candidates and legacy mappings still require manager confirmation before moving or deduplicating files.

## Steps
- 2026-05-25T19:34:01Z: task created
- 2026-05-25T19:42:00Z: revised taxonomy outputs to canonical HF paths and validated TSV/count/top-level coverage/diff check.
- 2026-05-25T19:36:20Z: completed - Align HF taxonomy plan with canonical paths
  - pushed_commit: 11ffbca
