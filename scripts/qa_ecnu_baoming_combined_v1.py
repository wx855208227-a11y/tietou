from __future__ import annotations

import json
import zipfile
from collections import Counter
from pathlib import Path

import fitz
from docx import Document

from merge_ecnu_baoming_manuals import SOURCES, compact, source_chapters


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "deliverables/华东师范大学347保命手册_导论实验测量合订版V1.docx"
PDF = DOCX.with_suffix(".pdf")
PAGE_MAP = ROOT / "content/ecnu_baoming_combined_v1_page_map.json"


def source_body(document: Document) -> list[tuple[str, str]]:
    first_heading = next(
        index for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style.name == "Heading 1"
    )
    return [
        (paragraph.style.name, paragraph.text)
        for paragraph in document.paragraphs[first_heading:]
        if paragraph.text
    ]


def compute_pdf_page_map(pdf: fitz.Document) -> tuple[dict[str, int], dict[str, int]]:
    pages = [compact(page.get_text()) for page in pdf]
    part_indexes = {
        spec[0]: [index for index, text in enumerate(pages) if compact(spec[0]) in text][-1]
        for spec in SOURCES
    }
    first_body = part_indexes[SOURCES[0][0]]
    mapping: dict[str, int] = {}
    for subject_index, spec in enumerate(SOURCES):
        title = spec[0]
        start = part_indexes[title]
        stop = (
            part_indexes[SOURCES[subject_index + 1][0]]
            if subject_index + 1 < len(SOURCES)
            else len(pages)
        )
        mapping[title] = start - first_body + 1
        cursor = start
        for chapter in source_chapters(Document(spec[3])):
            needle = compact(chapter)
            found = next(index for index in range(cursor, stop) if needle in pages[index])
            mapping[f"{title}|{chapter}"] = found - first_body + 1
            cursor = found
    return mapping, part_indexes


def main() -> None:
    assert DOCX.exists() and PDF.exists() and PAGE_MAP.exists()
    with zipfile.ZipFile(DOCX) as archive:
        assert archive.testzip() is None

    merged = Document(DOCX)
    assert len(merged.sections) == 4
    assert len(merged.tables) == 0
    cover_title = next(
        paragraph.text for paragraph in merged.paragraphs
        if paragraph.style.name == "Title" and paragraph.text
    )
    assert cover_title == "华东师范大学347\n心理学保命手册"

    part_indexes = [
        index for index, paragraph in enumerate(merged.paragraphs)
        if paragraph.style.name == "Part Title"
    ]
    assert len(part_indexes) == 3
    for subject_index, spec in enumerate(SOURCES):
        expected = source_body(Document(spec[3]))
        start = part_indexes[subject_index] + 1
        stop = (
            part_indexes[subject_index + 1]
            if subject_index + 1 < len(part_indexes)
            else len(merged.paragraphs)
        )
        actual = [
            (paragraph.style.name, paragraph.text)
            for paragraph in merged.paragraphs[start:stop]
            if paragraph.text
        ]
        assert actual == expected, spec[1]

    source_documents = [Document(spec[3]) for spec in SOURCES]
    expected_h1 = sum(
        sum(paragraph.style.name == "Heading 1" for paragraph in document.paragraphs)
        for document in source_documents
    )
    expected_questions = sum(
        sum(paragraph.text.startswith("押题") for paragraph in document.paragraphs)
        for document in source_documents
    )
    expected_definitions = sum(
        "".join(paragraph.text for paragraph in document.paragraphs).count("【名词解释：")
        for document in source_documents
    )
    merged_text = "".join(paragraph.text for paragraph in merged.paragraphs)
    assert sum(paragraph.style.name == "Heading 1" for paragraph in merged.paragraphs) == expected_h1
    assert sum(paragraph.text.startswith("押题") for paragraph in merged.paragraphs) == expected_questions
    assert merged_text.count("【名词解释：") == expected_definitions
    assert "000" not in merged_text
    assert "扩容（选背）" not in merged_text and "扩容（选用）" not in merged_text
    assert "例子可灵活替换" not in merged_text

    body_started = False
    type_sizes: list[float | None] = []
    body_normal_sizes: list[float | None] = []
    for paragraph in merged.paragraphs:
        if paragraph.style.name == "Part Title":
            body_started = True
        if not body_started:
            continue
        for run in paragraph.runs:
            if not run.text:
                continue
            size = run.font.size.pt if run.font.size else None
            if paragraph.style.name == "Normal":
                body_normal_sizes.append(size)
            if "【简答】" in run.text or "【论述】" in run.text:
                type_sizes.append(size)
    assert type_sizes and set(type_sizes) == {12.0}
    assert body_normal_sizes and set(body_normal_sizes) == {12.0}

    pdf = fitz.open(PDF)
    page_texts = [page.get_text().strip() for page in pdf]
    assert len(pdf) == 189
    assert all(page_texts)
    assert compact(page_texts[0]) == compact("华东师范大学347心理学保命手册")
    assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)

    actual_page_map, pdf_part_indexes = compute_pdf_page_map(pdf)
    stored_page_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert actual_page_map == stored_page_map
    assert [pdf_part_indexes[spec[0]] for spec in SOURCES] == sorted(
        pdf_part_indexes[spec[0]] for spec in SOURCES
    )

    print(
        "PASS "
        f"pages={len(pdf)} body_pages={len(pdf) - pdf_part_indexes[SOURCES[0][0]]} "
        f"chapters={expected_h1} questions={expected_questions} definitions={expected_definitions} "
        f"type_font_sizes={Counter(type_sizes)}"
    )


if __name__ == "__main__":
    main()
