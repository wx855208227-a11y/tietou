#!/usr/bin/env python3
"""Export the Huadong review report to a printed-page Excel workbook."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation


FINDING_RE = re.compile(r"^\| (\d{3}) \| ([^|]+) \| (.+) \|$")
PAGE_RE = re.compile(r"P(\d+)(?:\s*([–—-])\s*P?(\d+))?")


def convert_page_expression(expression: str) -> str:
    """Convert DOCX physical page references to printed-page references."""

    def replace(match: re.Match[str]) -> str:
        start = int(match.group(1)) - 6
        if start < 1:
            raise ValueError(f"physical page is outside body: {match.group(0)}")
        if match.group(3):
            end = int(match.group(3)) - 6
            if end < start:
                raise ValueError(f"invalid page range: {match.group(0)}")
            return f"{start}—{end}"
        return str(start)

    converted = PAGE_RE.sub(replace, expression)
    if "P" in converted:
        raise ValueError(f"unconverted page expression: {expression}")
    return converted


def convert_location(location: str) -> tuple[str, str]:
    """Return a printed-page index and a human-readable detail locator."""

    matches = list(PAGE_RE.finditer(location))
    if not matches:
        raise ValueError(f"location has no physical page: {location}")
    printed_tokens: list[str] = []
    for match in matches:
        token = convert_page_expression(match.group(0))
        if token not in printed_tokens:
            printed_tokens.append(token)

    prefix, separator, suffix = location.partition("；")
    prefix_without_pages = PAGE_RE.sub("", prefix).strip(" 、，,")
    if separator and not prefix_without_pages:
        detail = suffix
    else:
        detail = PAGE_RE.sub(
            lambda match: f"第{convert_page_expression(match.group(0))}页",
            location,
        )
    return "、".join(printed_tokens), detail


def parse_report(path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    chapter = ""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## 第"):
            chapter = line.removeprefix("## ").strip()
            continue
        match = FINDING_RE.match(line)
        if not match:
            continue

        cells = [cell.strip() for cell in line[1:-1].split("|")]
        if len(cells) != 7:
            raise ValueError(f"line {line_number}: expected 7 cells, got {len(cells)}")
        number, severity_label, physical_location, original, issue, suggestion, confidence = cells
        printed_pages, detail = convert_location(physical_location)
        severity = severity_label[0]
        risk_label = severity_label[1:].strip()
        if risk_label.startswith("（") and risk_label.endswith("）"):
            risk_label = risk_label[1:-1]

        findings.append(
            {
                "编号": number,
                "章节": chapter,
                "严重程度": severity,
                "风险标签": risk_label or "常规编制问题",
                "一本通实际页码": printed_pages,
                "具体位置": detail,
                "一本通原文": original,
                "问题与教材依据": issue,
                "建议修改": suggestion,
                "置信度": confidence,
            }
        )

    expected = [f"{number:03d}" for number in range(1, 198)]
    actual = [item["编号"] for item in findings]
    if actual != expected:
        raise ValueError("finding numbers are not continuous from 001 to 197")
    return findings


def build_workbook(findings: list[dict[str, str]], output: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "审核问题清单"
    summary = wb.create_sheet("使用说明与汇总")

    navy = "1F4E78"
    light_blue = "D9EAF7"
    white = "FFFFFF"
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)

    headers = [
        "编号",
        "章节",
        "严重程度",
        "风险标签",
        "一本通实际页码",
        "具体位置",
        "一本通原文",
        "问题与教材依据",
        "建议修改",
        "置信度",
        "修改状态",
        "编辑备注",
    ]
    ws.append(headers)
    for finding in findings:
        ws.append([finding.get(header, "") for header in headers])

    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="微软雅黑", size=11, bold=True, color=white)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    ws.row_dimensions[1].height = 30

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
        row[0].alignment = Alignment(horizontal="center", vertical="top")
        row[2].alignment = Alignment(horizontal="center", vertical="top")
        row[4].alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        row[9].alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        row[10].alignment = Alignment(horizontal="center", vertical="top")

    widths = {
        "A": 8,
        "B": 25,
        "C": 10,
        "D": 23,
        "E": 16,
        "F": 31,
        "G": 44,
        "H": 72,
        "I": 58,
        "J": 24,
        "K": 13,
        "L": 28,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:L{ws.max_row}"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"

    status = DataValidation(
        type="list",
        formula1='"待处理,修改中,已修改,暂不修改"',
        allow_blank=True,
    )
    status.promptTitle = "修改状态"
    status.prompt = "请选择待处理、修改中、已修改或暂不修改。"
    ws.add_data_validation(status)
    status.add(f"K2:K{ws.max_row}")

    severity_fills = {
        "高": PatternFill("solid", fgColor="F4CCCC"),
        "中": PatternFill("solid", fgColor="FCE5CD"),
        "低": PatternFill("solid", fgColor="D9EAD3"),
    }
    for severity, fill in severity_fills.items():
        ws.conditional_formatting.add(
            f"C2:C{ws.max_row}",
            FormulaRule(formula=[f'$C2="{severity}"'], fill=fill),
        )

    severity_counts = Counter(item["严重程度"] for item in findings)
    source_risk_count = sum("教材" in item["风险标签"] for item in findings)
    summary_rows = [
        ("华东《心理学导论》一本通审核表", "197项问题·实际标注页码版"),
        ("页码口径", "“一本通实际页码”均为页面底部印出的页码，不是Word/PDF物理页码，也不是标题中的教材页码。"),
        ("页码换算", "正文物理第7页印为第1页，因此换算为：一本通实际页码＝物理页码－6。已逐页核验正文386页页脚。"),
        ("审核范围", "392个物理页；正文实际页码1—386；共18章。"),
        ("问题总数", str(len(findings))),
        ("高严重度", str(severity_counts["高"])),
        ("中严重度", str(severity_counts["中"])),
        ("低严重度", str(severity_counts["低"])),
        ("教材风险标签项", f"{source_risk_count}项；需学科负责人决定勘误、加注或保留教材口径。"),
        ("使用方法", "在“审核问题清单”中使用表头筛选；可在“修改状态”和“编辑备注”两列跟踪修订。"),
        ("优先顺序", "先处理高严重度，再处理中严重度，最后批量处理低严重度文字与格式问题。"),
    ]
    for row in summary_rows:
        summary.append(row)
    summary.column_dimensions["A"].width = 20
    summary.column_dimensions["B"].width = 105
    summary.row_dimensions[1].height = 34
    for row_number, row in enumerate(summary.iter_rows(), 1):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=11, bold=(row_number == 1 or cell.column == 1))
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = border
        if row_number == 1:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor=navy)
                cell.font = Font(name="微软雅黑", size=13, bold=True, color=white)
        elif row_number % 2 == 0:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor=light_blue)
    summary.freeze_panes = "A2"
    summary.sheet_view.showGridLines = False

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def validate_workbook(path: Path) -> None:
    wb = load_workbook(path, read_only=False, data_only=False)
    if wb.sheetnames != ["审核问题清单", "使用说明与汇总"]:
        raise ValueError(f"unexpected sheets: {wb.sheetnames}")
    ws = wb["审核问题清单"]
    if ws.max_row != 198 or ws.max_column != 12:
        raise ValueError(f"unexpected dimensions: {ws.max_row} x {ws.max_column}")
    if ws["E2"].value != "4" or ws["E198"].value != "369":
        raise ValueError(f"page conversion spot-check failed: {ws['E2'].value}, {ws['E198'].value}")
    if ws["E54"].value != "87、89" or "第89页" not in ws["F54"].value:
        raise ValueError("multi-segment page conversion failed for finding 053")
    if ws["E60"].value != "90、105":
        raise ValueError("multi-page conversion failed for finding 059")
    if ws["E197"].value != "218、299、341—342":
        raise ValueError("mixed page/range conversion failed for finding 196")
    if ws.freeze_panes != "A2" or ws.auto_filter.ref != "A1:L198":
        raise ValueError("worksheet filter/freeze settings missing")
    counts = Counter(ws.cell(row=row, column=3).value for row in range(2, 199))
    if counts != {"高": 48, "中": 87, "低": 62}:
        raise ValueError(f"severity totals mismatch: {counts}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    findings = parse_report(args.report)
    build_workbook(findings, args.output)
    validate_workbook(args.output)
    print(f"xlsx_ok findings={len(findings)} output={args.output}")


if __name__ == "__main__":
    main()
