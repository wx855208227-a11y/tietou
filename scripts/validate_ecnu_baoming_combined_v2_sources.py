from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_ecnu_baoming_combined_v2_sources import (
    COMPARE_CONCLUSIONS,
    EXPERIMENT_OUTPUT,
    EXPERIMENT_SOURCE,
    INTRO_OUTPUT,
    INTRO_SOURCE,
    transform,
)


TAG_RE = re.compile(r"【名词解释：([^】]+)】$")
QUESTION_RE = re.compile(r"^### 押题\d+【(简答|论述)】.+$", re.MULTILINE)


def plain(value: str) -> str:
    return re.sub(r"\*\*|__|`|\s+", "", value)


def normalized_definition(value: str) -> str:
    value = re.sub(r"^(?:\d+\.\s*|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-z]\.\s*)", "", value)
    return plain(value)


def question_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(QUESTION_RE.finditer(text))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        block = re.split(r"^## |^# ", block, maxsplit=1, flags=re.MULTILINE)[0]
        result.append((match.group(0), match.group(1), block.strip()))
    return result


def answer_length(block: str, include_expansion: bool) -> int:
    if not include_expansion:
        block = re.sub(r"（[^（）]*）", "", block)
    return len(re.sub(r"[\s*`#]", "", block))


def validate_one(
    text: str,
    *,
    name: str,
    expected_chapters: int,
    expected_units: Counter[str],
    expected_questions: Counter[str],
    expected_tags: int,
    expected_unique_tags: int,
) -> dict[str, float | int]:
    body = text[text.index("# 第一章 ") :]
    chapters = re.findall(r"^# (.+)$", body, re.MULTILINE)
    assert len(chapters) == expected_chapters, (name, chapters)
    levels = Counter(re.findall(r"^## .+【(★★★|★★|★)】$", body, re.MULTILINE))
    assert levels == expected_units, (name, levels)
    blocks = question_blocks(body)
    assert Counter(question_type for _, question_type, _ in blocks) == expected_questions

    for forbidden in (
        "扩容（选背）",
        "扩容（选用）",
        "固定实验可灵活选用",
        "具体方法可灵活替换",
        "答题思路",
        "到此停笔",
        "XXXX",
        "待补充",
    ):
        assert forbidden not in body, (name, forbidden)

    compare_count = 0
    simple_lengths: list[int] = []
    essay_lengths: list[int] = []
    for heading, question_type, block in blocks:
        assert "综上" in block, heading
        numbers = [int(value) for value in re.findall(r"^(\d+)\.\s", block, re.MULTILINE)]
        assert numbers and numbers == list(range(1, max(numbers) + 1)), (heading, numbers)
        for line in block.splitlines():
            if re.match(r"^(?:\d+\.\s|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-z]\.\s)", line):
                assert "**" in line, (heading, line)

        if any(marker in heading for marker in ("比较", "区别", "异同")):
            compare_count += 1
            has_contact = "**联系**：" in block or any(
                marker in block for marker in ("**共同点**", "**基本联系**", "**二者关系**", "**三者关系**")
            )
            has_difference = "**主要区别**：" in block or any(
                marker in block for marker in ("**不同点**", "**二者区别**", "**三者区别**")
            )
            assert has_contact and has_difference, heading

        value = answer_length(block, include_expansion=False)
        (essay_lengths if question_type == "论述" else simple_lengths).append(value)

    tag_lines = [line for line in body.splitlines() if "【名词解释：" in line]
    assert len(tag_lines) == expected_tags
    definitions: dict[str, set[str]] = defaultdict(set)
    for line in tag_lines:
        matches = TAG_RE.findall(line)
        assert len(matches) == 1 and TAG_RE.search(line).end() == len(line), line
        assert re.search(r"（.+）【名词解释：[^】]+】$", line), line
        assert "**" in line, line
        definitions[matches[0]].add(normalized_definition(line[: line.index("【名词解释：")]))
    assert len(definitions) == expected_unique_tags
    assert not {name: values for name, values in definitions.items() if len(values) != 1}

    ratio = statistics.median(essay_lengths) / statistics.median(simple_lengths)
    assert ratio >= 1.4
    return {
        "chapters": len(chapters),
        "units": sum(levels.values()),
        "questions": len(blocks),
        "compares": compare_count,
        "tags": len(tag_lines),
        "unique_tags": len(definitions),
        "simple_median": statistics.median(simple_lengths),
        "essay_median": statistics.median(essay_lengths),
        "ratio": ratio,
    }


def main() -> None:
    intro_source = INTRO_SOURCE.read_text(encoding="utf-8")
    experiment_source = EXPERIMENT_SOURCE.read_text(encoding="utf-8")
    intro = INTRO_OUTPUT.read_text(encoding="utf-8")
    experiment = EXPERIMENT_OUTPUT.read_text(encoding="utf-8")
    assert intro == transform(intro_source, version="V10", experiment=False)
    assert experiment == transform(experiment_source, version="V2", experiment=True)

    source_compare_headings = {
        plain(match.group(0)).removeprefix("###")
        for source in (intro_source, experiment_source)
        for match in QUESTION_RE.finditer(source)
        if any(marker in match.group(0) for marker in ("比较", "区别", "异同"))
    }
    assert source_compare_headings == set(COMPARE_CONCLUSIONS), (
        source_compare_headings - set(COMPARE_CONCLUSIONS),
        set(COMPARE_CONCLUSIONS) - source_compare_headings,
    )

    intro_stats = validate_one(
        intro,
        name="导论V10",
        expected_chapters=17,
        expected_units=Counter({"★★★": 44, "★★": 40, "★": 33}),
        expected_questions=Counter({"简答": 107, "论述": 38}),
        expected_tags=296,
        expected_unique_tags=256,
    )
    experiment_stats = validate_one(
        experiment,
        name="实验V2",
        expected_chapters=11,
        expected_units=Counter({"★★★": 18, "★★": 17, "★": 14}),
        expected_questions=Counter({"简答": 35, "论述": 14}),
        expected_tags=72,
        expected_unique_tags=68,
    )
    print(f"导论V10验证通过：{intro_stats}")
    print(f"实验V2验证通过：{experiment_stats}")
    print("比较题均已显式呈现联系与主要区别；名解核心定义＋扩容零异文；任务模块编号连续。")


if __name__ == "__main__":
    main()
