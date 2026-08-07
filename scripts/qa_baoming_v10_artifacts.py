from __future__ import annotations

import re
import zipfile
from pathlib import Path

import fitz
from lxml import etree

from build_baoming_v10 import CHAPTERS
from render_baoming_inline_docx import V10_CATALOG_PAGE_MAP


BASE = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_共用补充双加分版V10")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def is_black(color) -> bool:
    if color is None:
        return True
    if isinstance(color, int):
        return color == 0
    return all(abs(component) < 1e-8 for component in color)


def main() -> None:
    with zipfile.ZipFile(DOCX) as archive:
        xml = archive.read("word/document.xml")
    root = etree.fromstring(xml)
    colors = {
        node.get(f"{{{W_NS}}}val")
        for node in root.findall(f".//{{{W_NS}}}color")
    }
    assert colors == {"000000"}, colors
    assert not root.findall(f".//{{{W_NS}}}u"), "DOCX contains underline"
    assert not root.findall(f".//{{{W_NS}}}highlight"), "DOCX contains highlight"
    assert not root.findall(f".//{{{W_NS}}}shd"), "DOCX contains shading"
    docx_text = "".join(node.text or "" for node in root.findall(f".//{{{W_NS}}}t"))
    assert "**" not in docx_text
    assert "答题思路" not in docx_text
    assert docx_text.count("押题") == 63  # 62题＋目录用法提示1处
    assert docx_text.count("答案") >= 63

    document = fitz.open(PDF)
    assert len(document) == 23
    page_texts: list[str] = []
    image_blocks = 0
    overflow_blocks = 0
    non_black_spans = 0
    non_black_drawings = 0
    non_gray_pixels = 0
    for page in document:
        assert abs(page.rect.width - 595.276) < 1
        assert abs(page.rect.height - 841.89) < 1
        page_text = page.get_text()
        page_texts.append(page_text)
        page_dict = page.get_text("dict")
        for block in page_dict["blocks"]:
            if block["type"] == 1:
                image_blocks += 1
            if block["type"] != 0:
                continue
            x0, y0, x1, y1 = block["bbox"]
            if x0 < -0.5 or y0 < -0.5 or x1 > page.rect.width + 0.5 or y1 > page.rect.height + 0.5:
                overflow_blocks += 1
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if not is_black(span.get("color")):
                        non_black_spans += 1
        for drawing in page.get_drawings():
            if not is_black(drawing.get("color")) or not is_black(drawing.get("fill")):
                non_black_drawings += 1

        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
        samples = memoryview(pix.samples)
        non_gray_pixels += sum(
            1
            for offset in range(0, len(samples), pix.n)
            if not (samples[offset] == samples[offset + 1] == samples[offset + 2])
        )

    full_text = "\n".join(page_texts)
    assert image_blocks == 0
    assert overflow_blocks == 0
    assert non_black_spans == 0
    assert non_black_drawings == 0
    assert non_gray_pixels == 0
    assert "**" not in full_text
    assert full_text.count("押题") == 63
    assert full_text.count("答案") >= 63
    assert full_text.count("【名词解释：") == 123
    assert all(page.get_text().strip() for page in document)

    body_pages = page_texts[2:]
    actual_map: dict[str, int] = {}
    for chapter, units in CHAPTERS:
        for target in (chapter, *(unit.title for unit in units)):
            needle = normalize(target)
            for body_page, text in enumerate(body_pages, start=1):
                if needle in normalize(text):
                    actual_map[target] = body_page
                    break
    assert actual_map == V10_CATALOG_PAGE_MAP, (actual_map, V10_CATALOG_PAGE_MAP)

    print(
        "PASS "
        f"pages={len(document)} body_pages={len(body_pages)} images={image_blocks} "
        f"overflow={overflow_blocks} non_black_spans={non_black_spans} "
        f"non_black_drawings={non_black_drawings} non_gray_pixels={non_gray_pixels}"
    )


if __name__ == "__main__":
    main()
