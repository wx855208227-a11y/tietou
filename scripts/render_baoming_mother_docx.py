from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, RGBColor

from render_baoming_docx import (
    LIGHT_GRAY_FILL,
    add_body_paragraph,
    add_cover,
    add_heading,
    add_inline_runs,
    add_list_paragraph,
    add_table,
    configure_body_header_footer,
    configure_page,
    configure_styles,
    set_cell_border,
    set_cell_margins,
    set_paragraph_border,
    set_run_font,
    set_update_fields,
    shade_paragraph,
)


TAG_GRAY = RGBColor(89, 89, 89)
MOTHER_FILL = "E2F0D9"
MOTHER_BORDER = "70AD47"
DEFINITION_FILL = "DDEBF7"
DEFINITION_BORDER = "5B9BD5"
FLEXIBLE_FILL = "FFF2CC"
FLEXIBLE_BORDER = "BF9000"

COMPACT_UNIT_PREFIXES = (
    "九、脑功能的主要学说",
    "四、经典条件反射的基本规律",
    "五、信号系统与高级神经活动",
    "六、操作条件反射与行为调控",
    "七、经典条件反射与操作条件反射的比较",
    "十、观察学习",
    "十一、格雷的强化敏感性理论",
)

CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 3,
    "五、格式塔心理学": 4,
    "六、精神分析学派": 4,
    "七、人本主义心理学": 5,
    "八、认知心理学": 6,
    "九、观察法、相关研究法与实验法": 7,
    "十、实验变量": 8,
    "十一、测验法与信效度": 9,
    "十二、投射法与投射测验": 10,
    "十三、心理学的主要分支": 10,
    "第二章 心理和行为的生物学基础": 12,
    "一、神经元": 12,
    "二、神经冲动与突触传递": 12,
    "三、神经系统的构成与功能": 13,
    "四、大脑皮层的感觉区与运动区": 14,
    "五、大脑皮层的言语区与联合区": 15,
    "六、大脑两半球的功能分工": 16,
    "七、丘脑与下丘脑": 16,
    "八、边缘系统、海马与杏仁核": 17,
    "九、脑功能的主要学说": 18,
    "第三章 条件反射和学习": 19,
    "一、学习的含义与特征": 19,
    "二、反射、反射弧与反射类型": 19,
    "三、经典条件反射": 20,
    "四、经典条件反射的基本规律": 21,
    "五、信号系统与高级神经活动": 22,
    "六、操作条件反射与行为调控": 23,
    "七、经典条件反射与操作条件反射的比较": 24,
    "八、顿悟学习": 24,
    "九、目的行为学习理论": 25,
    "十、观察学习": 26,
    "十一、格雷的强化敏感性理论": 27,
}


def add_catalog(document: Document, lines: list[str]) -> None:
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(18)
    set_run_font(title.add_run("目录"), "宋体", 26, True)

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            heading = line[2:].strip()
            if heading.startswith("华东师范大学"):
                continue
            is_chapter = True
        elif line.startswith("## "):
            heading = line[3:].strip().split("【", 1)[0]
            is_chapter = False
        else:
            continue
        if heading not in CATALOG_PAGE_MAP:
            continue
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0 if is_chapter else 0.74)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.space_after = Pt(5 if is_chapter else 1)
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        set_run_font(
            paragraph.add_run(f"{heading}\t{CATALOG_PAGE_MAP[heading]}"),
            size=11,
            bold=is_chapter,
        )

    legend = document.add_paragraph()
    legend.paragraph_format.first_line_indent = Cm(0)
    legend.paragraph_format.space_before = Pt(8)
    legend.paragraph_format.space_after = Pt(0)
    shade_paragraph(legend, "D9EAD3")
    set_run_font(
        legend.add_run(
            "直接用法｜整份背熟；名解提取【名词解释】；简答按题干选分点；论述调用完整框架。"
        ),
        size=10,
        bold=True,
    )

    note = document.add_paragraph()
    note.paragraph_format.first_line_indent = Cm(0)
    note.paragraph_format.space_after = Pt(0)
    shade_paragraph(note, LIGHT_GRAY_FILL)
    set_run_font(
        note.add_run(
            "正文顺序就是背诵顺序，不再学习调用公式；【灵活扩充】按题干和时间选写。"
        ),
        size=9.5,
    )


def add_mother_answer_header(document: Document) -> None:
    header = document.add_paragraph()
    header.paragraph_format.first_line_indent = Cm(0)
    header.paragraph_format.line_spacing = 1.0
    header.paragraph_format.space_after = Pt(5)
    header.paragraph_format.keep_with_next = True
    shade_paragraph(header, MOTHER_FILL)
    set_paragraph_border(header, MOTHER_BORDER, "8")
    set_run_font(header.add_run("综合母答案"), "微软雅黑", 11, True)
    instruction = header.add_run("　背一份｜根据题干删减、重组和调整详略")
    set_run_font(instruction, "宋体", 9.5, True)
    instruction.font.color.rgb = TAG_GRAY


def add_definition_banner(document: Document, tagged_line: str):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.2
    paragraph.paragraph_format.space_after = Pt(1)
    shade_paragraph(paragraph, DEFINITION_FILL)
    set_paragraph_border(paragraph, DEFINITION_BORDER, "6")
    set_run_font(paragraph.add_run("【名词解释】｜"), "微软雅黑", 10, True)
    content = re.sub(r"(?:\*\*)?【名词解释】(?:\*\*)?\s*", "", tagged_line)
    add_inline_runs(paragraph, content, size=11)
    return paragraph


def add_flexible_banner(document: Document) -> None:
    header = document.add_paragraph()
    header.paragraph_format.first_line_indent = Cm(0)
    header.paragraph_format.line_spacing = 1.0
    header.paragraph_format.space_after = Pt(2)
    header.paragraph_format.keep_with_next = True
    shade_paragraph(header, FLEXIBLE_FILL)
    set_paragraph_border(header, FLEXIBLE_BORDER, "6")
    set_run_font(header.add_run("【灵活扩充】"), "微软雅黑", 10, True)
    note = header.add_run("　按题干和时间选写，不替代基础采分点")
    set_run_font(note, "宋体", 9, True)
    note.font.color.rgb = TAG_GRAY


def shade_tagged_paragraph(paragraph, fill: str, border: str) -> None:
    shade_paragraph(paragraph, fill)
    set_paragraph_border(paragraph, border, "4")


def render_markdown(markdown_path: Path, output_path: Path) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    subtitle = lines[2].removeprefix("## ").strip()
    document = Document()
    configure_styles(document)
    configure_page(document.sections[0])
    set_update_fields(document)
    document.core_properties.title = title
    document.core_properties.subject = "华东师范大学347心理学导论综合母答案版"
    document.core_properties.author = "铁头心理学考研"
    add_cover(document, title, subtitle)
    first_chapter_index = next(
        index for index, line in enumerate(lines) if line.startswith("# 第一章 ")
    )
    add_catalog(document, lines)

    body_section = document.add_section(WD_SECTION.NEW_PAGE)
    configure_page(body_section)
    configure_body_header_footer(body_section)

    answer_mode = False
    answer_container = document
    in_definition = False
    in_flexible = False
    question_block_active = False
    compact_unit_active = False
    first_chapter = True
    line_index = first_chapter_index
    while line_index < len(lines):
        raw_line = lines[line_index]
        stripped = raw_line.strip()
        if not stripped:
            if answer_mode and in_definition:
                in_definition = False
            line_index += 1
            continue
        if stripped == "---":
            line_index += 1
            continue
        if stripped.startswith("# "):
            add_heading(document, 1, stripped[2:].strip(), page_break_before=not first_chapter)
            first_chapter = False
            answer_mode = False
            answer_container = document
            in_definition = False
            in_flexible = False
            question_block_active = False
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            heading = add_heading(document, 2, heading_text)
            compact_unit_active = heading_text.startswith(COMPACT_UNIT_PREFIXES)
            if compact_unit_active:
                heading.paragraph_format.space_before = Pt(6)
                heading.paragraph_format.space_after = Pt(2)
            answer_mode = False
            answer_container = document
            in_definition = False
            in_flexible = False
            question_block_active = False
        elif stripped.startswith("### "):
            heading_text = stripped[4:].strip()
            if heading_text == "综合母答案":
                add_mother_answer_header(document)
                answer_container = document
                answer_mode = True
                in_definition = False
                in_flexible = False
                question_block_active = False
            else:
                displayed = "押题题目｜可能问法" if heading_text == "押题题目" else heading_text
                heading = add_heading(document, 3, displayed)
                if compact_unit_active:
                    heading.paragraph_format.space_before = Pt(4)
                    heading.paragraph_format.space_after = Pt(2)
                answer_mode = False
                answer_container = document
                question_block_active = heading_text == "押题题目"
        else:
            if answer_mode and "【名词解释】" in stripped:
                add_definition_banner(document, stripped)
                in_definition = True
                in_flexible = False
                line_index += 1
                continue
            if answer_mode and "【灵活扩充】" in stripped:
                add_flexible_banner(document)
                in_definition = False
                in_flexible = True
                line_index += 1
                continue

            target = answer_container if answer_mode else document
            if stripped.startswith("|"):
                table_lines: list[str] = []
                while line_index < len(lines) and lines[line_index].strip().startswith("|"):
                    table_lines.append(lines[line_index].strip())
                    line_index += 1
                add_table(target, table_lines)
                continue
            if stripped.startswith("> "):
                paragraph = target.add_paragraph()
                shade_paragraph(paragraph, LIGHT_GRAY_FILL)
                paragraph.paragraph_format.first_line_indent = Cm(0)
                add_inline_runs(paragraph, stripped[2:].strip())
            elif stripped.startswith("- ") or re.match(r"^\d+\.\s", stripped):
                paragraph = add_list_paragraph(
                    target,
                    raw_line,
                    False,
                    keep_with_next=question_block_active,
                    compact=compact_unit_active,
                    card=answer_mode,
                )
                if answer_mode and in_definition:
                    shade_tagged_paragraph(paragraph, DEFINITION_FILL, DEFINITION_BORDER)
                if answer_mode and in_flexible:
                    shade_tagged_paragraph(paragraph, FLEXIBLE_FILL, FLEXIBLE_BORDER)
                    for run in paragraph.runs:
                        run.font.color.rgb = TAG_GRAY
            else:
                paragraph = target.add_paragraph()
                paragraph.paragraph_format.line_spacing = (
                    1.18 if answer_mode and compact_unit_active else 1.35 if answer_mode else 1.5
                )
                paragraph.paragraph_format.space_after = Pt(
                    0 if compact_unit_active else 1 if answer_mode else 3
                )
                paragraph.paragraph_format.widow_control = True
                add_inline_runs(
                    paragraph,
                    stripped,
                    size=11 if answer_mode and compact_unit_active else 12,
                )
                if answer_mode and in_definition:
                    shade_tagged_paragraph(paragraph, DEFINITION_FILL, DEFINITION_BORDER)
                if answer_mode and in_flexible:
                    shade_tagged_paragraph(paragraph, FLEXIBLE_FILL, FLEXIBLE_BORDER)
        line_index += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    render_markdown(arguments.input, arguments.output)


if __name__ == "__main__":
    main()
