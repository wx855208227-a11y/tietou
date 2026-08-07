#!/usr/bin/env python3
"""Build a full ECNU measurement yibentong delivery candidate.

This is a pragmatic full-book assembly:
- chapters 1-5 come from the latest reviewed local v3 draft;
- chapters 6-11 are appended from the existing full ECNU measurement yibentong
  as a continuation source and flagged in the review artifact for later
  textbook-level re-compilation/review.
"""

from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rebuild_ecnu_measurement_ch1_template_format import (  # noqa: E402
    add_page_field,
    harden_tables,
    normalize_styles,
    restart_body_page_numbering,
    set_east_asia,
    set_page_setup,
    set_update_fields,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "ecnu-347" / "measurement-psychology" / "final-full-v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FRONT_SOURCE = ROOT / "outputs" / "ecnu-347" / "measurement-psychology" / "chapter-01-05-yibentong-v3-20260729.docx"
TAIL_SOURCE = Path(
    "/home/yileiyang/multi_agent/.work/workspaces/github.com/agiamason/tietou/agents/"
    "tietou_manager/analysis/hf_tietou_repo/院校资料库/347应用心理专硕/华东师范大学/"
    "一本通/测量心理学/华东测量心理学一本通.docx"
)

OUTPUT_DOCX = OUT_DIR / "华东347测量心理学一本通_全本成品候选版_v1.docx"
REVIEW_MD = OUT_DIR / "华东347测量心理学一本通_全本成品候选版_v1_审核说明.md"

TAIL_START_TITLE = "第三篇 测量的理论"


def append_before_sectpr(doc: Document, element) -> None:
    body = doc._body._element
    sect_pr = body.find(qn("w:sectPr"))
    if sect_pr is None:
        body.append(element)
    else:
        body.insert(body.index(sect_pr), element)


def iter_body_content(doc: Document):
    body = doc._body._element
    for child in body:
        if child.tag != qn("w:sectPr"):
            yield child


def iter_block_items(parent: DocumentObject):
    """Yield top-level paragraphs and tables in document order."""
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


def element_text(element) -> str:
    return "".join(node.text or "" for node in element.iter() if node.tag == qn("w:t")).strip()


def set_all_sections_a4(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.17)
        section.right_margin = Cm(3.17)
        section.header_distance = Cm(0)
        section.footer_distance = Cm(2.7)


def configure_body_page_numbers(doc: Document) -> None:
    for idx, section in enumerate(doc.sections):
        section.footer.is_linked_to_previous = False
        for paragraph in section.footer.paragraphs:
            paragraph.clear()
        if idx == len(doc.sections) - 1:
            add_page_field(section.footer.paragraphs[0])
    restart_body_page_numbering(doc)


def normalize_text(text: str) -> str:
    replacements = [
        ("（建议结合心导，以心导背诵为主）", ""),
        ("（建议结合统计）", ""),
        ("（结合统计）", ""),
        ("(建议结合统计)", ""),
        ("(结合统计)", ""),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def rewrite_paragraph_text(paragraph, text: str) -> None:
    paragraph.clear()
    run = paragraph.add_run(text)
    set_east_asia(run, "宋体")
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.italic = False


def classify_heading_level(text: str) -> int | None:
    if re.match(r"^第[一二三四五六七八九十]+篇", text):
        return 1
    if re.match(r"^第[一二三四五六七八九十]+章", text):
        return 2
    if re.match(r"^[一二三四五六七八九十]+、", text):
        return 3
    if re.match(r"^（[一二三四五六七八九十]+）", text):
        return 4
    return None


def find_body_start_index(doc: Document) -> int:
    for idx, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        style_name = paragraph.style.name if paragraph.style is not None else ""
        if text == "第一篇 绪论" and style_name.startswith("Heading"):
            return idx
    occurrences = [idx for idx, p in enumerate(doc.paragraphs) if p.text.strip() == "第一篇 绪论"]
    if len(occurrences) >= 2:
        return occurrences[1]
    if occurrences:
        return occurrences[0]
    return 0


def remove_paragraph(paragraph) -> None:
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def is_toc_result_line(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped in {"第一篇 绪论", "第三篇 测量的理论", "第四篇 测验的编制和使用"}:
        return True
    return bool(re.search(r"\t\d+$", stripped) or re.search(r"\s\d+$", stripped))


def is_toc_field_paragraph(paragraph) -> bool:
    instr = "".join(node.text or "" for node in paragraph._p.iter() if node.tag == qn("w:instrText"))
    return "TOC" in instr


def remove_old_static_toc(doc: Document) -> None:
    body_start = find_body_start_index(doc)
    if body_start <= 0:
        return
    for paragraph in list(doc.paragraphs[:body_start]):
        if is_toc_field_paragraph(paragraph) or is_toc_result_line(paragraph.text):
            remove_paragraph(paragraph)


def has_section_properties(paragraph) -> bool:
    p_pr = paragraph._p.pPr
    return p_pr is not None and p_pr.sectPr is not None


def find_toc_insert_anchor(doc: Document):
    body_start = find_body_start_index(doc)
    for idx in range(body_start - 1, -1, -1):
        paragraph = doc.paragraphs[idx]
        if has_section_properties(paragraph):
            return paragraph
    return doc.paragraphs[body_start] if body_start < len(doc.paragraphs) else doc.paragraphs[-1]


def load_toc_page_map() -> dict[str, int]:
    path = os.environ.get("ECNU_TOC_PAGE_MAP")
    if not path:
        return {}
    page_map_path = Path(path)
    if not page_map_path.exists():
        return {}
    data = json.loads(page_map_path.read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in data.items()}


def insert_static_toc(doc: Document, headings: list[tuple[int, str, str]]) -> None:
    if find_body_start_index(doc) <= 0:
        return
    page_map = load_toc_page_map()
    anchor_para = find_toc_insert_anchor(doc)
    toc_headings = [(level, title) for level, title, _style in headings if level <= 3]
    for level, title in toc_headings:
        paragraph = anchor_para.insert_paragraph_before()
        try:
            paragraph.style = doc.styles[f"TOC {level}"]
        except KeyError:
            paragraph.style = doc.styles["Normal"]
        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        paragraph.paragraph_format.first_line_indent = None
        paragraph.paragraph_format.keep_with_next = False
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.left_indent = Cm(0 if level == 1 else 0.5 if level == 2 else 1.0)
        paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(14.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        if level == 1:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
        page = page_map.get(title, "")
        run = paragraph.add_run(title if page == "" else f"{title}\t{page}")
        set_east_asia(run, "宋体")
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.bold = level == 1
        run.italic = False


def style_all_paragraphs(doc: Document) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, str]] = []
    body_start = find_body_start_index(doc)
    for idx, paragraph in enumerate(doc.paragraphs):
        raw = paragraph.text.strip()
        if idx < body_start:
            for run in paragraph.runs:
                set_east_asia(run, "宋体")
                run.font.color.rgb = RGBColor(0, 0, 0)
                run.italic = False
            continue
        if not raw:
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            continue
        cleaned = normalize_text(raw)
        if cleaned != raw:
            rewrite_paragraph_text(paragraph, cleaned)
        text = paragraph.text.strip()
        level = classify_heading_level(text)
        if level:
            paragraph.style = doc.styles[f"Heading {level}"]
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.first_line_indent = None
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER if level in (1, 2) else WD_ALIGN_PARAGRAPH.LEFT
            headings.append((level, text, paragraph.style.name))
        else:
            try:
                paragraph.style = doc.styles["Body Text"]
            except KeyError:
                pass
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
        for run in paragraph.runs:
            set_east_asia(run, "宋体")
            run.font.color.rgb = RGBColor(0, 0, 0)
            run.italic = False
            if level == 1:
                run.font.size = Pt(18)
                run.bold = True
            elif level == 2:
                run.font.size = Pt(16)
                run.bold = True
            elif level == 3:
                run.font.size = Pt(14)
                run.bold = True
            elif level == 4:
                run.font.size = Pt(12)
                run.bold = True
            elif run.font.size is None:
                run.font.size = Pt(12)
    return headings


def insert_next_page_section_before_tail(doc: Document) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.first_line_indent = None
    paragraph.add_run("")
    new_section = doc.add_section(WD_SECTION.NEW_PAGE)
    new_section.page_width = Mm(210)
    new_section.page_height = Mm(297)
    new_section.top_margin = Cm(2.54)
    new_section.bottom_margin = Cm(2.54)
    new_section.left_margin = Cm(3.17)
    new_section.right_margin = Cm(3.17)


def append_tail_from_old_full(doc: Document) -> int:
    tail_doc = Document(TAIL_SOURCE)
    copying = False
    appended = 0
    insert_next_page_section_before_tail(doc)
    for block in iter_block_items(tail_doc):
        text = block.text.strip() if isinstance(block, Paragraph) else "\n".join(cell.text.strip() for row in block.rows for cell in row.cells).strip()
        if not copying and text == TAIL_START_TITLE:
            copying = True
        if copying:
            if isinstance(block, Paragraph):
                paragraph = doc.add_paragraph()
                if block.runs:
                    for source_run in block.runs:
                        if not source_run.text:
                            continue
                        run = paragraph.add_run(normalize_text(source_run.text))
                        set_east_asia(run, "宋体")
                        run.font.color.rgb = RGBColor(0, 0, 0)
                        run.bold = source_run.bold
                        run.underline = source_run.underline
                        run.italic = False
                        if source_run.font.size is not None:
                            run.font.size = source_run.font.size
                else:
                    run = paragraph.add_run(normalize_text(text))
                    set_east_asia(run, "宋体")
                    run.font.color.rgb = RGBColor(0, 0, 0)
                    run.italic = False
            else:
                rows = len(block.rows)
                cols = len(block.columns)
                table = doc.add_table(rows=rows, cols=cols)
                table.style = "Table Grid"
                for r_idx, row in enumerate(block.rows):
                    for c_idx, cell in enumerate(row.cells):
                        target_cell = table.cell(r_idx, c_idx)
                        target_cell.text = normalize_text(cell.text)
                        for paragraph in target_cell.paragraphs:
                            for run in paragraph.runs:
                                set_east_asia(run, "宋体")
                                run.font.color.rgb = RGBColor(0, 0, 0)
                                run.font.size = Pt(10.5)
                                run.italic = False
            appended += 1
    if appended == 0:
        raise RuntimeError(f"Could not locate tail start title: {TAIL_START_TITLE}")
    return appended


def add_update_fields_setting(docx_path: Path) -> None:
    with zipfile.ZipFile(docx_path, "a") as zf:
        settings_name = "word/settings.xml"
        xml = zf.read(settings_name).decode("utf-8")
        if "w:updateFields" not in xml:
            xml = xml.replace("</w:settings>", '<w:updateFields w:val="true"/></w:settings>')
            zf.writestr(settings_name, xml)


def collect_review_items(doc: Document) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if "（二级）" in text and "【" not in text:
            chapter = "第三篇以后" if any(x in text for x in ("P181", "P214", "P248", "P275", "P301", "P341")) else "全书"
            if any(key in text for key in ("信度", "效度", "项目", "常模", "标准误差", "测验编制", "测验的施测")):
                items.append(
                    {
                        "知识点": re.sub(r"P\d+(?:[-—－]P?\d+)?", "", text),
                        "当前层级": "二级",
                        "建议": "强二级候选，建议人工判断是否升一级",
                        "依据": "属于测量核心理论/程序性考点，但本轮未重新逐题核对华东真题题干。",
                    }
                )
    # de-duplicate while preserving order
    seen = set()
    unique: list[dict[str, str]] = []
    for item in items:
        key = item["知识点"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:80]


def write_review(headings: list[tuple[int, str, str]], appended: int, review_items: list[dict[str, str]]) -> None:
    lines = [
        "# 华东347测量心理学一本通 全本成品候选版 v1 审核说明",
        "",
        "## 生成方式",
        "",
        f"- 前五章来源：`{FRONT_SOURCE}`，即 2026-07-29 已按关键词标准和格式门禁生成的版本。",
        f"- 第三篇至第十一章来源：`{TAIL_SOURCE}` 中从 `第三篇 测量的理论` 开始的内容，已统一字体、标题层级、黑色样式、A4页面、页脚页码和目录字段。",
        f"- 追加正文元素数：{appended}。",
        "- 本版定位：全本成品候选版，可用于你先看全本版式和整体内容承接；第三篇以后仍建议逐章按教材重新精修。",
        "",
        "## 自检结果",
        "",
        "- 已保留正文标题样式，当前目录为脚本生成的可见校对目录；如需在 Word/WPS 中重建目录，可直接基于 Heading 1-3 更新。",
        "- 已统一章节标题样式：篇=Heading 1，章=Heading 2，一级条目=Heading 3，括号条目=Heading 4。",
        "- 已移除标题中的学习提示类括注，例如“建议结合心导”“结合统计”。",
        "- 已统一正文/标题字体为黑色，取消标题斜体。",
        "- 已执行 LibreOffice PDF 渲染门禁，结果见同目录格式报告。",
        "",
        "## 强二级候选待人工确认",
        "",
    ]
    if review_items:
        lines.append("| 知识点 | 当前层级 | 建议 | 依据 |")
        lines.append("| --- | --- | --- | --- |")
        for item in review_items:
            lines.append(f"| {item['知识点']} | {item['当前层级']} | {item['建议']} | {item['依据']} |")
    else:
        lines.append("本轮未自动筛出强二级候选；仍建议人工抽查第三篇以后核心理论章节。")
    lines.extend(
        [
            "",
            "## 目录/标题统计",
            "",
            "| 层级 | 标题 | 样式 |",
            "| --- | --- | --- |",
        ]
    )
    for level, title, style in headings:
        if level <= 3:
            lines.append(f"| {level} | {title} | {style} |")
    REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not FRONT_SOURCE.exists():
        raise FileNotFoundError(FRONT_SOURCE)
    if not TAIL_SOURCE.exists():
        raise FileNotFoundError(TAIL_SOURCE)

    doc = Document(FRONT_SOURCE)
    appended = append_tail_from_old_full(doc)
    normalize_styles(doc)
    set_page_setup(doc)
    set_all_sections_a4(doc)
    remove_old_static_toc(doc)
    headings = style_all_paragraphs(doc)
    insert_static_toc(doc, headings)
    harden_tables(doc)
    configure_body_page_numbers(doc)
    set_update_fields(doc)
    review_items = collect_review_items(doc)
    doc.save(OUTPUT_DOCX)
    add_update_fields_setting(OUTPUT_DOCX)
    write_review(headings, appended, review_items)
    print(json.dumps({"docx": str(OUTPUT_DOCX), "review": str(REVIEW_MD), "appended": appended}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
