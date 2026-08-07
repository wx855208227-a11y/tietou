from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from build_baoming_v11 import CHAPTERS, D, OUTPUT, P


V10_OUTPUT = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_共用补充双加分版V10.md")


FORBIDDEN = (
    "答题思路",
    "到此停笔",
    "调用公式",
    "背诵检索串",
    "背诵主线",
    "综合答案",
    "综合母答案",
    "【共用】",
    "【本题补充】",
)


def plain(markdown: str) -> str:
    return re.sub(r"[\*_]+", "", markdown)


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
    assert "<u>" not in text.lower(), "Markdown contains HTML underline"

    definition_variants: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        match = re.match(
            r"(?:\d+\. )?_?(.+?)\s*\*\*【名词解释：([^】]+)】\*\*_?$",
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
    assert not re.search(r"^(?:\d+\. )?_?\*\*【名词解释：", text, re.M)
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
    lines = text.splitlines()
    expected_lines: Counter[str] = Counter()
    for item in questions:
        for module in item.leads:
            expected_lines[module if module_uses[module] > 1 else f"_{module}_"] += 1
        for point_number, module in enumerate(item.points, start=1):
            rendered = module if module_uses[module] > 1 else f"_{module}_"
            expected_lines[f"{point_number}. {rendered}"] += 1
        first_bonus_number = len(item.points) + 1
        for point_number, module in enumerate(item.bonus_points, start=first_bonus_number):
            rendered = module if module_uses[module] > 1 else f"_{module}_"
            expected_lines[f"{point_number}. {rendered}"] += 1
    actual_lines = Counter(lines)
    assert all(actual_lines[line] == count for line, count in expected_lines.items())
    italic_module_lines = sum(
        count
        for line, count in actual_lines.items()
        if re.match(r"^(?:\d+\. )?_.+_$", line)
    )
    assert italic_module_lines == expected_supplement
    assert expected_common + expected_supplement == sum(module_uses.values())

    # V11只替换共享关系的显示方式，不改动V10题目与答案正文。
    v10 = V10_OUTPUT.read_text(encoding="utf-8")
    v10 = v10.replace("前三章·共用补充双加分版V10", "前三章·正斜体区分版V11")
    v10 = v10.replace("**【共用】** ", "").replace("**【本题补充】** ", "")
    assert plain(v10) == plain(text)

    bonus_answers = sum(bool(item.bonus_points) for item in questions)
    assert text.count("**【整体加分】**") == bonus_answers
    point_bonus_expected = sum(
        count for module, count in module_uses.items() if "**【采分点加分】**" in module
    )
    assert text.count("**【采分点加分】**") == point_bonus_expected
    assert all(
        line.strip().rstrip("_").endswith("**【采分点加分】**")
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
        f"roman_module_uses={expected_common} italic_module_uses={expected_supplement} "
        f"answer_bonus_blocks={bonus_answers} point_bonus_uses={point_bonus_expected}"
    )


if __name__ == "__main__":
    main()
