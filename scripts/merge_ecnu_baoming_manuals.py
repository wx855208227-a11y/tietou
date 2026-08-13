from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables/华东师范大学347保命手册_导论实验测量合订版V1.docx"
PAGE_MAP_OUTPUT = ROOT / "content/ecnu_baoming_combined_v1_page_map.json"

SOURCES = (
    (
        "第一部分 心理学导论",
        "心理学导论",
        "华东师范大学347｜心理学导论保命手册",
        ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_极简直背版V9.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "华东师范大学347｜实验心理学保命手册",
        ROOT / "deliverables/华东师范大学347实验心理学保命手册_全本_极简直背版V1.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "华东师范大学347｜心理测量保命手册",
        ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_极简直背版V3.docx",
    ),
)

BLACK = RGBColor(0, 0, 0)
STRIP_NON_CHAPTER_PAGE_BREAKS = False
COMBINED_NON_CHAPTER_PAGE_BREAK_TEXTS: set[str] = set()


def set_run_font(run, name: str = "宋体", size: float = 12, bold: bool | None = None) -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.color.rgb = BLACK
    run.font.italic = False
    if bold is not None:
        run.bold = bold


def configure_page(section) -> None:
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.0)


def clear_container(container) -> None:
    element = container._element
    for child in list(element):
        element.remove(child)
    element.append(OxmlElement("w:p"))


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
    result = OxmlElement("w:t")
    result.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, result, end])
    set_run_font(run, size=12)


def remove_header_footer_references(section) -> None:
    properties = section._sectPr
    for tag in ("w:headerReference", "w:footerReference"):
        for child in list(properties.findall(qn(tag))):
            properties.remove(child)


def configure_front_section(section) -> None:
    configure_page(section)
    remove_header_footer_references(section)
    page_number_type = section._sectPr.find(qn("w:pgNumType"))
    if page_number_type is not None:
        section._sectPr.remove(page_number_type)


def configure_body_section(section, header_text: str, restart: bool) -> None:
    configure_page(section)
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    clear_container(section.header)
    clear_container(section.footer)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run(header_text)
    set_run_font(header_run, size=9)
    add_page_field(section.footer.paragraphs[0])

    page_number_type = section._sectPr.find(qn("w:pgNumType"))
    if restart:
        if page_number_type is None:
            page_number_type = OxmlElement("w:pgNumType")
            section._sectPr.append(page_number_type)
        page_number_type.set(qn("w:start"), "1")
    elif page_number_type is not None:
        page_number_type.attrib.pop(qn("w:start"), None)


def clear_document_body(document: Document) -> None:
    body = document._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def ensure_styles(document: Document) -> None:
    for style_name in ("Part Title", "Front Heading", "Catalog Part"):
        if style_name not in document.styles:
            document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)

    normal = document.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)
    normal.font.color.rgb = BLACK

    specs = {
        "Part Title": ("宋体", 18, True),
        "Front Heading": ("宋体", 16, True),
        "Catalog Part": ("宋体", 13, True),
    }
    for style_name, (font_name, size, bold) in specs.items():
        style = document.styles[style_name]
        style.font.name = font_name
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font_name)
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.italic = False
        style.font.color.rgb = BLACK
        style.paragraph_format.keep_with_next = True


def set_update_fields(document: Document) -> None:
    settings = document.settings.element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


def add_cover(document: Document) -> None:
    for _ in range(7):
        document.add_paragraph()
    paragraph = document.add_paragraph(style="Title")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    run = paragraph.add_run("华东师范大学347\n心理学保命手册")
    set_run_font(run, "微软雅黑", 24, True)
    document.add_page_break()


def add_front_heading(document: Document, text: str, size: float = 16) -> None:
    paragraph = document.add_paragraph(style="Front Heading")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(12)
    run = paragraph.add_run(text)
    set_run_font(run, "宋体", size, True)


def add_guide(document: Document) -> None:
    add_front_heading(document, "使用说明", 18)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(6)
    set_run_font(heading.add_run("星级"), size=14, bold=True)

    lines = (
        "★★★  核心优先｜速背手册原一级；一本通与考纲中的核心内容，华东或相关真题信号强，主观题可考性和答案复用价值最高。优先完整背诵。",
        "★★  重点掌握｜同属速背手册原一级；一本通与考纲依据明确，具有稳定可考性，但真题信号或综合优先度略低于三星。完成三星后继续掌握。",
        "★  基础覆盖｜速背手册原二级；速背手册或一本通有收录且属于考纲范围，但真题信号和主观题可考性相对较弱。用于补足范围。",
    )
    for text in lines:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.35
        paragraph.paragraph_format.space_after = Pt(5)
        set_run_font(paragraph.add_run(text), size=12)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(6)
    set_run_font(heading.add_run("怎么用"), size=14, bold=True)

    for text in (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数。",
        "2. （）内是扩容项，选背；用于丰富答题角度、锦上添花，追求更高分数。如果其中是例子，可以根据题目灵活替换。",
    ):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.35
        paragraph.paragraph_format.space_after = Pt(6)
        set_run_font(paragraph.add_run(text), size=12)

    document.add_page_break()


def body_heading_paragraphs(document: Document):
    first_heading = next(paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 1")
    started = False
    for child in document._element.body:
        if child is first_heading._p:
            started = True
        if started and child.tag != qn("w:sectPr"):
            yield child


def source_chapters(document: Document) -> list[str]:
    first_heading = next(index for index, paragraph in enumerate(document.paragraphs) if paragraph.style.name == "Heading 1")
    return [
        paragraph.text.strip()
        for paragraph in document.paragraphs[first_heading:]
        if paragraph.style.name == "Heading 1" and paragraph.text.strip()
    ]


def add_catalog(
    document: Document,
    source_documents: list[Document],
    page_map: dict[str, int] | None,
) -> None:
    add_front_heading(document, "目录", 26)
    for source_spec, source_document in zip(SOURCES, source_documents, strict=True):
        part_title, _, _, _ = source_spec
        paragraph = document.add_paragraph(style="Catalog Part")
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(7)
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        part_page = str((page_map or {}).get(part_title, "000"))
        set_run_font(paragraph.add_run(f"{part_title}\t{part_page}"), size=13, bold=True)

        for chapter in source_chapters(source_document):
            key = f"{part_title}|{chapter}"
            page = str((page_map or {}).get(key, "000"))
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.left_indent = Cm(0.74)
            paragraph.paragraph_format.line_spacing = 1.05
            paragraph.paragraph_format.space_after = Pt(1)
            paragraph.paragraph_format.tab_stops.add_tab_stop(
                Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
            )
            set_run_font(paragraph.add_run(f"{chapter}\t{page}"), size=10.5)


def add_part_title(document: Document, title: str) -> None:
    paragraph = document.add_paragraph(style="Part Title")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(10)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(title)
    set_run_font(run, "宋体", 18, True)

    properties = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "5")
    bottom.set(qn("w:color"), "000000")
    borders.append(bottom)
    properties.append(borders)


def copied_body_child(child, *, strip_non_chapter_page_breaks: bool):
    copied = deepcopy(child)
    if not strip_non_chapter_page_breaks or copied.tag != qn("w:p"):
        return copied
    properties = copied.find(qn("w:pPr"))
    if properties is None:
        return copied
    style = properties.find(qn("w:pStyle"))
    style_name = style.get(qn("w:val"), "") if style is not None else ""
    if style_name in {"Heading1", "1"}:
        return copied
    for page_break in list(properties.findall(qn("w:pageBreakBefore"))):
        properties.remove(page_break)
    text = "".join(node.text or "" for node in copied.iter(qn("w:t"))).strip()
    if text in COMBINED_NON_CHAPTER_PAGE_BREAK_TEXTS:
        properties.append(OxmlElement("w:pageBreakBefore"))
    return copied


def build(output_path: Path, page_map: dict[str, int] | None = None) -> None:
    source_documents = [Document(spec[3]) for spec in SOURCES]
    document = Document(SOURCES[0][3])
    clear_document_body(document)
    ensure_styles(document)
    set_update_fields(document)
    configure_front_section(document.sections[0])

    document.core_properties.title = "华东师范大学347心理学保命手册"
    document.core_properties.subject = "心理学导论、实验心理学、心理与教育测量合订版"
    document.core_properties.author = "铁头心理学考研"

    add_cover(document)
    add_guide(document)
    add_catalog(document, source_documents, page_map)

    for index, (source_spec, source_document) in enumerate(zip(SOURCES, source_documents, strict=True)):
        part_title, _, header_text, _ = source_spec
        section = document.add_section(WD_SECTION.NEW_PAGE)
        configure_body_section(section, header_text, restart=index == 0)
        add_part_title(document, part_title)
        for child in body_heading_paragraphs(source_document):
            document._element.body.insert(
                -1,
                copied_body_child(
                    child,
                    strip_non_chapter_page_breaks=(
                        STRIP_NON_CHAPTER_PAGE_BREAKS and index == len(SOURCES) - 1
                    ),
                ),
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def compact(text: str) -> str:
    return "".join(text.split())


def extract_page_map(pdf_path: Path) -> dict[str, int]:
    import fitz

    document = fitz.open(pdf_path)
    pages = [compact(page.get_text()) for page in document]
    part_page_indexes: dict[str, int] = {}
    for part_title, _, _, _ in SOURCES:
        part_compact = compact(part_title)
        hits = [index for index, text in enumerate(pages) if part_compact in text]
        if not hits:
            raise ValueError(f"PDF 中未找到分科标题：{part_title}")
        # 总目录和正文均会出现分科标题；最后一次出现的位置才是正文起始页。
        part_page_indexes[part_title] = hits[-1]

    first_body_index = part_page_indexes[SOURCES[0][0]]
    page_map: dict[str, int] = {}
    source_documents = [Document(spec[3]) for spec in SOURCES]
    for subject_index, (source_spec, source_document) in enumerate(
        zip(SOURCES, source_documents, strict=True)
    ):
        part_title = source_spec[0]
        start = part_page_indexes[part_title]
        stop = (
            part_page_indexes[SOURCES[subject_index + 1][0]]
            if subject_index + 1 < len(SOURCES)
            else len(pages)
        )
        page_map[part_title] = start - first_body_index + 1
        cursor = start
        for chapter in source_chapters(source_document):
            needle = compact(chapter)
            found = next(index for index in range(cursor, stop) if needle in pages[index])
            page_map[f"{part_title}|{chapter}"] = found - first_body_index + 1
            cursor = found

    PAGE_MAP_OUTPUT.write_text(
        json.dumps(page_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return page_map


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--page-map", type=Path)
    parser.add_argument("--extract-page-map", type=Path)
    arguments = parser.parse_args()

    if arguments.extract_page_map:
        mapping = extract_page_map(arguments.extract_page_map)
        build(arguments.output, mapping)
        return

    mapping = None
    if arguments.page_map:
        mapping = json.loads(arguments.page_map.read_text(encoding="utf-8"))
    build(arguments.output, mapping)


if __name__ == "__main__":
    main()
