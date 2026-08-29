from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from rebuild_shenzhen_baoming_v3 import (
    EXPERIMENT_OUTPUT,
    GENERAL_GROUPS,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)


EXPECTED = {
    GENERAL_OUTPUT: {"chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"chapters": 5, "units": 27, "questions": 27},
    MEASUREMENT_OUTPUT: {"chapters": 13, "units": 39, "questions": 45},
}

PREFIX_RE = re.compile(r"^(\d+\.\s*|（\d+）\s*|[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]\s*|[a-z]\.\s*)")


def compact(value: str) -> str:
    return re.sub(r"[\s*`#]", "", value)


def question_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(re.finditer(r"^### 押题\d+【(简答|论述)】.*$", text, re.MULTILINE))
    result: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        answer = re.split(r"^#{1,2} ", text[match.end() : end], maxsplit=1, flags=re.MULTILINE)[0]
        answer = re.sub(r"^---$", "", answer, flags=re.MULTILINE).strip()
        result.append((match.group(0), match.group(1), answer))
    return result


def outside_expansions(answer: str) -> str:
    previous = None
    while previous != answer:
        previous = answer
        answer = re.sub(r"（[^（）]*）", "", answer)
    return answer


def validate_numbering(path: Path, heading: str, answer: str) -> None:
    top = [int(value) for value in re.findall(r"^(\d+)\.\s", answer, re.MULTILINE)]
    assert top == list(range(1, len(top) + 1)), (path.name, heading, top)
    assert top, (path.name, heading)

    # Every real parent module restarts its direct children from （1）.
    active_children: list[int] = []
    for line in answer.splitlines():
        if re.match(r"^\d+\.\s", line):
            if active_children:
                assert active_children == list(range(1, len(active_children) + 1)), (
                    path.name,
                    heading,
                    active_children,
                )
            active_children = []
        elif match := re.match(r"^（(\d+)）", line):
            active_children.append(int(match.group(1)))
    if active_children:
        assert active_children == list(range(1, len(active_children) + 1)), (
            path.name,
            heading,
            active_children,
        )


def validate_one(path: Path, expected: dict[str, int]) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    chapters = re.findall(r"^# (?!深圳大学)(.+)$", text, re.MULTILINE)
    units = re.findall(r"^## [一二三四五六七八九十]+、.+【(?:★★★|★★|★)】$", text, re.MULTILINE)
    blocks = question_blocks(text)
    assert len(chapters) == expected["chapters"], (path.name, len(chapters))
    assert len(units) == expected["units"], (path.name, len(units))
    assert len(blocks) == expected["questions"], (path.name, len(blocks))

    lengths: dict[str, list[int]] = defaultdict(list)
    for heading, question_type, answer in blocks:
        assert answer.endswith("。") and "综上" in answer, (path.name, heading)
        validate_numbering(path, heading, answer)
        outside = outside_expansions(answer)
        if "比较" in heading or "异同" in heading:
            assert "联系" in outside and "区别" in outside, (path.name, heading)
        if any(value in heading for value in ("举例", "实例", "结合实验")):
            assert any(value in outside for value in ("实例", "实验依据", "实验现象", "科学问题示例")), (
                path.name,
                heading,
            )
        lengths[question_type].append(len(compact(answer)))

    definitions: dict[str, list[str]] = defaultdict(list)
    for number, line in enumerate(text.splitlines(), 1):
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        assert len(tags) <= 1, (path.name, number)
        if not tags:
            continue
        assert line.endswith(f"【名词解释：{tags[0]}】"), (path.name, number)
        definitions[tags[0]].append(PREFIX_RE.sub("", line[: line.rfind("【名词解释：")]))
    for term, values in definitions.items():
        assert len(set(values)) == 1, (path.name, term)

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


def validate_general_task_alignment(text: str) -> None:
    first = question_blocks(text)[0]
    answer = first[2]
    required = (
        "1. 心理学是主要研究",
        "（1）**认知**",
        "（2）**动机和情绪**：",
        "①动机是",
        "②情绪是",
        "（3）**心理特征**",
        "2. 行为是由一系列",
        "3. **心理与行为的关系**",
    )
    assert all(value in answer for value in required)
    assert "个体性与社会性" not in answer

    for fragment, groups in GENERAL_GROUPS.items():
        hits = [(heading, answer) for heading, _, answer in question_blocks(text) if fragment in heading]
        assert len(hits) == 1, (fragment, len(hits))
        answer = hits[0][1]
        for parent, _ in groups:
            if parent is not None:
                assert parent in answer, (fragment, parent)

    sound_heading, _, sound = next(item for item in question_blocks(text) if "声音的心理维度" in item[0])
    assert "声音掩蔽" in sound_heading and "声音掩蔽" in sound
    conditioning_heading, _, conditioning = next(
        item for item in question_blocks(text) if "经典条件作用的形成过程" in item[0]
    )
    assert "理论发展" in conditioning_heading and "理论发展" in conditioning


def validate_cross_manual_definitions(paths: list[Path]) -> None:
    definitions: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            tags = re.findall(r"【名词解释：([^】]+)】", line)
            if tags:
                definitions[tags[0]].append(PREFIX_RE.sub("", line[: line.rfind("【名词解释：")]))
    for term, values in definitions.items():
        assert len(set(values)) == 1, term


def main() -> None:
    builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    for path, built in builds.items():
        assert path.read_text(encoding="utf-8") == built, path.name

    results = {path.name: validate_one(path, expected) for path, expected in EXPECTED.items()}
    validate_general_task_alignment(GENERAL_OUTPUT.read_text(encoding="utf-8"))
    validate_cross_manual_definitions(list(EXPECTED))
    for name, result in results.items():
        print(name, result)
    print("PASS：162道押题完成题干任务层级、序号、题干必答项、名解一致性和无关内容检查。")


if __name__ == "__main__":
    main()
