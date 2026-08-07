from __future__ import annotations

import re

from build_baoming_v12 import CHAPTERS, OUTPUT


def plain(text: str) -> str:
    return re.sub(r"\*\*|【[^】]+】", "", text)


def main() -> None:
    markdown = OUTPUT.read_text(encoding="utf-8")
    units = [unit for _, chapter_units in CHAPTERS for unit in chapter_units]
    questions = [item for unit in units for item in unit.questions]
    modules = [module for item in questions for module in (*item.leads, *item.points, *item.bonus_points)]

    assert len(CHAPTERS) == 3
    assert len(units) == 33
    assert len(questions) == 62
    assert sum(item.kind == "简答" for item in questions) == 56
    assert sum(item.kind == "论述" for item in questions) == 6

    forbidden = (
        "#### 答案",
        "【采分点加分】",
        "【整体加分】",
        "【共用】",
        "【本题补充】",
        "答题思路",
        "背诵检索串",
        "到此停笔",
        "<br>",
    )
    assert all(term not in markdown for term in forbidden)
    assert not re.search(r"(?<!\*)\*(?!\*)", markdown), "学生版不得出现斜体标记"
    assert "答案" not in markdown, "学生版不显示‘答案’提示语"

    expected_definition = (
        "**心理学**是研究人的**行为**和**心理活动规律**的**中间科学**，"
        "兼有**自然科学和社会科学**的性质。**【名词解释：心理学】**"
    )
    psychology_definitions = [module for module in modules if "【名词解释：心理学】" in module]
    assert psychology_definitions
    assert set(psychology_definitions) == {expected_definition}

    first_question = CHAPTERS[0][1][0].questions[0]
    assert first_question.leads == (expected_definition,)
    assert first_question.points == ()
    assert first_question.bonus_points == (
        "其研究对象主要包括**心理过程**和**人格**。**【加分项】**",
    )

    for module in modules:
        if "【加分项】" in module:
            assert module.endswith("**【加分项】**"), module
            assert module.count("【加分项】") == 1, module
    assert max(
        sum(module.count("【加分项】") for module in (*item.leads, *item.points, *item.bonus_points))
        for item in questions
    ) <= 1

    definitions: dict[str, set[str]] = {}
    pattern = re.compile(r"^(.*)\*\*【名词解释：([^】]+)】\*\*$")
    for module in modules:
        match = pattern.match(module)
        if match:
            definitions.setdefault(match.group(2), set()).add(match.group(1))
    conflicts = {name: texts for name, texts in definitions.items() if len(texts) > 1}
    assert not conflicts, conflicts

    # 高风险题：构成、特点、位置/功能/受损表现均须能从本题直接提取。
    psychology_structure = "".join(CHAPTERS[0][1][0].questions[1].points)
    for term in ("心理过程包括", "认知过程、情绪情感过程和意志过程", "人格包括", "心理动力", "心理特征"):
        assert term in plain(psychology_structure)

    projection = "".join((*CHAPTERS[0][1][11].questions[0].leads, *CHAPTERS[0][1][11].questions[0].points))
    for term in ("意义模糊", "自由作答", "掩蔽性", "整体解释", "罗夏墨渍测验", "主题统觉测验"):
        assert term in plain(projection)

    language_areas = "".join(CHAPTERS[1][1][4].questions[0].leads)
    for term in ("布洛卡区", "威尔尼克区", "角回", "书写区", "位于", "受损"):
        assert term in plain(language_areas)

    definition_uses = sum(module.count("【名词解释：") for module in modules)
    bonus_uses = sum(module.count("【加分项】") for module in modules)
    print(
        "PASS "
        f"chapters={len(CHAPTERS)} units={len(units)} questions={len(questions)} "
        f"definition_labels={definition_uses} unique_definitions={len(definitions)} "
        f"definition_conflicts={len(conflicts)} bonus_uses={bonus_uses}"
    )


if __name__ == "__main__":
    main()
