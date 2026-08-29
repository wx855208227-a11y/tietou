#!/usr/bin/env python3
"""Repackage the completed SZU audit in the proven Huadong review-table form.

The source findings are unchanged. This builder makes the primary sheet
editor-facing by placing textbook print pages, scan-PDF pages, exam evidence,
reasoning, and the proposed replacement in one readable evidence chain.
"""

from __future__ import annotations

import re
import zipfile
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SOURCE = REPO / "analysis/深大普通心理学一本通_全量审核表_20260829_实际页码.xlsx"
OUTPUT = REPO / "analysis/深大普通心理学一本通_审核表_华东样表标准版_20260829.xlsx"

BLUE = "1F4E78"
WHITE = "FFFFFF"
GRID = Side(style="thin", color="B7C9D6")
BORDER = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
SEVERITY_FILL = {"高": "F4CCCC", "中": "FFF2CC", "低": "D9EAD3"}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def pdf_label(value: str) -> str:
    """Convert '第32页/第32—33页' to 'PDF P32/P32—33'."""
    value = clean_text(value)
    if not value or value == "—":
        return ""
    match = re.fullmatch(r"第(.+?)页", value)
    if match:
        return f"PDF P{match.group(1)}"
    if value.startswith("P"):
        return f"PDF {value}"
    return f"扫描PDF {value}"


def risk_label(kind: str, source: str) -> str:
    kind = clean_text(kind)
    source = clean_text(source)
    major_missing = (
        "整节漏编", "整块缺失", "整点缺漏", "整段核心内容缺漏",
        "结构结论缺漏", "研究设计内容整块缺失", "方法内容整块缺失",
        "疑似内容缺漏",
    )
    format_terms = (
        "标题样式", "标点", "符号", "括号", "引号", "空白页", "孤行页",
        "表格跨页", "目录/页码", "编号", "中英文混排", "中英文标点",
        "连接号", "真题/题型标记",
    )
    if "教材原文风险" in source or "教材原文风险" in kind:
        broad = "教材表述风险"
    elif "补充内容/来源待确认" in source:
        broad = "补充内容待确认"
    elif any(term in kind for term in major_missing):
        broad = "内容整块缺漏"
    elif "真题" in kind or "真题标注" in source:
        broad = "真题标注问题"
    elif "Tips" in kind or "Tips" in source or "自编Tips" in source:
        broad = "Tips/例子问题"
    elif any(term in kind for term in format_terms):
        broad = "格式与标注问题"
    else:
        broad = "常规编制问题"
    return f"{broad}\n{kind}"


def confidence_label(judgement: str, confidence: str) -> str:
    judgement = clean_text(judgement)
    confidence = clean_text(confidence)
    if judgement == "确定错误":
        return "确定"
    if judgement == "疑似问题":
        return "待确认"
    if judgement == "优化建议":
        return "建议项"
    return confidence or "待确认"


def evidence_text(row: dict[str, object]) -> str:
    book_page = clean_text(row.get("教材书内页码"))
    scan_page = clean_text(row.get("教材扫描PDF页码"))
    exam = clean_text(row.get("真题依据"))
    explanation = clean_text(row.get("核对依据与问题说明"))
    parts: list[str] = []
    if book_page and book_page != "—":
        if "待确认" in book_page:
            parts.append("教材出处及页码待确认。")
        else:
            scan = pdf_label(scan_page)
            page_clause = f"主教材 {book_page}"
            if scan:
                page_clause += f"（{scan}）"
            parts.append(page_clause + "。")
    elif scan_page and scan_page != "—":
        parts.append(pdf_label(scan_page) + "。")
    if exam and exam != "—":
        parts.append(f"深大真题：{exam}。")
    if explanation:
        parts.append(explanation)
    return "".join(parts)


def style_header(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def style_body(ws, center_columns: set[int] | None = None) -> None:
    center_columns = center_columns or set()
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=9)
            cell.alignment = Alignment(
                horizontal="center" if cell.column in center_columns else "left",
                vertical="top", wrap_text=True,
            )
            cell.border = BORDER


def estimated_height(values: list[object], widths: list[float], minimum: float = 30, maximum: float = 120) -> float:
    lines = 1
    for value, width in zip(values, widths):
        text = clean_text(value)
        if not text:
            continue
        visual = sum(2 if ord(char) > 127 else 1 for char in text)
        lines = max(lines, (visual // max(8, int(width * 1.7))) + text.count("\n") + 1)
    return min(maximum, max(minimum, lines * 16.5))


def build() -> None:
    source_wb = load_workbook(SOURCE, data_only=True)
    source_ws = source_wb["审核问题清单"]
    headers = [clean_text(cell.value) for cell in source_ws[1]]
    source_rows = [dict(zip(headers, values)) for values in source_ws.iter_rows(min_row=2, values_only=True)]

    wb = Workbook()
    ws = wb.active
    ws.title = "审核问题清单"
    output_headers = [
        "编号", "章节", "严重程度", "风险标签", "一本通实际页码", "具体位置",
        "一本通原文", "问题与教材依据", "建议修改", "置信度", "修改状态", "编辑备注",
    ]
    ws.append(output_headers)
    for row in source_rows:
        ws.append([
            clean_text(row.get("编号")), clean_text(row.get("章节")),
            clean_text(row.get("严重程度")),
            risk_label(clean_text(row.get("问题类型")), clean_text(row.get("来源性质"))),
            clean_text(row.get("一本通实际页码")), clean_text(row.get("具体位置")),
            clean_text(row.get("一本通原文")), evidence_text(row),
            clean_text(row.get("修改建议")),
            confidence_label(clean_text(row.get("判断层级")), clean_text(row.get("置信度"))),
            clean_text(row.get("修改状态")) or "待处理", clean_text(row.get("编辑备注")),
        ])

    widths = [9, 31, 11, 27, 18, 34, 50, 83, 72, 14, 14, 30]
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + index)].width = width
    style_header(ws)
    style_body(ws, {1, 3, 5, 10, 11})
    ws.row_dimensions[1].height = 32
    for row_index in range(2, ws.max_row + 1):
        values = [ws.cell(row_index, col).value for col in range(1, ws.max_column + 1)]
        ws.row_dimensions[row_index].height = estimated_height(values, widths)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:L{ws.max_row}"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    for severity, color in SEVERITY_FILL.items():
        ws.conditional_formatting.add(
            f"C2:C{ws.max_row}",
            FormulaRule(formula=[f'$C2="{severity}"'], fill=PatternFill("solid", fgColor=color)),
        )
    status_validation = DataValidation(type="list", formula1='"待处理,修改中,已修改,暂不修改"')
    ws.add_data_validation(status_validation)
    status_validation.add(f"K2:K{ws.max_row}")

    summary = wb.create_sheet("使用说明与汇总")
    severity_counts = Counter(clean_text(row.get("严重程度")) for row in source_rows)
    judgement_counts = Counter(clean_text(row.get("判断层级")) for row in source_rows)
    summary_rows = [
        ("深大《普通心理学》一本通审核表", f"{len(source_rows)}项问题·华东样表标准版"),
        ("页码口径", "“一本通实际页码”使用文档正文页脚印出的P1—P492，不使用Word/PDF物理页码。"),
        ("教材依据", "彭聃龄《普通心理学》第六版为正文内容最高依据；每条有教材依据的问题均同时列书内印刷页与扫描PDF页。"),
        ("真题边界", "深圳大学2019—2026年初试真题仅用于核查年份标注、考点覆盖和重点等级，不替代教材判断正文内容。"),
        ("审核范围", "最新版一本通全部标题、正文、表格、Tips、补充内容和真题标注；本次独立重审，不与旧版比较。"),
        ("逐条覆盖", "已复核4,963个非空正文单元；完整底账见“逐条覆盖底账”。问题数量只代表成立项目，不代表审核深度。"),
        ("问题总数", str(len(source_rows))), ("高严重度", str(severity_counts["高"])),
        ("中严重度", str(severity_counts["中"])), ("低严重度", str(severity_counts["低"])),
        ("确定错误", str(judgement_counts["确定错误"])),
        ("疑似问题", str(judgement_counts["疑似问题"])),
        ("优化建议", str(judgement_counts["优化建议"])),
        ("使用方法", "在主清单中筛选章节、严重程度和风险标签；按“修改状态”跟踪修订，并在“编辑备注”记录处理口径。"),
        ("优先顺序", "先处理高严重度概念、整块缺漏和真题问题，再处理中严重度，最后批量处理低严重度文字与格式问题。"),
    ]
    for row in summary_rows:
        summary.append(row)
    summary.column_dimensions["A"].width = 24
    summary.column_dimensions["B"].width = 120
    style_header(summary)
    style_body(summary, {1})
    summary.freeze_panes = "A2"
    summary.sheet_view.showGridLines = False
    for index in range(1, summary.max_row + 1):
        summary.row_dimensions[index].height = 34 if index > 1 else 36

    ledger_source = source_wb["逐条覆盖底账"]
    ledger = wb.create_sheet("逐条覆盖底账")
    for values in ledger_source.iter_rows(values_only=True):
        ledger.append([clean_text(value) for value in values])
    ledger_widths = [12, 16, 32, 18, 16, 14, 42, 80, 20, 21, 29, 46, 20]
    for index, width in enumerate(ledger_widths, start=1):
        ledger.column_dimensions[chr(64 + index)].width = width
    style_header(ledger)
    style_body(ledger, {1, 2, 9, 10, 13})
    ledger.row_dimensions[1].height = 32
    for row_index in range(2, ledger.max_row + 1):
        ledger.row_dimensions[row_index].height = 30
    ledger.freeze_panes = "A2"
    ledger.auto_filter.ref = f"A1:M{ledger.max_row}"
    ledger.sheet_view.showGridLines = False

    wb.active = 0
    wb.save(OUTPUT)
    with zipfile.ZipFile(OUTPUT) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"Corrupt XLSX member: {bad}")
    print(OUTPUT)
    print(f"issues={ws.max_row - 1}, ledger={ledger.max_row - 1}")


if __name__ == "__main__":
    build()
