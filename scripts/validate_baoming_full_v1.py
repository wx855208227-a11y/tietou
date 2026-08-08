from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_逐题直背版V1.md")
CHAPTERS = (
    "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章",
    "第九章", "第十章", "第十一章", "第十二章", "第十三章", "第十四章", "第十五章",
    "第十六章", "第十八章",
)
FORBIDDEN_BODY = (
    "XXXX", "待补充", "答题思路", "到此停笔", "【共用】", "【本题补充】",
    "格雷", "强化敏感性理论", "行为趋近系统", "行为抑制系统", "BAS", "BIS",
)
TAG_RE = re.compile(r"【名词解释：([^】]+)】")
EXPANSION_RE = re.compile(r"【扩容（选用）：.*?】")


def plain(text: str) -> str:
    return text.replace("**", "")


def visible_length(text: str, include_expansion: bool) -> int:
    if not include_expansion:
        text = EXPANSION_RE.sub("", text)
    text = TAG_RE.sub("", text)
    text = text.replace("【扩容（选用）：", "").replace("】", "")
    text = text.replace("**", "")
    return len(re.sub(r"\s+", "", text))


def question_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^### (押题\d+【(?:简答|论述)】[^\n]+)$", text, re.MULTILINE))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():end]
        block = re.split(r"(?=^#{1,2} )", block, maxsplit=1, flags=re.MULTILINE)[0]
        blocks.append((match.group(1), block.strip()))
    return blocks


def normalized_definition(line: str, segment_start: int, tag_start: int) -> str:
    definition = plain(line[segment_start:tag_start]).strip()
    definition = re.sub(r"^(?:\d+\.\s*|（\d+）\s*)", "", definition)
    return definition


def main() -> None:
    text = MARKDOWN.read_text(encoding="utf-8")
    body = text[text.index("# 第一章 "):]

    chapters = [match.group(1) for match in re.finditer(r"^# (第[^\s]+章)", body, re.MULTILINE)]
    assert tuple(chapters) == CHAPTERS, chapters
    assert "第十七章" not in body

    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(units) == 121, len(units)
    assert Counter(level for _, level in units) == {"一级": 25, "二级": 96}
    assert "八、边缘系统、海马与杏仁核【二级】" in body
    assert not any(token in body for token in FORBIDDEN_BODY)
    assert "<u>" not in body and "==" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body), "正文存在斜体标记"
    assert not re.search(r"^####\s+答案", body, re.MULTILINE)

    blocks = question_blocks(body)
    kinds = Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks)
    assert len(blocks) == 150, len(blocks)
    assert kinds == {"简答": 109, "论述": 41}, kinds

    current_unit = None
    question_count_by_unit: Counter[str] = Counter()
    for line in body.splitlines():
        if line.startswith("## "):
            current_unit = line
        elif line.startswith("### 押题"):
            assert current_unit is not None
            question_count_by_unit[current_unit] += 1
    assert max(question_count_by_unit.values()) <= 4

    definitions: dict[str, set[str]] = defaultdict(set)
    simple_lengths: list[tuple[int, int, str]] = []
    essay_lengths: list[tuple[int, int, str]] = []
    for heading, block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and line.strip() != "---"]
        assert lines, heading
        assert not re.match(r"^(?:\d+\.\s|（\d+）)", plain(lines[0])), f"缺少总起：{heading}"
        assert any(re.match(r"^1\.\s", plain(line)) for line in lines), f"缺少一级分点：{heading}"
        summary_positions = [i for i, line in enumerate(lines) if plain(line).startswith("综上")]
        assert summary_positions, f"缺少总结：{heading}"
        assert summary_positions[-1] in {len(lines) - 1, len(lines) - 2}, f"总结位置异常：{heading}"
        if summary_positions[-1] == len(lines) - 2:
            assert lines[-1].startswith("【扩容（选用）："), f"总结后存在非整题扩容：{heading}"

        for line in lines:
            plain_line = plain(line)
            previous_tag_end = 0
            for match in TAG_RE.finditer(plain_line):
                definition = normalized_definition(plain_line, previous_tag_end, match.start())
                assert definition.endswith("。"), (heading, match.group(1), definition)
                definitions[match.group(1)].add(definition)
                previous_tag_end = match.end()
            for expansion in EXPANSION_RE.findall(line):
                assert expansion.endswith("。】") or expansion.endswith("！】") or expansion.endswith("？】"), expansion

        lengths = (
            visible_length(block, include_expansion=False),
            visible_length(block, include_expansion=True),
            heading,
        )
        (simple_lengths if "【简答】" in heading else essay_lengths).append(lengths)

    conflicts = {name: values for name, values in definitions.items() if len(values) > 1}
    assert not conflicts, conflicts
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }
    assert len(definitions) == 263, len(definitions)

    assert min(item[0] for item in simple_lengths) >= 150
    assert max(item[0] for item in simple_lengths) <= 470
    assert min(item[0] for item in essay_lengths) >= 350
    assert max(item[0] for item in essay_lengths) <= 620
    simple_median = statistics.median(item[0] for item in simple_lengths)
    essay_median = statistics.median(item[0] for item in essay_lengths)
    assert 1.5 <= essay_median / simple_median <= 2.1

    print(
        "全本内容验证通过："
        f"{len(chapters)}章、{len(units)}个单元、{len(blocks)}道押题；"
        f"{len(definitions)}个名词解释无异文；"
        f"简答基础容量中位数{simple_median:.0f}字，论述{essay_median:.0f}字，"
        f"容量比{essay_median / simple_median:.2f}。"
    )


if __name__ == "__main__":
    main()
