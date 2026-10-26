#!/usr/bin/env python3
"""Build the concise Shenzhen exam distribution workbook from classified questions.

The layout follows the user-supplied sample: one sheet per subject, with an
all-years chapter summary on the left and a year summary on the right.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font


GP = "普通心理学（第6版）"
EP = "实验心理学（第2版）"
MEAS = "心理与教育测量（第4版）"
STAT = "现代心理与教育统计学（第5版）"
SOC = "社会心理学（跨教材拓展）"
ABN = "变态与咨询心理学（跨教材拓展）"
ORG = "管理与组织心理学（跨教材拓展）"
MIX = "跨科目综合"

SHEET_GROUPS = [
    ("统计", [STAT]),
    ("实验", [EP]),
    ("测量", [MEAS]),
    ("普心", [GP]),
    ("拓展（旧题）", [SOC, ABN, ORG, MIX]),
]

TYPE_GROUPS = [
    ("选择/判断/填空", {"单选题", "判断题", "填空题"}),
    ("名词解释", {"名词解释"}),
    ("简答/论述题", {"简答题", "论述题"}),
    ("实验/案例/综合题", {"实验设计题", "案例分析题", "综合应用题"}),
]
TYPE_TO_GROUP = {
    question_type: group_name
    for group_name, question_types in TYPE_GROUPS
    for question_type in question_types
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def chapter_rows(
    catalog: list[dict[str, str]], subjects: list[str], *, extension: bool
) -> list[tuple[str, str, str]]:
    selected = [row for row in catalog if row["科目"] in subjects]

    def key(row: dict[str, str]) -> tuple[int, int, str]:
        subject_rank = subjects.index(row["科目"])
        sequence = row["章节序号"]
        chapter_rank = int(sequence) if sequence.isdigit() else 999
        return subject_rank, chapter_rank, row["章节名称"]

    selected.sort(key=key)
    rows: list[tuple[str, str, str]] = []
    for row in selected:
        if extension:
            short_subject = row["科目"].replace("心理学（跨教材拓展）", "")
            label = f"{short_subject}｜{row['章节名称']}"
        else:
            label = row["章节名称"]
        rows.append((row["科目"], row["章节名称"], label))
    return rows


def grouped_type(question_type: str) -> str:
    try:
        return TYPE_TO_GROUP[question_type]
    except KeyError as exc:
        raise ValueError(f"未纳入简明表的题型：{question_type}") from exc


def write_subject_sheet(
    wb: Workbook,
    sheet_name: str,
    subjects: list[str],
    chapters: list[tuple[str, str, str]],
    questions: list[dict[str, str]],
    years: list[int],
) -> None:
    ws = wb.create_sheet(sheet_name)
    ws.merge_cells("A1:F2")
    ws["A1"] = "按专题归纳" if len(subjects) > 1 else "分章归纳"
    ws.merge_cells("H1:M2")
    ws["H1"] = "按年份归纳"

    headers = ["章节", *[name for name, _ in TYPE_GROUPS], "总计"]
    year_headers = ["年份", *[f"{name}数量" for name, _ in TYPE_GROUPS], "题目总量"]
    for column, value in enumerate(headers, start=1):
        ws.cell(3, column, value)
    for column, value in enumerate(year_headers, start=8):
        ws.cell(3, column, value)

    subject_questions = [row for row in questions if row["主科目"] in subjects]
    chapter_counts = Counter(
        (row["主科目"], row["教材主章节"], grouped_type(row["题型"]))
        for row in subject_questions
    )
    for row_number, (subject, chapter, label) in enumerate(chapters, start=4):
        values = [chapter_counts[(subject, chapter, name)] for name, _ in TYPE_GROUPS]
        ws.cell(row_number, 1, label)
        for column, value in enumerate(values, start=2):
            ws.cell(row_number, column, value)
        ws.cell(row_number, 6, sum(values))

    year_counts = Counter(
        (int(row["年份"]), grouped_type(row["题型"])) for row in subject_questions
    )
    for row_number, year in enumerate(years, start=4):
        values = [year_counts[(year, name)] for name, _ in TYPE_GROUPS]
        ws.cell(row_number, 8, year)
        for column, value in enumerate(values, start=9):
            ws.cell(row_number, column, value)
        ws.cell(row_number, 13, sum(values))

    max_row = max(3 + len(chapters), 3 + len(years))
    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=13):
        for cell in row:
            cell.font = Font(name="等线", size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    widths = {
        "A": 42 if len(subjects) == 1 else 34,
        "B": 15,
        "C": 11,
        "D": 13,
        "E": 17,
        "F": 8,
        "G": 3,
        "H": 8,
        "I": 18,
        "J": 13,
        "K": 15,
        "L": 19,
        "M": 10,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width
    ws.row_dimensions[3].height = 33
    ws.sheet_view.showGridLines = True
    ws.freeze_panes = "A4"

    left_total = sum(ws.cell(row, 6).value or 0 for row in range(4, 4 + len(chapters)))
    right_total = sum(ws.cell(row, 13).value or 0 for row in range(4, 4 + len(years)))
    expected = len(subject_questions)
    if left_total != expected or right_total != expected:
        raise AssertionError(
            f"{sheet_name}汇总不一致：章节={left_total}，年份={right_total}，逐题={expected}"
        )


def validate_output(output: Path, expected_questions: int, years: list[int]) -> None:
    wb = load_workbook(output, data_only=True)
    expected_sheets = [name for name, _ in SHEET_GROUPS]
    if wb.sheetnames != expected_sheets:
        raise AssertionError(f"工作表不一致：{wb.sheetnames}")

    workbook_total = 0
    year_totals = Counter()
    for ws in wb.worksheets:
        sheet_total = 0
        for row in range(4, ws.max_row + 1):
            if ws.cell(row, 1).value:
                sheet_total += ws.cell(row, 6).value or 0
        workbook_total += sheet_total
        for offset, year in enumerate(years, start=4):
            if ws.cell(offset, 8).value != year:
                raise AssertionError(f"{ws.title}年份行错位：{ws.cell(offset, 8).value}")
            year_totals[year] += ws.cell(offset, 13).value or 0

    if workbook_total != expected_questions:
        raise AssertionError(f"工作簿合计{workbook_total}，应为{expected_questions}")
    if sum(year_totals.values()) != expected_questions:
        raise AssertionError(f"年度合计{sum(year_totals.values())}，应为{expected_questions}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    questions = read_tsv(args.questions)
    catalog = read_tsv(args.catalog)
    years = sorted({int(row["年份"]) for row in questions})

    unknown_types = sorted({row["题型"] for row in questions} - set(TYPE_TO_GROUP))
    if unknown_types:
        raise ValueError(f"存在未映射题型：{unknown_types}")
    unknown_subjects = sorted(
        {row["主科目"] for row in questions}
        - {subject for _, subjects in SHEET_GROUPS for subject in subjects}
    )
    if unknown_subjects:
        raise ValueError(f"存在未映射科目：{unknown_subjects}")

    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.title = "深圳大学2019—2026历年真题分布表（简明版）"
    wb.properties.subject = "按科目展示章节累计与年份累计"
    wb.properties.creator = "tietou_review"

    for sheet_name, subjects in SHEET_GROUPS:
        chapters = chapter_rows(catalog, subjects, extension=len(subjects) > 1)
        write_subject_sheet(wb, sheet_name, subjects, chapters, questions, years)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    validate_output(args.output, len(questions), years)

    year_counts = Counter(int(row["年份"]) for row in questions)
    print(f"output={args.output}")
    print(f"questions={len(questions)}")
    print("year_counts=" + ",".join(f"{year}:{year_counts[year]}" for year in years))
    print("sheets=" + ",".join(name for name, _ in SHEET_GROUPS))


if __name__ == "__main__":
    main()
