from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt

import merge_ecnu_baoming_manuals as merger
import render_shenzhen_general_baoming as renderer
from build_shenzhen_baoming_v19_final_artifacts import (
    convert_pdf,
    extract_subject_page_map,
)


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
CONTENT = ROOT / "content"

SUBJECTS = (
    (
        "普通心理学",
        DELIVERABLES / "深圳大学347普通心理学保命手册_V19完整范围排版优化版V23.md",
        DELIVERABLES / "深圳大学347普通心理学保命手册_V19完整范围排版优化版V23.docx",
        CONTENT / "shenzhen_general_baoming_v23_page_map.json",
    ),
    (
        "实验心理学",
        DELIVERABLES / "深圳大学347实验心理学保命手册_V19完整范围排版优化版V23.md",
        DELIVERABLES / "深圳大学347实验心理学保命手册_V19完整范围排版优化版V23.docx",
        CONTENT / "shenzhen_experiment_baoming_v23_page_map.json",
    ),
    (
        "心理与教育测量",
        DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19完整范围排版优化版V23.md",
        DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19完整范围排版优化版V23.docx",
        CONTENT / "shenzhen_measurement_baoming_v23_page_map.json",
    ),
)

COMBINED_DOCX = DELIVERABLES / "深圳大学347心理学保命手册_普心实验测量合订V19完整范围排版优化版V23.docx"
COMBINED_PAGE_MAP = CONTENT / "shenzhen_baoming_combined_v23_page_map.json"


STAR_LINES = (
    "★★★  核心优先｜对应速背手册原一级；深大真题、命题风格和知识点可考性证据较强，主观题复用价值最高。",
    "★★  重点掌握｜同属速背手册原一级；能够形成稳定的主观题，但深大直接证据或综合优先度略低于三星。",
    "★  基础覆盖｜对应速背手册原二级；用于补足速背手册保留的基础范围。",
)

USE_LINES = (
    "1. 圆括号外是背诵主体，写全可以拿到主要分数；正文加粗处为需要优先记忆的关键词。",
    "2. （）内是扩容项，选背；既可增加采分点，也可补充相关概念、解释或例子。例子可以根据题目灵活替换。",
)


def add_student_guide(document: Document) -> None:
    title = document.add_paragraph()
    title.alignment = 1
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(16)
    renderer.set_run_font(title.add_run("使用说明"), "宋体", 22, True)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_after = Pt(7)
    renderer.set_run_font(heading.add_run("星级"), "宋体", 14, True)
    for value in STAR_LINES:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.right_indent = Cm(0.3)
        paragraph.paragraph_format.line_spacing = 1.45
        paragraph.paragraph_format.space_after = Pt(8)
        renderer.set_run_font(paragraph.add_run(value), "宋体", 12)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(7)
    renderer.set_run_font(heading.add_run("怎么用"), "宋体", 14, True)
    for value in USE_LINES:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.line_spacing = 1.45
        paragraph.paragraph_format.space_after = Pt(7)
        renderer.set_run_font(paragraph.add_run(value), "宋体", 12)
    document.add_page_break()


def render_subject(
    subject: str,
    markdown_path: Path,
    docx_path: Path,
    page_map_path: Path | None,
) -> None:
    renderer.add_student_guide = add_student_guide
    renderer.render(
        markdown_path,
        docx_path,
        page_map_path,
        subject_label=subject,
        header_text=f"深圳大学347｜{subject}保命手册",
        compact_answers=False,
    )


def add_combined_guide(document: Document) -> None:
    merger.add_front_heading(document, "使用说明", 18)
    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(7)
    merger.set_run_font(heading.add_run("星级"), size=14, bold=True)
    for value in STAR_LINES:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.45
        paragraph.paragraph_format.space_after = Pt(8)
        merger.set_run_font(paragraph.add_run(value), size=12)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(8)
    heading.paragraph_format.space_after = Pt(7)
    merger.set_run_font(heading.add_run("怎么用"), size=14, bold=True)
    for value in USE_LINES:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.45
        paragraph.paragraph_format.space_after = Pt(7)
        merger.set_run_font(paragraph.add_run(value), size=12)
    document.add_page_break()


def configure_combined() -> None:
    merger.OUTPUT = COMBINED_DOCX
    merger.PAGE_MAP_OUTPUT = COMBINED_PAGE_MAP
    merger.COVER_TITLE = "深圳大学347心理学保命手册"
    merger.CORE_TITLE = "深圳大学347心理学保命手册"
    merger.CORE_SUBJECT = "普通心理学、实验心理学、心理与教育测量合订版"
    merger.STRIP_NON_CHAPTER_PAGE_BREAKS = False
    merger.COMBINED_NON_CHAPTER_PAGE_BREAK_TEXTS = set()
    merger.SOURCES = tuple(
        (
            f"第{'一二三'[index]}部分 {subject}",
            subject,
            f"深圳大学347｜{subject}保命手册",
            docx_path,
        )
        for index, (subject, _markdown, docx_path, _page_map) in enumerate(SUBJECTS)
    )
    merger.add_guide = add_combined_guide


def build_combined() -> None:
    configure_combined()
    merger.build(COMBINED_DOCX, None)
    draft_pdf = convert_pdf(COMBINED_DOCX)
    page_map = merger.extract_page_map(draft_pdf)
    COMBINED_PAGE_MAP.write_text(
        json.dumps(page_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    merger.build(COMBINED_DOCX, page_map)
    convert_pdf(COMBINED_DOCX)


def main() -> None:
    for subject, markdown_path, docx_path, page_map_path in SUBJECTS:
        render_subject(subject, markdown_path, docx_path, None)
        pdf_path = convert_pdf(docx_path)
        extract_subject_page_map(markdown_path, pdf_path, page_map_path)
        render_subject(subject, markdown_path, docx_path, page_map_path)
        convert_pdf(docx_path)
        print(f"PASS built {subject}")
    build_combined()
    print("PASS built V23 subject and combined artifacts")


if __name__ == "__main__":
    main()
