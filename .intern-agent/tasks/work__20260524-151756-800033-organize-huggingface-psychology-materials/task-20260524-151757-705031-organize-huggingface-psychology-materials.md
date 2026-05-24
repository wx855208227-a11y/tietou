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
- TODO: fill when reporting completion.

### Artifacts And Evidence
- TODO: fill with changed files, commits, generated artifacts, logs, screenshots, or test output.

## Steps
- 2026-05-24T15:17:57Z: task created
- 2026-05-24T15:19:06Z: Record HF organization task plan
