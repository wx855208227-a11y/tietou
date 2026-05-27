# DOCX render preview format loop

- task_id: task-20260527-103202-282373-docx-render-preview-qa-gate
- branch: work/20260527-docx-render-preview-gate
- branch_slug: work__20260527-docx-render-preview-gate
- created_utc: 2026-05-27T10:32:02Z
- status: active

## Description
Create an independent Word/DOCX formatting render loop: after generating a 一本通 DOCX, convert it to PDF with LibreOffice, export page preview images, and write `format_report.md` so Codex can see real pagination and fix formatting problems in the DOCX generation logic before delivery.

## Review Brief
### Original Request
Create an independent Word/DOCX formatting render loop: after generating a 一本通 DOCX, convert it to PDF with LibreOffice, export page preview images, and write `format_report.md` so Codex can see real pagination and fix formatting problems in the DOCX generation logic before delivery. User clarified this is not primarily a QA task; it is a generation feedback loop for solving Word formatting problems.

### Assigned Scope
- Create an independent DOCX format feedback-loop subtask that does not modify prior 一本通 content deliverables.
- Install/use Linux headless rendering dependencies in the current Codex session where available.
- Add a reusable script that converts DOCX to PDF, renders page preview images, creates contact sheets, and writes `format_report.md`.
- Document the render loop and update 一本通 skill/requirements so future DOCX generation uses this feedback cycle before delivery.

### Deliverables
- `scripts/docx_format_preview.py`: reusable render-preview script for DOCX format repair.
- `docs/yibentong/docx-format-render-loop.md`: usage, dependencies, expected outputs, and generation-loop criteria.
- `.gitignore`: ignore generated `format-preview/` bundles.
- `skills/tietou-yibentong-compilation/SKILL.md`: require render-preview format loop for final/near-final DOCX generation.
- `skills/tietou-yibentong-compilation/references/requirements.md`: add render-preview format loop to formatting and self-check standards.

### Validation Plan
- Verify system tools: LibreOffice, `pdfinfo`, `pdftoppm`, `pdftotext`.
- Run `python3 -m py_compile scripts/docx_format_preview.py`.
- Run the script against a temporary smoke-test DOCX and confirm it outputs `output.docx`, `output.pdf`, `previews/page-*.png`, contact sheet PNG, `output.txt`, and `format_report.md`.
- Run it against an existing 一本通 DOCX sample to see whether it exposes practical format risks such as non-A4 pages, title colors, missing TOC fields, text-light pages, or page-layout risks.
- Run `git diff --check` before commit.

### Constraints And Non-Goals
- Do not alter previous 华东测量 一本通 content files or old `outputs/` artifacts.
- Do not commit generated render-preview output bundles.
- The render loop is used to fix DOCX generation; it is not a perfect replacement for Word/WPS manual review.
- Do not touch credentials or HF data.

### Claimed Output
- Installed the needed Linux rendering stack in the current session: LibreOffice Writer/Core/Common, Noto CJK fonts, and Poppler utilities.
- Added `scripts/docx_format_preview.py`, which copies a generated DOCX to a render bundle, exports PDF through LibreOffice, renders page PNGs through Poppler, creates contact sheets, extracts PDF text, analyzes basic page visual metrics, and writes `format_report.md`.
- Reframed the workflow as a DOCX generation feedback loop rather than standalone QA: render, inspect PDF/images/report, fix DOCX generator/style logic, rerender.
- Documented the workflow in `docs/yibentong/docx-format-render-loop.md` and updated 一本通 skill/requirements to require this loop for final/near-final DOCX generation.

### Artifacts And Evidence
- Changed files: `.gitignore`; `scripts/docx_format_preview.py`; `docs/yibentong/docx-format-render-loop.md`; `skills/tietou-yibentong-compilation/SKILL.md`; `skills/tietou-yibentong-compilation/references/requirements.md`; this task record.
- Smoke validation: `python3 -m py_compile scripts/docx_format_preview.py` passed.
- Smoke validation: temporary DOCX rendered to `format-preview/docx-render/smoke/` with `output.docx`, `output.pdf`, `previews/page-*.png`, `contact-sheet-01.png`, `output.txt`, and `format_report.md`.
- Real sample validation: `outputs/ecnu-347/measurement-psychology/chapter-01-yibentong-v11-selective-tips.docx` rendered to `format-preview/docx-render/ecnu-measurement-ch1-v11/`. Report showed A4 portrait was OK, but flagged missing Heading/TOC structure and possible blue text pages, demonstrating the loop can expose practical format problems.
- Generated render bundles are under ignored `format-preview/` and are not committed.

## Steps
- 2026-05-27T10:32:02Z: task created
- 2026-05-27T10:33Z: installed LibreOffice Writer/Core/Common, Noto CJK fonts, and confirmed Poppler tools are available in the Linux session.
- 2026-05-27T10:38Z: implemented initial DOCX render script, added documentation and skill/requirements updates, and smoke-tested DOCX -> PDF -> PNG previews -> report.
- 2026-05-27T10:45Z: user clarified this is a generation feedback loop, not a standalone QA task; renamed/reframed artifacts around format preview and iterative DOCX repair.
- 2026-05-27T10:48Z: added page-image metrics for bottom whitespace and possible blue rendered text; ran the loop on a temporary smoke DOCX and an existing 一本通 DOCX sample.
