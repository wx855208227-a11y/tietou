from __future__ import annotations

from pathlib import Path

from docx.shared import Cm, Pt

import merge_ecnu_baoming_manuals as base


ROOT = Path(__file__).resolve().parents[1]

base.OUTPUT = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订版V5.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/shenzhen_baoming_combined_v5_page_map.json"
base.COVER_TITLE = "深圳大学347心理学保命手册"
base.CORE_TITLE = "深圳大学347心理学保命手册"
base.CORE_SUBJECT = "普通心理学、实验心理学、心理与教育测量合订版"
base.GUIDE_LEVEL_LINES = (
    "★★★  核心优先｜对应速背手册原一级；同时得到深大真题、现行考纲、指定教材或一本通中的强证据支持，主观题可考性和答案复用价值最高。",
    "★★  重点掌握｜同属速背手册原一级；教材、一本通和考纲／真题依据明确，能够形成稳定主观题，但综合优先度略低于三星。",
    "★  基础覆盖｜对应速背手册原二级；速背手册或一本通确有收录，属于指定教材范围，但主观题信号和综合可考性相对较弱。",
)
base.STRIP_NON_CHAPTER_PAGE_BREAKS = True
base.COMBINED_NON_CHAPTER_PAGE_BREAK_TEXTS = set()
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "深圳大学347｜普通心理学保命手册",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V6.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "深圳大学347｜实验心理学保命手册",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V5.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "深圳大学347｜心理与教育测量保命手册",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V5.docx",
    ),
)


def add_guide(document) -> None:
    base.add_front_heading(document, "使用说明", 18)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(6)
    base.set_run_font(heading.add_run("星级"), size=14, bold=True)
    for text in base.GUIDE_LEVEL_LINES:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.35
        paragraph.paragraph_format.space_after = Pt(5)
        base.set_run_font(paragraph.add_run(text), size=12)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(6)
    base.set_run_font(heading.add_run("怎么用"), size=14, bold=True)
    for text in (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数。",
        "2. （）内是扩容项，选背；既可补充其他采分点，也可补充相关概念、解释或例子。例子可以根据题目灵活替换。",
    ):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.35
        paragraph.paragraph_format.space_after = Pt(6)
        base.set_run_font(paragraph.add_run(text), size=12)
    document.add_page_break()


base.add_guide = add_guide


if __name__ == "__main__":
    base.main()
