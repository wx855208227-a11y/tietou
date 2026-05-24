# HF Psychology Material Library Taxonomy Proposal

Source input: sanitized inventory `hf_file_inventory.tsv` from task `task-20260524-151757-705031-organize-huggingface-psychology-materials`.

Scope note: this proposal classifies by filename and path only. It does not inspect file contents and does not move or edit the HuggingFace clone.

## Final Directory Taxonomy

```text
00_编制规范/
  一本通编制要求/
    README.md
    一本通编制要求及细则.pdf
    一本通编制要求及细则_抽取文本.txt
    一本通编制要求学习笔记.md

01_院校库/
  347应用心理专硕/
    {学校}/
      00_院校索引.md
      01_官方考纲/
        {年份}_{学校}_{科目或专业综合}_官方考纲.{ext}
        批注版/
      02_官方参考教材/
        {科目}/
          {教材名}_{版次}_{作者}.{ext}
      03_历年真题/
        试题/{年份}_{学校}_347_初试真题.{ext}
        答案/{年份}_{学校}_347_参考答案.{ext}
        待拆分/{原始扫描或未标年份文件}.{ext}
      04_已编一本通/
        正式版/{科目}_一本通.{ext}
        不完整或待复核/{科目}_一本通_{状态}.{ext}
      90_待确认/

02_官方参考教材库/
  347应用心理专硕/
    {科目}/
      {教材名}_{版次}_{作者}/
        原始文件.{ext}
        适用院校索引.tsv
  312心理学统考/
    {科目}/

03_题库辅助/
  312统考辅助题库/
    真题详解/
  泛347辅助题库/
    {机构或系列}/
      试题册/
      解析册/

04_归档_迁移来源/
  legacy_教材/
  legacy_考纲/
  hf_root_metadata/

99_清理暂存/
  macos_ds_store_inventory.txt
  upload_or_temp_noise_inventory.txt
```

## Placement Rules

1. `01_院校库/347应用心理专硕/{学校}` is the retrieval entry point for a school-specific 一本通 task. A compiler should find the target school's official outline, official/reference textbooks, target-school true questions and answers, and existing 一本通 from this folder or its index.
2. School evidence stays separate from auxiliary evidence. Target-school true questions and official outlines belong in the school folder; 312 and generic 347 books belong under `03_题库辅助`.
3. Official/reference textbooks can be stored in the school folder when they are only used for that school. If the same textbook is used by multiple schools, keep one canonical copy under `02_官方参考教材库` and point each school index to it. Do not deduplicate until filenames and, if needed later, file content confirm equivalence.
4. Official outlines should retain year and school in filenames. Annotated versions should be under `批注版/` or a compilation-process subfolder so they are not mistaken for the official source.
5. True questions and answers should be split by year when the filename supports it. Scans or generic answer files without clear year mapping should remain in `待拆分/` or `90_待确认/`.
6. Existing 一本通 files should distinguish `正式版` from `不完整或待复核`. Filename terms such as `不完整版` or `不完整版本` should not be treated as final deliverables without manager confirmation.
7. `00_编制规范` remains global and versioned separately from school materials, because every future 一本通 compilation needs the same rule source.
8. Legacy top-level `教材/` and `考纲/` paths should be migrated only after review. Until then, retain their original path under `04_归档_迁移来源` and add a pointer from the target school or canonical textbook library.

## Why This Supports 一本通 Compilation

- The workflow begins with a target school, so the school-first structure reduces retrieval time and keeps decisive evidence in one place.
- The taxonomy mirrors the required evidence hierarchy: official textbooks/reference textbooks, official outlines, target-school true questions, existing 一本通, then auxiliary 312/泛347 evidence.
- Separating target-school materials from auxiliary题库 prevents generic 347 or 312 materials from being mistaken for decisive school evidence.
- A shared official textbook library supports future expansion because common textbooks such as 普通心理学 or 心理测量 can be reused by multiple schools without uncontrolled copies.
- `待确认` and `不完整或待复核` preserve uncertain materials without forcing a false classification, which matches the 一本通 rule to flag uncertainty rather than invent evidence.
- The taxonomy can expand to more schools, more exam years, and more subjects by adding school folders and updating `00_院校索引.md` or `适用院校索引.tsv` instead of changing category semantics.

## Current Top-Level Inventory Accounting

| Current top-level path | Inventory count excluding `.DS_Store` | Proposed target | Notes |
|---|---:|---|---|
| `.gitattributes` | 1 | `04_归档_迁移来源/hf_root_metadata/` or repository root | Repository metadata, not study material. |
| `README.md` | 1 | `04_归档_迁移来源/hf_root_metadata/` or repository root | Repository metadata, not study material. |
| `312心理学统考` | 2 | `03_题库辅助/312统考辅助题库/真题详解/` | Auxiliary evidence only. |
| `347应用心理专硕` | 8 | `03_题库辅助/泛347辅助题库/{机构或系列}/` | Generic 347 collections, not school-decisive evidence. |
| `上海交通大学` | 9 | `01_院校库/347应用心理专硕/上海交通大学/` | School folder has 一本通、教材、真题; no school-folder考纲 in inventory. |
| `华东师范大学` | 10 | `01_院校库/347应用心理专硕/华东师范大学/` | School folder has 一本通、教材、真题、考纲. |
| `深圳大学` | 11 | `01_院校库/347应用心理专硕/深圳大学/` | School folder has 一本通、教材、真题、考纲; one考纲批注版 should be separated from official source. |
| `西北师范大学` | 61 | `01_院校库/347应用心理专硕/西北师范大学/` | School folder has 一本通、教材、真题/答案、考纲; several files need year/status confirmation. |
| `教材` | 4 | `04_归档_迁移来源/legacy_教材/`, then `02_官方参考教材库/` after confirmation | Legacy paths for 华东师范大学 and 深圳大学 textbooks. |
| `考纲` | 2 | `04_归档_迁移来源/legacy_考纲/`, then target school考纲 after confirmation | Legacy 华东师范大学考纲 path. |
| `编制规范` | 4 | `00_编制规范/一本通编制要求/` | Global workflow/specification source. |

Inventory total: 134 entries. `.DS_Store` noise: 21 entries. Non-`.DS_Store` entries accounted above: 113.

## Migration Sequence

1. Remove or ignore `.DS_Store` files in the material library.
2. Create the target taxonomy skeleton and school indexes.
3. Move current school folders into `01_院校库/347应用心理专硕/` without renaming files yet.
4. Move `312心理学统考` and top-level `347应用心理专硕` into `03_题库辅助`.
5. Move `编制规范` into `00_编制规范`.
6. Put legacy `教材/` and `考纲/` under `04_归档_迁移来源`, then deduplicate or link only after manager confirmation.
7. Rename true-question/answer files by year only when filename evidence supports the year; otherwise keep under `待拆分`.
