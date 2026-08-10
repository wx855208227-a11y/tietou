from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import zipfile

import fitz
from lxml import etree

from qa_baoming_full_v6_artifacts import (
    W_NS,
    compact,
    is_black,
    paragraph_text,
    run_is_bold,
    semantic_text,
)
from validate_measurement_baoming_v3 import RESERVED, expansion_contents


BASE = Path("deliverables/华东师范大学347心理测量保命手册_全本_极简直背版V3")
MARKDOWN = BASE.with_suffix(".md")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
PAGE_MAP = Path("content/measurement_baoming_v3_page_map.json")
TITLE = "华东师范大学347心理测量保命手册"
HEADER = "华东师范大学347｜心理测量保命手册"
FIRST_CHAPTER = "第一章心理测量和测验的历史回顾"


def plain_expansion(value: str) -> str:
    return value.replace("**", "").replace("__", "").replace("`", "")


def main() -> None:
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 ") :]
    question_count = len(re.findall(r"^### 押题", body, re.MULTILINE))
    definition_count = body.count("【名词解释：")
    expansions = expansion_contents(body)
    stars = Counter(re.findall(r"^## .+【(★★★|★★|★)】$", body, re.MULTILINE))
    assert (question_count, definition_count, len(expansions)) == (45, 81, 165)
    assert stars == {"★★★": 16, "★★": 13, "★": 10}
    page_map: dict[str, int] = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert len(page_map) == 50

    with zipfile.ZipFile(DOCX) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
        header_text = "".join(
            "".join(
                node.text or ""
                for node in etree.fromstring(archive.read(name)).findall(f".//{{{W_NS}}}t")
            )
            for name in archive.namelist()
            if name.startswith("word/header") and name.endswith(".xml")
        )
    raw_docx_text = "".join(
        node.text or "" for node in root.findall(f".//{{{W_NS}}}t")
    )
    docx_text = raw_docx_text.replace("\u2060", "")
    assert all(
        "\u2060" not in tag
        for tag in re.findall(r"【.*?】", raw_docx_text)
        if compact(tag).startswith(compact("【名词解释："))
    ), "名词解释标签中仍存在拉大字距的连接字符"
    colors = {node.get(f"{{{W_NS}}}val") for node in root.findall(f".//{{{W_NS}}}color")}
    assert colors == {"000000"}, colors
    assert all(
        node.get(f"{{{W_NS}}}val", "none").lower() in {"none", "0", "false", "off"}
        for node in root.findall(f".//{{{W_NS}}}u")
    )
    assert all(
        node.get(f"{{{W_NS}}}val", "1").lower() in {"0", "false", "off"}
        for node in root.findall(f".//{{{W_NS}}}i")
    )
    assert not root.findall(f".//{{{W_NS}}}highlight")
    assert not root.findall(f".//{{{W_NS}}}shd")
    assert "**" not in docx_text
    assert "扩容（选背）" not in docx_text and "扩容（选用）" not in docx_text
    assert "例子可灵活替换" not in docx_text
    assert "全本·极简直背版V3" not in docx_text
    assert HEADER in header_text
    for phrase in (
        "一本通与考纲中的核心内容",
        "华东或相关真题信号强",
        "主观题可考性和答案复用价值最高",
        "圆括号外是背诵主体，写全可以拿到主要分数",
        "（）内是扩容项，选背",
        "丰富答题角度、锦上添花，追求更高分数",
        "如果其中是例子，可以根据题目灵活替换",
    ):
        assert phrase in docx_text, phrase
    for phrase in (
        "星级只表示背诵顺序，不代表必考概率",
        "名词解释背【名词解释：……】前的定义及紧邻扩容",
    ):
        assert phrase not in docx_text, phrase

    paragraphs = root.findall(f".//{{{W_NS}}}p")
    assert all(paragraph_text(paragraph).count("【名词解释：") <= 1 for paragraph in paragraphs)
    assert all(
        "【名词解释：" not in paragraph_text(paragraph)
        or re.search(r"【名词解释：[^】]+】$", paragraph_text(paragraph))
        for paragraph in paragraphs
    ), "DOCX中存在名解标签后继续堆写正文的段落"
    body_paragraph_index = next(
        index
        for index, paragraph in enumerate(paragraphs)
        if compact(paragraph_text(paragraph)) == compact(FIRST_CHAPTER)
    )
    for paragraph in paragraphs[body_paragraph_index:]:
        paragraph_style = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pStyle")
        if paragraph_style is not None or not paragraph_text(paragraph).strip():
            continue
        run_sizes = []
        for run in paragraph.findall(f"./{{{W_NS}}}r"):
            run_text = "".join(
                node.text or "" for node in run.findall(f".//{{{W_NS}}}t")
            )
            if not run_text:
                continue
            size = run.find(f"./{{{W_NS}}}rPr/{{{W_NS}}}sz")
            assert size is not None, paragraph_text(paragraph)
            run_sizes.append(int(size.get(f"{{{W_NS}}}val")))
        assert not run_sizes or set(run_sizes) == {24}, (
            paragraph_text(paragraph),
            sorted(set(run_sizes)),
        )
    docx_body = "".join(
        paragraph_text(paragraph) for paragraph in paragraphs[body_paragraph_index:]
    ).replace("\u2060", "")
    assert compact(docx_body).count("【名词解释：") == definition_count
    for wrapped, count in Counter(
        f"（{plain_expansion(value)}）" for value in expansions
    ).items():
        assert docx_body.count(wrapped) >= count, wrapped
    assert all(
        value in RESERVED or value.startswith("名词解释：")
        for value in re.findall(r"【(.*?)】", docx_body)
    ), "DOCX正文仍存在使用方括号的扩容项"

    docx_units = Counter()
    for paragraph in paragraphs:
        match = re.match(r"^.+【(★★★|★★|★)】$", paragraph_text(paragraph))
        if match:
            docx_units[match.group(1)] += 1
    assert docx_units == stars
    question_headings = [
        paragraph for paragraph in paragraphs if re.match(r"^押题\d+【", paragraph_text(paragraph))
    ]
    assert len(question_headings) == question_count
    for paragraph in question_headings:
        type_runs = []
        for run in paragraph.findall(f"./{{{W_NS}}}r"):
            run_text = "".join(node.text or "" for node in run.findall(f".//{{{W_NS}}}t"))
            if run_text not in {"【简答】", "【论述】"}:
                continue
            properties = run.find(f"./{{{W_NS}}}rPr")
            assert properties is not None
            size = properties.find(f"./{{{W_NS}}}sz")
            fonts = properties.find(f"./{{{W_NS}}}rFonts")
            assert size is not None and int(size.get(f"{{{W_NS}}}val")) == 24
            assert fonts is not None and fonts.get(f"{{{W_NS}}}eastAsia") == "宋体"
            type_runs.append(run_text)
        assert len(type_runs) == 1, paragraph_text(paragraph)
    later_questions = [
        paragraph for paragraph in paragraphs if re.match(r"^押题(?:2|3|4)【", paragraph_text(paragraph))
    ]
    question_gaps = []
    for paragraph in later_questions:
        spacing = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}spacing")
        assert spacing is not None
        question_gaps.append(int(spacing.get(f"{{{W_NS}}}before")))
    assert question_gaps and min(question_gaps) >= 320

    sample_body = next(
        paragraph
        for paragraph in paragraphs
        if compact(paragraph_text(paragraph)).startswith(compact("测量是按照一定的法则"))
    )
    sample_spacing = sample_body.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}spacing")
    assert sample_spacing is not None
    assert int(sample_spacing.get(f"{{{W_NS}}}line")) >= 360
    assert int(sample_spacing.get(f"{{{W_NS}}}after")) >= 100

    document = fitz.open(PDF)
    assert len(document) == 43
    page_texts: list[str] = []
    image_blocks = overflow_blocks = non_black_spans = non_black_drawings = 0
    non_gray_pixels = italic_spans = 0
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
        pixmap = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
        samples = memoryview(pixmap.samples)
        non_gray_pixels += sum(
            1
            for offset in range(0, len(samples), pixmap.n)
            if not (samples[offset] == samples[offset + 1] == samples[offset + 2])
        )

    full_text = "\n".join(page_texts)
    assert image_blocks == overflow_blocks == 0
    assert non_black_spans == non_black_drawings == non_gray_pixels == italic_spans == 0
    assert all(text.strip() for text in page_texts)
    assert compact(page_texts[0]) == compact(TITLE)
    assert "V3" not in page_texts[0] and "2026" not in page_texts[0]
    assert "使用说明" in page_texts[1] and "（）内是扩容项" in compact(page_texts[1])
    assert "星级只表示背诵顺序，不代表必考概率" not in full_text
    assert "名词解释背【名词解释：……】前的定义及紧邻扩容" not in compact(full_text)
    assert full_text.count("押题") == question_count + 1

    first_body = next(
        index
        for index, text in enumerate(page_texts)
        if compact(FIRST_CHAPTER) in compact(text) and compact(HEADER) in compact(text)
    )
    assert first_body == 4
    pdf_body = "\n".join(page_texts[first_body:])
    assert "扩容（选背）" not in pdf_body and "扩容（选用）" not in pdf_body
    assert "例子可灵活替换" not in pdf_body
    assert definition_count - 1 <= compact(pdf_body).count("【名词解释：") <= definition_count + 1
    semantic_pdf = semantic_text(pdf_body)
    for expansion in expansions:
        assert semantic_text(expansion) in semantic_pdf, expansion

    for physical_page, text in enumerate(page_texts[first_body:], start=first_body + 1):
        assert len(re.sub(r"\s+", "", text)) >= 220, physical_page
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        meaningful = [line for line in lines if line != HEADER and not line.isdigit()]
        assert meaningful
        assert not re.match(
            r"^(?:第[^ ]+章|押题\d+【|[一二三四五六七八九十]+、.*【★{1,3}】)$",
            meaningful[-1],
        ), (physical_page, meaningful[-1])

    actual_map = {}
    for title in page_map:
        needle = compact(title)
        for physical_page in range(first_body, len(page_texts)):
            if needle in compact(page_texts[physical_page]):
                actual_map[title] = physical_page - first_body + 1
                break
    assert actual_map == page_map, (actual_map, page_map)
    catalog_text = "\n".join(page_texts[2:first_body])
    assert "直接用法" in catalog_text and "（）内是可选扩容" in compact(catalog_text)

    print(
        "测量保命手册V3制品质检通过："
        f"pages={len(document)} body_pages={len(document) - first_body} questions={question_count} "
        f"stars={dict(stars)} definitions={definition_count} expansions={len(expansions)} "
        f"images={image_blocks} overflow={overflow_blocks} colors={non_black_spans + non_black_drawings} "
        f"non_gray_pixels={non_gray_pixels} italic={italic_spans} "
        f"question_gap_min_twips={min(question_gaps)} catalog_items={len(page_map)}"
    )


if __name__ == "__main__":
    main()
