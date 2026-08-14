from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_shenzhen_experiment_baoming_v1 import OUTPUT as EXPERIMENT, build as build_experiment
from build_shenzhen_general_baoming_v2 import OUTPUT as GENERAL, SOURCE as GENERAL_SOURCE, transform
from build_shenzhen_measurement_baoming_v1 import OUTPUT as MEASUREMENT, build as build_measurement


RESERVED = {"简答", "论述", "★★★", "★★", "★"}
PREFIX_RE = re.compile(r"^(\d+\.\s*|（\d+）\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*)")
EXPECTED = {
    GENERAL: {
        "chapters": 15,
        "units": 75,
        "stars": {"★★★": 44, "★★": 25, "★": 6},
        "questions": {"简答": 57, "论述": 33},
        "simple": (350, 800),
        "essay": (550, 1250),
    },
    EXPERIMENT: {
        "chapters": 5,
        "units": 28,
        "stars": {"★★★": 20, "★★": 7, "★": 1},
        "questions": {"简答": 19, "论述": 9},
        "simple": (280, 650),
        "essay": (520, 900),
    },
    MEASUREMENT: {
        "chapters": 13,
        "units": 39,
        "stars": {"★★★": 21, "★★": 15, "★": 3},
        "questions": {"简答": 38, "论述": 7},
        "simple": (340, 750),
        "essay": (550, 1200),
    },
}


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
    assert "_" not in body and "<u>" not in body.lower()
    assert text.count("（") == text.count("）"), path.name
    assert not re.search(r"^（(?!\d+）)", body, re.MULTILINE), path.name

    chapters = re.findall(r"^# (?!深圳大学)(.+)$", body, re.MULTILINE)
    units = re.findall(r"^## [一二三四五六七八九十]+、.+【(★★★|★★|★)】$", body, re.MULTILINE)
    assert len(chapters) == rules["chapters"], (path.name, chapters)
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
        length = len(compact(answer))
        lower, upper = rules["simple" if question_type == "简答" else "essay"]
        assert lower <= length <= upper, (path.name, heading, length)
        lengths[question_type].append(length)
        for line in answer.splitlines():
            if re.match(r"^(?:\d+\. |（\d+）)", line) and len(compact(line)) >= 35:
                assert "**" in line, (path.name, heading, line)
    assert statistics.median(lengths["论述"]) >= statistics.median(lengths["简答"]) * 1.35

    definitions: dict[str, list[str]] = defaultdict(list)
    for line_number, line in enumerate(lines, 1):
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        assert len(tags) <= 1, (path.name, line_number)
        if not tags:
            continue
        assert line.endswith(f"【名词解释：{tags[0]}】"), (path.name, line_number, line)
        assert len(compact(normalize_definition(line))) >= 25, (path.name, line_number, tags[0])
        definitions[tags[0]].append(normalize_definition(line))
    for term, values in definitions.items():
        assert len(set(values)) == 1, (path.name, term, values)

    for bracket in re.findall(r"【([^】]+)】", body):
        assert bracket in RESERVED or bracket.startswith("名词解释："), (path.name, bracket)

    body_lines = body.splitlines()
    quarter_densities: list[float] = []
    for quarter in range(4):
        chunk = "\n".join(
            body_lines[len(body_lines) * quarter // 4 : len(body_lines) * (quarter + 1) // 4]
        )
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
    assert GENERAL.read_text(encoding="utf-8") == transform(GENERAL_SOURCE.read_text(encoding="utf-8"))
    assert EXPERIMENT.read_text(encoding="utf-8") == build_experiment()
    assert MEASUREMENT.read_text(encoding="utf-8") == build_measurement()

    results = {path.name: validate_one(path, rules) for path, rules in EXPECTED.items()}
    validate_cross_manual_definitions(list(EXPECTED))

    experiment_text = EXPERIMENT.read_text(encoding="utf-8")
    for required in ("构念效度", "内部效度", "统计结论效度", "外部效度", "核对清单阅读法"):
        assert required in experiment_text
    for excluded in ("# 第六章 注意", "# 第七章 知觉", "# 第八章 记忆与学习", "# 第九章 思维", "# 第十章 情绪"):
        assert excluded not in experiment_text

    measurement_text = MEASUREMENT.read_text(encoding="utf-8")
    for required in ("概化理论", "项目反应理论", "认知诊断", "目标参照测验", "测验等值"):
        assert required in measurement_text

    for name, result in results.items():
        print(name, result)
    print("PASS：三科任务分块、比较结构、名解零异文、关键词、容量及现行考纲范围验证通过。")


if __name__ == "__main__":
    main()
