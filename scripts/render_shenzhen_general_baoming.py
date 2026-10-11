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


# These source-backed answers otherwise leave only a short conclusion or final
# scoring point on the last page immediately before a mandatory chapter break.
# A slightly tighter paragraph rhythm is applied to the whole unit; font size,
# wording and scoring-point hierarchy remain unchanged.
DENSE_UNIT_PREFIXES = (
    "六、心理学的主要流派",
    "六、决策理论与启发式偏差",
    "五、动机的一般理论",
    "五、情绪智力与情绪调节",
    "六、埃里克森心理社会性发展理论",
    "十一、实验效度",
    "三、测验结果的报告",
    "三、组内常模与标准分数",
)

# These units were found by page-level PDF QA to leave only a short tail of
# scoring points or a conclusion on the page immediately before the next
# mandatory chapter break.  Apply single-line rhythm only inside these units;
# this avoids a nearly empty continuation page without shrinking the 12 pt
# body text or changing answer content.
EXTRA_DENSE_UNIT_PREFIXES = (
    "六、心理学的主要流派",
    "二、语言的神经基础",
    "五、情绪智力与情绪调节",
    "七、认知学习与动作技能学习",
    "十一、实验效度",
    "四、序列反应时与内隐联想测验",
    "三、内隐学习",
    "四、多重选择题项目分析",
    "三、组内常模与标准分数",
    "三、瑞文测验",
)

# A few source-heavy chapters still produced a short chapter-end continuation
# page after the final unit was tightened.  Using the normal 1.1 compact rhythm
# across the whole chapter lets the content flow naturally onto the preceding
# pages while retaining 12 pt text and all scoring points.
DENSE_CHAPTER_PREFIXES = (
    "第五章 意识",
    "第二章 实验研究的基本问题",
    "第八章 记忆与学习",
    "第八章 常模参照测验",
    "第十一章 能力测验",
    "第十六章 测量理论与应用的新发展",
)

TIGHTER_CHAPTER_PREFIXES = (
    "第二章 实验研究的基本问题",
)


def tighten_dense_paragraph(paragraph) -> None:
    spacing = paragraph.paragraph_format.line_spacing
    if isinstance(spacing, (int, float)):
        paragraph.paragraph_format.line_spacing = min(spacing, 1.1)
    paragraph.paragraph_format.space_before = min(
        paragraph.paragraph_format.space_before or Pt(0), Pt(2)
    )
    paragraph.paragraph_format.space_after = min(
        paragraph.paragraph_format.space_after or Pt(0), Pt(0.5)
    )


def tighten_extra_dense_paragraph(paragraph) -> None:
    tighten_dense_paragraph(paragraph)
    paragraph.paragraph_format.line_spacing = 0.96
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    if paragraph.paragraph_format.left_indent is not None:
        paragraph.paragraph_format.left_indent = max(
            paragraph.paragraph_format.left_indent - Cm(0.12),
            Cm(0),
        )


def tighten_chapter_paragraph(paragraph) -> None:
    tighten_dense_paragraph(paragraph)
    paragraph.paragraph_format.line_spacing = 1.06
    paragraph.paragraph_format.space_before = min(
        paragraph.paragraph_format.space_before or Pt(0), Pt(1)
    )
    paragraph.paragraph_format.space_after = Pt(0)


def add_student_guide(document: Document) -> None:
    title = document.add_paragraph()
    title.alignment = 1
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(16)
    set_run_font(title.add_run("使用说明"), "宋体", 22, True)

    level_heading = document.add_paragraph()
    level_heading.paragraph_format.first_line_indent = Cm(0)
    level_heading.paragraph_format.space_after = Pt(7)
    set_run_font(level_heading.add_run("星级"), "宋体", 14, True)
    levels = (
        (
            "★★★  核心优先｜",
            "对应速背手册原一级；同时得到深大真题、现行考纲、指定教材或一本通中的强证据支持，主观题可考性和复用价值最高。",
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
        set_run_font(paragraph.add_run(label), "宋体", 11.5, True)
        set_run_font(paragraph.add_run(explanation), "宋体", 11.5)

    use_heading = document.add_paragraph()
    use_heading.paragraph_format.first_line_indent = Cm(0)
    use_heading.paragraph_format.space_before = Pt(6)
    use_heading.paragraph_format.space_after = Pt(7)
    set_run_font(use_heading.add_run("怎么用"), "宋体", 14, True)
    uses = (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数。",
        "2. （）内是扩容项，选背；用于丰富答题角度、锦上添花。如果其中是例子，可以根据题目灵活替换。",
    )
    for value in uses:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.line_spacing = 1.4
        paragraph.paragraph_format.space_after = Pt(6)
        set_run_font(paragraph.add_run(value), "宋体", 11.5)
    document.add_page_break()


def default_page_map(lines: list[str]) -> dict[str, int]:
    return {
        line.lstrip("# ").strip().split("【", 1)[0]: 0
        for line in lines
        if line.startswith("# 第")
        or line.startswith("# 补充章")
        or re.match(r"^## [一二三四五六七八九十]+、", line)
    }


def render(
    markdown_path: Path,
    output_path: Path,
    page_map_path: Path | None = None,
    *,
    subject_label: str = "普通心理学",
    header_text: str | None = None,
    compact_answers: bool = False,
) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    first_chapter = next(index for index, line in enumerate(lines) if line.startswith("# 第一章 "))
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
    document.core_properties.subject = f"深圳大学347{subject_label}逐题直背保命手册"
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
        header_text or f"深圳大学347｜{subject_label}保命手册",
    )

    first_body_chapter = True
    dense_chapter = False
    tighter_chapter = False
    dense_unit = False
    extra_dense_unit = False
    for raw_line in lines[first_chapter:]:
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith("# "):
            chapter_text = stripped[2:].strip()
            add_heading(document, 1, chapter_text, page_break_before=not first_body_chapter)
            first_body_chapter = False
            dense_chapter = compact_answers and chapter_text.startswith(
                DENSE_CHAPTER_PREFIXES
            )
            tighter_chapter = compact_answers and chapter_text.startswith(
                TIGHTER_CHAPTER_PREFIXES
            )
            dense_unit = False
            extra_dense_unit = False
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            dense_unit = compact_answers and (
                dense_chapter or heading_text.startswith(DENSE_UNIT_PREFIXES)
            )
            extra_dense_unit = compact_answers and heading_text.startswith(
                EXTRA_DENSE_UNIT_PREFIXES
            )
            heading = add_heading(document, 2, heading_text)
            heading.paragraph_format.space_before = Pt(9 if compact_answers else 13)
            heading.paragraph_format.space_after = Pt(5 if compact_answers else 7)
            if extra_dense_unit:
                tighten_extra_dense_paragraph(heading)
            elif tighter_chapter:
                tighten_chapter_paragraph(heading)
            elif dense_unit:
                tighten_dense_paragraph(heading)
        elif stripped.startswith("### "):
            paragraph = inline.add_question_heading(
                document,
                stripped[4:].strip(),
                monochrome=True,
                large_between_question_gap=True,
                comfortable=True,
                bare_expansions=True,
                tight_layout=compact_answers,
            )
            if extra_dense_unit:
                tighten_extra_dense_paragraph(paragraph)
            elif tighter_chapter:
                tighten_chapter_paragraph(paragraph)
            elif dense_unit:
                tighten_dense_paragraph(paragraph)
        elif re.match(r"^\d+\.\s", stripped):
            inline.add_list_paragraph(
                document,
                raw_line,
                answer_mode=True,
                compact=False,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
                tight_layout=compact_answers,
            )
            if extra_dense_unit:
                tighten_extra_dense_paragraph(document.paragraphs[-1])
            elif tighter_chapter:
                tighten_chapter_paragraph(document.paragraphs[-1])
            elif dense_unit:
                tighten_dense_paragraph(document.paragraphs[-1])
        elif re.match(r"^（\d+）", stripped):
            inline.add_secondary_list_paragraph(
                document,
                raw_line,
                answer_mode=True,
                compact=False,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
                tight_layout=compact_answers,
            )
            if extra_dense_unit:
                tighten_extra_dense_paragraph(document.paragraphs[-1])
            elif tighter_chapter:
                tighten_chapter_paragraph(document.paragraphs[-1])
            elif dense_unit:
                tighten_dense_paragraph(document.paragraphs[-1])
        elif re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", stripped):
            inline.add_deep_list_paragraph(
                document,
                raw_line,
                answer_mode=True,
                compact=False,
                level=3,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
                tight_layout=compact_answers,
            )
            if extra_dense_unit:
                tighten_extra_dense_paragraph(document.paragraphs[-1])
            elif tighter_chapter:
                tighten_chapter_paragraph(document.paragraphs[-1])
            elif dense_unit:
                tighten_dense_paragraph(document.paragraphs[-1])
        elif re.match(r"^[a-z]\.\s", stripped):
            inline.add_deep_list_paragraph(
                document,
                raw_line,
                answer_mode=True,
                compact=False,
                level=4,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
                tight_layout=compact_answers,
            )
            if extra_dense_unit:
                tighten_extra_dense_paragraph(document.paragraphs[-1])
            elif tighter_chapter:
                tighten_chapter_paragraph(document.paragraphs[-1])
            elif dense_unit:
                tighten_dense_paragraph(document.paragraphs[-1])
        else:
            inline.add_body_paragraph(
                document,
                stripped,
                compact=False,
                monochrome=True,
                comfortable=True,
                bare_expansions=True,
                tight_layout=compact_answers,
            )
            if extra_dense_unit:
                tighten_extra_dense_paragraph(document.paragraphs[-1])
            elif tighter_chapter:
                tighten_chapter_paragraph(document.paragraphs[-1])
            elif dense_unit:
                tighten_dense_paragraph(document.paragraphs[-1])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-map", type=Path)
    parser.add_argument("--subject-label", default="普通心理学")
    parser.add_argument("--header-text")
    parser.add_argument("--compact-answers", action="store_true")
    arguments = parser.parse_args()
    render(
        arguments.input,
        arguments.output,
        arguments.page_map,
        subject_label=arguments.subject_label,
        header_text=arguments.header_text,
        compact_answers=arguments.compact_answers,
    )


if __name__ == "__main__":
    main()
