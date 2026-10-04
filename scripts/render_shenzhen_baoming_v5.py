from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

import render_shenzhen_general_baoming as base


def add_student_guide(document: Document) -> None:
    title = document.add_paragraph()
    title.alignment = 1
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(16)
    base.set_run_font(title.add_run("使用说明"), "宋体", 22, True)

    level_heading = document.add_paragraph()
    level_heading.paragraph_format.first_line_indent = Cm(0)
    level_heading.paragraph_format.space_after = Pt(7)
    base.set_run_font(level_heading.add_run("星级"), "宋体", 14, True)
    levels = (
        (
            "★★★  核心优先｜",
            "对应速背手册原一级；同时得到深大真题、现行考纲、指定教材或一本通中的强证据支持，主观题可考性和答案复用价值最高。",
        ),
        (
            "★★  重点掌握｜",
            "同属速背手册原一级；教材、一本通和考纲／真题依据明确，能够形成稳定主观题，但综合优先度略低于三星。",
        ),
        (
            "★  基础覆盖｜",
            "对应速背手册原二级；速背手册或一本通确有收录，属于指定教材范围，但主观题信号和综合可考性相对较弱。",
        ),
    )
    for label, explanation in levels:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.right_indent = Cm(0.3)
        paragraph.paragraph_format.line_spacing = 1.42
        paragraph.paragraph_format.space_after = Pt(8)
        base.set_run_font(paragraph.add_run(label), "宋体", 11.5, True)
        base.set_run_font(paragraph.add_run(explanation), "宋体", 11.5)

    use_heading = document.add_paragraph()
    use_heading.paragraph_format.first_line_indent = Cm(0)
    use_heading.paragraph_format.space_before = Pt(6)
    use_heading.paragraph_format.space_after = Pt(7)
    base.set_run_font(use_heading.add_run("怎么用"), "宋体", 14, True)
    uses = (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数；正文加粗处为需要优先记忆的关键词。",
        "2. （）内是扩容项，选背；既可补充其他采分点，也可补充相关概念、解释或例子。例子可以根据题目灵活替换。",
    )
    for value in uses:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.line_spacing = 1.4
        paragraph.paragraph_format.space_after = Pt(6)
        base.set_run_font(paragraph.add_run(value), "宋体", 11.5)
    document.add_page_break()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-map", type=Path)
    parser.add_argument("--subject-label", default="普通心理学")
    parser.add_argument("--header-text")
    arguments = parser.parse_args()
    base.add_student_guide = add_student_guide
    base.render(
        arguments.input,
        arguments.output,
        arguments.page_map,
        subject_label=arguments.subject_label,
        header_text=arguments.header_text,
    )


if __name__ == "__main__":
    main()
