from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import re
from zipfile import ZipFile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from lxml import etree
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/ecnu-347/measurement-psychology"
DELIVER = ROOT / "deliverables/ecnu-measurement-ch1-latest"
SOURCE_V11 = BASE / "chapter-01-yibentong-v11.md"
LATEST_MD = DELIVER / "华东347测量心理学一本通_第1章_最新标准版.md"
OUTPUT_DOCX = DELIVER / "华东347测量心理学一本通_第1章_最新标准版.docx"
OUTPUT_XLSX = DELIVER / "华东347测量心理学一本通_第1章_审核表.xlsx"
FORMAT_SAMPLE = ROOT / "skills/tietou-yibentong-compilation/references/format-samples/shenda-general-psychology-yibentong-format-sample.docx"

TIP_LABELS = {"**Tips**", "Tips", "**铁头tips**", "铁头tips"}


def set_east_asia_font(run, name="宋体"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)


def format_run(run, *, size=12, bold=False, underline=False, font="宋体"):
    set_east_asia_font(run, font)
    run.font.size = Pt(size)
    if bold:
        run.bold = True
    if underline:
        run.underline = True


def set_p_shading(paragraph, fill="DAE3F3"):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = p_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        p_pr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)


def set_p_double_border(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    borders = p_pr.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        p_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        element = borders.find(qn("w:" + edge))
        if element is None:
            element = OxmlElement("w:" + edge)
            borders.append(element)
        element.set(qn("w:val"), "double")
        element.set(qn("w:color"), "000000")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")


def set_paragraph_spacing(paragraph, *, before=0, after=0, line=1.5):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def set_keep(paragraph, *, together=False, next=False):
    fmt = paragraph.paragraph_format
    fmt.keep_together = together
    fmt.keep_with_next = next


def add_inline_runs(paragraph, text, *, size=12, force_bold=False):
    pattern = re.compile(r"(\*\*.*?\*\*|<u>.*?</u>)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            format_run(run, size=size, bold=force_bold)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            format_run(run, size=size, bold=True)
        else:
            run = paragraph.add_run(token[3:-4])
            format_run(run, size=size, underline=True, bold=force_bold)
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        format_run(run, size=size, bold=force_bold)


def clean_source_text():
    text = SOURCE_V11.read_text(encoding="utf-8")
    replacements = {
        "# 第1章 心理测量和测验的历史回顾":
            "# 第1 章 心理测量和测验的历史回顾",
        "中国古代心理测量属于低频历史内容，了解教材给出的基本线索即可。":
            "中国古代心理测量主要体现为三类线索：**测量前提**、**代表思想**和**实践形式**。",
        "我国心理测量发展史属于低频历史内容，按阶段线索了解即可。":
            "我国心理测量发展可以按三个阶段把握：**1949年之前**的引入与发展、**1949年至1978年**的停止发展、**1978年以后**的恢复与重新发展。",
        "### （一）比奈和世界上第一个智力测验P11（一级）【20年真题；考纲】":
            "### （一）比奈—西蒙量表与世界上第一个智力测验P11（一级）【20年真题】【选择】",
        "### （一）智力落后儿童的分类与训练P6（三级）":
            "### （一）智力落后儿童的分类与训练P6",
        "### （二）冯特实验心理学的影响P7":
            "### （二）冯特实验心理学的影响P7（三级）",
        "### （二）团体测验的产生P11（二级)":
            "### （二）团体测验的产生P11",
        "### （二）团体测验的产生P11（二级）":
            "### （二）团体测验的产生P11",
        "补充内容：**比奈/比内译名**": "易混提示：**比奈/比内译名**",
        "本知识点核心信息：**1905年**、**比奈—西蒙量表**、<u>世界上第一个真正意义上的智力测验</u>。":
            "需要准确对应的事实是：**1905年**、**比奈—西蒙量表**、<u>世界上第一个真正意义上的智力测验</u>。",
        "真题问“1905年第一个智力测验”选它":
            "“1905年第一个智力测验”对应它",
        "隔靴搔痒地测身体特征":
            "只看身体外形这些间接线索",
        "保留四个节点：":
            "关键节点包括：",
        "这一阶段理解为：":
            "这一阶段的主要影响因素包括：",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("不展开背诵", "")
    text = text.replace("了解即可", "")
    text = text.replace("无真题支撑", "")
    text = text.replace("低频历史内容", "")
    return text


def setup_document(doc):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.75)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    h1 = doc.styles["Heading 1"]
    h1.font.name = "宋体"
    h1._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.line_spacing = 2.4
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(12)
    h1.paragraph_format.keep_with_next = True

    h2 = doc.styles["Heading 2"]
    h2.font.name = "宋体"
    h2._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    h2.font.size = Pt(14)
    h2.font.bold = True
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h2.paragraph_format.line_spacing = 1.73
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(8)
    h2.paragraph_format.keep_with_next = True

    h3 = doc.styles["Heading 3"]
    h3.font.name = "宋体"
    h3._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    h3.font.size = Pt(12)
    h3.font.bold = True
    h3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h3.paragraph_format.line_spacing = 1.72
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after = Pt(8)
    h3.paragraph_format.keep_with_next = True


def add_center_paragraph(doc, text, *, size, font="华文楷体", bold=True, before=0, after=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, before=before, after=after, line=1.0)
    run = p.add_run(text)
    format_run(run, size=size, bold=bold, font=font)
    return p


def add_cover(doc):
    add_center_paragraph(doc, "铁头心理", size=26, before=28, after=18)
    add_center_paragraph(doc, "重难点一本通", size=48, before=8, after=16)
    add_center_paragraph(doc, "（华东师范大学347应用心理专用）", size=26, before=6, after=36)
    add_center_paragraph(doc, "测量心理学", size=72, before=12, after=46)
    add_center_paragraph(doc, "参考书目：", size=26, before=10, after=8)
    add_center_paragraph(doc, "《测量心理学》（第三版）", size=26, before=0, after=70)
    add_center_paragraph(doc, "版权所有，违者必究", size=10, before=40, after=0)
    doc.add_section(WD_SECTION.NEW_PAGE)


def add_toc(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, after=16)
    run = p.add_run("目录")
    format_run(run, size=26, bold=True)

    p = doc.add_paragraph()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\u'
    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run = p.add_run()
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_separate)
    toc_entries = [
        "第1 章 心理测量和测验的历史回顾\t1",
        "一、心理测量和测验产生的背景\t1",
        "二、中国古代的心理测量思想和实践\t1",
        "三、近代心理测量的早期尝试与先驱者探索\t2",
        "四、社会需要与现代心理测验的形成\t4",
        "五、心理测量和测验在我国的发展\t6",
    ]
    for idx, entry in enumerate(toc_entries):
        if idx:
            run._r.append(OxmlElement("w:br"))
        result_text = OxmlElement("w:t")
        result_text.set(qn("xml:space"), "preserve")
        result_text.text = entry
        run._r.append(result_text)
    run._r.append(fld_end)
    format_run(run, size=11)

    set_update_fields(doc)
    doc.add_section(WD_SECTION.NEW_PAGE)


def set_update_fields(doc):
    settings = doc.settings.element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def add_page_number(section):
    section.footer.is_linked_to_previous = False
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    format_run(run, size=14)


def is_markdown_image(line):
    return re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", line.strip()) is not None


def image_path_from_line(line):
    match = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", line.strip())
    if not match:
        return None
    path = Path(match.group(1))
    return path if path.is_absolute() else BASE / path


def is_markdown_table_start(lines, index):
    if index + 1 >= len(lines):
        return False
    first = lines[index].strip()
    second = lines[index + 1].strip()
    return first.startswith("|") and first.endswith("|") and re.match(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|$", second) is not None


def parse_markdown_table(lines, start):
    table_lines = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
        table_lines.append(lines[i].strip())
        i += 1
    rows = []
    for idx, line in enumerate(table_lines):
        if idx == 1:
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows, i


@lru_cache(maxsize=1)
def sample_tip_label_element():
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(FORMAT_SAMPLE) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
    for paragraph in root.xpath(".//w:p", namespaces=ns):
        text = "".join(paragraph.xpath(".//w:t/text()", namespaces=ns)).strip()
        if text == "铁头tips铁头tips":
            return paragraph
    return None


def insert_tip_label(doc):
    sample = sample_tip_label_element()
    if sample is not None:
        label = deepcopy(sample)
        doc._body._element.insert_element_before(label, "w:sectPr")
        return
    p = doc.add_paragraph()
    run = p.add_run("铁头tips")
    format_run(run, size=10, bold=True)


def add_body_paragraph(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, after=2)
    stripped = text.strip()
    is_list = bool(re.match(r"^(\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[A-Z]\.|[a-z]\.)", stripped))
    if not is_list:
        p.paragraph_format.first_line_indent = Cm(0.74)
    add_inline_runs(p, stripped, size=12)
    return p


def add_heading(doc, level, text):
    style = f"Heading {level}"
    p = doc.add_paragraph(style=style)
    p.clear()
    add_inline_runs(p, text, size=16 if level == 1 else 14 if level == 2 else 12, force_bold=True)
    set_keep(p, together=True, next=True)
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def set_cell_margins(cell, *, top=80, start=120, bottom=80, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.find(qn("w:tcMar"))
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for name, value in {"top": top, "start": start, "bottom": bottom, "end": end}.items():
        element = margins.find(qn("w:" + name))
        if element is None:
            element = OxmlElement("w:" + name)
            margins.append(element)
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")


def set_cell_shading(cell, fill="F2F2F2"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def add_markdown_table(doc, rows, *, font_size=10, in_tip=False):
    table = doc.add_table(rows=len(rows), cols=max(len(r) for r in rows))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for r_idx, row in enumerate(rows):
        prevent_row_split(table.rows[r_idx])
        for c_idx, cell in enumerate(table.rows[r_idx].cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if r_idx == 0:
                set_cell_shading(cell, "DBE3F4" if in_tip else "EDEDED")
            elif in_tip:
                set_cell_shading(cell, "DAE3F3")
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_spacing(para, after=0, line=1.15)
            text = row[c_idx] if c_idx < len(row) else ""
            add_inline_runs(para, text, size=font_size)
            if r_idx == 0:
                for run in para.runs:
                    run.bold = True
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, after=3)


def add_tip_table_block(doc, title, rows):
    insert_tip_label(doc)
    if title:
        add_tip_paragraph(doc, title, title=True)
    add_markdown_table(doc, rows, font_size=10, in_tip=True)
    doc.add_paragraph()


def add_tip_paragraph(doc, text="", *, title=False, source=False):
    p = doc.add_paragraph()
    set_p_shading(p, "DBE3F4" if title else "DAE3F3")
    set_paragraph_spacing(p, after=0)
    if title:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_inline_runs(p, text, size=12, force_bold=True)
    elif source:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        add_inline_runs(p, text, size=12)
    else:
        p.paragraph_format.first_line_indent = Cm(0.74)
        add_inline_runs(p, text, size=12)
    return p


def add_tip_block(doc, tip_lines):
    if not tip_lines:
        return
    insert_tip_label(doc)
    first = tip_lines[0]
    body = tip_lines[:]
    title = None
    if not first.startswith("例如") and not is_markdown_image(first) and not first.startswith("|"):
        plain = re.sub(r"\*\*|<u>|</u>", "", first)
        if len(plain) <= 45 or first.startswith(("易混", "图示", "现代")):
            title = first
            body = tip_lines[1:]
    if title:
        add_tip_paragraph(doc, title, title=True)
    for line in body:
        if is_markdown_image(line):
            p = doc.add_paragraph()
            set_p_shading(p, "DAE3F3")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(str(image_path_from_line(line)), width=Cm(14.5))
            continue
        if line.startswith("|"):
            continue
        if line.startswith("【") and line.endswith("】"):
            add_tip_paragraph(doc, line, source=True)
        else:
            add_tip_paragraph(doc, line)
    doc.add_paragraph()


def add_supplement_box(doc, lines):
    for idx, line in enumerate(lines):
        p = doc.add_paragraph()
        set_p_double_border(p)
        set_paragraph_spacing(p, after=0)
        if idx == 0:
            add_inline_runs(p, line, size=12, force_bold=True)
        elif len(line) <= 24 and not line.endswith("。"):  # title line
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline_runs(p, line, size=12, force_bold=True)
        else:
            p.paragraph_format.first_line_indent = Cm(0.74)
            add_inline_runs(p, line, size=12)
    doc.add_paragraph()


def collect_tip_lines(lines, start):
    collected = []
    i = start
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped in TIP_LABELS or stripped.startswith("#"):
            break
        if not stripped:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or lines[j].strip() in TIP_LABELS or lines[j].strip().startswith("#"):
                break
            i += 1
            continue
        collected.append(stripped)
        i += 1
    return collected, i


def build_docx(markdown_text):
    doc = Document()
    setup_document(doc)
    add_cover(doc)
    add_toc(doc)
    add_page_number(doc.sections[-1])
    lines = markdown_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line in TIP_LABELS:
            tip_lines, i = collect_tip_lines(lines, i + 1)
            if tip_lines and tip_lines[0].startswith("补充内容："):
                add_supplement_box(doc, tip_lines)
            else:
                table_idx = next((idx for idx in range(len(tip_lines)) if is_markdown_table_start(tip_lines, idx)), None)
                if table_idx is not None:
                    title_lines = tip_lines[:table_idx]
                    title = title_lines[0] if title_lines else ""
                    rows, _ = parse_markdown_table(tip_lines, table_idx)
                    add_tip_table_block(doc, title, rows)
                else:
                    add_tip_block(doc, tip_lines)
            continue
        if line.startswith("# "):
            add_heading(doc, 1, line[2:].strip())
        elif line.startswith("## "):
            add_heading(doc, 2, line[3:].strip())
        elif line.startswith("### "):
            add_heading(doc, 3, line[4:].strip())
        elif is_markdown_table_start(lines, i):
            rows, i = parse_markdown_table(lines, i)
            add_markdown_table(doc, rows)
            continue
        elif is_markdown_image(line):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(image_path_from_line(line)), width=Cm(15.0))
        else:
            add_body_paragraph(doc, line)
        i += 1
    doc.save(OUTPUT_DOCX)


def build_review_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "强二级复核"
    headers = ["知识点", "位置", "当前层级", "强二级理由", "目标院校证据", "考纲证据", "可能题型", "建议", "负责人确认"]
    ws.append(headers)
    rows = [
        ["心理测量完整实践的三个前提", "P3", "二级", "属于历史章节中的一般原理线索，有独立简答/选择可能", "无直接真题", "心理测量基本原理和方法", "选择/简答", "保留二级，若后续真题强化可升一级", ""],
        ["高尔顿的贡献", "P8", "二级", "测验运动先驱，人物贡献稳定可考", "无直接真题", "心理测量和测验的历史、发展", "选择/名词解释", "保留二级偏强", ""],
        ["卡特尔及早期心理测验", "P9", "二级", "“心理测验”术语和统一程序是历史核心线索", "无直接真题", "心理测量和测验的历史、发展", "选择/名词解释", "保留二级偏强", ""],
        ["复杂心理功能测验的探索", "P10", "二级", "承接早期感觉测验不足，并直接引出比奈智力测验", "无直接真题", "智力测验的起源", "选择/简答", "保留二级偏强", ""],
        ["团体测验的产生", "P11", "二级", "与智力测验起源相邻，含陆军甲/乙种测验等稳定选择题点", "无直接真题", "智力测验的起源", "选择/简答", "保留二级偏强", ""],
    ]
    for row in rows:
        ws.append(row)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    widths = [24, 10, 10, 36, 18, 26, 16, 30, 16]
    for idx, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + idx)].width = width

    ev = wb.create_sheet("证据与自检")
    ev.append(["项目", "结论"])
    evidence_rows = [
        ["材料", "教材第1章底稿、2025华东347考纲、华东题册/真题解析抽取文本、深大普心格式母版"],
        ["题型池", "第1章直接证据为选择题；非直接题型仅用于审核表，不在成品正文乱标"],
        ["真题一级", "比奈/比内—西蒙量表：1905年第一个智力测验，题册显示为选择题"],
        ["考纲覆盖", "心理测量基本原理和方法、心理测量和测验的历史发展、智力测验的起源"],
        ["中国背景处理", "中国古代与我国发展史无直接真题，按三级压缩保留线索，不写了解即可"],
        ["过程话术检查", "已清理了解即可、无真题支撑、不展开背诵等话术"],
        ["Tips", "保留现代智力测验形成路径、比奈生活化例子、比奈/比内译名、比奈量表辨析、个别/团体测验辨析"],
        ["格式", "使用深大母版的封面/TOC字段/Heading 1-3/宋体小四/铁头tips标签/浅蓝底/表格样式"],
        ["风险", "本地无 Word/WPS 渲染能力，TOC字段和跨页需打开 Word/WPS 后最终刷新检查"],
    ]
    for row in evidence_rows:
        ev.append(row)
    for cell in ev[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
    ev.column_dimensions["A"].width = 20
    ev.column_dimensions["B"].width = 90
    for row in ev.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    wb.save(OUTPUT_XLSX)


def main():
    DELIVER.mkdir(parents=True, exist_ok=True)
    markdown = clean_source_text()
    LATEST_MD.write_text(markdown, encoding="utf-8")
    build_docx(markdown)
    build_review_xlsx()
    print(OUTPUT_DOCX)
    print(OUTPUT_XLSX)


if __name__ == "__main__":
    main()
