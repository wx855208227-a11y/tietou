# Ambiguous Move Items

Do not move or delete these items in the HuggingFace clone without manager decision. They were flagged from filename/path only; no file contents were inspected.

| old_path | candidate_target | issue | recommended decision |
|---|---|---|---|
| `教材/347应用心理专硕/华东师范大学/心理测量/README.md` | `院校资料库/347应用心理专硕/华东师范大学/教材/心理测量/README.md` | Legacy subject README may duplicate the new school index or contain subject-specific notes. | Inspect text and either merge into the school/subject README or `git mv` as a retained subject README. |
| `教材/347应用心理专硕/华东师范大学/心理测量/心理测量 第三版.pdf` | `院校资料库/347应用心理专硕/华东师范大学/教材/心理测量/心理测量 第三版.pdf` | Filename overlaps with `华东师范大学/教材/华东心理测量_第三版_金瑜.pdf`; size metadata also differs, so it may be a full file vs an LFS pointer or a duplicate edition. | Compare Git/LFS object and filename metadata before moving; do not delete unless duplicate is confirmed. |
| `教材/347应用心理专硕/深圳大学/普通心理学/README.md` | `院校资料库/347应用心理专硕/深圳大学/教材/普通心理学/README.md` | Legacy subject README may duplicate the new school index or contain subject-specific notes. | Inspect text and either merge into the school/subject README or `git mv` as a retained subject README. |
| `教材/347应用心理专硕/深圳大学/普通心理学/普通心理学  彭聃龄版  第6版.pdf` | `院校资料库/347应用心理专硕/深圳大学/教材/普通心理学/普通心理学  彭聃龄版  第6版.pdf` | Filename overlaps with `深圳大学/教材/深大普通心理学_第6版_彭聃龄.pdf`; size metadata also differs, so it may be a full file vs an LFS pointer or a duplicate edition. | Compare Git/LFS object and filename metadata before moving; do not delete unless duplicate is confirmed. |
| `西北师范大学/考纲/西北师范大学非全报考.docx` | `院校资料库/347应用心理专硕/西北师范大学/招生信息/西北师范大学非全报考.docx` or `院校资料库/347应用心理专硕/西北师范大学/考纲/西北师范大学非全报考.docx` | Filename suggests non-full-time admissions/application information rather than a pure exam outline. | Manager should choose `招生信息` vs `考纲`; keep in place until decided. |

Notes:

- The move TSV marks these as `review_merge`, `review_duplicate`, or `review_move` rather than executable `move`/`delete` rows.
- No duplicate deletion is proposed without manager confirmation.
- Incomplete filenames such as `不完整版` are not target-path ambiguous; move them with their current filenames but mention their status in the future per-school README.
