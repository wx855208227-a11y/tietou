#!/usr/bin/env python3
"""Build the user-facing workbook from the 255-row re-audit trail."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from build_sample_layout_workbook import (
    OFFICIAL_SUBJECTS,
    SHEET_GROUPS,
    STAT,
    SUBJECT_LABELS,
    chapter_rows,
    read_tsv,
    write_subject_sheet,
)


def canonical_rows(reviewed: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for row in reviewed:
        if row["是否纳入四本教材统计"] != "是":
            continue
        if row["题目ID"] == "2023-综合应用题-001":
            split_units = [
                (
                    "A",
                    "第八章 假设检验",
                    "独立样本t检验：比较两个性别群体的幸福感差异",
                ),
                (
                    "B",
                    "第九章 方差分析",
                    "方差分析：比较不同年龄或不同城市人群的幸福感差异",
                ),
                (
                    "C",
                    "第五章 相关关系",
                    "相关分析：检验幸福感与人均收入、亲子关系之间的相关",
                ),
                (
                    "D",
                    "第十二章 线性回归",
                    "线性回归：用人均收入、亲子关系等变量预测幸福感",
                ),
            ]
            for suffix, chapter, topic in split_units:
                copied = dict(row)
                copied["题目ID"] = f"{row['题目ID']}-{suffix}"
                copied["主科目"] = STAT
                copied["教材主章节"] = chapter
                copied["核心考点"] = topic
                copied["次要考点或跨章节"] = "同一综合应用题按四种统计方法拆分；源题数量仍为1道"
                copied["题目全文"] = row["题目全文"].strip()
                copied["复核依据"] = (
                    f"依据用户确认，本统计单元对应{chapter}；"
                    "同一源题另拆为t检验、方差分析、相关和线性回归共4个统计单元。"
                )
                result.append(copied)
            continue
        copied = dict(row)
        copied["主科目"] = row["复核科目"]
        copied["教材主章节"] = row["复核章节"]
        copied["核心考点"] = row["复核核心考点"]
        result.append(copied)
    return result


def question_number_key(value: str) -> tuple[int, str]:
    return (int(value), value) if value.isdigit() else (999, value)


def ordered_questions(
    questions: list[dict[str, str]], catalog: list[dict[str, str]]
) -> list[dict[str, str]]:
    chapter_order = {
        (row["科目"], row["章节名称"]): int(row["章节序号"])
        for row in catalog
        if row["科目"] in OFFICIAL_SUBJECTS and row["章节序号"].isdigit()
    }
    subject_order = {
        subject: index
        for index, (_, subjects) in enumerate(SHEET_GROUPS)
        for subject in subjects
    }
    return sorted(
        questions,
        key=lambda row: (
            -int(row["年份"]),
            subject_order[row["主科目"]],
            chapter_order[(row["主科目"], row["教材主章节"])],
            row["题型"],
            question_number_key(row["题号"]),
        ),
    )


def style_header(ws, row_number: int, values: list[str]) -> None:
    for column, value in enumerate(values, start=1):
        cell = ws.cell(row_number, column, value)
        cell.font = Font(name="等线", size=10, bold=True)
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def write_detail_sheet(
    wb: Workbook,
    questions: list[dict[str, str]],
    catalog: list[dict[str, str]],
) -> None:
    ws = wb.create_sheet("真题明细")
    headers = [
        "年份",
        "科目",
        "教材章节",
        "核心考点",
        "题型",
        "题号",
        "真题原文",
    ]
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    ws.cell(1, 1, "真题明细（可按年份、科目、教材章节、核心考点和题型筛选）")
    ws.cell(1, 1).font = Font(name="等线", size=11, bold=True)
    ws.cell(1, 1).alignment = Alignment(horizontal="left", vertical="center")
    style_header(ws, 2, headers)

    for row_number, row in enumerate(ordered_questions(questions, catalog), start=3):
        values = [
            int(row["年份"]),
            SUBJECT_LABELS[row["主科目"]],
            row["教材主章节"],
            row["核心考点"],
            row["题型"],
            row["题号"],
            row["题目全文"].strip(),
        ]
        for column, value in enumerate(values, start=1):
            cell = ws.cell(row_number, column, value)
            cell.font = Font(name="等线", size=9)
            cell.alignment = Alignment(
                horizontal="left" if column in {3, 4, 7} else "center",
                vertical="top",
                wrap_text=column in {3, 4, 7},
            )
        ws.row_dimensions[row_number].height = 44

    ws.auto_filter.ref = f"A2:G{2 + len(questions)}"
    ws.freeze_panes = "A3"
    ws.sheet_view.showGridLines = True
    for column, width in {
        "A": 8,
        "B": 8,
        "C": 34,
        "D": 28,
        "E": 12,
        "F": 8,
        "G": 80,
    }.items():
        ws.column_dimensions[column].width = width
    ws.row_dimensions[1].height = 24
    ws.row_dimensions[2].height = 30


def validate_output(
    output: Path,
    questions: list[dict[str, str]],
    years: list[int],
) -> None:
    wb = load_workbook(output, data_only=True)
    expected_sheets = [name for name, _ in SHEET_GROUPS] + ["真题明细"]
    if wb.sheetnames != expected_sheets:
        raise AssertionError(f"工作表不一致：{wb.sheetnames}")

    summary_total = 0
    year_totals = Counter()
    for ws in wb.worksheets[:4]:
        for row_number in range(4, ws.max_row + 1):
            if ws.cell(row_number, 1).value:
                summary_total += ws.cell(row_number, 6).value or 0
        for offset, year in enumerate(years, start=4):
            if ws.cell(offset, 8).value != year:
                raise AssertionError(f"{ws.title}年份行错位：{ws.cell(offset, 8).value}")
            year_totals[year] += ws.cell(offset, 13).value or 0
    if summary_total != len(questions) or sum(year_totals.values()) != len(questions):
        raise AssertionError(
            f"汇总不一致：章节={summary_total}，年份={sum(year_totals.values())}，逐题={len(questions)}"
        )

    detail = wb["真题明细"]
    expected_headers = ["年份", "科目", "教材章节", "核心考点", "题型", "题号", "真题原文"]
    actual_headers = [detail.cell(2, column).value for column in range(1, 8)]
    detail_count = sum(
        1 for row in range(3, detail.max_row + 1) if detail.cell(row, 1).value
    )
    if actual_headers != expected_headers or detail_count != len(questions):
        raise AssertionError(
            f"真题明细异常：headers={actual_headers}，rows={detail_count}"
        )
    if detail.auto_filter.ref != f"A2:G{2 + len(questions)}":
        raise AssertionError(f"真题明细筛选范围异常：{detail.auto_filter.ref}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reviewed = read_tsv(args.questions)
    questions = canonical_rows(reviewed)
    catalog = read_tsv(args.catalog)
    years = sorted({int(row["年份"]) for row in questions})

    valid_chapters = {
        (row["科目"], row["章节名称"])
        for row in catalog
        if row["科目"] in OFFICIAL_SUBJECTS
    }
    invalid = [
        row["题目ID"]
        for row in questions
        if (row["主科目"], row["教材主章节"]) not in valid_chapters
    ]
    if invalid:
        raise AssertionError(f"纳入题使用了目录外章节：{invalid}")

    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.title = "深圳大学2019—2026历年真题分布表（逐题复核版）"
    wb.properties.subject = "按四本指定教材的实际讲授位置复核科目与章节"
    wb.properties.creator = "tietou_review"
    for sheet_name, subjects in SHEET_GROUPS:
        chapters = chapter_rows(catalog, subjects)
        write_subject_sheet(wb, sheet_name, subjects, chapters, questions, years)
    write_detail_sheet(wb, questions, catalog)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)
    validate_output(args.output, questions, years)

    print(f"output={args.output}")
    included_source_questions = sum(
        row["是否纳入四本教材统计"] == "是" for row in reviewed
    )
    print(f"included_source_questions={included_source_questions}")
    print(f"classification_units={len(questions)}")
    print(f"excluded_source_questions={len(reviewed) - included_source_questions}")


if __name__ == "__main__":
    main()
