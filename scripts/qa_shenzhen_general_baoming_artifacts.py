from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import zipfile

import fitz
from docx import Document


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.docx"
PDF = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.pdf"
PAGE_MAP = ROOT / "content/shenzhen_general_baoming_v1_page_map.json"
TITLE = "深圳大学347普通心理学保命手册"
HEADER = "深圳大学347｜普通心理学保命手册"


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def compute_page_map(pdf: fitz.Document) -> dict[str, int]:
    pages = [compact(page.get_text()) for page in pdf]
    first_body = next(
        index
        for index, text in enumerate(pages)
        if compact(HEADER) in text and compact("第一章 心理学的研究对象和方法") in text
    )
    stored = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    result: dict[str, int] = {}
    cursor = first_body
    for heading in stored:
        needle = compact(heading)
        found = next(index for index in range(cursor, len(pages)) if needle in pages[index])
        result[heading] = found - first_body + 1
        cursor = found
    return result


def main() -> None:
    assert DOCX.is_file() and PDF.is_file() and PAGE_MAP.is_file()
    with zipfile.ZipFile(DOCX) as archive:
        assert archive.testzip() is None

    document = Document(DOCX)
    assert len(document.sections) == 2
    assert len(document.tables) == 0
    cover_title = next(
        paragraph.text for paragraph in document.paragraphs
        if paragraph.style.name == "Title" and paragraph.text
    )
    assert cover_title == TITLE

    h1 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 1"]
    h2 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 2"]
    questions = [paragraph for paragraph in document.paragraphs if paragraph.text.startswith("押题")]
    all_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert len(h1) == 15 and len(h2) == 75 and len(questions) == 90
    assert all_text.count("【名词解释：") == 231
    assert "扩容（选背）" not in all_text and "扩容（选用）" not in all_text
    assert "到此停笔" not in all_text and "答题思路" not in all_text

    body_start = next(
        index for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style.name == "Heading 1"
    )
    body_sizes: list[float] = []
    type_sizes: list[float] = []
    definition_sizes: list[float] = []
    non_black = []
    styled = []
    for paragraph in document.paragraphs[body_start:]:
        for run in paragraph.runs:
            if not run.text:
                continue
            color = run.font.color.rgb
            if color is not None and str(color) != "000000":
                non_black.append((paragraph.text, run.text, str(color)))
            if run.font.italic or run.font.underline or run.font.highlight_color is not None:
                styled.append((paragraph.text, run.text))
            size = run.font.size.pt if run.font.size else None
            if paragraph.style.name == "Normal":
                assert size is not None
                body_sizes.append(size)
            if "【简答】" in run.text or "【论述】" in run.text:
                type_sizes.append(size)
            if "【名词解释：" in run.text:
                definition_sizes.append(size)
    assert body_sizes and set(body_sizes) == {12.0}
    assert type_sizes and set(type_sizes) == {12.0}
    assert definition_sizes and set(definition_sizes) == {12.0}
    assert not non_black, non_black[:5]
    assert not styled, styled[:5]

    pdf = fitz.open(PDF)
    assert len(pdf) == 87
    assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)
    page_texts = [page.get_text().strip() for page in pdf]
    assert all(page_texts)
    assert compact(page_texts[0]) == compact(TITLE)
    assert "使用说明" in page_texts[1]
    assert all(not page.get_images(full=True) for page in pdf)
    assert all(
        span["color"] == 0
        for page in pdf
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
    )
    for page in pdf:
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            assert x0 >= -1 and y0 >= -1 and x1 <= page.rect.width + 1 and y1 <= page.rect.height + 1

    stored_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert compute_page_map(pdf) == stored_map
    assert "0" not in re.findall(r"\.{3,}\s*(\d+)\s*$", "\n".join(page_texts[2:5]), re.MULTILINE)

    print(
        "PASS "
        f"pages={len(pdf)} chapters={len(h1)} units={len(h2)} questions={len(questions)} "
        f"definitions={all_text.count('【名词解释：')} body_sizes={Counter(body_sizes)} "
        f"type_sizes={Counter(type_sizes)} definition_sizes={Counter(definition_sizes)}"
    )


if __name__ == "__main__":
    main()
