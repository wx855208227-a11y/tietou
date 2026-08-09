from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_measurement_baoming_v2 import EXPANSIONS
from validate_measurement_baoming_v1 import plain, question_blocks, visible_length


V1 = Path("deliverables/华东师范大学347心理测量保命手册_全本_逐题直背版V1.md")
V2 = Path("deliverables/华东师范大学347心理测量保命手册_全本_名解完整扩容版V2.md")
TAG_RE = re.compile(r"【名词解释：([^】]+)】")
PAIR_RE = re.compile(r"【名词解释：([^】]+)】【扩容（选用）：(.*?)】")
EXPANSION_RE = re.compile(r"【扩容（选用）：.*?】")


def normalize_definition(segment: str) -> str:
    value = plain(segment).strip()
    value = re.sub(r"^(?:\d+\.\s*|（\d+）\s*)", "", value)
    if "：" in value:
        label, definition = value.split("：", 1)
        if len(label) <= 24 and definition:
            value = definition.strip()
    return value


def definition_table(text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        plain_line = plain(line)
        previous = 0
        for match in TAG_RE.finditer(plain_line):
            result[match.group(1)].add(normalize_definition(plain_line[previous:match.start()]))
            previous = match.end()
    return result


def without_expansions(text: str) -> str:
    return EXPANSION_RE.sub("", text).replace(
        "## 全本·名解完整扩容版V2",
        "## 全本·逐题直背版V1",
    )


def main() -> None:
    v1 = V1.read_text(encoding="utf-8")
    v2 = V2.read_text(encoding="utf-8")
    assert without_expansions(v2) == without_expansions(v1), "V2改变了V1基础作答或结构"

    body = v2[v2.index("# 第一章 "):]
    assert len(re.findall(r"^# 第[^\n]+章", body, re.MULTILINE)) == 11
    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(units) == 39
    assert Counter(level for _, level in units) == {"一级": 29, "二级": 10}
    blocks = question_blocks(body)
    assert len(blocks) == 45
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 41,
        "论述": 4,
    }

    tags = TAG_RE.findall(body)
    pairs = PAIR_RE.findall(body)
    assert len(tags) == len(pairs) == 81
    assert set(tags) == set(EXPANSIONS) and len(set(tags)) == 60
    expansion_table: dict[str, set[str]] = defaultdict(set)
    for name, expansion in pairs:
        expansion_table[name].add(expansion)
        assert expansion == EXPANSIONS[name], (name, expansion)
        assert expansion.endswith(("。", "！", "？")), (name, expansion)
        assert "**" in expansion, (name, expansion)
    assert not {name: values for name, values in expansion_table.items() if len(values) != 1}

    v1_definitions = definition_table(v1[v1.index("# 第一章 "):])
    v2_definitions = definition_table(body)
    assert v2_definitions == v1_definitions
    assert not {name: values for name, values in v2_definitions.items() if len(values) != 1}
    assert not any(line.startswith("【扩容（选用）：") for line in body.splitlines())
    assert not re.search(r"(?<!\*)\*(?!\*)", body)

    simple_lengths = []
    essay_lengths = []
    for heading, block in blocks:
        values = (visible_length(block, False), visible_length(block, True), heading)
        (simple_lengths if "【简答】" in heading else essay_lengths).append(values)
    simple_median = statistics.median(item[0] for item in simple_lengths)
    essay_median = statistics.median(item[0] for item in essay_lengths)
    assert 1.75 <= essay_median / simple_median <= 2.1

    print(
        "测量保命手册V2内容验证通过："
        "11章、39单元（一级29／二级10）、45题（简答41／论述4）；"
        "60个唯一名解、81处调用均紧跟标准扩容，定义与扩容均零异文；"
        f"基础答案与V1逐字一致；简答基础容量中位数{simple_median:.0f}字，"
        f"论述{essay_median:.0f}字，容量比{essay_median / simple_median:.2f}。"
    )


if __name__ == "__main__":
    main()
