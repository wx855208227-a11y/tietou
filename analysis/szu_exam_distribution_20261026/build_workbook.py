#!/usr/bin/env python3
"""Build the user-facing Shenzhen University exam-distribution workbook."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

from classify_questions import ABN, EP, GP, MEAS, MIX, ORG, SOC, STAT


QUESTION_TYPES = [
    "单选题",
    "判断题",
    "填空题",
    "名词解释",
    "简答题",
    "论述题",
    "实验设计题",
    "案例分析题",
    "综合应用题",
]
SUBJECTS = [GP, EP, STAT, MEAS, SOC, ABN, ORG, MIX]
SUBJECT_ORDER = {subject: index for index, subject in enumerate(SUBJECTS)}

NAVY = "17365D"
BLUE = "2F75B5"
LIGHT_BLUE = "D9EAF7"
PALE_BLUE = "EAF2F8"
PALE_YELLOW = "FFF2CC"
PALE_GREEN = "E2F0D9"
PALE_RED = "FCE4D6"
WHITE = "FFFFFF"
GRAY = "666666"
THIN_GRAY = Side(style="thin", color="D9E1F2")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def add_title(ws, title: str, subtitle: str, columns: int) -> int:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=columns)
    cell = ws.cell(1, 1, title)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.font = Font(color=WHITE, bold=True, size=15)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=columns)
    cell = ws.cell(2, 1, subtitle)
    cell.fill = PatternFill("solid", fgColor=PALE_BLUE)
    cell.font = Font(color=GRAY, size=9)
    cell.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[2].height = 30
    return 4


def style_header(ws, row: int, columns: int) -> None:
    for cell in ws[row][:columns]:
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.font = Font(color=WHITE, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=THIN_GRAY)
    ws.row_dimensions[row].height = 28


def add_table(ws, header_row: int, end_row: int, end_col: int, name: str) -> None:
    if end_row <= header_row:
        return
    reference = f"A{header_row}:{get_column_letter(end_col)}{end_row}"
    table = Table(displayName=name, ref=reference)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    ws.add_table(table)


def finalize_sheet(ws, freeze: str, widths: dict[int, float]) -> None:
    ws.freeze_panes = freeze
    ws.sheet_view.showGridLines = False
    ws.auto_filter.ref = ws.tables[next(iter(ws.tables))].ref if ws.tables else None
    for column, width in widths.items():
        ws.column_dimensions[get_column_letter(column)].width = width
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.outlinePr.summaryBelow = True


def write_data_sheet(
    wb: Workbook,
    name: str,
    title: str,
    subtitle: str,
    headers: list[str],
    rows: list[list[object]],
    widths: dict[int, float],
    table_name: str,
    count_columns: tuple[int, int] | None = None,
) -> None:
    ws = wb.create_sheet(name)
    header_row = add_title(ws, title, subtitle, len(headers))
    ws.append([])
    ws.append([])
    # append() cannot target a future row reliably after merged rows; write explicitly.
    for column, header in enumerate(headers, start=1):
        ws.cell(header_row, column, header)
    style_header(ws, header_row, len(headers))
    for row_index, values in enumerate(rows, start=header_row + 1):
        for column, value in enumerate(values, start=1):
            cell = ws.cell(row_index, column, value)
            cell.alignment = Alignment(vertical="top", wrap_text=column in widths and widths[column] >= 24)
            cell.border = Border(bottom=THIN_GRAY)
    end_row = header_row + len(rows)
    add_table(ws, header_row, end_row, len(headers), table_name)
    finalize_sheet(ws, f"A{header_row + 1}", widths)
    if count_columns and rows:
        start_col, end_col = count_columns
        start = f"{get_column_letter(start_col)}{header_row + 1}"
        end = f"{get_column_letter(end_col)}{end_row}"
        ws.conditional_formatting.add(
            f"{start}:{end}",
            ColorScaleRule(
                start_type="num",
                start_value=0,
                start_color=WHITE,
                mid_type="percentile",
                mid_value=50,
                mid_color=LIGHT_BLUE,
                end_type="max",
                end_color=BLUE,
            ),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    questions = read_tsv(args.questions)
    catalog = read_tsv(args.catalog)
    years = sorted({int(row["年份"]) for row in questions})
    question_counter = Counter(
        (int(row["年份"]), row["主科目"], row["教材主章节"], row["题型"])
        for row in questions
    )

    catalog.sort(
        key=lambda row: (
            SUBJECT_ORDER.get(row["科目"], 999),
            int(row["章节序号"]) if row["章节序号"].isdigit() else 999,
            row["章节名称"],
        )
    )

    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.title = "深圳大学2019—2026历年真题科目章节题型分布表"
    wb.properties.subject = "逐题唯一归类与可追溯统计"
    wb.properties.creator = "tietou_review"
    wb.properties.created = datetime.now()

    # 统计说明
    ws = wb.create_sheet("统计说明")
    add_title(
        ws,
        "深圳大学2019—2026历年真题科目·章节·题型分布",
        "源于HF深大初试真题册；255道顶层题号逐题归类。所有汇总数字均可回溯到“逐题明细”。",
        11,
    )
    notes = [
        ("统计范围", "2019—2026年深圳大学347应用心理硕士初试真题，共255道。"),
        ("计数单位", "每个顶层题号计1道；案例题中的（1）（2）等子问不拆分，避免总数膨胀。"),
        ("唯一归类", "每题只指定一个主科目和一个教材主章节参与统计；次要考点单列但不重复计数。"),
        ("章节依据", "普通心理学第6版、实验心理学第2版、心理与教育测量第4版、现代心理与教育统计学第5版的目录章名。"),
        ("拓展内容", "旧题中的社会、管理、变态与咨询内容超出当前四本指定教材，明确标为“跨教材拓展”，未强行并入错误章节。"),
        ("纠错原则", "不机械照抄原题科目括注。例如2026年单选第7题原括注为“心理统计”，主考点实为被试间设计与随机分配，归入实验心理学。"),
        ("使用建议", "先看“完整矩阵”掌握零/非零分布，再在“有题汇总”筛选重点，最后到“逐题明细”定位原题。"),
    ]
    row = 4
    for label, value in notes:
        ws.cell(row, 1, label).font = Font(bold=True, color=NAVY)
        ws.cell(row, 1).fill = PatternFill("solid", fgColor=LIGHT_BLUE)
        ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=11)
        ws.cell(row, 2, value).alignment = Alignment(wrap_text=True, vertical="top")
        for column in range(1, 12):
            ws.cell(row, column).border = Border(bottom=THIN_GRAY)
        ws.row_dimensions[row].height = 34
        row += 1

    row += 1
    year_header = row
    year_headers = ["年份", *QUESTION_TYPES, "合计"]
    for column, value in enumerate(year_headers, start=1):
        ws.cell(row, column, value)
    style_header(ws, row, len(year_headers))
    for year in years:
        row += 1
        values = [year]
        for kind in QUESTION_TYPES:
            values.append(sum(1 for item in questions if int(item["年份"]) == year and item["题型"] == kind))
        values.append(sum(values[1:]))
        for column, value in enumerate(values, start=1):
            ws.cell(row, column, value)
            ws.cell(row, column).alignment = Alignment(horizontal="center")
    row += 1
    totals = ["总计"]
    for kind in QUESTION_TYPES:
        totals.append(sum(1 for item in questions if item["题型"] == kind))
    totals.append(sum(totals[1:]))
    for column, value in enumerate(totals, start=1):
        ws.cell(row, column, value)
        ws.cell(row, column).font = Font(bold=True)
        ws.cell(row, column).fill = PatternFill("solid", fgColor=PALE_GREEN)
        ws.cell(row, column).alignment = Alignment(horizontal="center")
    ws.freeze_panes = f"A{year_header + 1}"
    ws.sheet_view.showGridLines = False
    for column, width in {1: 16, **{index: 12 for index in range(2, 12)}}.items():
        ws.column_dimensions[get_column_letter(column)].width = width
    ws.tabColor = NAVY

    # 逐题明细
    detail_headers = [
        "题目ID",
        "年份",
        "题型",
        "题号",
        "题干",
        "主科目",
        "教材主章节",
        "核心考点",
        "次要考点或跨章节",
        "归类依据",
        "归类备注",
        "唯一计数",
        "原始定位",
        "题目全文",
    ]
    detail_rows = [[row.get(header, "") for header in detail_headers] for row in questions]
    write_data_sheet(
        wb,
        "逐题明细",
        "逐题归类明细（255道）",
        "筛选任意年份/题型/科目/章节；“唯一计数”均为1，次要考点不参与重复统计。",
        detail_headers,
        detail_rows,
        {1: 25, 2: 9, 3: 14, 4: 8, 5: 48, 6: 30, 7: 38, 8: 28, 9: 38, 10: 30, 11: 42, 12: 10, 13: 18, 14: 55},
        "QuestionDetail",
    )
    wb["逐题明细"].tabColor = BLUE

    # 四维长表：只列非零组合。
    long_rows: list[list[object]] = []
    for (year, subject, chapter, kind), count in sorted(
        question_counter.items(),
        key=lambda item: (
            item[0][0],
            SUBJECT_ORDER.get(item[0][1], 999),
            item[0][2],
            QUESTION_TYPES.index(item[0][3]),
        ),
    ):
        long_rows.append([year, subject, chapter, kind, count])
    write_data_sheet(
        wb,
        "四维长表",
        "年份 × 科目 × 章节 × 题型（非零组合）",
        "这是最贴合统计分析/透视表的数据结构；每一行表示一个非零组合。",
        ["年份", "科目", "教材章节", "题型", "题目数量"],
        long_rows,
        {1: 10, 2: 32, 3: 42, 4: 16, 5: 12},
        "LongSummary",
        (5, 5),
    )

    # 完整矩阵：所有年份×所有目录章节，包括零。
    matrix_rows: list[list[object]] = []
    nonzero_rows: list[list[object]] = []
    for year in years:
        for entry in catalog:
            values = [
                question_counter[(year, entry["科目"], entry["章节名称"], kind)]
                for kind in QUESTION_TYPES
            ]
            result = [year, entry["科目"], entry["章节名称"], *values, sum(values)]
            matrix_rows.append(result)
            if sum(values):
                nonzero_rows.append(result)
    matrix_headers = ["年份", "科目", "教材章节", *QUESTION_TYPES, "合计"]
    matrix_widths = {1: 9, 2: 32, 3: 43, **{index: 12 for index in range(4, 14)}}
    write_data_sheet(
        wb,
        "完整矩阵",
        "完整分布矩阵（含零）",
        "逐年列出四本指定教材的每一章及真题涉及的拓展专题；0表示该年该章该题型未出现。",
        matrix_headers,
        matrix_rows,
        matrix_widths,
        "FullMatrix",
        (4, 13),
    )
    wb["完整矩阵"].tabColor = "5B9BD5"
    write_data_sheet(
        wb,
        "有题汇总",
        "有题章节汇总（剔除全零行）",
        "用于快速查看命题落点；合计仍与逐题明细一致。",
        matrix_headers,
        nonzero_rows,
        matrix_widths,
        "NonZeroMatrix",
        (4, 13),
    )

    # 年度科目汇总。
    year_subject_rows: list[list[object]] = []
    for year in years:
        for subject in SUBJECTS:
            values = [
                sum(
                    count
                    for (row_year, row_subject, _chapter, row_kind), count in question_counter.items()
                    if row_year == year and row_subject == subject and row_kind == kind
                )
                for kind in QUESTION_TYPES
            ]
            if sum(values):
                year_subject_rows.append([year, subject, *values, sum(values)])
    subject_headers = ["年份", "科目", *QUESTION_TYPES, "合计"]
    write_data_sheet(
        wb,
        "年度科目汇总",
        "年度 × 科目 × 题型汇总",
        "每一行是某年某主科目的题型分布；跨教材拓展科目保持独立。",
        subject_headers,
        year_subject_rows,
        {1: 9, 2: 34, **{index: 12 for index in range(3, 13)}},
        "YearSubject",
        (3, 12),
    )

    # 章节目录。
    catalog_rows = [[row["科目"], row["章节序号"], row["章节名称"], row["来源"]] for row in catalog]
    write_data_sheet(
        wb,
        "章节目录",
        "章节归类目录",
        "四本指定教材保留原章名；拓展专题用于承接旧真题中教材未覆盖的内容。",
        ["科目", "章节序号", "章节名称", "来源"],
        catalog_rows,
        {1: 34, 2: 12, 3: 48, 4: 48},
        "ChapterCatalog",
    )

    # 核对结果。
    source_year = Counter(int(row["年份"]) for row in questions)
    matrix_year = Counter()
    for row in matrix_rows:
        matrix_year[int(row[0])] += int(row[-1])
    checks: list[list[object]] = []
    for year in years:
        checks.append([f"{year}年题数一致", source_year[year], matrix_year[year], "PASS" if source_year[year] == matrix_year[year] else "FAIL"])
    checks.extend(
        [
            ["逐题明细总数", 255, len(questions), "PASS" if len(questions) == 255 else "FAIL"],
            ["题目ID无重复", len(questions), len({row["题目ID"] for row in questions}), "PASS" if len(questions) == len({row["题目ID"] for row in questions}) else "FAIL"],
            ["必填归类无空值", 0, sum(not row["主科目"] or not row["教材主章节"] for row in questions), "PASS" if all(row["主科目"] and row["教材主章节"] for row in questions) else "FAIL"],
            ["四维长表合计", len(questions), sum(row[-1] for row in long_rows), "PASS" if sum(row[-1] for row in long_rows) == len(questions) else "FAIL"],
            ["完整矩阵合计", len(questions), sum(row[-1] for row in matrix_rows), "PASS" if sum(row[-1] for row in matrix_rows) == len(questions) else "FAIL"],
            ["年度科目汇总合计", len(questions), sum(row[-1] for row in year_subject_rows), "PASS" if sum(row[-1] for row in year_subject_rows) == len(questions) else "FAIL"],
        ]
    )
    write_data_sheet(
        wb,
        "核对结果",
        "统计一致性核对",
        "所有汇总均由逐题明细复算；只有全部PASS才输出最终文件。",
        ["核对项目", "预期值", "实际值", "结果"],
        checks,
        {1: 34, 2: 16, 3: 16, 4: 12},
        "ValidationChecks",
    )
    for cell in wb["核对结果"]["D"]:
        if cell.value == "PASS":
            cell.fill = PatternFill("solid", fgColor=PALE_GREEN)
            cell.font = Font(bold=True, color="006100")
        elif cell.value == "FAIL":
            cell.fill = PatternFill("solid", fgColor=PALE_RED)
            cell.font = Font(bold=True, color="9C0006")
    if any(row[-1] != "PASS" for row in checks):
        raise ValueError(f"validation failed: {checks}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)

    # Reload once to catch damaged workbook relationships/tables.
    checked = load_workbook(args.output, data_only=False)
    expected_sheets = [
        "统计说明",
        "逐题明细",
        "四维长表",
        "完整矩阵",
        "有题汇总",
        "年度科目汇总",
        "章节目录",
        "核对结果",
    ]
    if checked.sheetnames != expected_sheets:
        raise ValueError(f"unexpected sheets: {checked.sheetnames}")
    if checked["逐题明细"].max_row != len(questions) + 4:
        raise ValueError("detail sheet row count mismatch")
    checked.close()
    print(f"output={args.output}")
    print(f"questions={len(questions)}")
    print(f"long_rows={len(long_rows)} full_matrix_rows={len(matrix_rows)} nonzero_rows={len(nonzero_rows)}")
    print("validation=PASS")


if __name__ == "__main__":
    main()
