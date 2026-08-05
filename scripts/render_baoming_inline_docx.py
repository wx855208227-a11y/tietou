from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.shared import Cm, Pt, RGBColor

from render_baoming_docx import (
    LIGHT_GRAY_FILL,
    add_cover,
    add_heading,
    add_table,
    configure_body_header_footer,
    configure_page,
    configure_styles,
    markdown_tokens,
    set_run_font,
    set_update_fields,
    shade_paragraph,
)
from render_baoming_mother_docx import CATALOG_PAGE_MAP, COMPACT_UNIT_PREFIXES


TAG_GRAY = RGBColor(89, 89, 89)
OPTIONAL_GRAY = RGBColor(96, 96, 96)
DEFINITION_TAG_RE = re.compile(r"【名词解释：[^】]+】")


def add_inline_runs(paragraph, content: str, size: float = 12, optional: bool = False) -> None:
    for text, is_bold, is_underlined in markdown_tokens(content):
        if not text:
            continue
        for part in re.split(r"(【[^】]+】)", text):
            if not part:
                continue
            run = paragraph.add_run(part)
            if DEFINITION_TAG_RE.fullmatch(part):
                set_run_font(run, "宋体", 9.5, True)
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW
            elif re.fullmatch(r"【[^】]+】", part):
                set_run_font(run, "宋体", 9.5, True)
                run.font.color.rgb = TAG_GRAY
            else:
                set_run_font(run, "宋体", 9.5 if optional else size, is_bold)
                run.underline = is_underlined
                if optional:
                    run.font.color.rgb = OPTIONAL_GRAY


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

    note = document.add_paragraph()
    note.paragraph_format.first_line_indent = Cm(0)
    note.paragraph_format.space_before = Pt(8)
    note.paragraph_format.space_after = Pt(0)
    shade_paragraph(note, LIGHT_GRAY_FILL)
    set_run_font(
        note.add_run(
            "直接用法｜整篇顺背；名词解释提取黄色标签前的定义；括号内加分项按题干和时间灵活选写。"
        ),
        size=9.5,
        bold=True,
    )


def add_answer_heading(document: Document) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.keep_with_next = True
    set_run_font(paragraph.add_run("综合答案"), "宋体", 11, True)


def add_list_paragraph(document: Document, raw_line: str, answer_mode: bool, compact: bool) -> None:
    stripped = raw_line.strip()
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.75)
    paragraph.paragraph_format.first_line_indent = Cm(-0.48)
    paragraph.paragraph_format.line_spacing = 1.2 if compact else 1.35
    paragraph.paragraph_format.space_after = Pt(0 if answer_mode else 1)
    paragraph.paragraph_format.widow_control = True
    paragraph.paragraph_format.keep_with_next = not answer_mode
    add_inline_runs(paragraph, stripped, size=10.5 if not answer_mode else 11.5)


def add_body_paragraph(document: Document, content: str, compact: bool) -> None:
    optional = content.startswith("（加分项：")
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.18 if optional else 1.25 if compact else 1.4
    paragraph.paragraph_format.space_after = Pt(1)
    paragraph.paragraph_format.widow_control = True
    if optional:
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(1)
    add_inline_runs(paragraph, content, size=11.5, optional=optional)


def render_markdown(markdown_path: Path, output_path: Path) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    subtitle = lines[2].removeprefix("## ").strip()
    document = Document()
    configure_styles(document)
    configure_page(document.sections[0])
    set_update_fields(document)
    document.core_properties.title = title
    document.core_properties.subject = "华东师范大学347心理学导论直背综合答案版"
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
    compact_unit = False
    first_chapter = True
    line_index = first_chapter_index
    while line_index < len(lines):
        raw_line = lines[line_index]
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            line_index += 1
            continue
        if stripped.startswith("# "):
            add_heading(document, 1, stripped[2:].strip(), page_break_before=not first_chapter)
            first_chapter = False
            answer_mode = False
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            heading = add_heading(document, 2, heading_text)
            compact_unit = heading_text.startswith(COMPACT_UNIT_PREFIXES)
            if compact_unit:
                heading.paragraph_format.space_before = Pt(7)
                heading.paragraph_format.space_after = Pt(3)
            answer_mode = False
        elif stripped.startswith("### "):
            heading_text = stripped[4:].strip()
            if heading_text == "综合答案":
                add_answer_heading(document)
                answer_mode = True
            else:
                displayed = "押题题目" if heading_text == "押题题目" else heading_text
                heading = add_heading(document, 3, displayed)
                heading.paragraph_format.space_before = Pt(5)
                heading.paragraph_format.space_after = Pt(2)
                answer_mode = False
        elif stripped.startswith("|"):
            table_lines: list[str] = []
            while line_index < len(lines) and lines[line_index].strip().startswith("|"):
                table_lines.append(lines[line_index].strip())
                line_index += 1
            add_table(document, table_lines)
            continue
        elif re.match(r"^\d+\.\s", stripped):
            add_list_paragraph(document, raw_line, answer_mode, compact_unit)
        else:
            add_body_paragraph(document, stripped, compact_unit)
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
