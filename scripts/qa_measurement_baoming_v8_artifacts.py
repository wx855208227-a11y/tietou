from __future__ import annotations

import re
import zipfile
from pathlib import Path

import fitz
from lxml import etree

import qa_measurement_baoming_v6_artifacts as base_qa
from build_measurement_baoming_v8 import SOURCE, transform
from qa_baoming_full_v6_artifacts import W_NS, paragraph_text


BASE = Path("deliverables/华东师范大学347心理测量保命手册_全本_名解准入精校版V8")
PAGE_MAP = Path("content/measurement_baoming_v8_page_map.json")
CHAPTER_RE = re.compile(r"^第[^\s]+章")


def body_blocks(page: fitz.Page) -> list[tuple[float, float, str]]:
    values: list[tuple[float, float, str]] = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        text = "".join(
            span.get("text", "")
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ).strip()
        if not text:
            continue
        y0, y1 = block["bbox"][1], block["bbox"][3]
        if y0 < 55 or y1 > 800:
            continue
        values.append((y0, y1, text))
    return sorted(values)


def main() -> None:
    base_qa.BASE = BASE
    base_qa.MARKDOWN = BASE.with_suffix(".md")
    base_qa.DOCX = BASE.with_suffix(".docx")
    base_qa.PDF = BASE.with_suffix(".pdf")
    base_qa.PAGE_MAP = PAGE_MAP
    base_qa.VERSION = "V8"
    base_qa.EXPECTED_PAGES = 36
    base_qa.EXPECTED_DEFINITION_COUNT = 61
    base_qa.main()

    source = SOURCE.read_text(encoding="utf-8")
    markdown = BASE.with_suffix(".md").read_text(encoding="utf-8")
    assert markdown == transform(source)
    for term in ("16PF", "MMPI", "EPQ"):
        assert markdown.count(f"【名词解释：{term}】") == 1
    for term in ("E量表", "N量表", "P量表", "L量表"):
        assert f"【名词解释：{term}】" not in markdown

    with zipfile.ZipFile(BASE.with_suffix(".docx")) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    paragraphs = root.findall(f".//{{{W_NS}}}p")
    chapters = [
        paragraph
        for paragraph in paragraphs
        if CHAPTER_RE.match(paragraph_text(paragraph).strip())
        and paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pStyle") is not None
    ]
    assert len(chapters) == 11
    for paragraph in chapters[1:]:
        page_break = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pageBreakBefore")
        assert page_break is None or page_break.get(f"{{{W_NS}}}val", "1") in {
            "0",
            "false",
            "off",
        }, paragraph_text(paragraph)

    document = fitz.open(BASE.with_suffix(".pdf"))
    assert len(document) == 36
    max_internal_gap = 0.0
    excessive_bottom: list[tuple[int, float]] = []
    sparse_pages: list[tuple[int, int]] = []
    for page_number, page in enumerate(document[4:], start=5):
        blocks = body_blocks(page)
        assert blocks
        bottom_blank = 800 - blocks[-1][1]
        if bottom_blank > 250:
            excessive_bottom.append((page_number, bottom_blank))
        character_count = len(re.sub(r"\s+", "", page.get_text()))
        if character_count < 220:
            sparse_pages.append((page_number, character_count))
        for previous, current in zip(blocks, blocks[1:]):
            max_internal_gap = max(max_internal_gap, current[0] - previous[1])
    assert not excessive_bottom, excessive_bottom
    assert not sparse_pages, sparse_pages
    assert max_internal_gap < 22, max_internal_gap

    print(
        "测量保命手册V8名解与排版质检通过："
        "16PF／MMPI／EPQ完整名解各1处；E／N／P／L未误标；"
        f"pages={len(document)} body_pages={len(document) - 4} "
        f"excessive_bottom={len(excessive_bottom)} sparse_pages={len(sparse_pages)} "
        f"max_internal_gap={max_internal_gap:.1f}pt"
    )


if __name__ == "__main__":
    main()
