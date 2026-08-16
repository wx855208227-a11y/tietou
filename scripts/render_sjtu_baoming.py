from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.shared import Cm, Pt

import render_baoming_inline_docx as inline
from render_baoming_docx import (
    add_cover,
    add_heading,
    configure_body_header_footer,
    configure_page,
    configure_styles,
    set_run_font,
    set_update_fields,
)


def add_student_guide(document: Document) -> None:
    title = document.add_paragraph()
    title.alignment = 1
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(16)
    set_run_font(title.add_run("使用说明"), "宋体", 22, True)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_after = Pt(7)
    set_run_font(heading.add_run("星级"), "宋体", 14, True)
    levels = (
        (
            "★★★  核心优先｜",
            "上交近年真题直接考查，或同时得到一本通、速背手册／指定教材与312／347高频命题强证据支持，最应优先背诵。",
        ),
        (
            "★★  重点掌握｜",
            "速背手册或一本通列为重点，指定教材依据明确，能够形成稳定的名词解释、简答、论述或实验设计题。",
        ),
        (
            "★  基础覆盖｜",
            "速背手册、一本通或指定教材确有收录，但上交直接命题证据和主观题综合可考性相对较弱。",
        ),
    )
    for label, explanation in levels:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.right_indent = Cm(0.3)
        paragraph.paragraph_format.line_spacing = 1.42
        paragraph.paragraph_format.space_after = Pt(8)
        set_run_font(paragraph.add_run(label), "宋体", 12, True)
        set_run_font(paragraph.add_run(explanation), "宋体", 12)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(7)
    set_run_font(heading.add_run("怎么用"), "宋体", 14, True)
    for value in (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数。",
        "2. （）内是扩容项，选背；用于丰富答题角度、锦上添花。如果其中是例子，可以根据题目灵活替换。",
    ):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.line_spacing = 1.4
        paragraph.paragraph_format.space_after = Pt(6)
        set_run_font(paragraph.add_run(value), "宋体", 12)
    document.add_page_break()


def default_page_map(lines: list[str]) -> dict[str, int]:
    return {
        line.lstrip("# ").strip().split("【", 1)[0]: 0
        for line in lines
        if re.match(r"^# 第[一二三四五六七八九十百]+章", line)
        or re.match(r"^## [一二三四五六七八九十]+、", line)
    }


def render(
    markdown_path: Path,
    output_path: Path,
    page_map_path: Path | None = None,
    *,
    subject_label: str,
) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    first_chapter = next(
        index for index, line in enumerate(lines) if re.match(r"^# 第一章", line)
    )
    page_map = default_page_map(lines)
    if page_map_path:
        page_map = json.loads(page_map_path.read_text(encoding="utf-8"))

    inline.ACTIVE_BARE_EXPANSION_RE = re.compile(r"(?!)")
    document = Document()
    configure_styles(document)
    inline.force_monochrome_title_style(document)
    configure_page(document.sections[0])
    set_update_fields(document)
    document.core_properties.title = title
    document.core_properties.subject = f"上海交通大学347{subject_label}保命手册"
    document.core_properties.author = "铁头心理学考研"

    add_cover(document, title, "", edition="")
    add_student_guide(document)
    inline.add_catalog(
        document,
        lines,
        page_map,
        monochrome=True,
        question_specific=True,
        direct_without_answer_label=True,
        selective_expansion=True,
        bare_expansions=True,
    )

    body_section = document.add_section(WD_SECTION.NEW_PAGE)
    configure_page(body_section)
    configure_body_header_footer(
        body_section,
        f"上海交通大学347｜{subject_label}保命手册",
    )

    first_body_chapter = True
    for raw_line in lines[first_chapter:]:
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("# "):
            add_heading(document, 1, stripped[2:].strip(), page_break_before=not first_body_chapter)
            first_body_chapter = False
        elif stripped.startswith("## "):
            heading = add_heading(document, 2, stripped[3:].strip())
            heading.paragraph_format.space_before = Pt(13)
            heading.paragraph_format.space_after = Pt(7)
        elif stripped.startswith("### "):
            inline.add_question_heading(
                document,
                stripped[4:].strip(),
                monochrome=True,
                large_between_question_gap=True,
                comfortable=True,
                bare_expansions=True,
            )
        elif re.match(r"^\d+\.\s", stripped):
            inline.add_list_paragraph(
                document,
                raw_line,
                answer_mode=True,
                compact=False,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
            )
        elif re.match(r"^（\d+）", stripped):
            inline.add_secondary_list_paragraph(
                document,
                raw_line,
                answer_mode=True,
                compact=False,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
            )
        else:
            inline.add_body_paragraph(
                document,
                stripped,
                compact=False,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-map", type=Path)
    parser.add_argument("--subject-label", required=True)
    arguments = parser.parse_args()
    render(
        arguments.input,
        arguments.output,
        arguments.page_map,
        subject_label=arguments.subject_label,
    )


if __name__ == "__main__":
    main()
