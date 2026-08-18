#!/usr/bin/env python3
"""Extract dated questions from the HF Shenzhen University true-question TSV."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


EXAM_HEADER_RE = re.compile(r"(20\d{2})年深圳大学347应用心理硕士初试真题(?!参考答案|真题解析|解析)")
ANSWER_HEADER_RE = re.compile(r"20\d{2}年深圳大学347应用心理硕士初试真题(?:参考答案|真题解析|解析)")
TYPE_RE = re.compile(r"^[一二三四五六七八九十]+、\s*(单选题|选择题|判断题|名词解释|简答题|论述题|综合运用题|综合题)")
QUESTION_RE = re.compile(r"^(\d{1,3})[.．、]?\s*(.+)$")
OPTION_RE = re.compile(r"^[A-HＡ-Ｈ][.．、]?\s*")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.source.open(encoding="utf-8", newline="") as stream:
        source_rows = list(csv.DictReader(stream, delimiter="\t"))

    results: list[dict[str, str]] = []
    year = ""
    question_type = ""
    active = False
    current: dict[str, str] | None = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            current["题目全文"] = "\n".join(part for part in current.pop("_parts").split("\u0000") if part)
            results.append(current)
            current = None

    for row in source_rows:
        text = row["text"].strip()
        header = EXAM_HEADER_RE.search(text)
        if header:
            flush()
            year = header.group(1)
            question_type = ""
            active = True
            continue
        if ANSWER_HEADER_RE.search(text):
            flush()
            active = False
            continue
        if not active or not text:
            continue

        type_match = TYPE_RE.match(text)
        if type_match:
            flush()
            question_type = type_match.group(1)
            continue
        if not question_type:
            continue

        question_match = QUESTION_RE.match(text)
        # A new numbered question normally starts with a non-option stem.  When
        # a long composite item contains subnumbers, the document style remains
        # body text; preserve them inside the active question if numbering does
        # not advance plausibly.
        if question_match and not OPTION_RE.match(text):
            number = int(question_match.group(1))
            previous = int(current["题号"]) if current is not None else 0
            plausible = current is None or number == previous + 1 or number == 1
            if plausible:
                flush()
                stem = question_match.group(2).strip()
                current = {
                    "年份": year,
                    "题型": question_type,
                    "题号": str(number),
                    "题干": stem,
                    "原始定位": row["locator"],
                    "_parts": stem,
                }
                continue

        if current is not None:
            current["_parts"] += "\u0000" + text

    flush()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(results)

    counts: dict[str, int] = {}
    for row in results:
        counts[row["年份"]] = counts.get(row["年份"], 0) + 1
    print(f"questions={len(results)}")
    for exam_year, count in sorted(counts.items()):
        print(f"{exam_year}\t{count}")


if __name__ == "__main__":
    main()
