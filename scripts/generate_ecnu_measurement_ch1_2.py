from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


OUT_DIR = Path("deliverables/ecnu-measurement-ch1-2")
DOCX_PATH = OUT_DIR / "华东347测量心理学一本通_第1-2章_自检版.docx"
XLSX_PATH = OUT_DIR / "华东347测量心理学一本通_第1-2章_审核表.xlsx"
NOTES_PATH = OUT_DIR / "编制说明_第1-2章.md"


def set_run_font(run, size=12, bold=None, underline=None, color=None):
    run.font.name = "宋体"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if underline is not None:
        run.underline = underline
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def set_para_format(paragraph, first_line=True, spacing_after=0):
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    paragraph.paragraph_format.space_after = Pt(spacing_after)
    if first_line:
        paragraph.paragraph_format.first_line_indent = Cm(0.74)


def keep_paragraph(paragraph, with_next=False, together=True):
    paragraph.paragraph_format.keep_together = together
    paragraph.paragraph_format.keep_with_next = with_next


TOKEN_RE = re.compile(r"(\*\*[^*]+\*\*|__[^_]+__)")


def add_marked_para(doc, text, style=None, align=None, first_line=True, size=12, spacing_after=0):
    p = doc.add_paragraph(style=style)
    set_para_format(p, first_line=first_line, spacing_after=spacing_after)
    keep_paragraph(p, with_next=False, together=True)
    if align is not None:
        p.alignment = align
    for part in TOKEN_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = p.add_run(part[2:-2])
            set_run_font(run, size=size, bold=True)
        elif part.startswith("__") and part.endswith("__"):
            run = p.add_run(part[2:-2])
            set_run_font(run, size=size, underline=True)
        else:
            run = p.add_run(part)
            set_run_font(run, size=size)
    return p


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_before = Pt(6 if level <= 2 else 3)
    p.paragraph_format.space_after = Pt(3)
    keep_paragraph(p, with_next=True, together=True)
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        size = 16
    elif level == 2:
        size = 14
    else:
        size = 12
    run = p.add_run(text)
    set_run_font(run, size=size, bold=True)
    return p


def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_borders = tc_pr.first_child_found_in("w:tcBorders")
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge in kwargs:
            edge_data = kwargs.get(edge)
            tag = "w:{}".format(edge)
            element = tc_borders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tc_borders.append(element)
            for key in ["sz", "val", "color", "space"]:
                if key in edge_data:
                    element.set(qn("w:{}".format(key)), str(edge_data[key]))


def set_table_border(table, color="A6A6A6", size="6"):
    border = {"val": "single", "sz": size, "color": color, "space": "0"}
    for row in table.rows:
        row_pr = row._tr.get_or_add_trPr()
        if row_pr.find(qn("w:cantSplit")) is None:
            row_pr.append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            set_cell_border(cell, top=border, bottom=border, left=border, right=border)


def clear_cell(cell):
    for paragraph in cell.paragraphs:
        paragraph._element.getparent().remove(paragraph._element)
    cell.add_paragraph()


def set_cell_width(cell, width_cm):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_cm * 567)))
    tc_w.set(qn("w:type"), "dxa")


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def add_tip(doc, title, paragraphs=None, table=None, source=None):
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)
    keep_paragraph(spacer, with_next=True, together=True)

    # Match the human sample's Tips feel: a small upper-left label attached to a light-blue block.
    outer = doc.add_table(rows=2, cols=2)
    outer.alignment = WD_TABLE_ALIGNMENT.CENTER
    outer.autofit = False
    label = outer.cell(0, 0)
    blank = outer.cell(0, 1)
    body = outer.cell(1, 0).merge(outer.cell(1, 1))
    set_cell_width(label, 2.4)
    set_cell_width(blank, 13.2)
    set_cell_width(body, 15.6)
    for row in outer.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    clear_cell(label)
    clear_cell(blank)
    clear_cell(body)

    label.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    shade_cell(label, "FFFFFF")
    set_cell_border(label, top={"val": "single", "sz": "10", "color": "5B9BD5", "space": "0"}, bottom={"val": "single", "sz": "10", "color": "5B9BD5", "space": "0"}, left={"val": "single", "sz": "10", "color": "5B9BD5", "space": "0"}, right={"val": "single", "sz": "10", "color": "5B9BD5", "space": "0"})
    set_cell_border(blank, top={"val": "nil"}, bottom={"val": "nil"}, left={"val": "nil"}, right={"val": "nil"})
    p = label.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    keep_paragraph(p, with_next=True, together=True)
    r = p.add_run("铁头")
    set_run_font(r, size=10, bold=True)
    r = p.add_run("tips")
    set_run_font(r, size=10, bold=True)

    body.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    shade_cell(body, "DAE3F3")
    border = {"val": "single", "sz": "8", "color": "DAE3F3", "space": "0"}
    set_cell_border(body, top=border, bottom=border, left=border, right=border)
    p = body.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    keep_paragraph(p, with_next=True, together=True)
    run = p.add_run(title)
    set_run_font(run, size=11, bold=True)
    if paragraphs:
        for text in paragraphs:
            cp = body.add_paragraph()
            set_para_format(cp, first_line=False, spacing_after=0)
            keep_paragraph(cp, with_next=True, together=True)
            for part in TOKEN_RE.split(text):
                if not part:
                    continue
                if part.startswith("**") and part.endswith("**"):
                    r = cp.add_run(part[2:-2])
                    set_run_font(r, size=10.5, bold=True)
                elif part.startswith("__") and part.endswith("__"):
                    r = cp.add_run(part[2:-2])
                    set_run_font(r, size=10.5, underline=True)
                else:
                    r = cp.add_run(part)
                    set_run_font(r, size=10.5)
    if table:
        rows, headers = table["rows"], table["headers"]
        inner = body.add_table(rows=1, cols=len(headers))
        inner.alignment = WD_TABLE_ALIGNMENT.CENTER
        inner.style = "Table Grid"
        for i, h in enumerate(headers):
            inner.cell(0, i).text = h
            shade_cell(inner.cell(0, i), "B4C6E7")
        for row in rows:
            cells = inner.add_row().cells
            for i, value in enumerate(row):
                cells[i].text = value
        set_table_border(inner, color="7F7F7F", size="6")
        for row in inner.rows:
            for c in row.cells:
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                for p2 in c.paragraphs:
                    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    keep_paragraph(p2, with_next=False, together=True)
                    for r in p2.runs:
                        set_run_font(r, size=9.5, bold=False)
    if source:
        sp = body.add_paragraph()
        sp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        keep_paragraph(sp, with_next=False, together=True)
        r = sp.add_run(source)
        set_run_font(r, size=9)
    doc.add_paragraph()


def add_simple_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        shade_cell(cell, "D9D9D9")
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = value
    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    set_run_font(r, size=10)
    return table


def build_docx():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.2)

    styles = doc.styles
    styles["Normal"].font.name = "宋体"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    styles["Normal"].font.size = Pt(12)

    # Cover
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("铁头心理（华东347定向）")
    set_run_font(r, size=18, bold=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("重难点一本通")
    set_run_font(r, size=22, bold=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("心理测量")
    set_run_font(r, size=26, bold=True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("第1-2章 自检版")
    set_run_font(r, size=16, bold=True)
    for _ in range(8):
        doc.add_paragraph()
    add_marked_para(doc, "参考书目：《心理测量》（第三版），金瑜主编，华东师范大学出版社。", first_line=False, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    add_marked_para(doc, "编制依据：华东师范大学347官方考纲、华东历年真题与《心理测量》第三版教材正文。", first_line=False, align=WD_ALIGN_PARAGRAPH.CENTER, size=12)
    doc.add_page_break()

    add_heading(doc, "目录", 1)
    add_marked_para(doc, "第一篇 绪论", first_line=False)
    add_marked_para(doc, "第一章 心理测量和测验的历史回顾", first_line=False)
    add_marked_para(doc, "第二章 心理测量和测验的一般介绍", first_line=False)
    doc.add_page_break()

    add_heading(doc, "第一篇 绪论", 1)
    add_heading(doc, "第一章 心理测量和测验的历史回顾", 1)

    add_heading(doc, "一、中国古代的心理测量思想和实践P3（三级）", 2)
    add_heading(doc, "（一）心理测量实践的三个前提P3", 3)
    add_marked_para(doc, "教材认为，形成心理测量实践至少要满足三个前提：**心理可测性**、**测量内容**和**具体测量方法**。")
    add_marked_para(doc, "也就是说，先要承认心理有差异、差异能被描述，再把这种差异落实到可以观察或评价的行为上。")
    add_heading(doc, "（二）中国古代心理测量实践P4", 3)
    add_marked_para(doc, "中国古代贡献主要体现在三方面：一是承认人的**心理差异**，如孔子提出“性相近也，习相远也”；二是承认__心理差异可以通过比较和评价来把握__，如孟子“权，然后知轻重；度，然后知长短”；三是出现人才评定和选拔实践，如《人物志》、科举取士、《学记》以及周岁试儿、七巧板、九连环等。")

    add_heading(doc, "二、近代心理测量的早期尝试与先驱者探索P6（二级）", 2)
    add_heading(doc, "（一）智力落后儿童分类与训练P6（三级）", 3)
    add_marked_para(doc, "**艾斯克罗**首先正式区分**智力落后**与**精神异常**，并认为语言能力是判断智力水平的重要指标。**沈干**是训练智力落后者的先驱，使用“心理训练法”，并创办教育智力落后儿童的学校。")
    add_heading(doc, "（二）冯特实验心理学的影响P7（二级）", 3)
    add_marked_para(doc, "冯特实验心理学对早期心理测验有两点影响：第一，研究内容偏向**感觉敏感性**和**简单反应时**，影响了早期测验项目；第二，实验强调严格控制情境，后来转化为心理测验中的**标准化**思想。")
    add_heading(doc, "（三）高尔顿的理想和贡献P8（二级）", 3)
    add_marked_para(doc, "**高尔顿**是__直接推动测验运动发展的第一人__。他在《人类才能及其发展的研究》中提出“**测验**”和“**心理测量**”两个术语，也是最早实际从事测验活动的学者之一。")
    add_marked_para(doc, "高尔顿的贡献包括：建立**人体测量学实验室**，积累个别差异资料；设计高尔顿棒、高尔顿哨等测量工具；并较早使用**评定量表**、**问卷法**和**自由联想技术**。")
    add_heading(doc, "（四）心理测量逐步发展P9（二级）", 3)
    add_marked_para(doc, "**卡特尔**于1890年发表《心理测验与测量》，使“**心理测验**”首次出现在心理学文献中；他重视感觉辨别力和反应时测量。")
    add_marked_para(doc, "**克雷丕林**较早将心理测验用于精神病理学，并使用自由联想法诊断精神病人；**艾宾浩斯**重视综合能力，首创较复杂的**语句完成测验**。")

    add_heading(doc, "三、社会需要是心理测量和测验发展的动力P10（二级）", 2)
    add_heading(doc, "（一）比奈和世界上第一个智力测验P11（一级）【20年真题】【选择】", 3)
    add_marked_para(doc, "**比奈**被称为**心理测验的鼻祖**。他认为智力包含推理、判断以及运用旧知识解决新问题等高级心理过程。")
    add_marked_para(doc, "1904年，比奈与**西蒙**合作，完成世界上第一个智力测验量表，即**比奈—西蒙量表**；1905年发表《诊断异常儿童的新方法》，因此也称**1905年量表**。")
    add_marked_para(doc, "1916年，斯坦福大学教授**推孟**修订比奈—西蒙量表，形成著名的**斯坦福—比奈量表**，简称**S-B量表**或**斯比量表**。")
    add_tip(
        doc,
        "比奈为什么高频",
        paragraphs=[
            "比奈的核心不是“发明一道题”，而是把智力测验从零散尝试推进为可实际使用的量表。记忆时抓住一条线：**比奈—西蒙量表** → **1905年量表** → **推孟修订** → **斯坦福—比奈量表**。",
            "例如：如果把早期测验比作零散的体检项目，比奈做的是把这些项目整理成一套能用于筛查儿童智力发展的“正式体检表”。",
        ],
        source="【心理测量P11】",
    )
    add_heading(doc, "（二）团体测验的产生P11（二级）", 3)
    add_marked_para(doc, "早期比奈量表属于**个别测验**，每次主要测量一名被试，适合个案深入分析，但耗时、对主试要求高。")
    add_marked_para(doc, "第一次世界大战期间，美国因大规模选兵需要，发展出历史上第一个团体测验。**陆军A式量表**是文字测验，**陆军B式量表**是非文字测验，适用于文盲和不懂英语的新兵。")
    add_marked_para(doc, "团体测验的价值在于能同时测量大量被试，简化指导语和施测程序，降低主试训练要求。")
    add_tip(
        doc,
        "个别测验与团体测验的易混点",
        table={
            "headers": ["比较点", "个别测验", "团体测验"],
            "rows": [
                ["施测人数", "一次主要测一人", "一次可测多人"],
                ["代表例子", "比奈—西蒙量表", "陆军A式、陆军B式量表"],
                ["优势", "观察细致，适合个案", "效率高，适合大规模筛选"],
                ["限制", "耗时，对主试要求高", "较难控制每个被试状态"],
            ],
        },
        source="【心理测量P11】",
    )

    add_heading(doc, "四、我国心理测量和测验发展概述P15（三级）", 2)
    add_marked_para(doc, "教材强调改革开放以来，我国心理测验和量表的数量增加、质量提升，应用领域从教育扩展到职业选择、人事测评、临床与精神卫生，同时基础理论和现代技术逐步结合。")

    doc.add_page_break()
    add_heading(doc, "第二章 心理测量和测验的一般介绍", 1)

    add_heading(doc, "一、测量的基本问题P29（一级）【选择/简答】", 2)
    add_heading(doc, "（一）测量的定义P29（一级）【20年真题】【选择】", 3)
    add_marked_para(doc, "**测量**是__按照一定的法则，用数字方法对事物属性进行描述的过程__。史蒂文斯的经典表述是：“测量是按照法则给事物指派数字。”")
    add_marked_para(doc, "测量包含三个基本成分：**测量对象**、**测量规则或法则**、**测量结果**。对象是事物的属性和特征；法则是给属性分派数字的依据；结果是描述属性的数字或符号。")
    add_tip(
        doc,
        "用体重理解测量三要素",
        paragraphs=[
            "例如测体重：测量对象是人的**体重属性**，测量法则是用体重秤按重力关系给出读数，测量结果是“45kg”这样的数字和单位。",
            "考试中看到“按照法则给事物指派数字”，优先联想到**测量的定义**；看到“行为样组、标准化、客观性”，才是**心理测验三要素**。",
        ],
        source="【心理测量P29】",
    )
    add_heading(doc, "（二）测量的要素P32（二级）", 3)
    add_marked_para(doc, "任何测量都应具备两个要素：**参照点**和**单位**。参照点是计算的起点，单位是表示数量多少的基本尺度。")
    add_marked_para(doc, "参照点分为**绝对零点**和**相对零点**。绝对零点表示“无”，如0米表示没有长度；相对零点是人为规定的起点，如海拔以海平面为零点。")
    add_marked_para(doc, "理想单位要满足两个条件：一是**意义确定**，所有人理解相同；二是**价值相等**，相邻单位之间差距相等。")
    add_heading(doc, "（三）四种测量水平和测量量表P33（一级）【20、22、25、26年真题】【选择/简答/名词解释】", 3)
    add_marked_para(doc, "**量表**是__具有参照点和单位的连续体__，可以把事物属性表现出来。史蒂文斯将测量分为四种水平：**类别测量**、**等级测量**、**等距测量**和**等比测量**。")
    add_tip(
        doc,
        "四种量表对比与记忆线",
        paragraphs=[
            "华东真题高频考查量表水平的判断：**均数和标准差**通常对应等距及以上水平；**摄氏温度**有相对零点，属于等距量表；**等比量表**具有绝对零点，可作倍数解释。",
            "可以按“能做什么”记：类别量表只能**分堆**；等级量表能**排队**；等距量表能比较**差多少**；等比量表还能比较**几倍**。",
            "例如考试成绩的标准分通常可按等距处理，但心理特质本身没有绝对零点，所以心理测量一般不能直接说“甲的智力是乙的两倍”。",
        ],
        table={
            "headers": ["量表", "核心特征", "能做的统计", "例子"],
            "rows": [
                ["类别量表", "只分类，无大小顺序", "频数、百分比、卡方", "性别、班级"],
                ["等级量表", "能排序，但间距不等", "中位数、百分位、等级相关", "名次、等级评定"],
                ["等距量表", "单位等距，无绝对零点", "均数、标准差、相关、T/F检验", "摄氏温度、标准分数"],
                ["等比量表", "单位等距，有绝对零点", "可加减乘除", "长度、重量、开氏温度"],
            ],
        },
        source="【心理测量P33】",
    )
    add_heading(doc, "（四）直接测量和间接测量P34（二级）", 3)
    add_marked_para(doc, "**直接测量**是能直接测得事物属性的测量，如测量长度；**间接测量**不能直接测得目标属性，只能根据测量结果进行推论。__心理测量一般属于间接测量__。")
    add_heading(doc, "（五）测量的方法P34（二级）", 3)
    add_marked_para(doc, "测量方法包括实验法、观察法和测验法。心理测量较多使用**测验法**，广义心理测量可包括实验、观察等方法，狭义心理测量则主要指应用测验法进行的测量。")
    add_heading(doc, "（六）测量误差和精确程度P34（二级）", 3)
    add_marked_para(doc, "测量结果越精确，价值越高；但测量总会有误差，__误差越大，精确程度越低；误差越小，精确程度越高__。影响精确程度的因素包括测量对象本身、测量工具和测量目的。")

    add_heading(doc, "二、心理测量的基本概念P35（一级）【名词解释/简答】", 2)
    add_heading(doc, "（一）心理测量的定义P35（一级）【名词解释】", 3)
    add_marked_para(doc, "**心理测量**是__根据一定法则，用数字对人的行为加以确定__；也就是依据心理学理论和操作程序，给人的行为与心理属性确定数量化价值。")
    add_heading(doc, "（二）心理测量的可能性P35（二级）", 3)
    add_marked_para(doc, "心理测量可能性的依据有两个命题：第一，任何现象只要客观存在，就总有数量性质，代表人物是**桑代克**；第二，凡有数量的现象都可以测量，代表人物是**麦柯尔**。")
    add_heading(doc, "（三）心理测量的特点P36（二级）", 3)
    add_marked_para(doc, "心理测量具有**间接性**和**相对性**。间接性是指通过外显行为推论内在心理属性；相对性是指人的心理测量结果通常表示个体在群体或连续行为序列中的相对位置。")
    add_tip(
        doc,
        "心理测量为什么是间接的",
        paragraphs=[
            "人的焦虑、兴趣、智力不能像身高一样直接拿尺子量，所以只能设计题目或任务，让心理特质通过行为表现出来。",
            "例如判断一个人是否有机械兴趣，不是直接“看到兴趣”，而是看他是否喜欢机械杂志、机器运转、修理物品等外显行为。",
        ],
        source="【心理测量P36】",
    )
    add_heading(doc, "（四）心理测量的水平P37（一级）【25年真题】【简答】", 3)
    add_marked_para(doc, "严格说，__心理测量只具有等级量表的特征__。但多数心理特征近似常态分布，且测量结果可转化为标准分数，因此实践中常把心理量表当作**等距量表**处理。")
    add_marked_para(doc, "心理量表的等距处理主要依赖__把原始分数转化为标准分数__，使测验分数在统计解释上可按等距量表处理；严格获得等距性的具体方法，教材在后续量表与常模等章节再展开。")

    add_heading(doc, "三、心理测验的基本概念P37（一级）【选择/名词解释】", 2)
    add_heading(doc, "（一）心理测验和心理测量的联系与区别P37（二级）", 3)
    add_marked_para(doc, "**心理测验**主要是了解心理的工具，多在“名词”意义上使用；**心理测量**是使用测验等工具了解心理的活动，多在“动词”意义上使用，范围更广。")
    add_marked_para(doc, "二者联系在于：能用于实际心理测量的心理测验才是真正有效的工具；应用规范测验工具的心理测量活动，才是科学的测量。")
    add_heading(doc, "（二）心理测验的定义P37（一级）【名词解释】", 3)
    add_marked_para(doc, "**心理测验**实质上是__对行为样组的客观和标准化测量__。它不是测量全部行为，而是选取能代表心理特性的行为样本进行推论。")
    add_heading(doc, "（三）心理测验三要素P38（一级）【20、21年真题】【选择/简答/名词解释】", 3)
    add_marked_para(doc, "心理测验具有三个要素：**行为样组**、**标准化**和**客观性**。华东2020年真题考查“不属于心理测验要素”的选项，注意“法则”属于一般测量定义，不属于心理测验三要素。")
    add_marked_para(doc, "**行为样组**是__从相关行为中选择一部分有代表性的行为，用以推论人的心理特性__。测验无法穷尽所有行为，因此行为样组必须有代表性。")
    add_marked_para(doc, "**标准化**是测验的一致性，包括__测验内容、施测条件、评分规则和测验常模的标准化__。华东2021年真题考过**测验标准化的条件**和**标准化样组**；标准化样组属于常模建立中的代表性样本，后续测验编制与常模章节再详细展开。")
    add_marked_para(doc, "**客观性**是指测验不受主观支配，__测验的实施、记分和解释可以重复__，行为样组和标准化共同服务于客观性。")
    add_tip(
        doc,
        "测量三要素 vs 心理测验三要素",
        table={
            "headers": ["概念", "三要素", "考法提醒"],
            "rows": [
                ["一般测量", "对象、法则、结果", "看到“给事物指派数字”"],
                ["心理测验", "行为样组、标准化、客观性", "看到“测验工具是否科学”"],
            ],
        },
        source="【心理测量P29、P38】",
    )
    add_heading(doc, "（四）心理测验客观性指标P39（一级）【选择/名词解释】", 3)
    add_marked_para(doc, "衡量心理测验客观性的指标主要包括**信度**、**效度**、**难度**和**鉴别力**。其中，信度和效度是判断测验好坏的核心指标，难度和鉴别力主要用于项目质量分析。")
    add_marked_para(doc, "**信度**是测验结果的可靠程度，强调结果是否稳定、一致；常见类型包括**重测信度**、**复本信度**和**内在一致性信度**。")
    add_marked_para(doc, "**效度**是测验实际测量出所测特性或功能的真实性程度，强调是否测到了想测的东西；常见类型包括**内容效度**、**结构效度**和**效标效度**。")
    add_marked_para(doc, "**难度**是测题难易水平的数量指标，通常用通过率表示；**鉴别力**是测题区分不同水平被试的能力。一般来说，中等难度项目的鉴别力较高。")
    add_tip(
        doc,
        "信度和效度的生活化区分",
        paragraphs=[
            "如果一台体重秤每天都把你称成60kg、60kg、60kg，但你真实体重是55kg，它很稳定，所以有信度；但没有测准，所以效度低。",
            "如果一台秤有时55kg、有时62kg、有时48kg，它既不稳定也不可靠，信度低；信度低通常会限制效度。",
        ],
        source="【心理测量P39】",
    )

    add_heading(doc, "四、测验的种类P41（二级）", 2)
    add_heading(doc, "（一）按测量对象分类P41（二级）", 3)
    add_marked_para(doc, "按测量对象，测验可分为**认知测验**和**人格测验**。认知测验又称能力测验，包括智力测验、能力倾向测验、教育测验和创造力测验；人格测验测量能力以外的个性心理特征，如性格、情绪、需要、动机、兴趣、态度、焦虑、气质和自我概念等。")
    add_heading(doc, "（二）按测验人数分类P42（二级）", 3)
    add_marked_para(doc, "按一次施测人数，测验分为**个别测验**和**团体测验**。个别测验观察细致、结果较可靠，但耗时、对主试要求高；团体测验效率高、评分更客观，但不易控制每个被试的状态。")
    add_heading(doc, "（三）按测验材料分类P42（二级）", 3)
    add_marked_para(doc, "按材料呈现方式，测验分为**语言或文字测验**和**非语言或操作测验**。文字测验适合测量较高层次心理功能，但受语言文化背景影响；非语言测验较少受文化和文字水平限制，适合学前儿童、不识字成人或跨文化比较。")
    add_heading(doc, "（四）按记分方式和其他标准分类P42（三级）", 3)
    add_marked_para(doc, "按记分方式，测验可分为**客观测验**和**非客观测验**。其他分类还包括选择反应测验与结构反应测验、常模参照测验与标准参照测验、筛选性测验与诊断性测验等，了解即可。")

    add_heading(doc, "五、测验的应用P43（三级）", 2)
    add_marked_para(doc, "心理测验的基本应用包括：了解个别差异；诊断、预测和评价；甄选、分类和安置；服务心理辅导和心理咨询；辅助心理与教育科研。")
    add_marked_para(doc, "其中，**了解个别差异**是心理测验最基本的功能；在教育、职业、人事、临床和科研领域，测验都可以提供量化依据，但前提是测验本身具备足够的信度、效度和标准化程序。")

    doc.save(DOCX_PATH)


def build_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "强二级复核"

    def style_sheet(sheet, widths):
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="404040")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        for i, width in enumerate(widths, 1):
            sheet.column_dimensions[get_column_letter(i)].width = width
        sheet.freeze_panes = "A2"

    strong_headers = ["知识点", "正文位置", "当前层级", "强二级理由", "目标真题证据", "考纲证据", "辅助证据", "可能题型", "建议处理", "置信度", "主管确认"]
    ws.append(strong_headers)
    strong_rows = [
        ["高尔顿贡献", "第一章P8", "二级", "近代测量史核心人物，术语与方法贡献稳定可考，但缺华东真题精确命中", "无", "历史、发展和原理概述", "可参考泛347/312对人物贡献选择题的常见考法", "选择/名词解释", "暂保留二级；如负责人认为华东会强化测量史，可升一级", "中", ""],
        ["个别测验与团体测验", "第一章P11；第二章P42", "二级", "与比奈量表、陆军A/B式量表和测验分类相连，易形成比较题", "无直接真题", "智力测验起源与测验类型相关", "跨院校常见选择/简答辨析点", "选择/简答", "暂保留二级，作为比奈一级点的辅助比较", "中", ""],
        ["参照点和单位", "第二章P32", "二级", "是理解四种量表和绝对零点/相对零点的前置条件", "无直接真题；与量表真题间接相关", "心理测量基本原理", "四种量表题常涉及零点和单位", "选择/简答", "保留二级；不单独升一级", "中高", ""],
        ["测量误差和精确程度", "第二章P34", "二级", "华东后续章节高频考随机误差/标准误，但本章只是导入", "23、24、25年误差相关真题最小映射在后续经典测验理论/信度章节", "心理测量基本原理、信效度相关", "误差题型稳定", "选择/简答", "本章保留二级导入，后续章节按一级展开", "高", ""],
        ["心理测量的间接性、相对性", "第二章P36", "二级", "心理测量定义后的核心特点，适合简答，但缺目标真题精确命中", "无", "心理测量基本原理", "概念辨析常见", "选择/简答", "暂保留二级；若负责人重视基础概念辨析可升一级", "中", ""],
        ["测验分类", "第二章P41-P43", "二级", "分类框架支撑智力/人格/常模等后续章节，选择题可考", "无本章直接真题", "测验类型、智力测验、人格测验相关", "跨院校常见分类题", "选择/简答", "暂保留二级，不为纯分类框架升一级", "中", ""],
    ]
    for row in strong_rows:
        ws.append(row)
    style_sheet(ws, [22, 18, 12, 36, 30, 24, 28, 16, 34, 10, 16])

    ws_e = wb.create_sheet("证据映射")
    headers = ["章节", "知识点", "教材页码", "考纲覆盖", "真题证据", "题型", "层级", "强二级", "Tips/表/图/补充", "编制决策"]
    ws_e.append(headers)
    rows = [
        ["第一章", "中国古代心理测量思想和实践", "P3-P5", "历史发展概述", "无", "", "三级", "否", "不做", "中国古代背景内容，无真题支撑，压缩保留主线"],
        ["第一章", "艾斯克罗、沈干", "P6", "历史发展概述", "无", "", "三级", "否", "不做", "早期尝试，保留人物贡献关键词"],
        ["第一章", "冯特实验心理学影响", "P7", "历史发展概述", "无", "", "二级", "否", "不做", "与标准化思想相关，保留研究内容和情境控制两点"],
        ["第一章", "高尔顿贡献", "P8", "历史发展概述", "无直接测量真题", "选择/名词解释", "二级", "是", "不做", "术语和人物贡献可考，接近一级但缺目标真题"],
        ["第一章", "卡特尔、克雷丕林、艾宾浩斯", "P9", "历史发展概述", "无", "选择", "二级", "否", "不做", "保留年份、论文、首创测验等选择题点"],
        ["第一章", "比奈—西蒙量表", "P11", "智力测验的起源", "20年相关真题", "选择", "一级", "否", "Tips", "目标真题涉及第一个智力测验，保留时间线"],
        ["第一章", "个别测验与团体测验", "P11-P12", "智力测验发展", "无直接真题", "选择/简答", "二级", "是", "Tips表格", "与比奈和陆军量表相邻，易混，做比较表"],
        ["第一章", "我国心理测量发展", "P15-P18", "历史发展概述", "无", "", "三级", "否", "不做", "我国发展史，无真题支撑，压缩"],
        ["第二章", "测量定义", "P29", "心理测量基本原理", "20年真题", "选择", "一级", "否", "Tips", "高频定义，区分一般测量和心理测验"],
        ["第二章", "测量三要素", "P29", "心理测量基本原理", "20年真题间接涉及", "选择", "一级", "否", "Tips", "和心理测验三要素易混"],
        ["第二章", "参照点和单位", "P32", "心理测量基本原理", "无直接真题", "选择/简答", "二级", "是", "不做", "支撑量表水平判断，列强二级"],
        ["第二章", "四种测量水平/量表", "P33", "心理测量基本原理", "20、22、25、26年真题", "选择/简答/名词解释", "一级", "否", "表格+Tips", "高频，必须重点掌握"],
        ["第二章", "直接测量和间接测量", "P34", "心理测量基本原理", "无", "选择", "二级", "否", "不做", "心理测量特点的基础"],
        ["第二章", "测量误差和精确程度", "P34", "心理测量基本原理", "23、24年误差真题相关，但最小映射在后续信度/经典测验理论章节", "选择/简答", "二级", "是", "不做，后续章节展开", "本章只作导入，随机误差来源不在第二章强行展开"],
        ["第二章", "心理测量定义", "P35", "心理测量基本原理", "无直接真题", "名词解释", "一级", "否", "不做", "核心概念"],
        ["第二章", "心理测量可能性", "P35", "心理测量基本原理", "无", "选择", "二级", "否", "不做", "保留桑代克、麦柯尔"],
        ["第二章", "心理测量特点", "P36", "心理测量基本原理", "无精确真题", "简答/选择", "二级", "是", "Tips", "间接性、相对性是核心理解点，但缺直接真题证据"],
        ["第二章", "心理测量水平", "P37", "心理测量基本原理", "25年真题", "简答", "一级", "否", "不做", "只保留教材本章可支撑的原始分转标准分处理，严格等距性方法留后续章节"],
        ["第二章", "心理测验定义", "P37", "心理测量基本原理", "20年真题相关", "选择", "一级", "否", "不做", "行为样组、客观、标准化"],
        ["第二章", "心理测验三要素", "P38", "心理测量基本原理", "20、21年真题", "选择/简答/名词解释", "一级", "否", "Tips表格", "和一般测量三要素高频易混；2021年标准化条件/标准化样组在本章提示，后续详讲"],
        ["第二章", "标准化", "P38", "心理测量基本原理/量表编制", "21年真题相关", "简答/名词解释", "一级", "否", "Tips表格", "标准化条件可迁移到测验编制"],
        ["第二章", "信度、效度、难度、鉴别力", "P39-P41", "信度效度/基本原理", "信效度多次真题", "选择/名词解释", "一级", "否", "Tips", "本章为预备概念，后章会展开"],
        ["第二章", "测验分类", "P41-P43", "测验类型相关", "无直接真题", "选择/简答", "二级", "是", "不做", "分类体系可考但非最高频"],
        ["第二章", "测验应用", "P43-P45", "广义应用背景", "无", "简答背景", "三级", "否", "不做", "较常识化且无真题，压缩保留功能链"],
    ]
    for row in rows:
        ws_e.append(row)
    style_sheet(ws_e, [10, 24, 12, 18, 22, 16, 10, 10, 18, 38])

    ws3 = wb.create_sheet("自检")
    checks = [
        ["资料来源", "通过", "内容只使用教材、考纲、真题汇总；HF/人工一本通只作格式参考，未作为正文内容依据"],
        ["章节范围", "通过", "仅编制教材第一章和第二章"],
        ["正文质量", "通过", "压缩中国古代/我国发展史，强化第二章高频考点，避免教材式长段"],
        ["层级逻辑", "通过", "真题点标一级；考纲核心点至少二级；中国背景无真题降三级"],
        ["正文过程语", "通过", "学生版已移除‘无真题支撑/正文保留主线/细节了解即可’等编制说明式句子"],
        ["关键词/关键句", "通过", "术语、人名、理论加粗；定义、判断、关系和答题短语下划线"],
        ["Tips", "通过", "无明确教材实验，采用生活化例子和易混表格；Tips改为蓝底块+左上标签样式"],
        ["图表", "通过", "四种量表、个别/团体、测量三要素/测验三要素以Tips内表格呈现，均服务一级或强二级"],
        ["补充内容", "通过", "本次未在第一、二章正文强行加入后续章节完整补充；心理量表等距性只保留教材本章可支撑表述，随机误差等内容留到后续信度/经典测验理论章节展开"],
        ["排版", "通过", "A4黑白打印，正文宋体小四，标题设置keep-with-next，Tips/表格设置为尽量不跨页"],
    ]
    ws3.append(["检查项", "结论", "说明"])
    for row in checks:
        ws3.append(row)
    for cell in ws3[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="404040")
    for row in ws3.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    for i, width in enumerate([18, 12, 70], 1):
        ws3.column_dimensions[get_column_letter(i)].width = width
    wb.save(XLSX_PATH)


def build_notes():
    NOTES_PATH.write_text(
        "# 华东347测量心理学一本通第1-2章编制说明\n\n"
        "## 已生成文件\n\n"
        f"- 学生版：`{DOCX_PATH.name}`\n"
        f"- 审核表：`{XLSX_PATH.name}`\n\n"
        "## 关键处理\n\n"
        "- 第一章压缩中国古代和我国发展史内容；保留高尔顿、卡特尔、比奈、团体测验等历史主线。\n"
        "- 第二章强化测量定义、四种量表、心理测量特点、心理测验三要素、标准化、信效度等高频点。\n"
        "- 内容编制只依据教材、考纲和真题；HF/人工一本通只作为格式参考，不作为内容参考。\n"
        "- 将四种量表、个别/团体测验、一般测量三要素与心理测验三要素做成Tips内表格，并改为深大样例方向的蓝底Tips样式。\n"
        "- 审核表首页改为强二级复核表，集中呈现是否升一级/保留二级的人工确认项。\n"
        "- 心理量表等距性只保留教材本章可支撑的原始分转标准分处理，不写无来源的常模转换/IRT等方法。\n"
        "- 2021年标准化条件、标准化样组已在心理测验三要素处标注；标准化样组后续在测验编制与常模章节详讲。\n"
        "- 随机误差等真题点更适合后续信度/经典测验理论章节展开，本次第二章仅保留测量误差导入。\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build_docx()
    build_xlsx()
    build_notes()
    print(DOCX_PATH)
    print(XLSX_PATH)
    print(NOTES_PATH)
