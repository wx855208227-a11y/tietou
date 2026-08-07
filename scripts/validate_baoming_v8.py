from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from build_baoming_v8 import CHAPTERS, D, OUTPUT, P


FORBIDDEN = (
    "答题思路",
    "到此停笔",
    "调用公式",
    "背诵检索串",
    "背诵主线",
    "综合答案",
    "综合母答案",
)


def plain(markdown: str) -> str:
    return re.sub(r"\*+", "", markdown)


def main() -> None:
    text = OUTPUT.read_text(encoding="utf-8")
    units = [unit for _, chapter_units in CHAPTERS for unit in chapter_units]
    questions = [item for unit in units for item in unit.questions]

    assert len(CHAPTERS) == 3
    assert len(units) == 33
    assert len(questions) == 62
    assert sum(item.kind == "简答" for item in questions) == 56
    assert sum(item.kind == "论述" for item in questions) == 6
    assert text.count("\n# 第一章 ") == 1
    assert text.count("\n# 第二章 ") == 1
    assert text.count("\n# 第三章 ") == 1
    assert len(re.findall(r"^## [一二三四五六七八九十]+、", text, re.M)) == 33
    assert len(re.findall(r"^### 押题\d+【(?:简答|论述)】", text, re.M)) == 62
    assert text.count("#### 答案") == 62

    for forbidden in FORBIDDEN:
        assert forbidden not in text, forbidden
    assert "_" not in text, "Markdown contains underscore/underline syntax"
    assert "<u>" not in text.lower(), "Markdown contains HTML underline"

    definition_variants: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        match = re.match(r"(?:\d+\. )?\*\*【名词解释：([^】]+)】\*\*\s+(.+)$", line)
        if match:
            definition_variants[match.group(1)].add(match.group(2).strip())

    assert definition_variants, "No definitions found"
    assert all(len(variants) == 1 for variants in definition_variants.values())
    assert set(definition_variants) == set(D)
    for name, variants in definition_variants.items():
        body = plain(next(iter(variants)))
        assert len(body) >= 20, f"Definition too short: {name} ({len(body)})"

    expected_psychology = (
        "心理学是研究人的行为和心理活动规律的中间科学，"
        "兼有自然科学和社会科学的性质。"
    )
    assert expected_psychology in plain(text)

    # Every answer must contain exactly the lead/point modules assigned to it.
    for unit in units:
        for item in unit.questions:
            assigned = (*item.leads, *item.points)
            assert assigned, f"Empty answer: {unit.title} / {item.stem}"
            for module in assigned:
                assert module in text, f"Missing module: {module[:40]}"

    # Shared definitions and scoring modules are emitted from single canonical
    # dictionaries. Repeated use must therefore preserve the exact text.
    repeated_definitions = {
        name: len(re.findall(re.escape(value), text))
        for name, value in D.items()
        if len(re.findall(re.escape(value), text)) > 1
    }
    repeated_points = {
        name: text.count(value)
        for name, value in P.items()
        if text.count(value) > 1
    }
    assert repeated_definitions, "Expected repeated definitions were not found"
    assert repeated_points, "Expected repeated scoring modules were not found"

    print(
        "PASS "
        f"chapters={len(CHAPTERS)} units={len(units)} questions={len(questions)} "
        f"definition_labels={sum(len(re.findall(re.escape(v), text)) for v in D.values())} "
        f"unique_definitions={len(definition_variants)} "
        f"repeated_definition_concepts={len(repeated_definitions)} "
        f"repeated_scoring_modules={len(repeated_points)}"
    )


if __name__ == "__main__":
    main()
