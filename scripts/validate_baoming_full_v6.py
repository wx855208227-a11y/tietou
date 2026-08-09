from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_baoming_full_v6 import PAIR_RE, TAG_RE as MODULE_RE, transform
from validate_baoming_full_v1 import (
    TAG_RE,
    normalized_definition,
    plain,
    question_blocks,
    visible_length,
)
from validate_baoming_full_v3 import CHAPTERS, FORBIDDEN_BODY, chapter_sections
from validate_baoming_full_v4 import leaf_point_lines
from validate_baoming_full_v5 import body_keyword_terms


V5 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_采分关键词精校版V5.md")
V6 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_名解完整扩容版V6.md")
EXPANSION_RE = re.compile(r"【扩容（选用）：.*?】")


def without_name_expansions(text: str) -> str:
    return MODULE_RE.sub(lambda match: f"【名词解释：{match.group(1)}】", text)


def definition_table(text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        plain_line = EXPANSION_RE.sub("", plain(line))
        previous = 0
        for match in TAG_RE.finditer(plain_line):
            result[match.group(1)].add(normalized_definition(plain_line, previous, match.start()))
            previous = match.end()
    return result


def main() -> None:
    v5 = V5.read_text(encoding="utf-8")
    v6 = V6.read_text(encoding="utf-8")
    body5 = v5[v5.index("# 第一章 "):]
    body6 = v6[v6.index("# 第一章 "):]

    # V6只替换／补齐名解标签后的标准扩容，不暗改题目、基础答案、
    # 分级、关键词或其他局部与整题扩容。
    assert without_name_expansions(body6) == without_name_expansions(body5)
    assert "全本·名解完整扩容版V6" in v6[: v6.index("# 第一章 ")]

    chapters = chapter_sections(body6)
    assert tuple(name for name, _ in chapters) == CHAPTERS
    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body6, re.MULTILINE)
    assert len(units) == 117
    assert Counter(level for _, level in units) == {"一级": 84, "二级": 33}
    blocks = question_blocks(body6)
    assert len(blocks) == 145
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 107,
        "论述": 38,
    }
    assert not any(token in body6 for token in FORBIDDEN_BODY)
    assert "<u>" not in body6 and "__" not in body6 and "==" not in body6
    assert not re.search(r"(?<!\*)\*(?!\*)", body6)

    _, standard = transform(v5)
    tags = TAG_RE.findall(body6)
    pairs = PAIR_RE.findall(body6)
    assert len(tags) == len(pairs) == 296
    assert len(set(tags)) == len(standard) == 256
    assert body6.count("【扩容（选用）：") == 599
    expansion_table: dict[str, set[str]] = defaultdict(set)
    for name, expansion in pairs:
        expansion_table[name].add(expansion)
        assert expansion == standard[name], (name, expansion)
        assert expansion.endswith(("。", "！", "？")), (name, expansion)
        assert "**" in expansion, (name, expansion)
        assert len(plain(expansion)) >= 7, (name, expansion)
    assert not {name: values for name, values in expansion_table.items() if len(values) != 1}

    definitions5 = definition_table(body5)
    definitions6 = definition_table(body6)
    assert definitions6 == definitions5
    assert len(definitions6) == 256
    assert not {name: values for name, values in definitions6.items() if len(values) != 1}
    assert min(len(next(iter(values))) for values in definitions6.values()) >= 16
    assert definitions6["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }

    # 每章重新检查基础正文关键词，防止后半册标记衰减；新加入的名解扩容
    # 也必须包含一组能够还原新增角度的关键词。
    chapter_stats: dict[str, tuple[int, int]] = {}
    for chapter, section in chapters:
        leaf_count = covered = 0
        for _, block in question_blocks(section):
            for line in leaf_point_lines(block):
                leaf_count += 1
                if body_keyword_terms(line):
                    covered += 1
        assert leaf_count and leaf_count == covered, (chapter, leaf_count, covered)
        chapter_stats[chapter] = (leaf_count, covered)

    simple_lengths: list[tuple[int, int]] = []
    essay_lengths: list[tuple[int, int]] = []
    for heading, block in blocks:
        values = (visible_length(block, False), visible_length(block, True))
        (simple_lengths if "【简答】" in heading else essay_lengths).append(values)
    simple_base = statistics.median(value[0] for value in simple_lengths)
    essay_base = statistics.median(value[0] for value in essay_lengths)
    simple_full = statistics.median(value[1] for value in simple_lengths)
    essay_full = statistics.median(value[1] for value in essay_lengths)
    assert 1.5 <= essay_base / simple_base <= 2.1
    # “含扩容”是假设把所有选用项同时写出的极端上限；V6为每个名解
    # 统一增加一条扩容后，名解密度更高的简答增幅会更大，因此只用于
    # 排查异常，不把上限容量机械校准为两倍。
    assert 1.45 <= essay_full / simple_full <= 2.2

    print(
        "全本V6内容验证通过："
        "17章、117单元（一级84／二级33）、145题（简答107／论述38）；"
        "256个唯一名解、296处调用均紧跟标准扩容，定义与扩容零异文；"
        "删除名解标准扩容后与V5正文逐字一致；"
        f"简答基础／含扩容中位数{simple_base:.0f}/{simple_full:.0f}字，"
        f"论述{essay_base:.0f}/{essay_full:.0f}字，"
        f"逐章关键词覆盖={chapter_stats}。"
    )


if __name__ == "__main__":
    main()
