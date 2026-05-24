# Organize HuggingFace psychology materials

- task_id: task-20260524-151757-705031-organize-huggingface-psychology-materials
- branch: work/20260524-151756-800033-organize-huggingface-psychology-materials
- branch_slug: work__20260524-151756-800033-organize-huggingface-psychology-materials
- created_utc: 2026-05-24T15:17:57Z
- status: active

## Description
User uploaded psychology考研 materials to HuggingFace dataset wx855208227/tietou, including four schools' official textbooks, official outlines, past papers, and existing 一本通 samples. Need classify and organize HF files for future yibentong compilation retrieval, following tietou manager-worker-reviewer workflow. Manager should use worker1/worker2 and reviewer, update skills if process issues appear, and push results.

## Review Brief
### Original Request
User uploaded psychology考研 materials to HuggingFace dataset wx855208227/tietou, including four schools' official textbooks, official outlines, past papers, and existing 一本通 samples. Need classify and organize HF files for future yibentong compilation retrieval, following tietou manager-worker-reviewer workflow. Manager should use worker1/worker2 and reviewer, update skills if process issues appear, and push results.

### Assigned Scope
- Organize the private HuggingFace dataset `wx855208227/tietou` so psychology考研 materials are easy to retrieve for later 一本通 compilation.
- Classify current materials by use in the 一本通 workflow: 院校库, official reference textbooks, official outlines, target-school true questions/answers, existing 一本通 samples, cross-school/312 auxiliary question banks, and compilation standards.
- Remove upload noise such as `.DS_Store`, consolidate duplicated legacy locations when safe, and add index/README documentation for future agents.
- Follow the manager-worker-reviewer workflow: worker plan/reorg outputs must be reviewed before final push.

### Deliverables
- HuggingFace dataset reorganized and pushed.
- GitHub repo documentation/index explaining the HF classification scheme for future agents.
- Sanitized file inventory and mapping/review artifacts for audit.
- Reviewer verdicts for worker milestone(s) and final integrated result.

### Validation Plan
- Compare pre/post HF file inventories and ensure no non-noise files are lost.
- Check directories follow the agreed taxonomy and support 一本通 retrieval: school -> material type -> subject/source.
- Verify `.DS_Store` and obvious upload noise are removed.
- Run `git status`, `git diff --stat`, and tree/listing checks in the HF clone before push.
- Ask `tietou_reviewer` to review plan/artifacts and final integrated HF tree before completion.

### Constraints And Non-Goals
- Do not expose or commit HF token or credential-bearing paths.
- Do not download large LFS files unless needed; filename/path-level organization is enough for this task.
- Do not alter file contents; only move/rename/remove upload noise and add index docs unless a reviewer-approved reason appears.
- Do not use unverified web materials as authoritative sources; HF organization is based on file names and supplied material categories.
- Only `tietou_manager` communicates with the user; workers and reviewer report to manager.

### Claimed Output
- HuggingFace dataset `wx855208227/tietou` reorganized locally in the HF clone and committed as `3c954e5 Organize psychology materials for retrieval` pending final reviewer approval and push.
- New HF taxonomy: `院校资料库/347应用心理专硕/<院校>/...`, `公共题库/312心理学统考/`, `公共题库/347应用心理专硕/`, `编制规范/一本通编制要求/`, and `索引/`.
- Added HF dataset docs/index: root `README.md`, `.gitignore`, `索引/资料目录.tsv`, and `索引/清理记录.md`.
- Generated GitHub audit artifacts under `outputs/hf-organization/`.
- Updated project/local `tietou-yibentong-compilation` skill with HF taxonomy, worker-stall fallback, `python3`, `lite-agent` PATH, and HF token/askpass handling notes.

### Artifacts And Evidence
- HF local commit: `3c954e5`.
- `outputs/hf-organization/hf_reorg_moves.tsv`: 101 move records, 27 remove records, 6 keep records.
- `outputs/hf-organization/hf_file_inventory_after.txt`: post-reorg file list, 110 files.
- `outputs/hf-organization/hf_lfs_before.txt` and `outputs/hf-organization/hf_lfs_after.txt`: LFS path audit.
- `outputs/hf-organization/hf_taxonomy.md`: taxonomy proposal and upload rules.
- `outputs/hf-organization/hf_validation_report.md`: validation summary and workflow issues.
- Validation: `.DS_Store` count is 0; unique LFS object ids before/after are both 98; missing unique LFS object ids 0; new unique LFS object ids 0.
- Workflow issue: `python` unavailable, use `python3`; `lite-agent` not on default PATH, use `/home/yileiyang/multi_agent/.venv/bin/lite-agent`; worker1/worker2 did not produce usable artifacts in time and worker1 left `outputs/hf-organization/test.tmp`, so manager completed a documented fallback pending reviewer review.

## Steps
- 2026-05-24T15:17:57Z: task created
- 2026-05-24T15:19:06Z: Record HF organization task plan
  - pushed_commit: c0983b7
- 2026-05-24T15:45:00Z: Reorganized HF dataset locally, added HF index docs, generated audit artifacts, and updated project/local skill with process fixes.
- 2026-05-24T15:30:58Z: Document HF material library reorganization
  - pushed_commit: d8a3029
