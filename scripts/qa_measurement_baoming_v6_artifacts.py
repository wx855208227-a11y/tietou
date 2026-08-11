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
)


BASE = Path("deliverables/华东师范大学347心理测量保命手册_全本_任务模块编号版V6")
MARKDOWN = BASE.with_suffix(".md")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
PAGE_MAP = Path("content/measurement_baoming_v6_page_map.json")
TITLE = "华东师范大学347心理测量保命手册"
HEADER = "华东师范大学347｜心理测量保命手册"
FIRST_CHAPTER = "第一章心理测量和测验的历史回顾"
def main() -> None:
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 ") :]
    question_count = len(re.findall(r"^### 押题", body, re.MULTILINE))
    definition_count = body.count("【名词解释：")
    stars = Counter(re.findall(r"^## .+【(★★★|★★|★)】$", body, re.MULTILINE))
    question_types = Counter(re.findall(r"^### 押题\d+【(简答|论述)】", body, re.MULTILINE))
    assert (question_count, definition_count) == (45, 58)
    assert question_types == {"简答": 38, "论述": 7}
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
    raw_docx_text = "".join(node.text or "" for node in root.findall(f".//{{{W_NS}}}t"))
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
    assert "任务模块编号版V6" not in docx_text
    assert HEADER in header_text
    for forbidden in (
        "扩容（选背）",
        "扩容（选用）",
        "例子可灵活替换",
        "答题思路",
        "到此停笔",
        "本题补充",
    ):
        assert forbidden not in docx_text, forbidden

    paragraphs = root.findall(f".//{{{W_NS}}}p")
    assert all(paragraph_text(paragraph).count("【名词解释：") <= 1 for paragraph in paragraphs)
    assert all(
        "【名词解释：" not in paragraph_text(paragraph)
        or re.search(r"【名词解释：[^】]+】$", paragraph_text(paragraph))
        for paragraph in paragraphs
    ), "DOCX中存在名解标签后继续堆写正文的段落"
    first_body_index = next(
        index
        for index, paragraph in enumerate(paragraphs)
        if compact(paragraph_text(paragraph)) == compact(FIRST_CHAPTER)
    )
    task_modules = [
        paragraph
        for paragraph in paragraphs[first_body_index:]
        if re.match(r"^\d+\.\s", paragraph_text(paragraph))
    ]
    second_level = [
        paragraph
        for paragraph in paragraphs[first_body_index:]
        if re.match(r"^（\d+）", paragraph_text(paragraph))
    ]
    third_level = [
        paragraph
        for paragraph in paragraphs[first_body_index:]
        if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", paragraph_text(paragraph))
    ]
    assert (len(task_modules), len(second_level), len(third_level)) == (94, 248, 43)
    for paragraph in task_modules:
        if not paragraph_text(paragraph).endswith("："):
            continue
        keep_next = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}keepNext")
        keep_lines = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}keepLines")
        assert keep_next is not None and keep_lines is not None, paragraph_text(paragraph)
    for paragraph in paragraphs[first_body_index:]:
        paragraph_style = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pStyle")
        if paragraph_style is not None or not paragraph_text(paragraph).strip():
            continue
        run_sizes = []
        for run in paragraph.findall(f"./{{{W_NS}}}r"):
            run_text = "".join(node.text or "" for node in run.findall(f".//{{{W_NS}}}t"))
            if not run_text:
                continue
            size = run.find(f"./{{{W_NS}}}rPr/{{{W_NS}}}sz")
            assert size is not None, paragraph_text(paragraph)
            run_sizes.append(int(size.get(f"{{{W_NS}}}val")))
        assert not run_sizes or set(run_sizes) == {24}, (
            paragraph_text(paragraph),
            sorted(set(run_sizes)),
        )

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
            size = properties.find(f"./{{{W_NS}}}sz") if properties is not None else None
            fonts = properties.find(f"./{{{W_NS}}}rFonts") if properties is not None else None
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

    document = fitz.open(PDF)
    assert len(document) == 45
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
    assert "V6" not in page_texts[0] and "2026" not in page_texts[0]
    assert "使用说明" in page_texts[1] and "（）内是扩容项" in compact(page_texts[1])
    assert full_text.count("押题") == question_count + 1

    first_body = next(
        index
        for index, text in enumerate(page_texts)
        if compact(FIRST_CHAPTER) in compact(text) and compact(HEADER) in compact(text)
    )
    assert first_body == 4
    pdf_body = "\n".join(page_texts[first_body:])
    assert definition_count - 1 <= compact(pdf_body).count("【名词解释：") <= definition_count + 1
    for required in (
        "1. 三种量表的理论基础、编制方法与结构特点分别如下",
        "2. 三种量表的联系在于",
        "3. 三种量表的主要区别如下",
        "1. 影响信度系数的主要因素包括以下几点",
        "2. 提高信度的主要方法包括",
    ):
        assert compact(required) in compact(pdf_body), required

    for physical_page, page_text in enumerate(page_texts[first_body:], start=first_body + 1):
        assert len(re.sub(r"\s+", "", page_text)) >= 220, physical_page
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        meaningful = [line for line in lines if line != HEADER and not line.isdigit()]
        assert meaningful
        assert not meaningful[-1].endswith("："), (physical_page, meaningful[-1])
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
        "测量保命手册V6制品质检通过："
        f"pages={len(document)} body_pages={len(document) - first_body} questions={question_count} "
        f"types={dict(question_types)} stars={dict(stars)} definitions={definition_count} "
        f"task_modules={len(task_modules)} second_level={len(second_level)} third_level={len(third_level)} "
        f"images={image_blocks} overflow={overflow_blocks} colors={non_black_spans + non_black_drawings} "
        f"non_gray_pixels={non_gray_pixels} italic={italic_spans} "
        f"question_gap_min_twips={min(question_gaps)} catalog_items={len(page_map)}"
    )


if __name__ == "__main__":
    main()
