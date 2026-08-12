from __future__ import annotations

from collections import Counter
import re
import statistics

from build_measurement_baoming_v5 import ADMITTED_TERMS, TERM_RE
from build_measurement_baoming_v6 import (
    CIRCLES,
    OUTPUT,
    QUESTION_RE,
    SOURCE,
    is_module_header,
    transform,
)
from validate_measurement_baoming_v1 import CHAPTERS, plain, question_blocks
from validate_measurement_baoming_v3 import definition_modules
from validate_measurement_baoming_v5 import base_length


TOP_RE = re.compile(r"^(\d+)\.\s+")
SECOND_RE = re.compile(r"^（(\d+)）")
CIRCLE_RE = re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])")
LETTER_RE = re.compile(r"^([a-z])\.\s+")
NUMBER_PREFIX_RE = re.compile(
    r"^(?:\d+\.\s+|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]|[a-z]\.\s+)",
    re.MULTILINE,
)
ROUND_EXPANSION_RE = re.compile(r"（[^（）]*）")
EXPECTED_ADMITTED_TERMS = ADMITTED_TERMS
EXPECTED_DEFINITION_COUNT = 58
CONTENT_FRAGMENT_EXEMPT_HEADINGS: set[str] = set()


def question_map(text: str) -> dict[str, str]:
    return {
        match.group("heading"): match.group("body").strip()
        for match in QUESTION_RE.finditer(text)
    }


def paragraphs(body: str) -> list[str]:
    return [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", body.strip())
        if paragraph.strip() and paragraph.strip() != "---"
    ]


def content_fragments(body: str) -> Counter[str]:
    value = NUMBER_PREFIX_RE.sub("", body)
    values = [
        re.sub(r"\s+", "", fragment)
        for fragment in re.split(r"(?<=[。！？；])|\n+", value)
        if re.sub(r"\s+", "", fragment)
    ]
    return Counter(values)


def level(paragraph: str) -> int:
    if TOP_RE.match(paragraph):
        return 1
    if SECOND_RE.match(paragraph):
        return 2
    if CIRCLE_RE.match(paragraph):
        return 3
    if LETTER_RE.match(paragraph):
        return 4
    return 0


def number_at_level(paragraph: str) -> int:
    if match := TOP_RE.match(paragraph):
        return int(match.group(1))
    if match := SECOND_RE.match(paragraph):
        return int(match.group(1))
    if match := CIRCLE_RE.match(paragraph):
        return CIRCLES.index(match.group(1)) + 1
    if match := LETTER_RE.match(paragraph):
        return ord(match.group(1)) - ord("a") + 1
    raise AssertionError(paragraph)


def check_numbering(heading: str, body: str) -> tuple[int, int]:
    values = paragraphs(body)
    assert values and not level(values[0]), heading
    assert values[-1].startswith("综上"), heading
    top_indices = [index for index, value in enumerate(values) if TOP_RE.match(value)]
    assert top_indices and top_indices[0] > 0, heading
    assert [number_at_level(values[index]) for index in top_indices] == list(
        range(1, len(top_indices) + 1)
    ), heading

    for index in top_indices:
        module_text = TOP_RE.sub("", values[index], count=1)
        assert is_module_header(module_text), (heading, values[index])

    for value in values[top_indices[0] + 1 : -1]:
        if level(value):
            continue
        assert not is_module_header(value), (heading, value)

    numbered_indices = [index for index, value in enumerate(values) if level(value)]
    leaf_count = 0
    for position, index in enumerate(numbered_indices):
        current = values[index]
        current_level = level(current)
        next_level = (
            level(values[numbered_indices[position + 1]])
            if position + 1 < len(numbered_indices)
            else 0
        )
        if current_level == 1 and current.endswith("："):
            assert next_level == 2, (heading, current)
        if next_level > current_level:
            continue
        leaf_count += 1
        main = TERM_RE.sub("", ROUND_EXPANSION_RE.sub("", current))
        assert re.search(r"\*\*.+?\*\*", main), (heading, current)

    for parent_level in (1, 2, 3):
        current_numbers: list[int] = []
        for value in values[top_indices[0] : -1]:
            current_level = level(value)
            if current_level == parent_level:
                if current_numbers:
                    assert current_numbers == list(range(1, len(current_numbers) + 1)), heading
                current_numbers = []
            elif current_level == parent_level + 1:
                current_numbers.append(number_at_level(value))
            elif current_level and current_level < parent_level:
                if current_numbers:
                    assert current_numbers == list(range(1, len(current_numbers) + 1)), heading
                current_numbers = []
        if current_numbers:
            assert current_numbers == list(range(1, len(current_numbers) + 1)), heading

    return len(top_indices), leaf_count


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    text = OUTPUT.read_text(encoding="utf-8")
    assert text == transform(source), "V6不是V5的可复现任务模块编号转换结果"
    body = text[text.index("# 第一章 ") :]

    chapters = tuple(
        match.group(1)
        for match in re.finditer(r"^# (第[^\s]+章)", body, re.MULTILINE)
    )
    assert chapters == CHAPTERS
    units = re.findall(r"^## (.+)【(★★★|★★|★)】$", body, re.MULTILINE)
    assert len(units) == 39
    assert Counter(level_value for _, level_value in units) == {"★★★": 16, "★★": 13, "★": 10}

    blocks = question_blocks(body)
    assert len(blocks) == 45
    types = Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks)
    assert types == {"简答": 38, "论述": 7}

    source_maps = question_map(source)
    maps = question_map(text)
    assert source_maps.keys() == maps.keys()
    for heading in source_maps:
        if heading in CONTENT_FRAGMENT_EXEMPT_HEADINGS:
            continue
        assert content_fragments(source_maps[heading]) == content_fragments(maps[heading]), heading

    actual_terms = set(TERM_RE.findall(body))
    assert actual_terms == EXPECTED_ADMITTED_TERMS
    assert body.count("【名词解释：") == EXPECTED_DEFINITION_COUNT
    definitions, expansions = definition_modules(body)
    assert set(definitions) == set(expansions) == EXPECTED_ADMITTED_TERMS
    assert all(len(values) == 1 for values in definitions.values())
    assert all(len(values) == 1 for values in expansions.values())
    assert all(line.count("【名词解释：") <= 1 for line in body.splitlines())
    assert all(
        "【名词解释：" not in line or re.search(r"【名词解释：[^】]+】$", line)
        for line in body.splitlines()
    )

    module_count = leaf_count = 0
    simple_lengths: list[int] = []
    essay_lengths: list[int] = []
    for heading, block in blocks:
        modules, leaves = check_numbering(heading, block)
        module_count += modules
        leaf_count += leaves
        length = base_length(block)
        (simple_lengths if "【简答】" in heading else essay_lengths).append(length)

    assert module_count == 94
    assert leaf_count == 286
    simple_median = statistics.median(simple_lengths)
    essay_median = statistics.median(essay_lengths)
    ratio = essay_median / simple_median
    assert 1.75 <= ratio <= 2.2

    compare_blocks = {
        heading: block for heading, block in maps.items() if "比较" in plain(heading)
    }
    assert len(compare_blocks) == 8
    for heading, block in compare_blocks.items():
        assert "联系" in plain(block), heading
        assert "区别" in plain(block), heading

    task_markers = {
        "押题1【论述】比较**16PF、MMPI和EPQ**的理论基础、编制方法与结构特点。": (
            "1. 三种量表的**理论基础、编制方法与结构特点**分别如下：",
            "2. 三种量表的**联系**在于",
            "3. 三种量表的**主要区别**如下：",
        ),
        "押题1【简答】简述影响信度系数的**主要因素**及提高信度的方法。": (
            "1. 影响信度系数的**主要因素**包括以下几点：",
            "2. 提高信度的**主要方法**包括：",
        ),
    }
    for heading, markers in task_markers.items():
        for marker in markers:
            assert marker in maps[heading], (heading, marker)

    for forbidden in (
        "扩容（选用）", "扩容（选背）", "例子可灵活替换", "答题思路",
        "到此停笔", "本题补充", "【共用】", "XXXX", "待补充",
    ):
        assert forbidden not in body, forbidden
    assert "<u>" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body)

    print(
        "测量保命手册V6内容验证通过："
        f"11章、39单元、45题（简答{types['简答']}／论述{types['论述']}）；"
        f"94个题干任务模块全部从1连续编号，总起与总结均不编号；"
        f"{leaf_count}个叶子采分点均有关键词；{len(EXPECTED_ADMITTED_TERMS)}个准入名解、"
        f"{EXPECTED_DEFINITION_COUNT}处调用零异文；"
        f"简答基础容量中位数{simple_median:.1f}字，论述{essay_median:.1f}字，容量比{ratio:.2f}。"
    )


if __name__ == "__main__":
    main()
