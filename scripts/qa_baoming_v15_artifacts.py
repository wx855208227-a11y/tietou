from __future__ import annotations

import re
import zipfile
from pathlib import Path

import fitz
from lxml import etree

from build_baoming_v15 import CHAPTERS
from render_baoming_inline_docx import V15_CATALOG_PAGE_MAP


BASE = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_总分总同行扩容版V15")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
LOCAL_EXPANSION_COUNT = sum(
    len(line.expansions)
    for _, units in CHAPTERS
    for unit in units
    for question in unit.questions
    for line in question.lines
)
FINAL_EXPANSION_COUNT = sum(
    len(question.final_expansions)
    for _, units in CHAPTERS
    for unit in units
    for question in unit.questions
)
EXPANSION_COUNT = LOCAL_EXPANSION_COUNT + FINAL_EXPANSION_COUNT
EXPANSION_PARAGRAPH_COUNT = sum(
    bool(line.expansions)
    for _, units in CHAPTERS
    for unit in units
    for question in unit.questions
    for line in question.lines
) + FINAL_EXPANSION_COUNT


def normalize(text: str) -> str:
    return re.sub(r"\s+|\u2060", "", text)


def is_black(color) -> bool:
    if color is None:
        return True
    if isinstance(color, int):
        return color == 0
    return all(abs(component) < 1e-8 for component in color)


def paragraph_text(paragraph) -> str:
    return "".join(
        node.text or "" for node in paragraph.findall(f".//{{{W_NS}}}t")
    ).replace("\u2060", "")


def run_is_bold(run) -> bool:
    bold = run.find(f"./{{{W_NS}}}rPr/{{{W_NS}}}b")
    return bold is not None and bold.get(f"{{{W_NS}}}val", "1").lower() not in {
        "0",
        "false",
        "off",
    }


def main() -> None:
    with zipfile.ZipFile(DOCX) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    docx_text = "".join(
        node.text or "" for node in root.findall(f".//{{{W_NS}}}t")
    ).replace("\u2060", "")
    colors = {node.get(f"{{{W_NS}}}val") for node in root.findall(f".//{{{W_NS}}}color")}
    assert colors == {"000000"}, colors
    assert not root.findall(f".//{{{W_NS}}}u"), "DOCX contains underline"
    italic_nodes = root.findall(f".//{{{W_NS}}}i")
    assert all(
        node.get(f"{{{W_NS}}}val", "1").lower() in {"0", "false", "off"}
        for node in italic_nodes
    ), "DOCX contains active italic"
    assert not root.findall(f".//{{{W_NS}}}highlight"), "DOCX contains highlight"
    assert not root.findall(f".//{{{W_NS}}}shd"), "DOCX contains shading"
    assert docx_text.count("押题") == 62  # 目录说明1次＋正文61次
    assert "答案" not in docx_text
    assert "【共用】" not in docx_text and "【本题补充】" not in docx_text
    assert "【加分项】" not in docx_text
    assert docx_text.count("【名词解释：") == 124
    assert docx_text.count("【扩容（选用）：") == EXPANSION_COUNT

    paragraphs = root.findall(f".//{{{W_NS}}}p")
    expansion_paragraphs = [
        paragraph for paragraph in paragraphs if "【扩容（选用）：" in paragraph_text(paragraph)
    ]
    standalone_expansions = [
        paragraph
        for paragraph in expansion_paragraphs
        if paragraph_text(paragraph).startswith("【扩容（选用）：")
    ]
    assert len(expansion_paragraphs) == EXPANSION_PARAGRAPH_COUNT
    assert len(standalone_expansions) == FINAL_EXPANSION_COUNT
    for paragraph in expansion_paragraphs:
        text = paragraph_text(paragraph)
        if paragraph in standalone_expansions:
            assert text.endswith("】")
        else:
            assert text.index("【扩容（选用）：") > 0

    expansion_prefix_runs = [
        run
        for run in root.findall(f".//{{{W_NS}}}r")
        if paragraph_text(run) == "【扩容（选用）："
    ]
    assert len(expansion_prefix_runs) == EXPANSION_COUNT
    for run in expansion_prefix_runs:
        assert run_is_bold(run)
        size = run.find(f"./{{{W_NS}}}rPr/{{{W_NS}}}sz")
        assert size is not None and int(size.get(f"{{{W_NS}}}val")) <= 19

    secondary_paragraphs = [
        paragraph
        for paragraph in paragraphs
        if re.match(r"^（\d+）", paragraph_text(paragraph))
    ]
    assert len(secondary_paragraphs) == 70
    for paragraph in secondary_paragraphs:
        indentation = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}ind")
        assert indentation is not None
        assert int(indentation.get(f"{{{W_NS}}}left")) >= 650
        assert int(indentation.get(f"{{{W_NS}}}hanging")) >= 250

    later_question_spacing: list[int] = []
    for paragraph in paragraphs:
        if not re.match(r"^押题(?:2|3)【", paragraph_text(paragraph)):
            continue
        spacing = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}spacing")
        assert spacing is not None
        later_question_spacing.append(int(spacing.get(f"{{{W_NS}}}before")))
    assert len(later_question_spacing) == 28
    assert min(later_question_spacing) >= 200

    document = fitz.open(PDF)
    assert len(document) == 30
    page_texts: list[str] = []
    image_blocks = 0
    overflow_blocks = 0
    non_black_spans = 0
    non_black_drawings = 0
    non_gray_pixels = 0
    italic_spans = 0
    for page in document:
        assert abs(page.rect.width - 595.276) < 1
        assert abs(page.rect.height - 841.89) < 1
        page_texts.append(page.get_text())
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
                    if span.get("flags", 0) & fitz.TEXT_FONT_ITALIC:
                        italic_spans += 1
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
    normalized_full_text = normalize(full_text)
    assert image_blocks == 0
    assert overflow_blocks == 0
    assert non_black_spans == 0
    assert non_black_drawings == 0
    assert non_gray_pixels == 0
    assert italic_spans == 0
    assert full_text.count("押题") == 62
    assert "答案" not in full_text
    assert normalized_full_text.count("【名词解释：") == 124
    assert normalized_full_text.count("【扩容（选用）：") == EXPANSION_COUNT
    assert not re.search(r"\n—\n", full_text)
    assert all(text.strip() for text in page_texts)

    body_pages = page_texts[2:]
    actual_map: dict[str, int] = {}
    for chapter, units in CHAPTERS:
        for target in (chapter, *(unit.title for unit in units)):
            needle = normalize(target)
            for body_page, text in enumerate(body_pages, start=1):
                if needle in normalize(text):
                    actual_map[target] = body_page
                    break
    assert actual_map == V15_CATALOG_PAGE_MAP, (actual_map, V15_CATALOG_PAGE_MAP)
    catalog_lines = [normalize(line) for line in page_texts[1].splitlines()]
    for title, page_number in V15_CATALOG_PAGE_MAP.items():
        needle = normalize(title)
        assert any(needle in line and line.endswith(str(page_number)) for line in catalog_lines), (
            title,
            page_number,
        )

    print(
        "V15制品质检通过 "
        f"pages={len(document)} body_pages={len(body_pages)} images={image_blocks} "
        f"overflow={overflow_blocks} non_black_spans={non_black_spans} "
        f"non_gray_pixels={non_gray_pixels} italic_spans={italic_spans} "
        f"secondary_points={len(secondary_paragraphs)} expansions={EXPANSION_COUNT} "
        f"standalone_expansions={len(standalone_expansions)} "
        f"question_gap_min_twips={min(later_question_spacing)}"
    )


if __name__ == "__main__":
    main()
