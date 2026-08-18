#!/usr/bin/env python3
"""Build the 2026-08-18 Huadong Yibentong re-audit workbook."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from export_review_xlsx import parse_report


NEW_FINDINGS = [
    {
        "编号": "198",
        "版本状态": "新增",
        "上版编号": "",
        "章节": "第十六章 人格",
        "严重程度": "高",
        "风险标签": "新版本改写错误",
        "一本通实际页码": "331",
        "具体位置": "“弗洛伊德的精神分析人格理论—生的本能”",
        "一本通原文": "各种本能可以归结为两种：生的本能和死的本能。是指一切与保全生命有关的本能……",
        "问题与教材依据": "新版删除了第二句的主语“生的本能”，使“是指……”没有明确指代，甚至可能被误读为同时定义生、死两种本能。主教材P524（PDF P536）原文为“生的本能……是指一切与保全生命有关的本能”。",
        "建议修改": "改为“各种本能可以归结为生的本能和死的本能两种。生的本能是指一切与保全生命有关的本能，是具有建设性和创造性的积极内在力量。”",
        "置信度": "确定",
    },
    {
        "编号": "199",
        "版本状态": "新增",
        "上版编号": "",
        "章节": "第十六章 人格",
        "严重程度": "中",
        "风险标签": "新版本内容缺漏",
        "一本通实际页码": "332",
        "具体位置": "“弗洛伊德的精神分析人格理论—死的本能”",
        "一本通原文": "死的本能是指驱使个体走向死亡的本能。",
        "问题与教材依据": "新版删掉了主教材P524（PDF P536）中的关键内容：“驱使个体回到有生命之前的无机物状态（即走向死亡）”以及“攻击与破坏两种能量”。只保留“走向死亡”过度简化，且会漏失理论得分点。",
        "建议修改": "恢复为“死的本能是指驱使个体回到有生命之前的无机物状态（即走向死亡）的本能，其中包含由此冲动促发的攻击与破坏两种能量。”",
        "置信度": "确定",
    },
    {
        "编号": "200",
        "版本状态": "新增",
        "上版编号": "",
        "章节": "第十六章 人格",
        "严重程度": "中",
        "风险标签": "新版本层级粘连",
        "一本通实际页码": "332",
        "具体位置": "“死的本能”末句与“人格结构”标题",
        "一本通原文": "死的本能是指驱使个体走向死亡的本能。（1）人格结构【15年真题】",
        "问题与教材依据": "新版把独立知识标题“（1）人格结构”直接粘到死的本能定义末尾，概念边界和标题层级均被破坏，不符合一本通分点分层及标题规范。",
        "建议修改": "在“本能。”后结束本段；将“（1）人格结构【15年真题】”另起一行，并恢复与同级标题一致的标题样式。",
        "置信度": "确定",
    },
]


HEADERS = [
    "编号",
    "版本状态",
    "上版编号",
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


def current_findings(report: Path) -> list[dict[str, str]]:
    prior = parse_report(report)
    if len(prior) != 197:
        raise ValueError(f"expected 197 prior findings, got {len(prior)}")
    findings: list[dict[str, str]] = []
    for item in prior:
        current = dict(item)
        current["版本状态"] = "仍存在"
        current["上版编号"] = item["编号"]
        if int(item["编号"]) >= 195:
            current["章节"] = "全书机械一致性"
        findings.append(current)
    findings.extend(NEW_FINDINGS)
    expected = [f"{number:03d}" for number in range(1, 201)]
    if [item["编号"] for item in findings] != expected:
        raise ValueError("current finding numbers are not continuous 001–200")
    return findings


def style_table(ws, *, filter_rows: bool = True) -> None:
    navy = "1F4E78"
    white = "FFFFFF"
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=white)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[1].height = 32
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
        for column in (1, 2, 3, 5, 7, 12, 13):
            row[column - 1].alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
    widths = [8, 11, 10, 25, 10, 23, 16, 33, 45, 72, 60, 24, 13, 28]
    for number, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + number)].width = width
    ws.freeze_panes = "A2"
    if filter_rows:
        ws.auto_filter.ref = f"A1:N{ws.max_row}"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"

    severity_fills = {
        "高": PatternFill("solid", fgColor="F4CCCC"),
        "中": PatternFill("solid", fgColor="FCE5CD"),
        "低": PatternFill("solid", fgColor="D9EAD3"),
    }
    for severity, fill in severity_fills.items():
        ws.conditional_formatting.add(
            f"E2:E{ws.max_row}",
            FormulaRule(formula=[f'$E2="{severity}"'], fill=fill),
        )
    ws.conditional_formatting.add(
        f"B2:B{ws.max_row}",
        FormulaRule(formula=['$B2="新增"'], fill=PatternFill("solid", fgColor="FFF2CC")),
    )

    status = DataValidation(
        type="list",
        formula1='"待处理,修改中,已修改,暂不修改"',
        allow_blank=True,
    )
    ws.add_data_validation(status)
    status.add(f"M2:M{ws.max_row}")


def add_findings_sheet(wb: Workbook, title: str, findings: list[dict[str, str]]) -> None:
    ws = wb.create_sheet(title)
    ws.append(HEADERS)
    for item in findings:
        ws.append([item.get(header, "") for header in HEADERS])
    style_table(ws)


def build_workbook(findings: list[dict[str, str]], output: Path) -> None:
    wb = Workbook()
    default = wb.active
    wb.remove(default)
    add_findings_sheet(wb, "当前问题清单（200项）", findings)
    add_findings_sheet(wb, "新增问题（3项）", NEW_FINDINGS)

    fixed = wb.create_sheet("上版已修复（0项）")
    fixed.append(HEADERS)
    fixed.append(["—", "已修复", "—", "—", "—", "—", "—", "本次复核未发现上版问题已被修复。"])
    style_table(fixed, filter_rows=False)

    summary = wb.create_sheet("使用说明与复审汇总")
    severity = Counter(item["严重程度"] for item in findings)
    version = Counter(item["版本状态"] for item in findings)
    source_risk = sum("教材" in item["风险标签"] for item in findings)
    rows = [
        ("华东《心理学导论》一本通新版复审核对", "2026-08-18上传版；实际标注页码Excel"),
        ("新版SHA-256", "e8160c98fd00948a09868b5a7975e1233f76e6e99500b3034f78efaf628193ef"),
        ("旧版SHA-256", "b2dd4abf0dff2a6e917187fac1ea4c7d66ff3920f1744e7d651569d84ee13572"),
        ("页码口径", "“一本通实际页码”是页面底部印出的页码；正文物理第7—392页与实际第1—386页逐页核验一致。"),
        ("当前问题总数", str(len(findings))),
        ("高严重度", str(severity["高"])),
        ("中严重度", str(severity["中"])),
        ("低严重度", str(severity["低"])),
        ("上版仍存在", str(version["仍存在"])),
        ("上版已修复", "0"),
        ("新版新增", str(version["新增"])),
        ("教材风险标签项", f"{source_risk}项；需学科负责人决定勘误、加注或保留教材口径。"),
        ("版本改动", "正文仅第十六章实际第331—332页发生改写；原197项均未修复，改写新增3项问题。"),
        ("使用方法", "在“当前问题清单（200项）”按章节、严重程度、版本状态或页码筛选；在“修改状态”和“编辑备注”列跟踪处理。"),
        ("处理顺序", "优先修改49项高严重度问题，再处理89项中严重度问题，最后批量处理62项低严重度问题。"),
    ]
    for row in rows:
        summary.append(row)
    summary.column_dimensions["A"].width = 22
    summary.column_dimensions["B"].width = 110
    summary.sheet_view.showGridLines = False
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)
    for row_number, row in enumerate(summary.iter_rows(), 1):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=11, bold=(row_number == 1 or cell.column == 1))
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = border
        if row_number == 1:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor="1F4E78")
                cell.font = Font(name="微软雅黑", size=13, bold=True, color="FFFFFF")
        elif row_number % 2 == 0:
            for cell in row:
                cell.fill = PatternFill("solid", fgColor="D9EAF7")
    summary.freeze_panes = "A2"

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def validate_workbook(path: Path) -> None:
    wb = load_workbook(path, read_only=False, data_only=False)
    expected_sheets = [
        "当前问题清单（200项）",
        "新增问题（3项）",
        "上版已修复（0项）",
        "使用说明与复审汇总",
    ]
    if wb.sheetnames != expected_sheets:
        raise ValueError(f"unexpected sheets: {wb.sheetnames}")
    ws = wb[expected_sheets[0]]
    if ws.max_row != 201 or ws.max_column != 14:
        raise ValueError(f"unexpected current sheet size: {ws.max_row} x {ws.max_column}")
    counts = Counter(ws.cell(row=row, column=5).value for row in range(2, 202))
    if counts != {"高": 49, "中": 89, "低": 62}:
        raise ValueError(f"severity mismatch: {counts}")
    versions = Counter(ws.cell(row=row, column=2).value for row in range(2, 202))
    if versions != {"仍存在": 197, "新增": 3}:
        raise ValueError(f"version status mismatch: {versions}")
    if ws["G2"].value != "4" or ws["G198"].value != "369":
        raise ValueError("prior printed-page spot check failed")
    if ws["G199"].value != "331" or ws["G201"].value != "332":
        raise ValueError("new finding printed-page spot check failed")
    if ws.freeze_panes != "A2" or ws.auto_filter.ref != "A1:N201":
        raise ValueError("filter/freeze settings missing")
    if wb[expected_sheets[1]].max_row != 4:
        raise ValueError("new-findings sheet does not contain three findings")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prior_report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    findings = current_findings(args.prior_report)
    build_workbook(findings, args.output)
    validate_workbook(args.output)
    print(f"reaudit_xlsx_ok findings={len(findings)} output={args.output}")


if __name__ == "__main__":
    main()
