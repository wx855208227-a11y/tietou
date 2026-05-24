from pathlib import Path
import re
from copy import deepcopy
from functools import lru_cache
from zipfile import ZipFile

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from lxml import etree


BASE = Path(__file__).resolve().parent
SOURCE = BASE / "chapter-01-yibentong-v2.md"
OUTPUT = BASE / "chapter-01-yibentong-v2.docx"
SAMPLE_TIPS_DOC = Path(
    "/home/yileiyang/multi_agent/.work/workspaces/github.com/agiamason/tietou/agents/tietou_manager/"
    "inbox/feishu/om_x100b6fecc49064a0b3c66e0e3862c8f/27_1_.docx"
)
TIP_LABELS = {"**Tips**", "Tips", "**铁头tips**", "铁头tips"}


def set_east_asia_font(run, name="宋体"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def format_run(run, *, size=12, bold=False, underline=False):
    set_east_asia_font(run)
    run.font.size = Pt(size)
    run.bold = bold
    run.underline = underline


def add_inline_runs(paragraph, text, *, size=12):
    pattern = re.compile(r"(\*\*.*?\*\*|<u>.*?</u>)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            format_run(run, size=size)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            format_run(run, size=size, bold=True)
        else:
            run = paragraph.add_run(token[3:-4])
            format_run(run, size=size, underline=True)
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        format_run(run, size=size)


def setup_document(doc):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.2)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)

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


def set_paragraph_spacing(paragraph, *, before=0, after=4, line=1.5):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def set_paragraph_keep(paragraph, *, together=False, next=False):
    fmt = paragraph.paragraph_format
    fmt.keep_together = together
    fmt.keep_with_next = next


def set_paragraph_element_keep(paragraph_element, *, together=False, next=False):
    p_pr = paragraph_element.find(qn("w:pPr"))
    if p_pr is None:
        p_pr = OxmlElement("w:pPr")
        paragraph_element.insert(0, p_pr)
    if together and p_pr.find(qn("w:keepLines")) is None:
        p_pr.append(OxmlElement("w:keepLines"))
    if next and p_pr.find(qn("w:keepNext")) is None:
        p_pr.append(OxmlElement("w:keepNext"))


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = tr_pr.find(qn("w:cantSplit"))
    if cant_split is None:
        cant_split = OxmlElement("w:cantSplit")
        tr_pr.append(cant_split)


def add_body_paragraph(doc, line):
    paragraph = doc.add_paragraph()
    set_paragraph_spacing(paragraph, after=4)

    stripped = line.strip()
    is_list = bool(re.match(r"^(\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[一二三四五六七八九十]+\.)", stripped))
    is_tips = stripped in TIP_LABELS
    if is_tips:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif not is_list:
        paragraph.paragraph_format.first_line_indent = Cm(0.74)

    add_inline_runs(paragraph, stripped, size=12)
    if is_tips:
        for run in paragraph.runs:
            run.bold = True
    return paragraph


@lru_cache(maxsize=1)
def sample_tip_label_element():
    if not SAMPLE_TIPS_DOC.exists():
        return None
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(SAMPLE_TIPS_DOC) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
    for paragraph in root.xpath(".//w:p", namespaces=ns):
        text = "".join(paragraph.xpath(".//w:t/text()", namespaces=ns)).strip()
        if text == "铁头tips铁头tips":
            return paragraph
    return None


def insert_tip_label(doc):
    sample_label = sample_tip_label_element()
    if sample_label is not None:
        label = deepcopy(sample_label)
        set_paragraph_element_keep(label, together=True, next=True)
        doc._body._element.insert_element_before(label, "w:sectPr")
        return

    paragraph = doc.add_paragraph()
    set_paragraph_spacing(paragraph, before=8, after=0)
    set_paragraph_keep(paragraph, together=True, next=True)
    paragraph.paragraph_format.left_indent = Cm(-0.2)
    run = paragraph.add_run("铁头tips")
    format_run(run, size=10, bold=True)


def set_cell_shading(cell, fill="D9EAF7"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)
    shd.set(qn("w:val"), "clear")


def remove_cell_borders(cell):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "nil")


def set_cell_margins(cell, *, top=120, start=220, bottom=120, end=220):
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


def add_table_paragraph(cell, text=""):
    paragraph = cell.paragraphs[0] if not cell.paragraphs[0].text else cell.add_paragraph()
    set_paragraph_spacing(paragraph, after=4)
    set_paragraph_keep(paragraph, together=True)
    if text:
        add_inline_runs(paragraph, text, size=12)
    return paragraph


def add_image_to_container(container, line, *, width=Cm(15.2)):
    match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
    if not match:
        return
    _, image_path = match.groups()
    path = Path(image_path)
    if not path.is_absolute():
        path = BASE / path
    paragraph = container.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(paragraph, before=4, after=6, line=1.2)
    set_paragraph_keep(paragraph, together=True)
    run = paragraph.add_run()
    run.add_picture(str(path), width=width)


def add_markdown_table_to_container(container, rows, *, font_size=10):
    if not rows:
        return
    col_count = max(len(row) for row in rows)
    table = container.add_table(rows=len(rows), cols=col_count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for r_idx, row in enumerate(rows):
        prevent_row_split(table.rows[r_idx])
        for c_idx in range(col_count):
            cell = table.cell(r_idx, c_idx)
            set_cell_margins(cell, top=70, start=95, bottom=70, end=95)
            if r_idx == 0:
                set_cell_shading(cell, "EDEDED")
            text = row[c_idx] if c_idx < len(row) else ""
            paragraph = cell.paragraphs[0]
            set_paragraph_spacing(paragraph, after=2, line=1.15)
            set_paragraph_keep(paragraph, together=True)
            add_inline_runs(paragraph, text, size=font_size)
            if r_idx == 0:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True


def add_tips_block(doc, tip_lines):
    if not tip_lines:
        return
    insert_tip_label(doc)

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    prevent_row_split(table.rows[0])
    cell = table.cell(0, 0)
    set_cell_shading(cell)
    remove_cell_borders(cell)
    set_cell_margins(cell)

    title = None
    body_lines = tip_lines[:]
    first = body_lines[0]
    if first.startswith("补充内容："):
        title = first
        body_lines = body_lines[1:]
    elif not first.startswith("例如") and len(re.sub(r"[\*_<u>/]", "", first)) <= 40 and not first.endswith(("。", "；", "：")):
        title = first
        body_lines = body_lines[1:]

    if title:
        title_paragraph = add_table_paragraph(cell)
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_inline_runs(title_paragraph, title, size=12)
        for run in title_paragraph.runs:
            run.bold = True

    i = 0
    while i < len(body_lines):
        line = body_lines[i]
        if is_markdown_image(line):
            add_image_to_container(cell, line, width=Cm(15.0))
            i += 1
            continue
        if is_markdown_table_start(body_lines, i):
            rows, i = parse_markdown_table(body_lines, i)
            add_markdown_table_to_container(cell, rows, font_size=9)
            continue
        paragraph = add_table_paragraph(cell)
        paragraph.paragraph_format.first_line_indent = Cm(0.74)
        add_inline_runs(paragraph, line, size=12)
        i += 1

    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, after=6)


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
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append(cells)
    return rows, i


def add_markdown_table(doc, rows):
    if not rows:
        return
    col_count = max(len(row) for row in rows)
    table = doc.add_table(rows=len(rows), cols=col_count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for r_idx, row in enumerate(rows):
        prevent_row_split(table.rows[r_idx])
        for c_idx in range(col_count):
            cell = table.cell(r_idx, c_idx)
            remove_cell_borders(cell)
            set_cell_margins(cell, top=80, start=120, bottom=80, end=120)
            if r_idx == 0:
                set_cell_shading(cell, "D9EAF7")
            text = row[c_idx] if c_idx < len(row) else ""
            paragraph = cell.paragraphs[0]
            set_paragraph_spacing(paragraph, after=2, line=1.2)
            set_paragraph_keep(paragraph, together=True)
            add_inline_runs(paragraph, text, size=11)
            if r_idx == 0:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.bold = True
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, after=6)


def is_markdown_image(line):
    return re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", line.strip()) is not None


def add_markdown_image(doc, line):
    add_image_to_container(doc, line, width=Cm(15.8))


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
            if j >= len(lines):
                break
            next_line = lines[j].strip()
            if next_line in TIP_LABELS or next_line.startswith("#"):
                break
            i += 1
            continue
        collected.append(stripped)
        i += 1
    return collected, i


def add_heading(doc, level, text):
    paragraph = doc.add_paragraph()
    set_paragraph_spacing(paragraph, before=8 if level > 1 else 0, after=6)
    set_paragraph_keep(paragraph, together=True, next=True)
    if level == 1:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        size = 16
    elif level == 2:
        size = 14
    else:
        size = 12
    add_inline_runs(paragraph, text, size=size)
    for run in paragraph.runs:
        run.bold = True
    return paragraph


def build_docx():
    doc = Document()
    setup_document(doc)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        if not line:
            i += 1
            continue
        if line in TIP_LABELS:
            tip_lines, i = collect_tip_lines(lines, i + 1)
            add_tips_block(doc, tip_lines)
            continue
        if is_markdown_image(line):
            add_markdown_image(doc, line)
            i += 1
            continue
        if is_markdown_table_start(lines, i):
            rows, i = parse_markdown_table(lines, i)
            add_markdown_table(doc, rows)
            continue
        if line.startswith("# "):
            add_heading(doc, 1, line[2:].strip())
        elif line.startswith("## "):
            add_heading(doc, 2, line[3:].strip())
        elif line.startswith("### "):
            add_heading(doc, 3, line[4:].strip())
        else:
            add_body_paragraph(doc, line)
        i += 1

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build_docx()
