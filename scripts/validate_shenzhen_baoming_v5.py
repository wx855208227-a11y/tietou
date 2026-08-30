from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from rebuild_shenzhen_baoming_v5 import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v4 import (
    compact,
    outside_expansions,
    question_blocks,
    validate_definitions,
    validate_numbering,
)


EXPECTED = {
    GENERAL_OUTPUT: {"chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"chapters": 13, "units": 39, "questions": 45},
}


def block_with(text: str, fragment: str) -> str:
    hits = [answer for heading, _, answer in question_blocks(text) if fragment in heading]
    assert len(hits) == 1, (fragment, len(hits))
    return hits[0]


def body_without_tags(answer: str) -> str:
    return outside_expansions(re.sub(r"【名词解释：[^】]+】", "", answer))


def assert_body_and_expansion(
    text: str,
    heading: str,
    body_terms: tuple[str, ...],
    expansion_terms: tuple[str, ...],
) -> None:
    answer = block_with(text, heading)
    body = body_without_tags(answer)
    assert all(term in body for term in body_terms), (heading, "body", body_terms)
    assert all(term in answer for term in expansion_terms), (heading, "coverage", expansion_terms)
    assert all(term not in body for term in expansion_terms), (heading, "expansion", expansion_terms)


def validate_one(path: Path, expected: dict[str, int]) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    chapters = re.findall(r"^# (?!深圳大学)(.+)$", text, re.MULTILINE)
    units = re.findall(r"^## [一二三四五六七八九十]+、.+【(?:★★★|★★|★)】$", text, re.MULTILINE)
    blocks = question_blocks(text)
    assert len(chapters) == expected["chapters"], (path.name, len(chapters))
    assert len(units) == expected["units"], (path.name, len(units))
    assert len(blocks) == expected["questions"], (path.name, len(blocks))
    assert "圆括号外是背诵主体，写全可以拿到主要分数" in text
    assert "既可补充其他采分点，也可补充相关概念、解释或例子" in text

    lengths: dict[str, list[int]] = defaultdict(list)
    for heading, kind, answer in blocks:
        assert answer.endswith("。") and "综上" in answer, (path.name, heading)
        validate_numbering(path, heading, answer)
        outside = outside_expansions(answer)
        if "比较" in heading or "异同" in heading:
            assert "联系" in outside and "区别" in outside, (path.name, heading)
        lengths[kind].append(len(compact(outside)))

    assert "答题思路" not in text and "到此停笔" not in text
    assert "扩容（选背）" not in text and "扩容（选用）" not in text
    assert not re.search(r"押题.*(?:请(?:完成|设计).{0,18}(?:实验|研究)|设计一项(?:实验|研究))", text)
    definitions = validate_definitions(path, text)
    return {
        "chapters": len(chapters),
        "units": len(units),
        "questions": len(blocks),
        "types": dict(Counter(kind for _, kind, _ in blocks)),
        "definitions": len(definitions),
        "definition_calls": text.count("【名词解释："),
        "whole_point_expansions": len(re.findall(r"^（\*\*", text, re.MULTILINE)),
        "simple_body_median": statistics.median(lengths["简答"]),
        "essay_body_median": statistics.median(lengths["论述"]),
    }


def main() -> None:
    builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    all_definitions: dict[str, str] = {}
    results: dict[str, object] = {}
    for path, expected in EXPECTED.items():
        assert path.read_text(encoding="utf-8") == builds[path], path.name
        results[path.name] = validate_one(path, expected)
        for term, definition in validate_definitions(path, builds[path]).items():
            if term in all_definitions:
                assert all_definitions[term] == definition, term
            all_definitions[term] = definition

    general = builds[GENERAL_OUTPUT]
    experiment = builds[EXPERIMENT_OUTPUT]
    measurement = builds[MEASUREMENT_OUTPUT]
    assert_body_and_expansion(
        general,
        "简述心理学的主要研究领域",
        ("普通心理学", "生理心理学", "发展心理学", "教育心理学", "社会心理学"),
        ("医学心理学", "健康心理学", "工业心理学", "军事心理学"),
    )
    assert_body_and_expansion(
        general,
        "简述深度知觉的主要线索",
        ("调节", "辐合", "遮挡", "相对高度", "双眼视差"),
        ("运动视差和运动透视", "明暗和阴影"),
    )
    assert_body_and_expansion(
        general,
        "简述运动知觉的含义和主要类型",
        ("真动知觉", "似动知觉", "动景运动", "诱发运动"),
        ("自主运动", "运动后效"),
    )
    assert_body_and_expansion(
        general,
        "简述错觉的含义、特点及主要理论解释",
        ("眼动说", "完形倾向说", "透视说", "常性误用说"),
        ("移情说", "神经抑制作用说"),
    )
    assert_body_and_expansion(
        general,
        "简述记忆的主要生理机制和脑机制观点",
        ("突触结构变化", "长时程增强", "反响回路", "整合论", "定位说"),
        ("SPI理论",),
    )
    assert_body_and_expansion(
        experiment,
        "简述反应时的主要影响因素",
        ("刺激强度", "刺激复杂度", "时空特征和通道效应", "适应水平", "动机", "个体差异"),
        ("线索提示与相容性", "年龄与教育训练"),
    )
    assert_body_and_expansion(
        measurement,
        "简述结构效度的含义、用途及特点",
        ("用途", "心理特质理论", "理论假设不成立或实验设计不适当", "没有单一的数量指标"),
        ("确定方法的一般步骤",),
    )
    assert_body_and_expansion(
        measurement,
        "简述标准化样组",
        ("成员定义明确", "具有总体代表性", "取样过程清楚", "样本规模适当", "具有时空限制"),
        ("常模类型结合",),
    )
    assert_body_and_expansion(
        measurement,
        "简述测验等值的含义及基本条件",
        ("同质性", "等信度", "公平性", "可递推性", "对称性"),
        ("样本不变性",),
    )

    assert sum(result["whole_point_expansions"] for result in results.values()) >= 18
    for name, result in results.items():
        print(name, result)
    print("PASS：160道押题通过主体采分点、整点扩容、点内扩容、题干任务、序号和名解一致性检查。")


if __name__ == "__main__":
    main()
