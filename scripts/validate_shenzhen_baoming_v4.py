from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from rebuild_shenzhen_baoming_v4 import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)


EXPECTED = {
    GENERAL_OUTPUT: {"chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"chapters": 13, "units": 39, "questions": 45},
}

PREFIX_RE = re.compile(r"^(\d+\.\s*|（\d+）\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*|[a-z]\.\s*)")
PAREN_RE = re.compile(r"（(?!\d+）)[^（）]*）")


def compact(value: str) -> str:
    return re.sub(r"[\s*`#]", "", value)


def outside_expansions(value: str) -> str:
    previous = None
    while value != previous:
        previous = value
        value = PAREN_RE.sub("", value)
    return value


def question_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(re.finditer(r"^### 押题\d+【(简答|论述)】.*$", text, re.MULTILINE))
    result: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        boundary = re.search(r"^#{1,2} ", text[match.end() : end], re.MULTILINE)
        if boundary:
            end = match.end() + boundary.start()
        answer = re.sub(r"^---$", "", text[match.end() : end], flags=re.MULTILINE).strip()
        result.append((match.group(0), match.group(1), answer))
    return result


def validate_numbering(path: Path, heading: str, answer: str) -> None:
    top = [int(value) for value in re.findall(r"^(\d+)\.\s", answer, re.MULTILINE)]
    assert top == list(range(1, len(top) + 1)), (path.name, heading, top)
    assert top, (path.name, heading)
    children: list[int] = []
    for line in answer.splitlines():
        if re.match(r"^\d+\.\s", line):
            if children:
                assert children == list(range(1, len(children) + 1)), (path.name, heading, children)
            children = []
        elif match := re.match(r"^（(\d+)）", line):
            children.append(int(match.group(1)))
    if children:
        assert children == list(range(1, len(children) + 1)), (path.name, heading, children)


def validate_definitions(path: Path, text: str) -> dict[str, str]:
    definitions: dict[str, list[str]] = defaultdict(list)
    for number, line in enumerate(text.splitlines(), 1):
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        assert len(tags) <= 1, (path.name, number, line)
        if not tags:
            continue
        tag = tags[0]
        assert line.endswith(f"【名词解释：{tag}】"), (path.name, number, line)
        before = line[: line.rfind("【名词解释：")]
        assert "（" in before and "）" in before, (path.name, number, tag)
        definitions[tag].append(PREFIX_RE.sub("", before))
    for term, values in definitions.items():
        assert len(set(values)) == 1, (path.name, term, values[:2])
    return {term: values[0] for term, values in definitions.items()}


def validate_one(path: Path, expected: dict[str, int]) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    chapters = re.findall(r"^# (?!深圳大学)(.+)$", text, re.MULTILINE)
    units = re.findall(r"^## [一二三四五六七八九十]+、.+【(?:★★★|★★|★)】$", text, re.MULTILINE)
    blocks = question_blocks(text)
    assert len(chapters) == expected["chapters"], (path.name, len(chapters))
    assert len(units) == expected["units"], (path.name, len(units))
    assert len(blocks) == expected["questions"], (path.name, len(blocks))
    assert "圆括号外是速背手册已有的主体采分点" in text
    assert "一本通、教材、相关角度或例子等扩容内容" in text

    lengths: dict[str, list[int]] = defaultdict(list)
    for heading, kind, answer in blocks:
        assert answer.endswith("。") and "综上" in answer, (path.name, heading)
        validate_numbering(path, heading, answer)
        outside = outside_expansions(answer)
        if "比较" in heading or "异同" in heading:
            assert "联系" in outside and "区别" in outside, (path.name, heading)
        lengths[kind].append(len(compact(answer)))

    outside = outside_expansions(text)
    assert not re.search(r"\*\*(?:实例|应用实例|科学问题示例)\*\*", outside)
    for forbidden in (
        "描述回答心理现象",
        "实验报告的基本结构",
        "核对清单阅读法",
        "反应时研究第一阶段",
        "10个临床量表和3个效度量表",
        "第一个婴儿发展量表",
        "数量生产",
        "题目属性变量、被试认知状态变量和作答反应变量联系起来",
        "对象、规则和结果三个构成部分",
    ):
        assert forbidden not in outside, (path.name, forbidden)
    assert not re.search(r"^### 押题.*(?:举例|实例)", text, re.MULTILINE)
    assert not re.search(r"押题.*(?:请(?:完成|设计).{0,18}(?:实验|研究)|设计一项(?:实验|研究))", text)
    assert "答题思路" not in text and "到此停笔" not in text

    definitions = validate_definitions(path, text)
    return {
        "chapters": len(chapters),
        "units": len(units),
        "questions": len(blocks),
        "types": dict(Counter(kind for _, kind, _ in blocks)),
        "definitions": len(definitions),
        "definition_calls": text.count("【名词解释："),
        "simple_median": statistics.median(lengths["简答"]),
        "essay_median": statistics.median(lengths["论述"]),
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

    assert "心理实验报告" not in builds[EXPERIMENT_OUTPUT]
    assert "反应时研究的历史" not in builds[EXPERIMENT_OUTPUT]
    assert "简述测量的**含义和基本要素**" in builds[MEASUREMENT_OUTPUT]
    assert "常见焦虑测验【★】" in builds[MEASUREMENT_OUTPUT]
    for name, result in results.items():
        print(name, result)
    print("PASS：160道押题通过来源分层、题干任务、序号、扩容位置、名解一致性和禁项检查。")


if __name__ == "__main__":
    main()
