from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path

import fitz
from lxml import etree

from build_baoming_v11 import CHAPTERS
from render_baoming_inline_docx import V11_CATALOG_PAGE_MAP


BASE = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_正斜体区分版V11")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text)


def plain(markdown: str) -> str:
    return re.sub(r"[\*_]+", "", markdown)


def run_is_italic(run) -> bool:
    italic = run.find(f"./{{{W_NS}}}rPr/{{{W_NS}}}i")
    if italic is None:
        return False
    return italic.get(f"{{{W_NS}}}val", "1").lower() not in {"0", "false", "off"}


def run_is_bold(run) -> bool:
    bold = run.find(f"./{{{W_NS}}}rPr/{{{W_NS}}}b")
    if bold is None:
        return False
    return bold.get(f"{{{W_NS}}}val", "1").lower() not in {"0", "false", "off"}


def is_black(color) -> bool:
    if color is None:
        return True
    if isinstance(color, int):
        return color == 0
    return all(abs(component) < 1e-8 for component in color)


def main() -> None:
    questions = [item for _, units in CHAPTERS for unit in units for item in unit.questions]
    module_uses = Counter(
        module
        for item in questions
        for module in (*item.leads, *item.points, *item.bonus_points)
    )
    roman_uses = sum(count for count in module_uses.values() if count > 1)
    italic_uses = sum(count for count in module_uses.values() if count == 1)
    point_bonus_uses = sum(
        count for module, count in module_uses.items() if "【采分点加分】" in module
    )
    answer_bonus_blocks = sum(bool(item.bonus_points) for item in questions)

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
    docx_text = "".join(node.text or "" for node in root.findall(f".//{{{W_NS}}}t")).replace("\u2060", "")
    assert "**" not in docx_text
    assert "答题思路" not in docx_text
    assert docx_text.count("押题") == 62
    assert docx_text.count("答案") >= 63
    assert "【共用】" not in docx_text
    assert "【本题补充】" not in docx_text
    assert "正文中的正体表示多题重复内容，斜体表示只在本题新增的内容" in docx_text
    assert docx_text.count("【采分点加分】") == point_bonus_uses + 1
    assert docx_text.count("【整体加分】") == answer_bonus_blocks + 1

    expected_paragraphs: Counter[tuple[str, bool]] = Counter()
    for item in questions:
        for module in item.leads:
            expected_paragraphs[(normalize(plain(module)), module_uses[module] == 1)] += 1
        for point_number, module in enumerate(item.points, start=1):
            key = normalize(f"{point_number}. {plain(module)}")
            expected_paragraphs[(key, module_uses[module] == 1)] += 1
        first_bonus_number = len(item.points) + 1
        for point_number, module in enumerate(item.bonus_points, start=first_bonus_number):
            key = normalize(f"{point_number}. {plain(module)}")
            expected_paragraphs[(key, module_uses[module] == 1)] += 1

    actual_paragraphs: Counter[tuple[str, bool]] = Counter()
    italic_bold_paragraphs = 0
    expected_texts = {text for text, _ in expected_paragraphs}
    expected_styles = {text: italic for text, italic in expected_paragraphs}
    for paragraph in root.findall(f".//{{{W_NS}}}p"):
        runs = paragraph.findall(f"./{{{W_NS}}}r")
        paragraph_text = normalize(
            "".join(
                node.text or ""
                for run in runs
                for node in run.findall(f".//{{{W_NS}}}t")
            ).replace("\u2060", "")
        )
        if paragraph_text not in expected_texts:
            continue
        should_be_italic = expected_styles[paragraph_text]
        actual_paragraphs[(paragraph_text, should_be_italic)] += 1
        italic_text = normalize(
            "".join(
                node.text or ""
                for run in runs
                if run_is_italic(run)
                for node in run.findall(f".//{{{W_NS}}}t")
            ).replace("\u2060", "")
        )
        roman_text = normalize(
            "".join(
                node.text or ""
                for run in runs
                if not run_is_italic(run)
                for node in run.findall(f".//{{{W_NS}}}t")
            ).replace("\u2060", "")
        )
        if should_be_italic:
            assert italic_text
            assert re.sub(r"^\d+\.", "", roman_text) == "", (paragraph_text, roman_text)
            if any(run_is_italic(run) and run_is_bold(run) for run in runs):
                italic_bold_paragraphs += 1
        else:
            assert not italic_text, paragraph_text
    assert actual_paragraphs == expected_paragraphs
    assert sum(count for (_, italic), count in actual_paragraphs.items() if italic) == italic_uses
    assert sum(count for (_, italic), count in actual_paragraphs.items() if not italic) == roman_uses
    assert italic_bold_paragraphs == italic_uses

    later_question_spacing: list[int] = []
    for paragraph in root.findall(f".//{{{W_NS}}}p"):
        paragraph_text = "".join(
            node.text or "" for node in paragraph.findall(f".//{{{W_NS}}}t")
        ).replace("\u2060", "")
        if not re.match(r"^押题(?:2|3)【", paragraph_text):
            continue
        spacing = paragraph.find(
            f"./{{{W_NS}}}pPr/{{{W_NS}}}spacing"
        )
        assert spacing is not None
        later_question_spacing.append(int(spacing.get(f"{{{W_NS}}}before")))
    assert len(later_question_spacing) == 29
    assert min(later_question_spacing) >= 200  # 10pt，明显大于答案内部段间距

    document = fitz.open(PDF)
    assert len(document) == 25
    page_texts: list[str] = []
    image_blocks = 0
    overflow_blocks = 0
    non_black_spans = 0
    non_black_drawings = 0
    non_gray_pixels = 0
    italic_spans = 0
    bold_italic_spans = 0
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
                    flags = span.get("flags", 0)
                    if flags & fitz.TEXT_FONT_ITALIC:
                        italic_spans += 1
                        if flags & fitz.TEXT_FONT_BOLD:
                            bold_italic_spans += 1
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
    assert italic_spans > 0
    assert bold_italic_spans > 0
    assert "**" not in full_text
    assert full_text.count("押题") == 62
    assert full_text.count("答案") >= 63
    assert full_text.count("【名词解释：") == 123
    assert "【共用】" not in full_text
    assert "【本题补充】" not in full_text
    assert full_text.count("【采分点加分】") == point_bonus_uses + 1
    assert full_text.count("【整体加分】") == answer_bonus_blocks + 1
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
    assert actual_map == V11_CATALOG_PAGE_MAP, (actual_map, V11_CATALOG_PAGE_MAP)

    print(
        "PASS "
        f"pages={len(document)} body_pages={len(body_pages)} images={image_blocks} "
        f"overflow={overflow_blocks} non_black_spans={non_black_spans} "
        f"non_black_drawings={non_black_drawings} non_gray_pixels={non_gray_pixels} "
        f"roman_module_uses={roman_uses} italic_module_uses={italic_uses} "
        f"italic_spans={italic_spans} bold_italic_spans={bold_italic_spans}"
    )


if __name__ == "__main__":
    main()
