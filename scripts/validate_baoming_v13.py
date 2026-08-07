from __future__ import annotations

import re

from build_baoming_v13 import (
    AUTONOMIC_COMPARISON,
    CHAPTERS,
    COGNITIVE_MAP_FUNCTION,
    FREUD_PERSONALITY_STRUCTURE,
    INTRANEURON_TRANSMISSION,
    OUTPUT,
    REFLEX_FUNCTION,
)


def plain(text: str) -> str:
    return re.sub(r"\*\*|【[^】]+】", "", text)


def question_base_text(item) -> str:
    return "".join(module.base for module in (*item.leads, *item.points))


def main() -> None:
    markdown = OUTPUT.read_text(encoding="utf-8")
    units = [unit for _, chapter_units in CHAPTERS for unit in chapter_units]
    questions = [item for unit in units for item in unit.questions]
    modules = [module for item in questions for module in (*item.leads, *item.points)]
    expansions = [
        optional
        for item in questions
        for optional in (
            *(module.expansion for module in (*item.leads, *item.points) if module.expansion),
            *item.final_expansions,
        )
    ]

    assert len(CHAPTERS) == 3
    assert len(units) == 33
    assert len(questions) == 62
    assert sum(item.kind == "简答" for item in questions) == 56
    assert sum(item.kind == "论述" for item in questions) == 6
    assert len(expansions) == 36

    forbidden = (
        "#### 答案",
        "【加分项】",
        "【采分点加分】",
        "【整体加分】",
        "【共用】",
        "【本题补充】",
        "答题思路",
        "背诵检索串",
        "到此停笔",
        "可按题干和时间灵活选写",
        "<br>",
    )
    assert all(term not in markdown for term in forbidden)
    assert not re.search(r"(?<!\*)\*(?!\*)", markdown), "学生版不得出现斜体标记"
    assert "答案" not in markdown, "学生版不显示‘答案’提示语"

    expansion_lines = [line for line in markdown.splitlines() if line.startswith("【扩容（选用）：")]
    assert len(expansion_lines) == 36
    assert all(line.startswith("【扩容（选用）：") and line.endswith("】") for line in expansion_lines)
    assert all(line.count("【扩容（选用）：") == 1 and line.count("】") == 1 for line in expansion_lines)
    assert not any(re.match(r"^\d+\.\s*【扩容", line) for line in expansion_lines)

    expected_definition = (
        "**心理学**是研究人的**行为**和**心理活动规律**的**中间科学**，"
        "兼有**自然科学和社会科学**的性质。**【名词解释：心理学】**"
    )
    psychology_definitions = [module.base for module in modules if "【名词解释：心理学】" in module.base]
    assert psychology_definitions
    assert set(psychology_definitions) == {expected_definition}

    first_question = CHAPTERS[0][1][0].questions[0]
    assert first_question.leads[0].base == expected_definition
    assert first_question.points == ()
    assert first_question.final_expansions == (
        "其研究对象主要包括**心理过程**和**人格**",
    )

    definitions: dict[str, set[str]] = {}
    pattern = re.compile(r"^(.*)\*\*【名词解释：([^】]+)】\*\*$")
    for module in modules:
        match = pattern.match(module.base)
        if match:
            definitions.setdefault(match.group(2), set()).add(match.group(1))
    conflicts = {name: texts for name, texts in definitions.items() if len(texts) > 1}
    assert not conflicts, conflicts

    # 多题重复的采分模块必须连同扩容一起逐字一致。
    for shared, expected_count in (
        (FREUD_PERSONALITY_STRUCTURE, 2),
        (INTRANEURON_TRANSMISSION, 2),
        (AUTONOMIC_COMPARISON, 2),
        (REFLEX_FUNCTION, 2),
        (COGNITIVE_MAP_FUNCTION, 2),
    ):
        assert modules.count(shared) == expected_count, shared

    # 题干明确要求举例时，例证必须位于基础正文，不能只藏在选用扩容中。
    example_questions = [item for item in questions if "结合实例" in plain(item.stem)]
    assert len(example_questions) == 4
    for item in example_questions:
        base = plain(question_base_text(item))
        assert "例" in base or "食物" in base or "铃声" in base, item.stem

    # 高风险题：基础正文必须独立覆盖题干全部考查词。
    psychology_structure = plain(question_base_text(CHAPTERS[0][1][0].questions[1]))
    for term in ("心理过程包括", "认知过程、情绪情感过程和意志过程", "人格包括", "心理动力", "心理特征"):
        assert term in psychology_structure

    projection = plain(question_base_text(CHAPTERS[0][1][11].questions[0]))
    for term in ("意义模糊", "自由作答", "掩蔽性", "整体解释", "罗夏墨渍测验", "主题统觉测验"):
        assert term in projection

    language_areas = plain(question_base_text(CHAPTERS[1][1][4].questions[0]))
    for term in ("布洛卡区", "威尔尼克区", "角回", "书写区", "位于", "受损"):
        assert term in language_areas

    autonomic = plain(AUTONOMIC_COMPARISON.base)
    for term in ("交感神经系统", "副交感神经系统", "作用方向通常相反", "适应和平衡"):
        assert term in autonomic

    definition_uses = sum(module.base.count("【名词解释：") for module in modules)
    print(
        "PASS "
        f"chapters={len(CHAPTERS)} units={len(units)} questions={len(questions)} "
        f"definition_labels={definition_uses} unique_definitions={len(definitions)} "
        f"definition_conflicts={len(conflicts)} expansions={len(expansions)} "
        f"explicit_example_questions={len(example_questions)}"
    )


if __name__ == "__main__":
    main()
