#!/usr/bin/env python3
"""Extract every original Shenzhen University question from the HF DOCX.

The source interleaves each year's original paper and answer analysis.  Only the
original-paper range is counted.  One row represents one top-level numbered
question; subitems remain attached to their parent question.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from docx import Document


EXAM_RE = re.compile(r"^(20\d{2})年深圳大学347应用心理硕士初试真题$")
ANSWER_RE = re.compile(
    r"^20\d{2}年深圳大学347应用心理硕士初试真题(?:参考答案|真题解析|解析|真题真题解析)"
)
TYPE_RE = re.compile(
    r"^[一二三四五六七八九十]+[、.．]\s*"
    r"(单选题|选择题|判断题|填空题?|名词解释|简答题?|论述题?|"
    r"综合运用题|综合应用题|综合题|案例分析题|实验设计题?|实验题)"
)
QUESTION_RE = re.compile(r"^(\d{1,3})[.．、]?\s*(.+)$")
OPTION_RE = re.compile(r"^[A-HＡ-Ｈ0][)）.．、]\s*")

TYPE_NAMES = {
    "选择题": "单选题",
    "填空": "填空题",
    "简答": "简答题",
    "论述": "论述题",
    "实验题": "实验设计题",
    "实验设计": "实验设计题",
    "综合运用题": "综合应用题",
    "综合题": "综合应用题",
}


def clean(text: str) -> str:
    return " ".join(text.replace("\u200e", "").replace("\xa0", " ").split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    document = Document(args.source)
    results: list[dict[str, str]] = []
    year = ""
    question_type = ""
    active = False
    current: dict[str, object] | None = None

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        parts = current.pop("_parts")
        assert isinstance(parts, list)
        current["题目全文"] = "\n".join(str(part) for part in parts)
        results.append({key: str(value) for key, value in current.items()})
        current = None

    for paragraph_index, paragraph in enumerate(document.paragraphs, start=1):
        text = clean(paragraph.text)
        if not text:
            continue

        exam_match = EXAM_RE.match(text)
        if exam_match:
            flush()
            year = exam_match.group(1)
            question_type = ""
            active = True
            continue
        if ANSWER_RE.match(text):
            flush()
            active = False
            question_type = ""
            continue
        if not active:
            continue

        type_match = TYPE_RE.match(text)
        if type_match:
            flush()
            raw_type = type_match.group(1)
            question_type = TYPE_NAMES.get(raw_type, raw_type)
            continue
        if not question_type:
            continue

        question_match = QUESTION_RE.match(text)
        if question_match and not OPTION_RE.match(text):
            number = int(question_match.group(1))
            stem = question_match.group(2).strip()
            flush()
            current = {
                "题目ID": f"{year}-{question_type}-{number:03d}",
                "年份": year,
                "题型": question_type,
                "题号": str(number),
                "题干": stem,
                "原始定位": f"DOCX段落{paragraph_index}",
                "_parts": [stem],
            }
            continue

        if current is None:
            # A few one-question sections (notably 2019 综合运用题) omit "1.".
            current = {
                "题目ID": f"{year}-{question_type}-001",
                "年份": year,
                "题型": question_type,
                "题号": "1",
                "题干": text,
                "原始定位": f"DOCX段落{paragraph_index}",
                "_parts": [text],
            }
        else:
            parts = current["_parts"]
            assert isinstance(parts, list)
            parts.append(text)

    flush()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["题目ID", "年份", "题型", "题号", "题干", "原始定位", "题目全文"]
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(results)

    by_year: dict[str, int] = {}
    by_year_type: dict[tuple[str, str], int] = {}
    for row in results:
        by_year[row["年份"]] = by_year.get(row["年份"], 0) + 1
        key = (row["年份"], row["题型"])
        by_year_type[key] = by_year_type.get(key, 0) + 1

    print(f"questions={len(results)}")
    for exam_year, count in sorted(by_year.items()):
        detail = ", ".join(
            f"{kind}={kind_count}"
            for (row_year, kind), kind_count in sorted(by_year_type.items())
            if row_year == exam_year
        )
        print(f"{exam_year}\t{count}\t{detail}")


if __name__ == "__main__":
    main()
