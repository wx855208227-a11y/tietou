from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

import fitz
from docx import Document

from build_shenzhen_subject_page_map import compact, heading_keys


ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V13.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V13.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V13.pdf",
        ROOT / "content/shenzhen_general_baoming_v13_page_map.json",
        (15, 75, 90, 236),
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V12.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V12.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V12.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v12_page_map.json",
        (4, 25, 25, 50),
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V12.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V12.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V12.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v12_page_map.json",
        (13, 39, 45, 76),
    ),
)


def validate_docx(docx_path: Path, expected: tuple[int, int, int, int]) -> None:
    with zipfile.ZipFile(docx_path) as archive:
        assert archive.testzip() is None
    document = Document(docx_path)
    h1 = [p for p in document.paragraphs if p.style.name == "Heading 1"]
    h2 = [p for p in document.paragraphs if p.style.name == "Heading 2"]
    questions = [p for p in document.paragraphs if p.text.startswith("押题")]
    all_text = "\n".join(p.text for p in document.paragraphs)
    assert (len(h1), len(h2), len(questions), all_text.count("【名词解释：")) == expected

    body_started = False
    body_sizes: set[float] = set()
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            body_started = True
            continue
        if not body_started:
            continue
        if paragraph.style.name == "Normal":
            for run in paragraph.runs:
                if run.text.strip() and run.font.size:
                    body_sizes.add(round(run.font.size.pt, 2))
        if paragraph.text.startswith("押题"):
            sizes = {round(run.font.size.pt, 2) for run in paragraph.runs if run.text.strip() and run.font.size}
            assert sizes == {12.0}, (paragraph.text, sizes)
    assert body_sizes == {12.0}, body_sizes


def validate_pdf(markdown: Path, pdf_path: Path, map_path: Path) -> tuple[int, int]:
    document = fitz.open(pdf_path)
    pages = [compact(page.get_text()) for page in document]
    assert all(pages)
    assert all(not page.get_images(full=True) for page in document)

    for page in document:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        assert span["color"] == 0, (page.number + 1, span["text"], span["color"])

    keys = heading_keys(markdown)
    first_hits = [index for index, text in enumerate(pages) if compact(keys[0]) in text]
    assert len(first_hits) >= 2
    first_body = first_hits[-1]
    cursor = first_body
    actual: dict[str, int] = {}
    for key in keys:
        found = next(index for index in range(cursor, len(pages)) if compact(key) in pages[index])
        actual[key] = found - first_body + 1
        cursor = found
    assert actual == json.loads(map_path.read_text(encoding="utf-8"))

    chapter_keys = [
        line[2:].strip().split("【", 1)[0]
        for line in markdown.read_text(encoding="utf-8").splitlines()
        if line.startswith("# ") and not line.startswith("# 深圳大学")
    ]
    for chapter in chapter_keys:
        page_index = next(index for index in range(first_body, len(pages)) if compact(chapter) in pages[index])
        blocks = [b for b in document[page_index].get_text("blocks") if compact(chapter) in compact(b[4])]
        assert blocks and min(block[1] for block in blocks) < 125, (chapter, page_index + 1, blocks)

    catalog_text = "\n".join(page.get_text() for page in document[:first_body])
    assert not re.search(r"\.{3,}\s*0\s*$", catalog_text, re.MULTILINE)
    return len(document), len(document) - first_body


def main() -> None:
    for subject, markdown, docx, pdf, page_map, expected in SPECS:
        assert all(path.is_file() for path in (markdown, docx, pdf, page_map))
        validate_docx(docx, expected)
        pages, body_pages = validate_pdf(markdown, pdf, page_map)
        print(
            f"PASS {subject} pages={pages} body_pages={body_pages} "
            f"chapters={expected[0]} units={expected[1]} questions={expected[2]} definitions={expected[3]}"
        )


if __name__ == "__main__":
    main()
