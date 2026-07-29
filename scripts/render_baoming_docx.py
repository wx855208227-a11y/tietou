from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


BLACK = RGBColor(0, 0, 0)
TAG_GRAY = RGBColor(89, 89, 89)
GRAY_FILL = "D9D9D9"
LIGHT_GRAY_FILL = "F2F2F2"
ANSWER_FILL = "E7E6E6"

COMPACT_UNIT_PREFIXES = (
    "十、观察学习",
    "十一、格雷的强化敏感性理论",
)

CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 3,
    "五、格式塔心理学": 3,
    "六、精神分析学派": 4,
    "七、人本主义心理学": 5,
    "八、认知心理学": 6,
    "九、观察法、相关研究法与实验法": 6,
    "十、实验变量": 7,
    "十一、测验法与信效度": 8,
    "十二、投射法与投射测验": 8,
    "十三、心理学的主要分支": 9,
    "第二章 心理和行为的生物学基础": 11,
    "一、神经元": 11,
    "二、神经冲动与突触传递": 11,
    "三、神经系统的构成与功能": 12,
    "四、大脑皮层的感觉区与运动区": 13,
    "五、大脑皮层的言语区与联合区": 14,
    "六、大脑两半球的功能分工": 14,
    "七、丘脑与下丘脑": 15,
    "八、边缘系统、海马与杏仁核": 16,
    "九、脑功能的主要学说": 16,
    "第三章 条件反射和学习": 18,
    "一、学习的含义与特征": 18,
    "二、反射、反射弧与反射类型": 18,
    "三、经典条件反射": 19,
    "四、经典条件反射的基本规律": 20,
    "五、信号系统与高级神经活动": 21,
    "六、操作条件反射与行为调控": 22,
    "七、经典条件反射与操作条件反射的比较": 23,
    "八、顿悟学习": 24,
    "九、目的行为学习理论": 24,
    "十、观察学习": 25,
    "十一、格雷的强化敏感性理论": 26,
}


def set_run_font(run, name: str = "宋体", size: float = 12, bold: bool | None = None) -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.color.rgb = BLACK
    if bold is not None:
        run.bold = bold


def shade_paragraph(paragraph, fill: str) -> None:
    properties = paragraph._p.get_or_add_pPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def shade_cell(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_update_fields(document: Document) -> None:
    settings = document.settings.element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


def configure_styles(document: Document) -> None:
    normal = document.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.first_line_indent = Cm(0.74)
    normal.paragraph_format.space_after = Pt(3)
    normal.paragraph_format.widow_control = True

    if "Subtitle" not in document.styles:
        document.styles.add_style("Subtitle", WD_STYLE_TYPE.PARAGRAPH)

    style_specs = {
        "Title": ("微软雅黑", 26, True),
        "Subtitle": ("微软雅黑", 16, True),
        "Heading 1": ("宋体", 16, True),
        "Heading 2": ("宋体", 14, True),
        "Heading 3": ("宋体", 12, True),
    }
    for style_name, (font_name, font_size, bold) in style_specs.items():
        style = document.styles[style_name]
        style.font.name = font_name
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font_name)
        style.font.size = Pt(font_size)
        style.font.bold = bold
        style.font.color.rgb = BLACK
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.widow_control = True


def configure_page(section) -> None:
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)


def add_page_field(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, end])
    set_run_font(run, size=12)


def configure_body_header_footer(section) -> None:
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run("华东师范大学347｜心理学导论保命手册")
    set_run_font(header_run, size=9)
    add_page_field(section.footer.paragraphs[0])
    page_number_type = section._sectPr.find(qn("w:pgNumType"))
    if page_number_type is None:
        page_number_type = OxmlElement("w:pgNumType")
        section._sectPr.append(page_number_type)
    page_number_type.set(qn("w:start"), "1")


def add_cover(document: Document, title: str, subtitle: str) -> None:
    document.add_paragraph()
    document.add_paragraph()
    document.add_paragraph()
    title_paragraph = document.add_paragraph(style="Title")
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_paragraph.paragraph_format.space_after = Pt(16)
    if "心理学导论" in title:
        school_title, manual_title = title.split("心理学导论", 1)
        title_run = title_paragraph.add_run(school_title.rstrip())
        set_run_font(title_run, "微软雅黑", 24, True)
        title_run.add_break()
        manual_run = title_paragraph.add_run("心理学导论" + manual_title)
        set_run_font(manual_run, "微软雅黑", 24, True)
    else:
        title_run = title_paragraph.add_run(title)
        set_run_font(title_run, "微软雅黑", 24, True)

    subtitle_paragraph = document.add_paragraph(style="Subtitle")
    subtitle_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle_paragraph.add_run(subtitle)
    set_run_font(subtitle_run, "微软雅黑", 16, True)

    document.add_paragraph()
    edition_paragraph = document.add_paragraph()
    edition_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    edition_paragraph.paragraph_format.first_line_indent = Cm(0)
    edition_run = edition_paragraph.add_run("前三章｜2026")
    set_run_font(edition_run, "微软雅黑", 11, True)
    document.add_page_break()


def add_catalog(document: Document, lines: list[str]) -> None:
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(18)
    title_run = title.add_run("目录")
    set_run_font(title_run, "宋体", 26, True)

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
        run = paragraph.add_run(f"{heading}\t{CATALOG_PAGE_MAP[heading]}")
        set_run_font(run, size=11, bold=is_chapter)

    legend = document.add_paragraph()
    legend.paragraph_format.first_line_indent = Cm(0)
    legend.paragraph_format.space_before = Pt(8)
    legend.paragraph_format.space_after = Pt(0)
    shade_paragraph(legend, LIGHT_GRAY_FILL)
    legend_run = legend.add_run(
        "使用图例｜名解核心：定义及题干对应分点；简答必写：基础得分点；"
        "论述展开：高分题续写；背诵检索串：仅用于闭卷复述，不写入答卷。"
    )
    set_run_font(legend_run, size=9.5)


def markdown_tokens(text: str) -> list[tuple[str, bool, bool]]:
    tokens: list[tuple[str, bool, bool]] = []
    buffer: list[str] = []
    is_bold = False
    is_underlined = False
    cursor = 0

    def flush_buffer() -> None:
        if buffer:
            tokens.append(("".join(buffer), is_bold, is_underlined))
            buffer.clear()

    while cursor < len(text):
        marker = text[cursor:cursor + 2]
        if marker == "**":
            flush_buffer()
            is_bold = not is_bold
            cursor += 2
            continue
        if marker == "++":
            flush_buffer()
            is_underlined = not is_underlined
            cursor += 2
            continue
        buffer.append(text[cursor])
        cursor += 1
    flush_buffer()
    return tokens


def add_inline_runs(paragraph, text: str, size: float = 12) -> None:
    tokens = markdown_tokens(text)
    for content, is_bold, is_underlined in tokens:
        if not content:
            continue
        for part in re.split(r"(【[^】]+】)", content):
            if not part:
                continue
            if re.fullmatch(r"【[^】]+】", part):
                tag_run = paragraph.add_run(part)
                set_run_font(tag_run, size=9.5, bold=True)
                tag_run.font.color.rgb = TAG_GRAY
                continue
            run = paragraph.add_run(part)
            set_run_font(run, size=size, bold=is_bold)
            run.underline = is_underlined


def add_heading(document: Document, level: int, text: str, page_break_before: bool = False):
    paragraph = document.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.page_break_before = page_break_before
    if level == 1:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(12)
        font_size = 16
    elif level == 2:
        paragraph.paragraph_format.space_before = Pt(12)
        paragraph.paragraph_format.space_after = Pt(6)
        font_size = 14
    else:
        paragraph.paragraph_format.space_before = Pt(8)
        paragraph.paragraph_format.space_after = Pt(4)
        font_size = 12
        if text.startswith("铁头tips"):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            shade_paragraph(paragraph, GRAY_FILL)
    run = paragraph.add_run(text)
    set_run_font(run, size=font_size, bold=True)
    return paragraph


def add_list_paragraph(
    document: Document,
    raw_line: str,
    underline_core: bool,
    keep_with_next: bool = False,
    compact: bool = False,
):
    leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
    stripped = raw_line.strip()
    displayed = "• " + stripped[2:] if stripped.startswith("- ") else stripped
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.75 + min(leading_spaces // 2, 3) * 0.42)
    paragraph.paragraph_format.first_line_indent = Cm(-0.48)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(0 if compact else 2)
    paragraph.paragraph_format.widow_control = True
    paragraph.paragraph_format.keep_with_next = keep_with_next
    add_inline_runs(paragraph, displayed)
    return paragraph


def add_body_paragraph(
    document: Document,
    text: str,
    underline_core: bool,
    compact: bool = False,
) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(0 if compact else 3)
    paragraph.paragraph_format.widow_control = True
    if re.match(r"^\*\*【(?:总|分)", text):
        shade_paragraph(paragraph, ANSWER_FILL)
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.keep_with_next = True
    elif text.startswith("**【答题调用】") or text.startswith("**【容量建议】"):
        shade_paragraph(paragraph, LIGHT_GRAY_FILL)
        paragraph.paragraph_format.first_line_indent = Cm(0)
    elif text.startswith("**真题依据**") or text.startswith("**考纲依据**"):
        shade_paragraph(paragraph, LIGHT_GRAY_FILL)
        paragraph.paragraph_format.first_line_indent = Cm(0)
    elif "【背诵检索串】" in text:
        shade_paragraph(paragraph, LIGHT_GRAY_FILL)
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(2)
    add_inline_runs(paragraph, text)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def prevent_row_split(row) -> None:
    properties = row._tr.get_or_add_trPr()
    if properties.find(qn("w:cantSplit")) is None:
        properties.append(OxmlElement("w:cantSplit"))


def add_table(document: Document, table_lines: list[str]) -> None:
    parsed_rows = [split_table_row(line) for line in table_lines]
    parsed_rows = [row for row in parsed_rows if row and not is_separator_row(row)]
    if not parsed_rows:
        return
    column_count = max(len(row) for row in parsed_rows)
    table = document.add_table(rows=len(parsed_rows), cols=column_count)
    table.style = "Table Grid"
    table.autofit = True
    for row_index, values in enumerate(parsed_rows):
        row = table.rows[row_index]
        prevent_row_split(row)
        for column_index in range(column_count):
            cell = row.cells[column_index]
            if row_index == 0:
                shade_cell(cell, GRAY_FILL)
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.line_spacing = 1.15
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.keep_together = True
            value = values[column_index] if column_index < len(values) else ""
            add_inline_runs(paragraph, value, size=10.5)
            for run in paragraph.runs:
                if row_index == 0:
                    run.bold = True
        if row_index == 0:
            header_properties = row._tr.get_or_add_trPr()
            repeat_header = OxmlElement("w:tblHeader")
            repeat_header.set(qn("w:val"), "true")
            header_properties.append(repeat_header)
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(4)


def render_markdown(markdown_path: Path, output_path: Path) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    subtitle = lines[2].removeprefix("## ").strip()
    document = Document()
    configure_styles(document)
    configure_page(document.sections[0])
    set_update_fields(document)
    document.core_properties.title = title
    document.core_properties.subject = "华东师范大学347心理学导论考前冲刺"
    document.core_properties.author = "铁头心理学考研"
    add_cover(document, title, subtitle)
    first_chapter_index = next(
        index for index, line in enumerate(lines) if line.startswith("# 第一章 ")
    )
    add_catalog(document, lines)

    body_section = document.add_section(WD_SECTION.NEW_PAGE)
    configure_page(body_section)
    configure_body_header_footer(body_section)

    answer_section_active = False
    question_block_active = False
    compact_unit_active = False
    first_chapter = True
    line_index = first_chapter_index
    while line_index < len(lines):
        raw_line = lines[line_index]
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            line_index += 1
            continue
        if stripped.startswith("| ") or stripped.startswith("|"):
            table_lines: list[str] = []
            while line_index < len(lines) and lines[line_index].strip().startswith("|"):
                table_lines.append(lines[line_index].strip())
                line_index += 1
            add_table(document, table_lines)
            answer_section_active = False
            continue
        if stripped.startswith("# "):
            add_heading(document, 1, stripped[2:].strip(), page_break_before=not first_chapter)
            first_chapter = False
            answer_section_active = False
            question_block_active = False
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            heading = add_heading(document, 2, heading_text)
            compact_unit_active = heading_text.startswith(COMPACT_UNIT_PREFIXES)
            if compact_unit_active:
                heading.paragraph_format.space_before = Pt(6)
                heading.paragraph_format.space_after = Pt(2)
            answer_section_active = False
            question_block_active = False
        elif stripped.startswith("### "):
            heading_text = stripped[4:].strip()
            heading = add_heading(document, 3, heading_text)
            if compact_unit_active:
                heading.paragraph_format.space_before = Pt(4)
                heading.paragraph_format.space_after = Pt(2)
            answer_section_active = False
            question_block_active = heading_text == "押题题目"
        elif stripped.startswith("> "):
            paragraph = document.add_paragraph()
            shade_paragraph(paragraph, LIGHT_GRAY_FILL)
            paragraph.paragraph_format.first_line_indent = Cm(0)
            add_inline_runs(paragraph, stripped[2:].strip())
        elif stripped.startswith("- ") or re.match(
            r"^(?:\*\*【[^】]+】\*\*\s*)*\d+\.\s",
            stripped,
        ):
            add_list_paragraph(
                document,
                raw_line,
                answer_section_active,
                keep_with_next=question_block_active,
                compact=compact_unit_active,
            )
        else:
            if re.match(r"^\*\*【(?:总|分)", stripped):
                answer_section_active = True
                add_body_paragraph(document, stripped, False, compact_unit_active)
            else:
                add_body_paragraph(
                    document,
                    stripped,
                    answer_section_active,
                    compact_unit_active,
                )
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
