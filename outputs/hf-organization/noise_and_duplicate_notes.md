# HF Inventory Noise, Duplicate, And Ambiguity Notes

Source input: sanitized inventory `hf_file_inventory.tsv`. Findings below are based only on path names, file names, and listed sizes.

## Noise

- `.DS_Store`: 21 entries. These are macOS metadata files and should be deleted or ignored during migration.
- Upload/temp noise search: no filenames containing `upload`, `上传`, `tmp`, or `__MACOSX` appeared in the sanitized inventory. If the live clone has additional upload artifacts, they need a separate scan before migration.
- Root metadata: `.gitattributes` and root `README.md` are not study materials. Keep them as repository metadata or archive under `04_归档_迁移来源/hf_root_metadata/`.
- Many pdf/docx/jpg paths list sizes around 130-134 bytes in the sanitized inventory. Treat size as inventory metadata only; do not infer file validity or content from it.

## Duplicate Or Legacy Locations To Confirm

1. `教材/347应用心理专硕/华东师范大学/心理测量/心理测量 第三版.pdf` appears filename-related to `华东师范大学/教材/华东心理测量_第三版_金瑜.pdf`. Confirm before deduplication.
2. `教材/347应用心理专硕/深圳大学/普通心理学/普通心理学  彭聃龄版  第6版.pdf` appears filename-related to `深圳大学/教材/深大普通心理学_第6版_彭聃龄.pdf`. Confirm before deduplication.
3. `考纲/347应用心理专硕/华东师范大学/2025华东347心理学专业综合考试范围.pdf` overlaps the same school/category as `华东师范大学/考纲/华东硕士研究生入学考试大纲.pdf`, but the filenames do not prove they are the same document. Keep both until year/content is confirmed.
4. `深圳大学/考纲/深圳大学2026年硕士研究生入学考试大纲.docx` and `深圳大学/考纲/深圳大学2026年硕士研究生入学考试大纲——批注版.docx` should be separated as official source vs annotated working derivative.
5. Common textbook names appear across schools, especially 普通心理学 and 实验心理学. Do not deduplicate across schools by subject alone; edition, author, school requirement, and file identity must be confirmed.

## Ambiguous Items Needing Manager Confirmation

- `西北师范大学/一本通/西北师大发展心理学一本通(不完整版).docx`: mark as incomplete/draft unless manager confirms it is usable as final.
- `西北师范大学/一本通/西北师组织行为学一本通（不完整版本）.docx`: mark as incomplete/draft unless manager confirms it is usable as final.
- `西北师范大学/考纲/西北师范大学非全报考.docx`: filename suggests admission/program information rather than an exam outline. Confirm whether it belongs under `官方考纲`, `招生信息`, or `待确认`.
- `西北师范大学/真题/真题23-25/答案.pdf`: filename lacks year; confirm which exam year it answers.
- `西北师范大学/真题/答案10-22/参考答案2.pdf` and `参考答案3.pdf`: filenames do not identify year coverage; keep in `待拆分` until mapped.
- `西北师范大学/真题/真题10-22/西北347真题10-19/0521_1.jpg` through `0521_22.jpg`: image sequence lacks per-file year/page metadata; keep as one raw scanned collection until split.
- `华东师范大学/考纲/华东硕士研究生入学考试大纲.pdf`: no year in filename; if multiple years exist later, rename or index with confirmed year.
- `上海交通大学/真题/上交2026初试真题.jpg` and `上交2026初试真题答案.pdf`: filename maps them to 2026, but later review should verify whether the answer file covers the whole paper.

## Recommended Cleanup Policy

1. Remove `.DS_Store` from the material library and add an ignore rule if the storage workflow permits it.
2. Move legacy `教材/` and `考纲/` folders into a migration archive first; deduplicate only after confirmation.
3. Preserve raw scan collections until a reviewer maps pages to years and questions.
4. Use `待确认` for uncertain files rather than forcing them into official outline, true question, answer, or final 一本通 categories.
