# HF Psychology Material Library Taxonomy Proposal

Source input: sanitized inventory `hf_file_inventory.tsv` from task `task-20260524-151757-705031-organize-huggingface-psychology-materials`.

Scope note: this proposal classifies by filename and path only. It does not inspect file contents and does not move or edit the HuggingFace clone.

## Final Canonical Directory Taxonomy

The final target should use the current canonical HF taxonomy names, without numeric top-level prefixes.

```text
院校资料库/
  347应用心理专硕/
    <院校>/
      教材/
        <科目>/
          <教材名>_<版次>_<作者或出版社>.{ext}
      考纲/
        <年份或待确认>_<院校>_347_考试大纲.{ext}
        批注版/
          <年份或待确认>_<院校>_347_考试大纲_批注版.{ext}
      真题/
        试题/
          <年份>_<院校>_347_初试真题.{ext}
        答案/
          <年份>_<院校>_347_参考答案.{ext}
        待拆分/
          <原始扫描或未标年份文件>.{ext}
      一本通/
        正式版/
          <科目>_一本通.{ext}
        不完整或待复核/
          <科目>_一本通_<状态>.{ext}
      报考信息/
        <年份或待确认>_<院校>_报考信息.{ext}
      待确认/

公共题库/
  312心理学统考/
    真题详解/
      <资料名>.{ext}
  347应用心理专硕/
    <机构或系列>/
      试题册/
        <资料名>.{ext}
      解析册/
        <资料名>.{ext}

编制规范/
  一本通编制要求/
    README.md
    一本通编制要求及细则.pdf
    一本通编制要求及细则_抽取文本.txt
    一本通编制要求学习笔记.md

索引/
  资料目录.tsv
  清理记录.md
```

## Placement Rules

1. `院校资料库/347应用心理专硕/<院校>/` is the retrieval entry point for a school-specific 一本通 task. A compiler should find that school's教材、考纲、真题、一本通 and报考信息 there or through `索引/资料目录.tsv`.
2. School evidence stays separate from auxiliary evidence. Target-school true questions and official outlines belong in the school folder; 312 and generic 347 books belong under `公共题库/`.
3. School folders use canonical subdirectories only: `教材`、`考纲`、`真题`、`一本通`、`报考信息` and `待确认` when a filename cannot be classified safely.
4. Official outlines should retain year and school in filenames when the filename proves them. Annotated versions belong under `考纲/批注版/` so they are not mistaken for official source documents.
5. True questions and answers should be split by year only when filename evidence supports it. Scans or generic answer files without clear year mapping should remain in `真题/待拆分/`.
6. Existing 一本通 files should distinguish `正式版` from `不完整或待复核`. Filename terms such as `不完整版` or `不完整版本` should not be treated as final deliverables without manager confirmation.
7. `编制规范/一本通编制要求/` remains global and versioned separately from school materials, because every future 一本通 compilation needs the same rule source.
8. `索引/资料目录.tsv` should record every material's current path, proposed canonical path, school, material type, subject/collection, status, and confirmation needs. `索引/清理记录.md` should record `.DS_Store` cleanup, legacy paths, root metadata decisions, duplicate candidates, and unresolved migration notes.
9. Legacy top-level `教材/` and `考纲/` paths should not create a new final top-level archive. Map them to the relevant `院校资料库/.../教材` or `院校资料库/.../考纲` path only after confirmation; until then, record them in `索引/清理记录.md` as migration/duplicate candidates.

## Why This Supports 一本通 Compilation

- The workflow begins with a target school, so `院校资料库/347应用心理专硕/<院校>/` keeps decisive school evidence in one place.
- The taxonomy mirrors the required evidence hierarchy: assigned教材, official考纲, target-school真题, existing一本通, then auxiliary 312/泛347 evidence.
- Separating `院校资料库` from `公共题库` prevents generic 347 or 312 materials from being mistaken for decisive school evidence.
- The canonical school subdirectories match the current 一本通 workflow: choose school -> locate教材/考纲/真题/一本通 -> use公共题库 only as auxiliary evidence -> consult编制规范.
- `待确认` plus `索引/清理记录.md` preserve uncertain materials without forcing false deduplication or invented metadata.
- The taxonomy expands by adding more schools under `院校资料库/347应用心理专硕/` and by appending rows to `索引/资料目录.tsv`, without changing category semantics.

## Current Top-Level Inventory Accounting

| Current top-level path | Inventory count excluding `.DS_Store` | Proposed canonical target | Notes |
|---|---:|---|---|
| `.gitattributes` | 1 | repository root, with decision noted in `索引/清理记录.md` | Repository metadata, not study material. |
| `README.md` | 1 | repository root, with decision noted in `索引/清理记录.md` | Repository metadata, not study material. |
| `312心理学统考` | 2 | `公共题库/312心理学统考/真题详解/` | Auxiliary evidence only. |
| `347应用心理专硕` | 8 | `公共题库/347应用心理专硕/<机构或系列>/` | Generic 347 collections, not school-decisive evidence. |
| `上海交通大学` | 9 | `院校资料库/347应用心理专硕/上海交通大学/` | School folder has 一本通、教材、真题; no school-folder考纲 in inventory. |
| `华东师范大学` | 10 | `院校资料库/347应用心理专硕/华东师范大学/` | School folder has 一本通、教材、真题、考纲. |
| `深圳大学` | 11 | `院校资料库/347应用心理专硕/深圳大学/` | School folder has 一本通、教材、真题、考纲; one考纲批注版 should be separated from official source. |
| `西北师范大学` | 61 | `院校资料库/347应用心理专硕/西北师范大学/` | School folder has 一本通、教材、真题/答案、考纲; `非全报考` may belong in `报考信息` after confirmation. |
| `教材` | 4 | `索引/清理记录.md` first; after confirmation map to `院校资料库/347应用心理专硕/华东师范大学/教材/心理测量/` and `院校资料库/347应用心理专硕/深圳大学/教材/普通心理学/` as applicable | Legacy paths for 华东师范大学 and 深圳大学 textbooks; filenames suggest possible duplicates but do not prove identity. |
| `考纲` | 2 | `索引/清理记录.md` first; after confirmation map to `院校资料库/347应用心理专硕/华东师范大学/考纲/` | Legacy 华东师范大学考纲 path; relationship to school-folder考纲 needs confirmation. |
| `编制规范` | 4 | `编制规范/一本通编制要求/` | Global workflow/specification source. |

Inventory total: 134 entries. `.DS_Store` noise: 21 entries. Non-`.DS_Store` entries accounted above: 113.

## Migration Sequence

1. Remove or ignore `.DS_Store` files in the material library and record the cleanup in `索引/清理记录.md`.
2. Create the canonical target skeleton: `院校资料库/`、`公共题库/`、`编制规范/`、`索引/`.
3. Move current school folders into `院校资料库/347应用心理专硕/` without renaming files yet.
4. Within each school folder, classify path-based categories into `教材`、`考纲`、`真题`、`一本通`、`报考信息` or `待确认`.
5. Move top-level `312心理学统考` into `公共题库/312心理学统考/` and top-level generic `347应用心理专硕` into `公共题库/347应用心理专硕/`.
6. Move `编制规范` into `编制规范/一本通编制要求/`.
7. Record legacy `教材/` and `考纲/` rows in `索引/清理记录.md`; map or deduplicate them only after manager confirmation.
8. Rename true-question/answer files by year only when filename evidence supports the year; otherwise keep under `真题/待拆分/` and record the ambiguity in `索引/清理记录.md`.

## 待确认/可选建议

- A shared textbook library may become useful if many schools use the same official textbook. The current canonical HF taxonomy does not define `官方参考教材库` as a final top-level category, so this should remain a manager-confirmed optional extension rather than part of the final taxonomy.
- If approved later, a shared textbook index should avoid moving school-required教材 away from `院校资料库` unless `索引/资料目录.tsv` clearly points each school to the canonical copy and file identity has been confirmed.
