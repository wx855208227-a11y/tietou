#!/usr/bin/env python3
"""Export the calibrated SZU audit in the accepted Huadong workbook format.

Content correctness is governed by Peng Danling's textbook.  Shenzhen
University exam papers are used only to audit true-question labels, coverage,
and importance levels; they are never substituted for textbook evidence.
"""

from __future__ import annotations

import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))

from export_szu_source_grounded_audit import (  # noqa: E402
    EXAM_SOURCE,
    TEXTBOOK,
    current_issues,
    textbook_pdf_locator,
)


OUTPUT = REPO / "analysis/深大普通心理学一本通_完整审核表_华东版式_实际页码.xlsx"

HEADERS = [
    "编号", "章节", "严重程度", "问题类型", "一本通实际页码", "具体位置",
    "一本通原文", "教材页码", "核对依据与问题说明", "修改建议", "置信度",
    "来源性质", "修改状态", "编辑备注",
]

CHAPTERS = [
    ("第一章 心理学的研究对象和方法", "1—22", "P2—33"),
    ("第二章 心理与行为的脑神经基础", "23—41", "P38—65"),
    ("第三章 感觉", "42—66", "P75—122"),
    ("第四章 知觉", "67—106", "P123—163"),
    ("第五章 意识", "107—144", "P166—199"),
    ("第六章 记忆", "145—190", "P202—243"),
    ("第七章 思维", "191—239", "P247—285"),
    ("第八章 语言", "240—255", "P288—314"),
    ("第九章 动机", "256—295", "P324—351"),
    ("第十章 情绪", "296—321", "P354—383"),
    ("第十一章 智力", "322—337", "P390—424"),
    ("第十二章 人格", "338—375", "P426—454"),
    ("第十三章 学习", "376—411", "P458—494"),
    ("第十四章 人生全程发展", "412—440", "P496—525"),
    ("补充章1 行为学习理论", "441—447", "补充来源待确认"),
    ("补充章2 认知学习理论", "448—467", "补充来源待确认"),
    ("补充章3 建构主义与人本主义学习理论", "468—480", "补充来源待确认"),
    ("补充章4 学习动机", "481—492", "补充来源待确认"),
]

# These candidates do not meet the calibrated defect threshold.  They are
# grammatically acceptable, harmless adaptations, or accepted term variants.
EXCLUDED = {
    ("第二章 心理与行为的脑神经基础", "39", "鲁利亚三个机能系统的关系"),
    ("第五章 意识", "129", "自动化加工"),
    ("第六章 记忆", "180", "识记材料的性质"),
    ("第七章 思维", "214", "层次网络模型"),
    ("第七章 思维", "237—238", "代表性启发法Tips"),
    ("第十一章 智力", "328", "多元智力理论相关表述"),
}


def printed_and_pdf_locator(value: object) -> str:
    text = str(value).strip()
    pdf = textbook_pdf_locator(text)
    if pdf == "—":
        return "—"
    return f"{text}（扫描PDF{pdf}）"


def source_type(item: dict[str, object]) -> str:
    raw = str(item["来源性质"])
    if raw == EXAM_SOURCE:
        return "真题标注核验"
    if "教材原文风险" in raw:
        return "教材原文风险（需负责人确认）"
    if "待确认" in raw or "专业判断" in raw or "Tips内容判断" in raw:
        return "补充内容/来源待确认"
    if "Tips" in str(item["具体位置"]) or "Tips" in raw:
        return "自编Tips/例子"
    if any(token in raw for token in ("一本通规范", "结构核验", "格式核验", "渲染核验", "标点核验")):
        return "格式规范"
    if "内部" in raw or "全书标点" in raw:
        return "文字/格式规范"
    return "人工编制/改写"


def confidence_label(item: dict[str, object], source: str) -> str:
    if source in {"教材原文风险（需负责人确认）", "补充内容/来源待确认"}:
        return "待确认"
    return "确定" if str(item["置信度"]) == "高" else "较高"


def evidence_fields(item: dict[str, object], source: str) -> tuple[str, str]:
    legacy = str(item["教材页码"]).strip()
    explanation = str(item["核对依据与问题说明"])
    if source == "真题标注核验":
        return "—（真题标注核验）", f"真题标注核验：{legacy}。{explanation}"
    if legacy.startswith("P"):
        return printed_and_pdf_locator(legacy), explanation.replace("教材", "主教材", 1)
    if source == "补充内容/来源待确认":
        return "—（补充来源待确认）", explanation
    if source in {"格式规范", "文字/格式规范", "自编Tips/例子"}:
        return "—（文内/规范核验）", explanation
    return "—（专业/文内核验）", explanation


def build_findings() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for item in current_issues():
        key = (str(item["章节"]), str(item["一本通实际页码"]), str(item["具体位置"]))
        if key in EXCLUDED:
            continue
        source = source_type(item)
        textbook_page, explanation = evidence_fields(item, source)
        findings.append({
            "章节": str(item["章节"]),
            "严重程度": str(item["严重程度"]),
            "问题类型": str(item["问题类型"]),
            "一本通实际页码": str(item["一本通实际页码"]),
            "具体位置": str(item["具体位置"]),
            "一本通原文": str(item["一本通原文"]),
            "教材页码": textbook_page,
            "核对依据与问题说明": explanation,
            "修改建议": str(item["修改建议"]),
            "置信度": confidence_label(item, source),
            "来源性质": source,
            "修改状态": "待处理",
            "编辑备注": "",
        })
    for number, item in enumerate(findings, 1):
        item["编号"] = f"{number:03d}"
    return findings


def style_findings(ws) -> None:
    navy, white = "1F4E78", "FFFFFF"
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=white)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[1].height = 34
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
        for column in (1, 3, 5, 8, 11, 13):
            row[column - 1].alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
    widths = [8, 25, 10, 18, 16, 32, 46, 24, 76, 62, 15, 28, 13, 28]
    for number, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + number)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:N{ws.max_row}"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    fills = {
        "高": PatternFill("solid", fgColor="F4CCCC"),
        "中": PatternFill("solid", fgColor="FCE5CD"),
        "低": PatternFill("solid", fgColor="D9EAD3"),
    }
    for severity, fill in fills.items():
        ws.conditional_formatting.add(
            f"C2:C{ws.max_row}", FormulaRule(formula=[f'$C2="{severity}"'], fill=fill)
        )
    status = DataValidation(type="list", formula1='"待处理,修改中,已修改,暂不修改"', allow_blank=True)
    ws.add_data_validation(status)
    status.add(f"M2:M{ws.max_row}")


def style_simple_table(ws, widths: list[int]) -> None:
    navy, white = "1F4E78", "FFFFFF"
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=white)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    for row_number, row in enumerate(ws.iter_rows(min_row=2), 2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
            if row_number % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="EAF2F8")
    for number, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + number)].width = width
    ws.freeze_panes = "A2"
    ws.sheet_view.showGridLines = False


def coverage_textbook_locator(value: str) -> str:
    if not value.startswith("P"):
        return value
    return printed_and_pdf_locator(value)


def build_workbook(findings: list[dict[str, str]]) -> Workbook:
    wb = Workbook()
    findings_ws = wb.active
    findings_ws.title = f"审核问题清单（{len(findings)}项）"
    findings_ws.append(HEADERS)
    for item in findings:
        findings_ws.append([item[header] for header in HEADERS])
    style_findings(findings_ws)

    counts = Counter(item["章节"] for item in findings)
    coverage = wb.create_sheet("章节覆盖")
    coverage.append(["章节", "一本通实际页码", "主教材页码（含扫描PDF页）", "问题数", "审核状态"])
    for chapter, ybt_pages, textbook_pages in CHAPTERS:
        number = counts[chapter]
        if chapter.startswith("补充章"):
            number += counts["补充章1—4"]
        coverage.append([
            chapter, ybt_pages, coverage_textbook_locator(textbook_pages), number,
            "已按教材/来源逐章核对；问题数仅用于修改分工，不代表审核深度",
        ])
    coverage.append([
        "全书性项目", "目录/多页", "—（结构、格式与真题标注核验）", counts["全书"],
        "已核对目录、标题、页码、真题标注、表格跨页与全书一致性",
    ])
    style_simple_table(coverage, [36, 18, 34, 12, 64])
    coverage.auto_filter.ref = f"A1:E{coverage.max_row}"

    severity = Counter(item["严重程度"] for item in findings)
    source_counts = Counter(item["来源性质"] for item in findings)
    notes = wb.create_sheet("审核说明")
    rows = [
        ("深大《普通心理学》一本通完整审核表", "采用华东审核表的呈现结构；当前上传稿的独立审核，定位均用一本通页脚实际页码。"),
        ("最高内容依据", f"{TEXTBOOK}。教材决定术语、定义、分类、机制、条件、范围词、逻辑和关键内容是否正确。"),
        ("真题使用边界", "深大2019—2026年真题只用于核查一本通的真题年份标注、考点覆盖和重点等级；真题不替代教材，不用真题题干改写教材定义。问题清单可按‘来源性质=真题标注核验’筛选。"),
        ("审核范围", "正文实际页码P1—492，共14章与4个补充章；另核目录、标题层级、教材页码、Tips、表格、标点和格式。"),
        ("判断标准", "允许忠实教材的化繁为简、分点分层和无害同义改写；只有术语、关键词、定义结构、分类成员、机制、条件、范围/程度、否定、逻辑、数字或句子完整性受损时才判为内容问题。"),
        ("数量原则", "不设置目标问题数，不以问题数量证明审核深度。语法成立的原句、无害人物名替换、可接受术语异写和仅仅‘不够顺口’的表达均不收录。"),
        ("教材页码口径", "每项同时给出教材书内印刷页码和扫描PDF物理页码；本扫描版固定为PDF页码=书内页码+12，例如教材P39对应扫描PDF第51页。"),
        ("补充内容", "四个补充章未给出完整出版物版本和页码。确定的错别字、病句、空标题等可直接改；专业性结论标‘待确认’，不得虚构教材或PDF页码。"),
        ("问题总数", f"{len(findings)}项（高{severity['高']}、中{severity['中']}、低{severity['低']}）；该数字仅为本次成立项目的汇总结果。"),
        ("待确认项目", f"教材原文或补充来源待确认共{source_counts['教材原文风险（需负责人确认）'] + source_counts['补充内容/来源待确认']}项，须先回源或由学科负责人判断，不能直接照建议批量修改。"),
        ("使用方法", "在问题清单按章节、程度、类型、一本通页码、来源性质筛选；优先处理高严重度，再处理中、低严重度；用‘修改状态’和‘编辑备注’跟踪。"),
        ("交付性质", "本文件为审核定位表，未直接修改用户DOCX。"),
    ]
    notes.append(["项目", "说明"])
    for row in rows:
        notes.append(row)
    style_simple_table(notes, [24, 118])
    return wb


def validate(path: Path, findings: list[dict[str, str]]) -> None:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("XLSX ZIP integrity check failed")
    wb = load_workbook(path, read_only=False, data_only=False)
    expected_sheets = [f"审核问题清单（{len(findings)}项）", "章节覆盖", "审核说明"]
    if wb.sheetnames != expected_sheets:
        raise RuntimeError(f"unexpected workbook sheets: {wb.sheetnames}")
    ws = wb[expected_sheets[0]]
    if [cell.value for cell in ws[1]] != HEADERS:
        raise RuntimeError("finding headers do not match the Huadong workbook format")
    if ws.max_row != len(findings) + 1 or ws.max_column != len(HEADERS):
        raise RuntimeError("finding sheet dimensions are wrong")
    if ws.freeze_panes != "A2" or ws.auto_filter.ref != f"A1:N{ws.max_row}":
        raise RuntimeError("finding filter/freeze settings are missing")
    if [ws.cell(row, 1).value for row in range(2, ws.max_row + 1)] != [
        f"{number:03d}" for number in range(1, len(findings) + 1)
    ]:
        raise RuntimeError("finding IDs are not continuous")
    for row in range(2, ws.max_row + 1):
        for column in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
            if ws.cell(row, column).value in (None, ""):
                raise RuntimeError(f"blank finding field at row {row}, column {column}")
    textbook_locators = [ws.cell(row, 8).value for row in range(2, ws.max_row + 1)]
    if "P39（扫描PDF第51页）" not in textbook_locators:
        raise RuntimeError("P39 to scanned PDF page 51 mapping is missing")
    if "P512—513（扫描PDF第524—525页）" not in textbook_locators:
        raise RuntimeError("P512—513 scanned PDF mapping is missing")
    exam_rows = [
        row for row in range(2, ws.max_row + 1)
        if ws.cell(row, 12).value == "真题标注核验"
    ]
    if not exam_rows or any(ws.cell(row, 8).value != "—（真题标注核验）" for row in exam_rows):
        raise RuntimeError("exam evidence leaked into textbook page locators")
    if any(
        ws.cell(row, 5).value == "39" and ws.cell(row, 6).value == "鲁利亚三个机能系统的关系"
        for row in range(2, ws.max_row + 1)
    ):
        raise RuntimeError("calibration exclusion failed")


def main() -> None:
    findings = build_findings()
    wb = build_workbook(findings)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    validate(OUTPUT, findings)
    severity = Counter(item["严重程度"] for item in findings)
    print(f"output={OUTPUT}")
    print(f"findings={len(findings)} high={severity['高']} medium={severity['中']} low={severity['低']}")
    print(f"excluded_non_defects={len(EXCLUDED)}")
    print("validation=ok")


if __name__ == "__main__":
    main()
