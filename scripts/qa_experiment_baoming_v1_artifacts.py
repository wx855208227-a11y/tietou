from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import zipfile

import fitz
from lxml import etree

from build_experiment_baoming_v1 import source_expansion_contents
from qa_baoming_full_v6_artifacts import compact, is_black, paragraph_text, semantic_text
from validate_experiment_baoming_v1 import RESERVED


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
BASE = Path("deliverables/华东师范大学347实验心理学保命手册_全本_极简直背版V1")
MARKDOWN = BASE.with_suffix(".md")
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
REPORT = Path(str(BASE) + "_质检报告.md")
PAGE_MAP = Path("content/experiment_baoming_v1_page_map.json")
TITLE = "华东师范大学347实验心理学保命手册"
HEADER = "华东师范大学347｜实验心理学保命手册"
FIRST_CHAPTER = "第一章绪论"


def plain_expansion(value: str) -> str:
    return value.replace("**", "").replace("__", "").replace("`", "")


def main() -> None:
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 ") :]
    question_count = len(re.findall(r"^### 押题", body, re.MULTILINE))
    definition_count = body.count("【名词解释：")
    expansions = source_expansion_contents("")
    stars = Counter(re.findall(r"^## .+【(★★★|★★|★)】$", body, re.MULTILINE))
    assert (question_count, definition_count, len(expansions)) == (49, 73, 116)
    assert stars == {"★★★": 18, "★★": 17, "★": 14}
    page_map: dict[str, int] = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert len(page_map) == 60

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
    ), "名词解释标签仍有异常逐字间距字符"
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
    assert "**" not in docx_text and "\u2060" not in docx_text
    assert "扩容（选背）" not in docx_text and "扩容（选用）" not in docx_text
    assert "例子可灵活替换" not in docx_text
    assert "全本·极简直背版V1" not in docx_text
    assert HEADER in header_text

    paragraphs = root.findall(f".//{{{W_NS}}}p")
    assert all(paragraph_text(paragraph).count("【名词解释：") <= 1 for paragraph in paragraphs)
    assert all(
        "【名词解释：" not in paragraph_text(paragraph)
        or re.search(r"【名词解释：[^】]+】$", paragraph_text(paragraph))
        for paragraph in paragraphs
    ), "DOCX中存在名解标签后继续堆写正文"
    body_index = next(
        index
        for index, paragraph in enumerate(paragraphs)
        if compact(paragraph_text(paragraph)) == compact(FIRST_CHAPTER)
    )
    for paragraph in paragraphs[body_index:]:
        paragraph_style = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}pStyle")
        if paragraph_style is not None or not paragraph_text(paragraph).strip():
            continue
        run_sizes: list[int] = []
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
    question_before: list[int] = []
    for paragraph in question_headings:
        spacing = paragraph.find(f"./{{{W_NS}}}pPr/{{{W_NS}}}spacing")
        assert spacing is not None
        question_before.append(int(spacing.get(f"{{{W_NS}}}before")))
    assert min(question_before) >= 180

    docx_body = "".join(paragraph_text(paragraph) for paragraph in paragraphs[body_index:])
    assert compact(docx_body).count("【名词解释：") == definition_count
    for wrapped, count in Counter(f"（{plain_expansion(value)}）" for value in expansions).items():
        assert docx_body.count(wrapped) >= count, wrapped
    assert all(
        value in RESERVED or value.startswith("名词解释：")
        for value in re.findall(r"【(.*?)】", docx_body)
    )

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
    assert image_blocks == overflow_blocks == 0
    assert non_black_spans == non_black_drawings == non_gray_pixels == italic_spans == 0
    assert all(text.strip() for text in page_texts)
    assert compact(page_texts[0]) == compact(TITLE)
    assert "V1" not in page_texts[0] and "2026" not in page_texts[0]
    assert "使用说明" in page_texts[1] and "（）内是扩容项" in compact(page_texts[1])
    first_body = next(
        index
        for index, text in enumerate(page_texts)
        if compact(FIRST_CHAPTER) in compact(text) and compact(HEADER) in compact(text)
    )
    assert first_body == 4
    pdf_body = "\n".join(page_texts[first_body:])
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

    actual_map: dict[str, int] = {}
    for title in page_map:
        needle = compact(title)
        for physical_page in range(first_body, len(page_texts)):
            if needle in compact(page_texts[physical_page]):
                actual_map[title] = physical_page - first_body + 1
                break
    assert actual_map == page_map, (actual_map, page_map)

    report = (
        "# 华东实验心理学保命手册V1质检报告\n\n"
        "- 内容：11个一级章节、49个单元、49道押题；三星18、二星17、一星14。\n"
        "- 答案：简答35道、论述14道；69个唯一名解、73处调用、116处同行扩容。\n"
        "- DOCX：正文非标题统一12磅；名解标签正常字距；无彩色、底纹、下划线和斜体；题目前距不小于9磅。\n"
        f"- PDF：A4共{len(document)}页，其中正文{len(document) - first_body}页；无图片块、越界文本、彩色像素和斜体文本。\n"
        "- 目录：60个章节／单元页码均与最终PDF正文页一致。\n"
    )
    REPORT.write_text(report, encoding="utf-8")
    print(
        "实验心理学保命手册V1制品质检通过："
        f"pages={len(document)} body_pages={len(document) - first_body} "
        f"questions={question_count} stars={dict(stars)} definitions={definition_count} "
        f"expansions={len(expansions)} overflow={overflow_blocks} colors=0 italic={italic_spans}"
    )


if __name__ == "__main__":
    main()
