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


BASE = Path("deliverables/华东师范大学347心理学导论保命手册_全本_三星分级选背版V7")
MARKDOWN = BASE.with_suffix(".md")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
PAGE_MAP = Path("content/baoming_full_v7_page_map.json")


def main() -> None:
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 "):]
    question_count = len(re.findall(r"^### 押题", body, re.MULTILINE))
    definition_count = body.count("【名词解释：")
    expansion_count = body.count("【扩容（选背）：")
    stars = Counter(re.findall(r"^## .+【(★★★|★★|★)】$", body, re.MULTILINE))
    assert (question_count, definition_count, expansion_count) == (145, 296, 599)
    assert stars == {"★★★": 44, "★★": 40, "★": 33}
    page_map: dict[str, int] = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert len(page_map) == 134

    with zipfile.ZipFile(DOCX) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
        header_text = "".join(
            "".join(node.text or "" for node in etree.fromstring(archive.read(name)).findall(f".//{{{W_NS}}}t"))
            for name in archive.namelist()
            if name.startswith("word/header") and name.endswith(".xml")
        )
    docx_text = "".join(node.text or "" for node in root.findall(f".//{{{W_NS}}}t")).replace("\u2060", "")
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
    assert "**" not in docx_text and "扩容（选用）" not in docx_text
    assert "全本·三星分级选背版V7" in docx_text and "全本｜2026" in docx_text
    assert "华东师范大学347｜心理学导论保命手册" in header_text
    assert compact(docx_text).count("【名词解释：") == definition_count
    assert compact(docx_text).count("【扩容（选背）：") == expansion_count
    assert len(re.findall(r"【扩容（选背）：.*?】【名词解释：[^】]+】", compact(docx_text))) == definition_count

    paragraphs = root.findall(f".//{{{W_NS}}}p")
    docx_units = Counter()
    for paragraph in paragraphs:
        match = re.match(r"^.+【(★★★|★★|★)】$", paragraph_text(paragraph))
        if match:
            docx_units[match.group(1)] += 1
    assert docx_units == stars

    bold_sequences = []
    for paragraph in paragraphs:
        buffer = ""
        for run in paragraph.findall(f"./{{{W_NS}}}r"):
            text = "".join(node.text or "" for node in run.findall(f".//{{{W_NS}}}t"))
            if run_is_bold(run):
                buffer += text
            elif buffer:
                bold_sequences.append(compact(buffer))
                buffer = ""
        if buffer:
            bold_sequences.append(compact(buffer))
    for phrase in (
        "行为和心理活动规律",
        "自然科学和社会科学",
        "开放性、责任心、外向性、宜人性和神经质",
        "个人绩效不能被单独评估时",
        "努力程度低于独自完成任务时",
    ):
        assert any(compact(phrase) in item for item in bold_sequences), phrase

    later_questions = [p for p in paragraphs if re.match(r"^押题(?:2|3|4)【", paragraph_text(p))]
    question_gaps = []
    for paragraph in later_questions:
        spacing = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}spacing")
        assert spacing is not None
        question_gaps.append(int(spacing.get(f"{{{W_NS}}}before")))
    assert question_gaps and min(question_gaps) >= 200

    document = fitz.open(PDF)
    assert len(document) == 84
    page_texts = []
    image_blocks = overflow_blocks = non_black_spans = non_black_drawings = 0
    non_gray_pixels = italic_spans = 0
    for page in document:
        assert abs(page.rect.width - 595.276) < 1 and abs(page.rect.height - 841.89) < 1
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
            1 for offset in range(0, len(samples), pixmap.n)
            if not (samples[offset] == samples[offset + 1] == samples[offset + 2])
        )

    full_text = "\n".join(page_texts)
    assert image_blocks == overflow_blocks == 0
    assert non_black_spans == non_black_drawings == non_gray_pixels == italic_spans == 0
    assert "**" not in full_text and "扩容（选用）" not in full_text
    assert all(text.strip() for text in page_texts)
    assert full_text.count("押题") == question_count + 1
    assert definition_count - 1 <= compact(full_text).count("【名词解释：") <= definition_count + 1
    assert expansion_count - 6 <= compact(full_text).count("【扩容（选背）：") <= expansion_count
    assert len(re.findall(r"【扩容（选背）：.*?】【名词解释：[^】]+】", compact(full_text))) >= definition_count - 6
    semantic_pdf = semantic_text(full_text)
    for expansion in re.findall(r"【扩容（选背）：(.*?)】", body, flags=re.DOTALL):
        assert semantic_text(expansion) in semantic_pdf, expansion

    first_body = next(
        index for index, text in enumerate(page_texts)
        if compact("第一章 心理学研究的对象、方法及其学科发展") in compact(text)
        and compact("华东师范大学347｜心理学导论保命手册") in compact(text)
    )
    assert first_body == 5
    for physical_page, text in enumerate(page_texts[first_body:], start=first_body + 1):
        assert len(re.sub(r"\s+", "", text)) >= 220, physical_page
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        meaningful = [line for line in lines if line != "华东师范大学347｜心理学导论保命手册" and not line.isdigit()]
        assert meaningful
        assert not re.match(r"^(?:第[^ ]+章|押题\d+【|[一二三四五六七八九十]+、.*【★{1,3}】)$", meaningful[-1]), (
            physical_page, meaningful[-1]
        )

    actual_map = {}
    for title in page_map:
        needle = compact(title)
        for physical_page in range(first_body, len(page_texts)):
            if needle in compact(page_texts[physical_page]):
                actual_map[title] = physical_page - first_body + 1
                break
    assert actual_map == page_map
    catalog_text = "\n".join(page_texts[1:first_body])
    assert "直接用法" in catalog_text and "扩容（选背）" in compact(catalog_text)
    assert not re.search(r"\.{3,}0(?:\n|$)", catalog_text)

    print(
        "全本V7制品质检通过："
        f"pages={len(document)} body_pages={len(document) - first_body} questions={question_count} "
        f"stars={dict(stars)} definitions={definition_count} expansions={expansion_count} "
        f"images={image_blocks} overflow={overflow_blocks} colors={non_black_spans + non_black_drawings} "
        f"non_gray_pixels={non_gray_pixels} italic={italic_spans} "
        f"question_gap_min_twips={min(question_gaps)} catalog_items={len(page_map)}"
    )


if __name__ == "__main__":
    main()
