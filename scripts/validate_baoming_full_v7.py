from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_baoming_full_v7 import THREE_STAR_UNITS
from validate_baoming_full_v1 import TAG_RE, normalized_definition, plain, question_blocks, visible_length
from validate_baoming_full_v3 import CHAPTERS, chapter_sections
from validate_baoming_full_v4 import leaf_point_lines
from validate_baoming_full_v5 import body_keyword_terms


V6 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_名解完整扩容版V6.md")
V7 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_三星分级选背版V7.md")
PAIR_RE = re.compile(r"【扩容（选背）：(.*?)】【名词解释：([^】]+)】")
SELECTED_RE = re.compile(r"【扩容（选背）：.*?】")


def body(text: str) -> str:
    return text[text.index("# 第一章 "):]


def normalize_to_v6(text: str) -> str:
    normalized = PAIR_RE.sub(
        lambda match: f"【名词解释：{match.group(2)}】【扩容（选背）：{match.group(1)}】",
        text,
    )
    normalized = normalized.replace("【扩容（选背）：", "【扩容（选用）：")
    normalized = re.sub(r"【(?:★★★|★★)】", "【一级】", normalized)
    normalized = normalized.replace("【★】", "【二级】")
    return normalized


def definition_table(text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for line in text.splitlines():
        plain_line = SELECTED_RE.sub("", plain(line))
        previous = 0
        for match in TAG_RE.finditer(plain_line):
            result[match.group(1)].add(normalized_definition(plain_line, previous, match.start()))
            previous = match.end()
    return result


def unit_map(text: str) -> dict[str, str]:
    result = {}
    chapter = ""
    for line in text.splitlines():
        if line.startswith("# 第"):
            chapter = line[2:].strip()
        match = re.match(r"^## (.+)【(★★★|★★|★)】$", line)
        if match:
            result[f"{chapter}｜{match.group(1)}"] = match.group(2)
    return result


def main() -> None:
    text6 = V6.read_text(encoding="utf-8")
    text7 = V7.read_text(encoding="utf-8")
    body6 = body(text6)
    body7 = body(text7)
    assert "全本·三星分级选背版V7" in text7[: text7.index("# 第一章 ")]
    assert normalize_to_v6(body7) == body6

    units = unit_map(body7)
    assert len(units) == 117
    assert Counter(units.values()) == {"★★★": 44, "★★": 40, "★": 33}
    assert {key for key, star in units.items() if star == "★★★"} == THREE_STAR_UNITS
    assert "【一级】" not in body7 and "【二级】" not in body7

    pairs = PAIR_RE.findall(body7)
    tags = TAG_RE.findall(body7)
    assert len(pairs) == len(tags) == 296
    assert body7.count("【扩容（选背）：") == 599
    assert "扩容（选用）" not in text7
    expansion_table: dict[str, set[str]] = defaultdict(set)
    for expansion, name in pairs:
        expansion_table[name].add(expansion)
        assert expansion.endswith(("。", "！", "？")), (name, expansion)
        assert "**" in expansion, (name, expansion)
        assert len(plain(expansion)) >= 7, (name, expansion)
    assert len(expansion_table) == 256
    assert not {name: values for name, values in expansion_table.items() if len(values) != 1}

    definitions = definition_table(body7)
    assert len(definitions) == 256
    assert not {name: values for name, values in definitions.items() if len(values) != 1}
    assert min(len(next(iter(values))) for values in definitions.values()) >= 16
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }

    normalized = normalize_to_v6(body7)
    chapters = chapter_sections(normalized)
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

    blocks = question_blocks(normalized)
    assert len(blocks) == 145
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 107,
        "论述": 38,
    }
    simple = [visible_length(block, False) for heading, block in blocks if "【简答】" in heading]
    essay = [visible_length(block, False) for heading, block in blocks if "【论述】" in heading]
    simple_median = statistics.median(simple)
    essay_median = statistics.median(essay)
    assert 1.5 <= essay_median / simple_median <= 2.1

    print(
        "全本V7内容验证通过："
        "17章、117单元（★★★44／★★40／★33），原一级与原二级边界零变动；"
        "145题（简答107／论述38）；296处名解全部位于对应选背扩容之后，"
        "256个唯一名解定义与扩容零异文；599处扩容全部改为选背；"
        f"简答／论述基础容量中位数{simple_median:.0f}/{essay_median:.0f}字；"
        f"逐章关键词覆盖={chapter_stats}。"
    )


if __name__ == "__main__":
    main()
