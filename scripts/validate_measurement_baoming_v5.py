from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import statistics

from build_measurement_baoming_v5 import (
    ADMITTED_TERMS,
    CUSTOM_BODIES,
    HEADING_REPLACEMENTS,
    OUTPUT,
    QUESTION_RE,
    SOURCE,
    TERM_RE,
    transform,
)
from validate_measurement_baoming_v1 import CHAPTERS, plain, question_blocks
from validate_measurement_baoming_v3 import definition_modules


TOP_LEVEL_RE = re.compile(r"^\d+\.\s")
SECOND_LEVEL_RE = re.compile(r"^（\d+）")
ROUND_EXPANSION_RE = re.compile(r"（[^（）]*）")


def question_map(text: str) -> dict[str, str]:
    return {
        match.group("heading"): match.group("body").strip()
        for match in QUESTION_RE.finditer(text)
    }


def base_length(body: str) -> int:
    value = ROUND_EXPANSION_RE.sub("", body)
    value = TERM_RE.sub("", value)
    value = value.replace("**", "")
    return len(re.sub(r"\s+|---", "", value))


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    text = OUTPUT.read_text(encoding="utf-8")
    assert text == transform(source), "V5不是V4的可复现任务驱动转换结果"
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
    types = Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks)
    assert types == {"简答": 38, "论述": 7}
    for old, new in HEADING_REPLACEMENTS.items():
        assert old not in body and new in body

    actual_terms = set(TERM_RE.findall(body))
    assert actual_terms == ADMITTED_TERMS
    assert body.count("【名词解释：") == 58
    for required in ("等比量表", "投射测验", "同时效度", "标准化样组"):
        assert required in actual_terms
    for removed in (
        "人格测验", "人格评定量表", "会聚效度", "区分效度", "单位", "参照点",
        "双向细目表", "常模表", "成就测验", "指导语", "效度系数", "效标",
        "智力测验", "标准化成就测验", "概化理论", "测验量表", "瑞文测验",
        "系统误差", "表面效度", "误差", "量表",
    ):
        assert f"【名词解释：{removed}】" not in body

    definitions, expansions = definition_modules(body)
    assert set(definitions) == set(expansions) == ADMITTED_TERMS
    assert all(len(values) == 1 for values in definitions.values())
    assert all(len(values) == 1 for values in expansions.values())
    assert all(line.count("【名词解释：") <= 1 for line in body.splitlines())
    assert all(
        "【名词解释：" not in line or re.search(r"【名词解释：[^】]+】$", line)
        for line in body.splitlines()
    ), "存在名解标签后继续堆写正文"

    maps = question_map(text)
    source_maps = question_map(source)
    structurally_changed = set(CUSTOM_BODIES) | {
        "押题1【论述】论述信度的**主要估计方法**，并比较其所反映的一致性及误差来源。",
        "押题2【简答】简述常模的**相对性**，并比较常模与标准。",
    }
    zero_drift_count = 0
    for old_heading, old_block in source_maps.items():
        new_heading = HEADING_REPLACEMENTS.get(old_heading, old_heading)
        if old_heading in structurally_changed:
            continue
        assert TERM_RE.sub("", old_block).strip() == TERM_RE.sub("", maps[new_heading]).strip(), old_heading
        zero_drift_count += 1
    expected_zero_drift_count = len(source_maps) - len(structurally_changed)
    assert zero_drift_count == expected_zero_drift_count == 38

    compare_blocks = {
        heading: block
        for heading, block in maps.items()
        if "比较" in plain(heading)
    }
    assert len(compare_blocks) == 8, compare_blocks.keys()
    for heading, block in compare_blocks.items():
        assert "联系" in plain(block), heading
        assert "区别" in plain(block), heading
        assert plain(block.splitlines()[-1]).startswith("综上"), heading

    task_markers = {
        "押题1【论述】比较**16PF、MMPI和EPQ**的理论基础、编制方法与结构特点。": (
            "三种量表的**联系**在于", "三种量表的**主要区别**如下",
            "**理论与测量取向不同**", "**编制方法不同**", "**结构特点不同**",
        ),
        "押题1【简答】组内常模指的是什么？请**举例说明**其应用。": (
            "**应用实例**", "某儿童在同年龄常模中获得离差智商115",
        ),
        "押题1【简答】简述影响信度系数的**主要因素**及提高信度的方法。": (
            "影响信度系数的**主要因素**包括以下几点：",
            "提高信度的**主要方法**包括：",
        ),
        "押题1【论述】论述影响测验效度的**主要因素及控制方法**。": (
            "影响测验效度的**主要因素及相应控制方法**包括：",
        ),
    }
    for heading, markers in task_markers.items():
        block = maps[heading]
        for marker in markers:
            assert marker in block, (heading, marker)

    simple_lengths: list[int] = []
    essay_lengths: list[int] = []
    for heading, block in blocks:
        values = [line for line in block.splitlines() if line.strip() and line.strip() != "---"]
        assert values and not TOP_LEVEL_RE.match(plain(values[0])), heading
        assert any(TOP_LEVEL_RE.match(plain(line)) for line in values), heading
        assert plain(values[-1]).startswith("综上"), heading
        length = base_length(block)
        (simple_lengths if "【简答】" in heading else essay_lengths).append(length)

    assert min(simple_lengths) >= 240 and max(simple_lengths) <= 620
    assert min(essay_lengths) >= 540 and max(essay_lengths) <= 1000
    simple_median = statistics.median(simple_lengths)
    essay_median = statistics.median(essay_lengths)
    ratio = essay_median / simple_median
    assert 1.75 <= ratio <= 2.2

    lines = body.splitlines()
    leaf_count = 0
    for index, line in enumerate(lines):
        if not (TOP_LEVEL_RE.match(line) or SECOND_LEVEL_RE.match(line)):
            continue
        current_level = 1 if TOP_LEVEL_RE.match(line) else 2
        next_level = 0
        for following in lines[index + 1 :]:
            if not following.strip():
                continue
            if TOP_LEVEL_RE.match(following):
                next_level = 1
            elif SECOND_LEVEL_RE.match(following):
                next_level = 2
            break
        if next_level > current_level:
            continue
        leaf_count += 1
        main = ROUND_EXPANSION_RE.sub("", line)
        assert re.search(r"\*\*.+?\*\*", main), line

    for forbidden in (
        "扩容（选用）", "扩容（选背）", "例子可灵活替换", "答题思路",
        "到此停笔", "本题补充", "【共用】", "XXXX", "待补充",
    ):
        assert forbidden not in body, forbidden
    assert "<u>" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body), "正文存在斜体标记"

    print(
        "测量保命手册V5内容验证通过："
        f"11章、39单元、45题（简答{types['简答']}／论述{types['论述']}）；"
        f"39个准入名解、58处调用零异文；8道比较题均含联系与区别；"
        f"{zero_drift_count}道非专项题删除名解标签后知识正文相对V4零漂移；"
        f"{leaf_count}个叶子采分点均有关键词；"
        f"简答基础容量中位数{simple_median:.1f}字，论述{essay_median:.1f}字，容量比{ratio:.2f}。"
    )


if __name__ == "__main__":
    main()
