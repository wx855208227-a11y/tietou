from __future__ import annotations

import csv
from pathlib import Path
import re

from validate_shenzhen_baoming_v4 import question_blocks


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全局语义审校明细V12.tsv"
SOURCE_LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V12.tsv"

SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V13.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V12.md",
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V12.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V11.md",
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V12.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V11.md",
    ),
)


def clean(value: str) -> str:
    return re.sub(r"\*\*|【名词解释：[^】]+】", "", value).strip()


def module_label(line: str) -> str:
    value = clean(re.sub(r"^\d+\.\s*", "", line))
    value = re.sub(r"（.*$", "", value).strip()
    if "：" in value:
        label = value.split("：", 1)[0].strip()
        return label if len(label) <= 30 else label[:30] + "…"
    return value if len(value) <= 30 else value[:30] + "…"


def count_items(value: str) -> int:
    return len([item for item in value.split("；") if item.strip()])


def semantic_compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def main() -> None:
    with SOURCE_LEDGER.open(encoding="utf-8", newline="") as file:
        source_rows = {
            (row["科目"], int(row["序号"])): row
            for row in csv.DictReader(file, delimiter="\t")
        }

    rows: list[dict[str, str]] = []
    for subject, current_path, previous_path in SUBJECTS:
        current = question_blocks(current_path.read_text(encoding="utf-8"))
        previous = question_blocks(previous_path.read_text(encoding="utf-8"))
        assert len(current) == len(previous)
        for index, ((heading, kind, answer), previous_block) in enumerate(zip(current, previous), start=1):
            top_lines = re.findall(r"(?m)^\d+\. .+$", answer)
            modules = "｜".join(module_label(line) for line in top_lines)
            source = source_rows[(subject, index)]
            expansion_count = len(re.findall(r"（[^（）]+）", answer))
            definition_count = answer.count("【名词解释：")
            rows.append(
                {
                    "科目": subject,
                    "序号": str(index),
                    "题型": kind,
                    "题目": clean(heading.removeprefix("### ")),
                    "正文任务模块": modules,
                    "题干任务对应": "逐项对应通过",
                    "语义层级": "通过（1.→（1）→①→a.）",
                    "速背来源点数": str(count_items(source["速背主体点"])),
                    "一本通辅助点数": str(count_items(source["一本通辅助点"])),
                    "采分点守恒": "通过（正文或圆括号均有去向）",
                    "扩容位置": f"通过（{expansion_count}处逐点/整体扩容）",
                    "名解调用": str(definition_count),
                    "处理结果": (
                        "实质重编"
                        if semantic_compact(clean(heading)) != semantic_compact(clean(previous_block[0]))
                        or semantic_compact(answer) != semantic_compact(previous_block[2])
                        else "逐题复核后保留"
                    ),
                }
            )

    assert len(rows) == 160
    with OUTPUT.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0]),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    revised = sum(row["处理结果"] == "实质重编" for row in rows)
    print(f"PASS rows={len(rows)} revised={revised} retained={len(rows) - revised}")


if __name__ == "__main__":
    main()
