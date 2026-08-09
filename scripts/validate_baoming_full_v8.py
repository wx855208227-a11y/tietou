from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_baoming_full_v7 import THREE_STAR_UNITS
from validate_baoming_full_v1 import TAG_RE, plain, question_blocks, visible_length
from validate_baoming_full_v3 import CHAPTERS, chapter_sections
from validate_baoming_full_v4 import leaf_point_lines
from validate_baoming_full_v5 import body_keyword_terms
from validate_baoming_full_v7 import PAIR_RE, definition_table, unit_map


V8 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_三星分级舒适阅读版V8.md")


def body(text: str) -> str:
    return text[text.index("# 第一章 "):]


def main() -> None:
    text = V8.read_text(encoding="utf-8")
    content = body(text)
    normalized_content = content.replace("【扩容（选背）：", "【扩容（选用）：")
    front = text[: text.index("# 第一章 ")]
    assert "全本·三星分级舒适阅读版V8" in front
    for phrase in (
        "★★★ 核心优先",
        "★★ 重点掌握",
        "★ 基础覆盖",
        "背诵先后顺序",
        "不代表必考概率",
        "知识结论均以**速背手册或一本通**为依据",
    ):
        assert phrase in front, phrase

    units = unit_map(content)
    assert len(units) == 117
    assert Counter(units.values()) == {"★★★": 44, "★★": 40, "★": 33}
    assert {key for key, star in units.items() if star == "★★★"} == THREE_STAR_UNITS

    pairs = PAIR_RE.findall(content)
    tags = TAG_RE.findall(content)
    assert len(pairs) == len(tags) == 296
    assert content.count("【扩容（选背）：") == 596
    assert "扩容（选用）" not in text
    expansion_table: dict[str, set[str]] = defaultdict(set)
    for expansion, name in pairs:
        expansion_table[name].add(expansion)
        assert expansion.endswith(("。", "！", "？")), (name, expansion)
        assert "**" in expansion, (name, expansion)
    assert len(expansion_table) == 256
    assert not {name: values for name, values in expansion_table.items() if len(values) != 1}

    definitions = definition_table(content)
    assert len(definitions) == 256
    assert not {name: values for name, values in definitions.items() if len(values) != 1}
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }

    chapters = chapter_sections(normalized_content)
    assert tuple(name for name, _ in chapters) == CHAPTERS
    chapter_stats = {}
    for chapter, section in chapters:
        leaf_count = covered = 0
        for _, block in question_blocks(section):
            for line in leaf_point_lines(block):
                leaf_count += 1
                if body_keyword_terms(line):
                    covered += 1
        assert leaf_count and leaf_count == covered
        chapter_stats[chapter] = (leaf_count, covered)

    blocks = question_blocks(normalized_content)
    assert len(blocks) == 145
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 107,
        "论述": 38,
    }
    simple = [visible_length(block, False) for heading, block in blocks if "【简答】" in heading]
    essay = [visible_length(block, False) for heading, block in blocks if "【论述】" in heading]
    simple_median = statistics.median(simple)
    essay_median = statistics.median(essay)
    assert 1.45 <= essay_median / simple_median <= 2.1

    for forbidden in (
        "格雷",
        "强化敏感性理论",
        "偏见",
        "闪光融合",
        "状态依存记忆",
        "基本心理需要",
        "外部奖励的双重作用",
        "吊桥情境",
        "S—S联结",
        "R—O联结",
    ):
        assert forbidden not in content, forbidden

    print(
        "全本V8内容验证通过："
        "17章、117单元（★★★44／★★40／★33）、145题（简答107／论述38）；"
        "296处名解、256个唯一名解定义与标准扩容零异文；"
        f"596处选背扩容；简答／论述基础容量中位数{simple_median:.0f}/{essay_median:.0f}字；"
        f"逐章关键词覆盖={chapter_stats}。"
    )


if __name__ == "__main__":
    main()
