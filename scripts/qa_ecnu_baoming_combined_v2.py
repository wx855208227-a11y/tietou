from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

import fitz
from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "deliverables/华东师范大学347保命手册_导论实验测量合订精校版V2"
DOCX = BASE.with_suffix(".docx")
PDF = BASE.with_suffix(".pdf")
PAGE_MAP = ROOT / "content/ecnu_baoming_combined_v2_page_map.json"
REPORT = BASE.with_name(BASE.name + "_质检报告.md")
HEADERS = {
    "华东师范大学347｜心理学导论保命手册",
    "华东师范大学347｜实验心理学保命手册",
    "华东师范大学347｜心理测量保命手册",
}


def compact(value: str) -> str:
    return re.sub(r"\s+|\u2060", "", value).translate(str.maketrans("", "", "—–－-"))


def body_blocks(page: fitz.Page) -> list[tuple[float, float, str]]:
    result = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        text = "".join(
            span.get("text", "")
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ).strip()
        y0, y1 = block["bbox"][1], block["bbox"][3]
        if text and y0 >= 55 and y1 <= 780 and not text.isdigit():
            result.append((y0, y1, text))
    return sorted(result)


def meaningful_lines(page: fitz.Page) -> list[str]:
    return [
        line.strip()
        for line in page.get_text().splitlines()
        if line.strip() and line.strip() not in HEADERS and not line.strip().isdigit()
    ]


def main() -> None:
    document = Document(DOCX)
    paragraphs = document.paragraphs
    all_text = "\n".join(paragraph.text for paragraph in paragraphs)
    assert not re.search(r"【名(?:\u2060|\s)+词|名词(?:\u2060|\s)+解释", all_text)
    assert "000" not in "\n".join(
        paragraph.text for paragraph in paragraphs if "\t" in paragraph.text
    ), "目录仍有占位页码"
    assert sum(paragraph.text.startswith("押题") for paragraph in paragraphs) == 239
    assert all_text.count("【名词解释：") == 429
    assert all_text.count("第一部分 心理学导论") == 2
    assert all_text.count("第二部分 实验心理学") == 2
    assert all_text.count("第三部分 心理与教育测量") == 2
    part_positions = [
        next(index for index, paragraph in enumerate(paragraphs) if paragraph.text == title)
        for title in ("第一部分 心理学导论", "第二部分 实验心理学", "第三部分 心理与教育测量")
    ]
    assert part_positions == sorted(part_positions)

    body_start = part_positions[0]
    body_sizes: Counter[float] = Counter()
    for paragraph in paragraphs[body_start:]:
        if paragraph.style.name not in {"Normal", "Heading 3"}:
            continue
        for run in paragraph.runs:
            if not run.text.strip():
                continue
            size = run.font.size.pt if run.font.size is not None else paragraph.style.font.size.pt
            body_sizes[size] += 1
            assert size == 12.0, (paragraph.style.name, run.text, size)
            assert run.font.italic in (None, False)
            assert run.font.underline in (None, False)
            if run.font.color.type is not None and run.font.color.rgb is not None:
                assert str(run.font.color.rgb) == "000000"
            if "【名词解释：" in run.text:
                spacing = run._r.get_or_add_rPr().find(qn("w:spacing"))
                assert spacing is None, run.text
            if "【简答】" in run.text or "【论述】" in run.text:
                assert size == 12.0
    assert body_sizes == {12.0: sum(body_sizes.values())}

    chapter_paragraphs = [paragraph for paragraph in paragraphs if paragraph.style.name == "Heading 1"]
    assert len(chapter_paragraphs) == 39
    first_chapters = {0, 17, 28}
    for index, paragraph in enumerate(chapter_paragraphs):
        page_break = paragraph._p.pPr.find(qn("w:pageBreakBefore"))
        enabled = page_break is not None and page_break.get(qn("w:val"), "1") not in {
            "0", "false", "off"
        }
        assert enabled == (index not in first_chapters), (index, paragraph.text, enabled)

    for section in document.sections:
        assert round(section.page_width.cm, 1) == 21.0
        assert round(section.page_height.cm, 1) == 29.7
        assert round(section.top_margin.cm, 1) == 2.0
        assert round(section.bottom_margin.cm, 1) == 1.8
        assert round(section.left_margin.cm, 1) == 2.2
        assert round(section.right_margin.cm, 1) == 2.0

    pdf = fitz.open(PDF)
    assert len(pdf) == 174
    assert all(abs(page.rect.width - 595.3) < 1 and abs(page.rect.height - 841.9) < 1 for page in pdf)
    assert not any(page.get_images(full=True) for page in pdf), "正文PDF不应依赖图片呈现"
    pdf_text = "\n".join(page.get_text() for page in pdf)
    assert pdf_text.count("押题") == 239
    assert compact(pdf_text).count("【名词解释：") == 429

    page_map: dict[str, int] = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert len(page_map) == 42
    first_body = 3  # 物理第4页；前三页依次为封面、使用说明、目录。
    chapter_pages: list[int] = []
    part_pages: list[int] = []
    for key, relative_page in page_map.items():
        physical_page = first_body + relative_page
        title = key.rsplit("|", 1)[-1]
        assert compact(title) in compact(pdf[physical_page - 1].get_text()), (key, physical_page)
        (chapter_pages if "|" in key else part_pages).append(physical_page)
    assert part_pages == [4, 102, 137]
    assert chapter_pages == sorted(set(chapter_pages)) and len(chapter_pages) == 39
    for physical_page in chapter_pages:
        lines = meaningful_lines(pdf[physical_page - 1])
        assert lines
        # 每章标题必须出现在页首区域；每部分第一章之前允许保留分科标题。
        expected_titles = [
            key.rsplit("|", 1)[-1]
            for key, relative in page_map.items()
            if "|" in key and first_body + relative == physical_page
        ]
        assert any(any(compact(title) == compact(line) for line in lines[:3]) for title in expected_titles)

    structural_end_pages = {page - 1 for page in chapter_pages[1:]}
    blank_pages: list[int] = []
    sparse_pages: list[tuple[int, int]] = []
    bottom_blank: list[tuple[int, float]] = []
    orphan_endings: list[tuple[int, str]] = []
    max_internal_gap = 0.0
    for physical_page, page in enumerate(pdf[3:], start=4):
        blocks = body_blocks(page)
        if not blocks:
            blank_pages.append(physical_page)
            continue
        structural = physical_page in structural_end_pages or physical_page == len(pdf)
        chars = len(re.sub(r"\s+", "", page.get_text()))
        if not structural and chars < 220:
            sparse_pages.append((physical_page, chars))
        if not structural and 800 - blocks[-1][1] > 250:
            bottom_blank.append((physical_page, 800 - blocks[-1][1]))
        if not structural:
            for previous, current in zip(blocks, blocks[1:]):
                max_internal_gap = max(max_internal_gap, current[0] - previous[1])
        lines = meaningful_lines(page)
        if lines and (
            lines[-1].endswith("：")
            or re.match(r"^(?:押题\d+【|[一二三四五六七八九十百]+、.*【★{1,3}】)$", lines[-1])
        ):
            orphan_endings.append((physical_page, lines[-1]))
    assert not blank_pages
    assert not sparse_pages
    assert not bottom_blank
    assert not orphan_endings
    assert max_internal_gap < 22

    report = f"""# 华东师范大学347保命手册合订精校版V2质检报告

## 成品

- 合订顺序：心理学导论 → 实验心理学 → 心理与教育测量。
- 共39章、205个知识单元、239道押题；名词解释标签共429处。
- PDF共174页：封面1页、使用说明1页、目录1页，正文171页。

## 内容与结构

- 导论V10：17章、117单元、145题；34道比较题均显式呈现联系与主要区别；296处名解、256个唯一名解零异文。
- 实验V2：11章、49单元、49题；10道比较题均显式呈现联系与主要区别；72处名解、68个唯一名解零异文。
- 测量V9：11章、39单元、45题；94个题干任务模块全部从1连续编号；61处名解、42个准入名解零异文。
- 导论和实验已按测量新标准校准题干任务分块、比较结论、实验逻辑、关键词和答案容量；测量V9内容保持冻结。
- 简答／论述容量的内容统计已完成；真实学员15—20分钟计时手写仍标记为待实测。

## 来源

- 导论知识主体继续使用速背手册和心理学导论一本通；V10新增内容仅为任务模块和基于既有正文的比较归纳。
- 实验49单元、68个唯一名解已通过速背手册／一本通边界审计。
- 测量沿用V9已验证内容基线。

## 排版

- A4，正文与押题题型标记、扩容、名解标签统一12磅；纯黑白，无下划线和斜体。
- 名解标签使用正常字距；39章均另起一页，章内连续紧凑排版。
- 目录42个分科／章节页码均与最终PDF一致。
- 无空白页、无非结构性稀疏页、无异常页底留白、无孤立押题／任务模块标题；正文最大段间空隙{max_internal_gap:.1f}pt。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(
        "华东三科合订V2质检通过："
        f"pages={len(pdf)} questions=239 tags=429 chapters=39 "
        f"blank=0 sparse=0 orphan=0 max_gap={max_internal_gap:.1f}pt"
    )


if __name__ == "__main__":
    main()
