---
name: intern-agent-pdf-ocr-batch
description: Use whenever an intern agent processes PDFs, scanned pages, screenshots, rendered page images, OCR, image-heavy documents, or any workflow that may load multiple document images into the model; prevents 413 Payload Too Large errors by requiring local extraction and small-batch visual inspection.
---

# Intern Agent PDF/OCR Batch Processing

Use this skill before inspecting an uploaded PDF or image-heavy document, especially when the file contains screenshots, scanned pages, or pages without a text layer.

## Hard Rules

- Do not bulk-open rendered page images in the model. Never view many PDF page images in one turn.
- Inspect structure locally first: page count, text-layer character counts, image blocks, and which pages likely need OCR.
- Process visual pages in batches of at most 2-3 pages. Prefer crops of relevant regions over full-page images.
- Keep durable notes in the repo or agent directory, such as `analysis/pdf_inventory.md`, so `/clear` or a model failure does not lose the extraction work.
- If a request returns `413 Payload Too Large`, do not retry the same image-heavy request. Report that the request body is too large, reduce the visual batch, and continue from local notes.

## Workflow

1. Locate the uploaded file path from the Feishu attachment message.
2. Run local inventory before model vision. You can use the bundled helper:

   ```bash
   python <this-skill-dir>/scripts/pdf_inventory.py <pdf_path>
   ```

3. Extract text-layer content with local tools. Treat extracted text as the primary source for rules and prose.
4. For image-only or screenshot-heavy pages, render or OCR only the next small batch. Summarize each batch before opening more pages.
5. Separate source types explicitly in your output:
   - `正文规则`: text-layer instructions from the PDF.
   - `截图示例`: formatting examples or screenshots.
   - `OCR/图片不确定`: content that needs user or reviewer confirmation.
6. When the user asks for a reusable rule or skill, save the distilled rules to a file instead of relying only on chat memory.
7. For a project-specific PDF that should guide future agents, create or update a dedicated skill: keep concise trigger/workflow instructions in `SKILL.md`, move extracted detailed rules into `references/`, and record where the original PDF lives in the project repo. Future agents should read the skill/reference first and open the PDF only for exact wording, screenshots, or disputed details.

## Recovery After 413

- The current model context may already contain too many images. Ask whether to `/clear` if future turns keep failing.
- Before clearing, preserve extracted text, page inventory, and decisions in local files.
- After clearing, reload only the distilled notes and process additional pages in small batches.
