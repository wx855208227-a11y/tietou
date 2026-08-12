from __future__ import annotations

import re
import zipfile
from pathlib import Path

import fitz
from lxml import etree

import qa_measurement_baoming_v6_artifacts as base_qa
from build_measurement_baoming_v9 import SOURCE, transform
from qa_baoming_full_v6_artifacts import W_NS, compact, paragraph_text


BASE = Path("deliverables/华东师范大学347心理测量保命手册_全本_逐章分页精校版V9")
PAGE_MAP = Path("content/measurement_baoming_v9_page_map.json")
HEADER = "华东师范大学347｜心理测量保命手册"
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


def meaningful_lines(page: fitz.Page) -> list[str]:
    return [
        line.strip()
        for line in page.get_text().splitlines()
        if line.strip() and line.strip() != HEADER and not line.strip().isdigit()
    ]


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    markdown = BASE.with_suffix(".md").read_text(encoding="utf-8")
    assert markdown == transform(source)
    chapter_titles = [
        line[2:].strip() for line in markdown.splitlines() if line.startswith("# 第")
    ]
    assert len(chapter_titles) == 11

    document = fitz.open(BASE.with_suffix(".pdf"))
    page_texts = [page.get_text() for page in document]
    chapter_pages: list[int] = []
    for title in chapter_titles:
        matches = [
            index + 1
            for index, text in enumerate(page_texts)
            if compact(title) in compact(text)
        ]
        assert matches, title
        physical_page = matches[-1]
        chapter_pages.append(physical_page)
        lines = meaningful_lines(document[physical_page - 1])
        assert lines and compact(lines[0]) == compact(title), (title, physical_page, lines[:2])
    assert chapter_pages == sorted(set(chapter_pages))
    structural_end_pages = {page - 1 for page in chapter_pages[1:]}

    base_qa.BASE = BASE
    base_qa.MARKDOWN = BASE.with_suffix(".md")
    base_qa.DOCX = BASE.with_suffix(".docx")
    base_qa.PDF = BASE.with_suffix(".pdf")
    base_qa.PAGE_MAP = PAGE_MAP
    base_qa.VERSION = "V9"
    base_qa.EXPECTED_PAGES = 42
    base_qa.EXPECTED_DEFINITION_COUNT = 61
    base_qa.ALLOWED_SPARSE_PHYSICAL_PAGES = structural_end_pages
    base_qa.main()

    with zipfile.ZipFile(BASE.with_suffix(".docx")) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    paragraphs = root.findall(f".//{{{W_NS}}}p")
    chapter_paragraphs = [
        paragraph
        for paragraph in paragraphs
        if CHAPTER_RE.match(paragraph_text(paragraph).strip())
        and paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pStyle") is not None
    ]
    assert len(chapter_paragraphs) == 11
    first_break = chapter_paragraphs[0].find(
        f"./{{{W_NS}}}pPr/{{{W_NS}}}pageBreakBefore"
    )
    assert first_break is None or first_break.get(f"{{{W_NS}}}val", "1") in {
        "0",
        "false",
        "off",
    }
    for paragraph in chapter_paragraphs[1:]:
        page_break = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pageBreakBefore")
        assert page_break is not None
        assert page_break.get(f"{{{W_NS}}}val", "1") not in {"0", "false", "off"}

    max_internal_gap = 0.0
    internal_bottom_blank: list[tuple[int, float]] = []
    internal_sparse_pages: list[tuple[int, int]] = []
    orphan_endings: list[tuple[int, str]] = []
    for physical_page, page in enumerate(document[4:], start=5):
        blocks = body_blocks(page)
        assert blocks
        structural = physical_page in structural_end_pages or physical_page == len(document)
        bottom_blank = 800 - blocks[-1][1]
        character_count = len(re.sub(r"\s+", "", page.get_text()))
        if not structural and bottom_blank > 250:
            internal_bottom_blank.append((physical_page, bottom_blank))
        if not structural and character_count < 220:
            internal_sparse_pages.append((physical_page, character_count))
        for previous, current in zip(blocks, blocks[1:]):
            max_internal_gap = max(max_internal_gap, current[0] - previous[1])
        lines = meaningful_lines(page)
        if lines and (
            lines[-1].endswith("：")
            or re.match(
                r"^(?:第[^ ]+章|押题\d+【|[一二三四五六七八九十]+、.*【★{1,3}】)$",
                lines[-1],
            )
        ):
            orphan_endings.append((physical_page, lines[-1]))
    assert not internal_bottom_blank, internal_bottom_blank
    assert not internal_sparse_pages, internal_sparse_pages
    assert not orphan_endings, orphan_endings
    assert max_internal_gap < 22, max_internal_gap

    print(
        "测量保命手册V9逐章分页质检通过："
        f"chapter_pages={chapter_pages} chapter_breaks=10 pages={len(document)} "
        f"structural_end_pages={len(structural_end_pages)} "
        f"internal_blank={len(internal_bottom_blank)} internal_sparse={len(internal_sparse_pages)} "
        f"orphan_endings={len(orphan_endings)} max_internal_gap={max_internal_gap:.1f}pt"
    )


if __name__ == "__main__":
    main()
