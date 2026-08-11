from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

from build_measurement_baoming_v4 import (
    CUSTOM_BODY,
    MODULES,
    OUTPUT,
    QUESTION_RE,
    REMOVE_PARAGRAPHS,
    SOURCE,
    TOP_LEVEL_RE,
    transform,
)
from validate_measurement_baoming_v1 import CHAPTERS, question_blocks
from validate_measurement_baoming_v3 import definition_modules


TRANSITION_ENDINGS = ("：",)
CUSTOM_TRANSITIONS = {
    "押题1【简答】简述影响信度系数的**主要因素**及提高信度的方法。": (
        "影响信度系数的**主要因素**包括以下几点：",
        "提高信度的**主要方法**包括：",
    ),
}


def paragraphs(body: str) -> list[str]:
    return [value for value in body.strip().split("\n\n") if value.strip()]


def normalize_top_number(value: str) -> str:
    return TOP_LEVEL_RE.sub("N. ", value, count=1)


def question_map(text: str) -> dict[str, str]:
    return {
        match.group("heading"): match.group("body").strip()
        for match in QUESTION_RE.finditer(text)
    }


def check_zero_drift(source: str, result: str) -> None:
    old = question_map(source)
    new = question_map(result)
    assert old.keys() == new.keys() == MODULES.keys()
    for heading in old:
        if heading in CUSTOM_BODY:
            continue
        source_paragraphs = [
            normalize_top_number(value)
            for value in paragraphs(old[heading])
            if value not in REMOVE_PARAGRAPHS.get(heading, set())
        ]
        transitions = {value for _, value in MODULES[heading]}
        result_paragraphs = [
            normalize_top_number(value)
            for value in paragraphs(new[heading])
            if value not in transitions
        ]
        assert result_paragraphs == source_paragraphs, heading


def check_modules(text: str) -> tuple[int, int]:
    blocks = question_map(text)
    transition_count = module_count = 0
    for heading, body in blocks.items():
        values = paragraphs(body)
        transitions = tuple(value for _, value in MODULES[heading]) or CUSTOM_TRANSITIONS[heading]
        positions = []
        for transition in transitions:
            assert transition.endswith(TRANSITION_ENDINGS), transition
            assert "**" in transition, transition
            assert values.count(transition) == 1, (heading, transition)
            index = values.index(transition)
            assert index + 1 < len(values) and values[index + 1].startswith("1. "), (
                heading,
                transition,
            )
            positions.append(index)
        assert positions == sorted(positions), heading
        transition_count += len(transitions)
        module_count += len(transitions)
        for position_index, start in enumerate(positions):
            end = positions[position_index + 1] if position_index + 1 < len(positions) else len(values)
            numbers = [
                int(match.group(1))
                for value in values[start + 1 : end]
                if (match := TOP_LEVEL_RE.match(value)) is not None
            ]
            assert numbers == list(range(1, len(numbers) + 1)), (heading, numbers)
            assert numbers, (heading, transitions[position_index])
        assert values[-1].startswith("综上"), heading
    return transition_count, module_count


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    text = OUTPUT.read_text(encoding="utf-8")
    assert text == transform(source), "V4不是V3的可复现结构优化结果"
    check_zero_drift(source, text)

    body = text[text.index("# 第一章 ") :]
    chapters = tuple(
        match.group(1)
        for match in re.finditer(r"^# (第[^\s]+章)", body, re.MULTILINE)
    )
    assert chapters == CHAPTERS
    units = re.findall(r"^## (.+)【(★★★|★★|★)】$", body, re.MULTILINE)
    assert len(units) == 39
    assert Counter(level for _, level in units) == {"★★★": 16, "★★": 13, "★": 10}
    blocks = question_blocks(body)
    assert len(blocks) == 45
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 41,
        "论述": 4,
    }
    assert body.count("【名词解释：") == 81
    definitions, expansions = definition_modules(body)
    assert len(definitions) == len(expansions) == 60
    assert all(len(values) == 1 for values in definitions.values())
    assert all(len(values) == 1 for values in expansions.values())

    transition_count, module_count = check_modules(text)
    assert transition_count == module_count == 82
    assert not re.search(r"^\d+[）)]", body, re.MULTILINE)
    assert not re.search(r"^[A-ZＡ-Ｚ][.．、]", body, re.MULTILINE)
    assert not re.search(r"^（\d+）", body, re.MULTILINE) or "1." in body
    assert all(
        "**" in line
        for line in body.splitlines()
        if TOP_LEVEL_RE.match(line)
    ), "存在没有关键词的一级采分点"
    for forbidden in (
        "扩容（选用）",
        "扩容（选背）",
        "例子可灵活替换",
        "答题思路",
        "到此停笔",
        "本题补充",
        "【共用】",
    ):
        assert forbidden not in body, forbidden

    custom = question_map(text)[next(iter(CUSTOM_BODY))]
    for phrase in (
        "影响信度系数的**主要因素**包括以下几点：",
        "提高信度的**主要方法**包括：",
        "1. **扩大被试分数的分布范围**",
        "2. **适当增加测验长度**",
        "3. **使测验保持适宜难度**",
        "4. **控制随机误差**",
    ):
        assert phrase in custom, phrase

    print(
        "测量保命手册V4内容验证通过：11章、39单元、45题；"
        "除信度校准题外基础内容相对V3零漂移；"
        f"82个自然答题模块均由过渡段引出并从1重新编号；"
        "60个唯一名解、81处调用零异文。"
    )


if __name__ == "__main__":
    main()
