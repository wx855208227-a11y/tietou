from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from rebuild_shenzhen_baoming_v2 import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)


EXPECTED = {
    GENERAL_OUTPUT: {
        "chapters": 15,
        "units": 75,
        "stars": {"★★★": 44, "★★": 25, "★": 6},
        "questions": {"简答": 51, "论述": 39},
    },
    EXPERIMENT_OUTPUT: {
        "chapters": 5,
        "units": 27,
        "stars": {"★★★": 19, "★★": 7, "★": 1},
        "questions": {"简答": 18, "论述": 9},
    },
    MEASUREMENT_OUTPUT: {
        "chapters": 13,
        "units": 39,
        "stars": {"★★★": 21, "★★": 15, "★": 3},
        "questions": {"简答": 37, "论述": 8},
    },
}

REQUIRED_APPLICATION_MARKERS = (
    "**科学问题示例**",
    "**实验依据**",
    "**实验现象**",
    "**实例**",
    "**实例与应对**",
    "**应用实例**",
)
RESERVED_BRACKETS = {"简答", "论述", "★★★", "★★", "★"}
PREFIX_RE = re.compile(r"^(\d+\.\s*|（\d+）\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*)")


def compact(value: str) -> str:
    return re.sub(r"[\s*`#]", "", value)


def question_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(re.finditer(r"^### 押题\d+【(简答|论述)】.*$", text, re.MULTILINE))
    result: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        block = re.split(r"^#{1,2} ", block, maxsplit=1, flags=re.MULTILINE)[0].strip()
        block = re.sub(r"^---$", "", block, flags=re.MULTILINE).strip()
        result.append((match.group(0), match.group(1), block))
    return result


def outside_expansions(answer: str) -> str:
    previous = None
    while previous != answer:
        previous = answer
        answer = re.sub(r"（[^（）]*）", "", answer)
    return answer


def normalize_definition(line: str) -> str:
    body = line[: line.rfind("【名词解释：")]
    return PREFIX_RE.sub("", body)


def validate_one(path: Path, rules: dict) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    first_chapter = next(index for index, line in enumerate(lines) if line.startswith("# 第一章 "))
    front = "\n".join(lines[:first_chapter])
    body = "\n".join(lines[first_chapter:])

    assert "## 星级" in front and "## 怎么用" in front
    assert "圆括号外是背诵主体" in front and "`（）`内是扩容项，选背" in front
    for forbidden in (
        "答题思路",
        "到此停笔",
        "共用",
        "本题补充",
        "可灵活替换",
        "【扩容",
        "扩容（选用）",
        "扩容（选背）",
    ):
        assert forbidden not in body, (path.name, forbidden)

    design_task = re.compile(
        r"^### 押题.*(?:请(?:完成|设计).{0,18}(?:实验|研究)|设计一项(?:实验|研究)|写出.{0,8}实验方案)",
        re.MULTILINE,
    )
    assert not design_task.search(body), (path.name, design_task.search(body).group(0) if design_task.search(body) else "")
    assert "综合实验设计" not in body

    chapters = re.findall(r"^# (?!深圳大学)(.+)$", body, re.MULTILINE)
    units = re.findall(r"^## [一二三四五六七八九十]+、.+【(★★★|★★|★)】$", body, re.MULTILINE)
    assert len(chapters) == rules["chapters"], (path.name, len(chapters))
    assert len(units) == rules["units"], (path.name, len(units))
    assert Counter(units) == Counter(rules["stars"]), (path.name, Counter(units))

    blocks = question_blocks(body)
    types = Counter(question_type for _, question_type, _ in blocks)
    assert types == Counter(rules["questions"]), (path.name, types)
    lengths: dict[str, list[int]] = defaultdict(list)
    for heading, question_type, answer in blocks:
        assert answer and answer.endswith("。"), (path.name, heading)
        assert "综上" in answer, (path.name, heading)
        numbers = [int(value) for value in re.findall(r"^(\d+)\. ", answer, re.MULTILINE)]
        assert numbers == list(range(1, len(numbers) + 1)), (path.name, heading, numbers)
        assert numbers, (path.name, heading)
        if "比较" in heading or "异同" in heading:
            assert "联系" in answer and "区别" in answer, (path.name, heading)
        if any(term in heading for term in ("举例", "实例", "结合实验")):
            required = outside_expansions(answer)
            assert any(marker in required for marker in REQUIRED_APPLICATION_MARKERS), (path.name, heading)
        lengths[question_type].append(len(compact(answer)))

    assert statistics.median(lengths["论述"]) > statistics.median(lengths["简答"]), path.name
    assert max(lengths["简答"]) <= 700, (path.name, max(lengths["简答"]))

    definitions: dict[str, list[str]] = defaultdict(list)
    for line_number, line in enumerate(lines, 1):
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        assert len(tags) <= 1, (path.name, line_number)
        if not tags:
            continue
        assert line.endswith(f"【名词解释：{tags[0]}】"), (path.name, line_number, line)
        definition = normalize_definition(line)
        assert len(compact(definition)) >= 25, (path.name, line_number, tags[0])
        definitions[tags[0]].append(definition)
    for term, values in definitions.items():
        assert len(set(values)) == 1, (path.name, term, values)

    for bracket in re.findall(r"【([^】]+)】", body):
        assert bracket in RESERVED_BRACKETS or bracket.startswith("名词解释："), (path.name, bracket)

    quarter_densities: list[float] = []
    body_lines = body.splitlines()
    for quarter in range(4):
        chunk = "\n".join(body_lines[len(body_lines) * quarter // 4 : len(body_lines) * (quarter + 1) // 4])
        total = len(re.sub(r"\s", "", chunk))
        bold = sum(len(value) for value in re.findall(r"\*\*([^*]+)\*\*", chunk))
        density = bold / total
        assert density >= 0.055, (path.name, quarter + 1, density)
        quarter_densities.append(density)

    return {
        "chapters": len(chapters),
        "units": len(units),
        "questions": len(blocks),
        "types": dict(types),
        "definitions": len(definitions),
        "calls": body.count("【名词解释："),
        "simple_median": statistics.median(lengths["简答"]),
        "essay_median": statistics.median(lengths["论述"]),
        "keyword_quarters": [round(value, 3) for value in quarter_densities],
    }


def validate_cross_manual_definitions(paths: list[Path]) -> None:
    definitions: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            tags = re.findall(r"【名词解释：([^】]+)】", line)
            if tags:
                definitions[tags[0]].append((path.name, normalize_definition(line)))
    for term, values in definitions.items():
        assert len({value for _, value in values}) == 1, (term, values)


def main() -> None:
    expected_builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    for path, expected in expected_builds.items():
        assert path.read_text(encoding="utf-8") == expected, path.name

    results = {path.name: validate_one(path, rules) for path, rules in EXPECTED.items()}
    validate_cross_manual_definitions(list(EXPECTED))
    for name, result in results.items():
        print(name, result)
    print("PASS：无实验设计押题；题干必需实例已进入主体；结构、题型、名解、关键词及容量校验通过。")


if __name__ == "__main__":
    main()
