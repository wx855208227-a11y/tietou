from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from build_baoming_v10 import CHAPTERS, D, OUTPUT, P


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
        match = re.match(
            r"(?:\d+\. )?\*\*【(?:共用|本题补充)】\*\*\s+"
            r"(.+?)\s*\*\*【名词解释：([^】]+)】\*\*$",
            line,
        )
        if match:
            definition_variants[match.group(2)].add(match.group(1).strip())

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
    assert not re.search(r"^(?:\d+\. )?(?:\*\*【(?:共用|本题补充)】\*\*\s+)?\*\*【名词解释：", text, re.M)
    assert "【加分项】" not in text
    assert P["心理学研究对象"] == "其研究对象主要包括**心理过程**和**人格**。"
    assert text.count(P["心理学研究对象"]) == 3
    assert "简述心理学的**含义**与**研究对象**" not in text

    module_uses = Counter(
        module
        for item in questions
        for module in (*item.leads, *item.points, *item.bonus_points)
    )
    expected_common = sum(count for count in module_uses.values() if count > 1)
    expected_supplement = sum(count for count in module_uses.values() if count == 1)
    assert text.count("**【共用】**") == expected_common
    assert text.count("**【本题补充】**") == expected_supplement
    assert expected_common + expected_supplement == sum(module_uses.values())

    bonus_answers = sum(bool(item.bonus_points) for item in questions)
    assert text.count("**【整体加分】**") == bonus_answers
    point_bonus_expected = sum(
        count for module, count in module_uses.items() if "**【采分点加分】**" in module
    )
    assert text.count("**【采分点加分】**") == point_bonus_expected
    assert all(
        line.strip().endswith("**【采分点加分】**")
        for line in text.splitlines()
        if "【采分点加分】" in line
    )

    first_unit = CHAPTERS[0][1][0]
    first_question, second_question = first_unit.questions
    assert first_question.bonus_points == second_question.points
    first_capacity = len(plain("".join((*first_question.leads, *first_question.bonus_points))))
    second_capacity = len(plain("".join(second_question.points)))
    assert max(first_capacity, second_capacity) / min(first_capacity, second_capacity) < 1.25

    # Every answer must contain exactly the lead/point modules assigned to it.
    for unit in units:
        for item in unit.questions:
            assigned = (*item.leads, *item.points, *item.bonus_points)
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
        f"repeated_scoring_modules={len(repeated_points)} "
        f"common_labels={expected_common} supplement_labels={expected_supplement} "
        f"answer_bonus_blocks={bonus_answers} point_bonus_uses={point_bonus_expected}"
    )


if __name__ == "__main__":
    main()
