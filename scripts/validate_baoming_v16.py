from __future__ import annotations

import importlib.util
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT = Path("scripts/build_baoming_v16.py")
MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_来源严格版V16.md")
TAG_RE = re.compile(r"(?:\*\*)?【名词解释：([^】]+)】(?:\*\*)?")
FORBIDDEN = (
    "XXXX",
    "待补充",
    "可举例",
    "答题思路",
    "到此停笔",
    "【共用】",
    "【本题补充】",
    "格雷",
    "强化敏感性理论",
    "行为趋近系统",
    "行为抑制系统",
    "随机分配",
    "行为调控",
    "行为塑造",
    "实施反馈",
    "迁移与保持",
)
LEAF_EXPANSION_EXCEPTIONS = {
    (0, 2, 0, "构造主义"),
    (0, 2, 1, "构造主义"),
    (0, 8, 0, "优点"),
    (0, 11, 0, "作答特点"),
    (0, 11, 0, "代表测验"),
    (2, 4, 1, "正诱导"),
    (2, 4, 1, "负诱导"),
    (2, 3, 0, "延迟"),
}


def load_module():
    spec = importlib.util.spec_from_file_location("baoming_v16", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def plain(text: str) -> str:
    return re.sub(r"\*\*|__", "", text)


def length(text: str) -> int:
    text = TAG_RE.sub("", plain(text))
    return len(re.sub(r"\s+", "", text))


def capacities(question) -> tuple[int, int]:
    base = sum(length(line.text) for line in question.lines)
    full = base + sum(length(item) for line in question.lines for item in line.expansions)
    full += sum(length(item) for item in question.final_expansions)
    return base, full


def main() -> None:
    module = load_module()
    markdown = MARKDOWN.read_text(encoding="utf-8")
    indexed_questions = [
        ((chapter_index, unit_index, question_index), question)
        for chapter_index, (_, units) in enumerate(module.CHAPTERS)
        for unit_index, unit in enumerate(units)
        for question_index, question in enumerate(unit.questions)
    ]
    questions = [question for _, question in indexed_questions]

    assert [len(units) for _, units in module.CHAPTERS] == [13, 9, 10]
    assert len(questions) == 56
    assert Counter(question.kind for question in questions) == {"简答": 51, "论述": 5}
    assert markdown.count("### 押题") == 56

    definitions: dict[str, set[str]] = defaultdict(set)
    local_expansions = 0
    final_expansions = 0
    child_count = 0
    missed_leaf_expansions: list[tuple[int, int, int, str]] = []

    for key, question in indexed_questions:
        assert question.lines[0].level == 0, f"缺少总起：{key} {question.stem}"
        assert question.lines[-1].level == 0, f"缺少总结：{key} {question.stem}"
        assert plain(question.lines[-1].text).startswith("综上"), question.stem
        assert any(line.level == 1 for line in question.lines), f"缺少分点：{question.stem}"

        parent_seen = False
        for index, line in enumerate(question.lines):
            assert line.text.strip(), f"存在空正文：{key}"
            if line.level == 1:
                parent_seen = True
            elif line.level == 2:
                assert parent_seen, f"二级编号缺少上位一级：{key}"
                child_count += 1
            for match in TAG_RE.finditer(line.text):
                definition = plain(line.text[: match.start()]).strip()
                assert definition.endswith("。"), (match.group(1), definition)
                definitions[match.group(1)].add(definition)
            for item in line.expansions:
                local_expansions += 1
                assert item.strip() and item.endswith(("。", "！", "？")), item

            is_numbered_leaf = line.level > 0 and not (
                index + 1 < len(question.lines)
                and question.lines[index + 1].level > line.level
            )
            keyword = module.first_keyword(line.text)
            if is_numbered_leaf and not line.expansions and (*key, keyword) not in LEAF_EXPANSION_EXCEPTIONS:
                missed_leaf_expansions.append((*key, keyword))

        for item in question.final_expansions:
            final_expansions += 1
            assert item.strip() and item.endswith(("。", "！", "？")), item

        if "实例" in plain(question.stem):
            full_text = "".join(line.text + "".join(line.expansions) for line in question.lines)
            assert any(token in plain(full_text) for token in ("例如", "实例", "巴甫洛夫")), question.stem

    assert not missed_leaf_expansions, missed_leaf_expansions
    conflicts = {name: values for name, values in definitions.items() if len(values) != 1}
    assert not conflicts, conflicts
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }
    assert len(definitions) == 75
    assert sum(len(TAG_RE.findall(line.text)) for question in questions for line in question.lines) == 113

    first_unit = module.CHAPTERS[0][1][0].questions
    first_base = [capacities(question)[0] for question in first_unit]
    first_full = [capacities(question)[1] for question in first_unit]
    assert max(first_base) / min(first_base) <= 1.25, first_base
    assert max(first_full) / min(first_full) <= 1.25, first_full

    simple = [capacities(question) for question in questions if question.kind == "简答"]
    essay = [capacities(question) for question in questions if question.kind == "论述"]
    base_ratio = statistics.median(item[0] for item in essay) / statistics.median(item[0] for item in simple)
    full_ratio = statistics.median(item[1] for item in essay) / statistics.median(item[1] for item in simple)
    assert 1.8 <= base_ratio <= 2.2, base_ratio
    assert 1.8 <= full_ratio <= 2.2, full_ratio

    standalone_expansions = [
        line for line in markdown.splitlines() if line.startswith("【扩容（选用）：")
    ]
    inline_expansion_count = sum(
        line.count("【扩容（选用）：")
        for line in markdown.splitlines()
        if not line.startswith(("【扩容（选用）：", ">"))
    )
    assert len(standalone_expansions) == final_expansions
    assert inline_expansion_count == local_expansions
    assert not any(
        " 【扩容（选用）：" in line
        for line in markdown.splitlines()
        if not line.startswith(("【扩容（选用）：", ">"))
    )
    assert not any(token in markdown for token in FORBIDDEN)
    assert "<u>" not in markdown and "==" not in markdown and "__" not in markdown
    assert not re.search(r"^####\s+答案", markdown, re.MULTILINE)

    print(
        "V16内容验证通过："
        f"56题，{len(definitions)}个唯一名词解释，{child_count}个二级采分点，"
        f"{local_expansions}处同行扩容、{final_expansions}处整题扩容；"
        f"简答中位数{statistics.median(item[0] for item in simple):.0f}/"
        f"{statistics.median(item[1] for item in simple):.0f}字，"
        f"论述中位数{statistics.median(item[0] for item in essay):.0f}/"
        f"{statistics.median(item[1] for item in essay):.0f}字，"
        f"容量比{base_ratio:.2f}/{full_ratio:.2f}。"
    )


if __name__ == "__main__":
    main()
