from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

from build_measurement_baoming_v2 import EXPANSIONS
from build_measurement_baoming_v3 import POST_TAG_TEXT_RE, SOURCE, OUTPUT, transform
from validate_measurement_baoming_v1 import CHAPTERS, normalize_definition, plain, question_blocks


RESERVED = {"简答", "论述", "★★★", "★★", "★"}
TAG_RE = re.compile(r"【名词解释：([^】]+)】")


def expansion_contents(text: str) -> list[str]:
    result = []
    for value in re.findall(r"【(.*?)】", text):
        plain_value = value.replace("**", "")
        if plain_value in RESERVED or plain_value.startswith("名词解释："):
            continue
        result.append(value)
    return result


def definition_modules(text: str) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    definitions: dict[str, set[str]] = defaultdict(set)
    expansions: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        match = TAG_RE.search(line)
        if match is None:
            continue
        assert len(TAG_RE.findall(line)) == 1
        prefix = line[: match.start()]
        expansion_match = re.search(r"【(?!名词解释：)(.*?)】$", prefix)
        assert expansion_match is not None, (match.group(1), line)
        definitions[match.group(1)].add(
            normalize_definition(prefix[: expansion_match.start()])
        )
        expansions[match.group(1)].add(expansion_match.group(1))
    return definitions, expansions


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    text = OUTPUT.read_text(encoding="utf-8")
    assert text == transform(source), "V3不是V2的已批准呈现规则转换"

    front = text[: text.index("# 第一章 ")]
    for phrase in (
        "速背手册原一级",
        "一本通与考纲",
        "华东或相关真题信号强",
        "主观题可考性",
        "答案复用价值",
        "方括号外是背诵主体",
        "可以拿到主要分数",
        "`【】`内是扩容项，选背",
        "丰富答题角度、锦上添花",
        "例子，可以根据题目灵活替换",
    ):
        assert phrase in front, phrase
    for phrase in (
        "星级只表示背诵顺序，不代表必考概率",
        "名词解释背`【名词解释：……】`前的定义及紧邻扩容",
    ):
        assert phrase not in front, phrase
    assert front.count("### ") == 2

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

    assert "扩容（选用）" not in body and "扩容（选背）" not in body
    assert "例子可灵活替换" not in body
    assert body.count("【名词解释：") == 81
    assert all(line.count("【名词解释：") <= 1 for line in body.splitlines())
    assert not POST_TAG_TEXT_RE.search(body), "名解标签后仍有正文堆在同一段"
    expansions = expansion_contents(body)
    assert len(expansions) == 165

    definitions, standard_expansions = definition_modules(body)
    assert len(definitions) == len(standard_expansions) == 60
    assert not {name: values for name, values in definitions.items() if len(values) != 1}
    assert not {name: values for name, values in standard_expansions.items() if len(values) != 1}
    expected_expansions = {
        name: value.replace("（例子可灵活替换）", "")
        for name, value in EXPANSIONS.items()
    }
    assert {name: next(iter(values)) for name, values in standard_expansions.items()} == expected_expansions

    print(
        "测量保命手册V3内容验证通过：V2知识内容零漂移；"
        "11章、39单元（★★★16／★★13／★10）、45题（简答41／论述4）；"
        "60个唯一名解、81处调用及标准扩容零异文，165处纯方括号扩容。"
    )


if __name__ == "__main__":
    main()
