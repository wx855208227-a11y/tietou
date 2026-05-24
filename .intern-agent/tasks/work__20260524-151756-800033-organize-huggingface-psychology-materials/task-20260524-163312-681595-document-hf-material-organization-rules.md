# Document HF material organization rules

- task_id: task-20260524-163312-681595-document-hf-material-organization-rules
- branch: work/20260524-151756-800033-organize-huggingface-psychology-materials
- branch_slug: work__20260524-151756-800033-organize-huggingface-psychology-materials
- created_utc: 2026-05-24T16:33:12Z
- status: active

## Description
用户要求：请把 HF 数据的整理思路也存在 md 中，方便之后新增数据继续整理。需要将确认过的 HF 资料库分类、整理判断顺序、命名、去重、确认和验证流程写入 Markdown，并推送保存。

## Review Brief
### Original Request
用户要求：请把 HF 数据的整理思路也存在 md 中，方便之后新增数据继续整理。需要将确认过的 HF 资料库分类、整理判断顺序、命名、去重、确认和验证流程写入 Markdown，并推送保存。

### Assigned Scope
- Create a reusable Markdown guide for future HuggingFace material organization.
- Store the guide in the GitHub project docs and in the HF dataset index so future agents can read it from either location.
- Update HF dataset entry points so the guide is discoverable.

### Deliverables
- GitHub doc: `docs/huggingface-material-organization.md`.
- HF dataset doc: `索引/HF资料整理思路.md`.
- HF dataset README and file index references to the new guide.

### Validation Plan
- Read the new Markdown files for completeness and consistency with the confirmed taxonomy.
- Check GitHub and HF git status before committing.
- Confirm HF index file remains tab-separated and includes the new guide.
- Push both the GitHub task branch and HF dataset commit.

### Constraints And Non-Goals
- Do not reorganize or delete additional HF files in this task.
- Do not print, move, or commit credentials.
- Keep the document focused on future HF data organization, not full 一本通 compilation rules.

### Claimed Output
- Added a reusable HF material organization guide to the GitHub project and the HF dataset.
- Updated the HF dataset README, file index, and cleanup log so future agents can discover the guide.
- HF dataset pushed to `main` at commit `72fd67a`.

### Artifacts And Evidence
- GitHub: `docs/huggingface-material-organization.md`.
- HF dataset: `索引/HF资料整理思路.md`.
- HF dataset references: `README.md`, `索引/资料目录.tsv`, `索引/清理记录.md`.
- Validation: TSV field check passed; `.DS_Store`/`test.tmp` check returned no files; HF LFS file count remained 101.

## Steps
- 2026-05-24T16:33:12Z: task created
- 2026-05-24T16:36:41Z: Document HF material organization workflow
  - pushed_commit: f4d4e5a
