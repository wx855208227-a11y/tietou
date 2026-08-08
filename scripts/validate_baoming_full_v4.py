from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from validate_baoming_full_v1 import (
    EXPANSION_RE,
    TAG_RE,
    normalized_definition,
    plain,
    question_blocks,
    visible_length,
)
from validate_baoming_full_v3 import CHAPTERS, FORBIDDEN_BODY, NUMERALS, chapter_sections


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_综合证据重编版V4.md")
EVIDENCE = Path("analysis/华东心理学导论保命手册V4_押题证据矩阵.md")


def body_bold_terms(line: str) -> list[str]:
    main = line.split("【扩容（选用）：", 1)[0]
    main = re.sub(r"\*\*【名词解释：.*?】\**", "", main)
    plain_main = main.replace("**", "")
    colon = plain_main.find("：")
    if colon >= 0 and colon < 28:
        # 分点小标题后的正文关键词，排除只加粗小标题的假覆盖。
        markdown_colon = main.find("：")
        main = main[markdown_colon + 1:]
    return [term for term in re.findall(r"\*\*(.+?)\*\*", main) if term.strip()]


def leaf_point_lines(block: str) -> list[str]:
    lines = [line.strip() for line in block.splitlines() if line.strip() and line.strip() != "---"]
    points = []
    for index, line in enumerate(lines):
        if not re.match(r"^(?:\d+\.\s|（\d+）)", plain(line)):
            continue
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if re.match(r"^\d+\.\s", plain(line)) and re.match(r"^（\d+）", plain(next_line)):
            continue
        points.append(line)
    return points


def main() -> None:
    text = MARKDOWN.read_text(encoding="utf-8")
    body = text[text.index("# 第一章 "):]
    chapters = chapter_sections(body)
    assert tuple(name for name, _ in chapters) == CHAPTERS
    assert "第十七章" not in body

    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(units) == 117
    assert Counter(level for _, level in units) == {"一级": 84, "二级": 33}
    assert not any(token in body for token in FORBIDDEN_BODY), {
        token for token in FORBIDDEN_BODY if token in body
    }
    assert "<u>" not in body and "==" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body), "正文存在斜体标记"
    assert not re.search(r"^####\s+答案", body, re.MULTILINE)

    chapter_metrics: dict[str, dict[str, int | float]] = {}
    for chapter, section in chapters:
        unit_numbers = [
            NUMERALS[number]
            for number in re.findall(r"^## ([一二三四五六七八九十]+)、", section, re.MULTILINE)
        ]
        assert unit_numbers == list(range(1, len(unit_numbers) + 1)), (chapter, unit_numbers)
        chapter_metrics[chapter] = {
            "units": len(unit_numbers),
            "questions": len(re.findall(r"^### 押题", section, re.MULTILINE)),
            "definitions": section.count("【名词解释："),
            "expansions": section.count("【扩容（选用）："),
        }

    blocks = question_blocks(body)
    kinds = Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks)
    assert len(blocks) == 145
    assert kinds == {"简答": 107, "论述": 38}
    assert body.count("【扩容（选用）：") == 438

    # 每题都必须在内部矩阵中只有一条证据记录。
    evidence = EVIDENCE.read_text(encoding="utf-8")
    evidence_rows = re.findall(r"^\| \d+ \|", evidence, re.MULTILINE)
    assert len(evidence_rows) == len(blocks), len(evidence_rows)
    assert "既往题型不是预测上限" in evidence
    assert "不补造年份或题型" in evidence

    definitions: dict[str, set[str]] = defaultdict(set)
    simple_lengths: list[tuple[int, int, str]] = []
    essay_lengths: list[tuple[int, int, str]] = []
    keyword_misses = []
    chapter_keyword_counts = defaultdict(lambda: [0, 0])
    current_chapter = ""
    for heading, block in blocks:
        chapter_matches = re.findall(r"# (第[^\s]+章)", body[:body.find(heading)])
        if chapter_matches:
            current_chapter = chapter_matches[-1]
        lines = [line.strip() for line in block.splitlines() if line.strip() and line.strip() != "---"]
        assert lines and not re.match(r"^(?:\d+\.\s|（\d+）)", plain(lines[0])), heading
        assert any(re.match(r"^1\.\s", plain(line)) for line in lines), heading
        summaries = [index for index, line in enumerate(lines) if plain(line).startswith("综上")]
        assert summaries and summaries[-1] in {len(lines) - 1, len(lines) - 2}, heading

        previous_line = ""
        for line in lines:
            plain_line = plain(line)
            previous_tag_end = 0
            for match in TAG_RE.finditer(plain_line):
                definition = normalized_definition(plain_line, previous_tag_end, match.start())
                assert definition.endswith("。"), (heading, match.group(1), definition)
                definitions[match.group(1)].add(definition)
                previous_tag_end = match.end()
            for expansion in EXPANSION_RE.findall(line):
                assert expansion.endswith(("。】", "！】", "？】")), expansion
                content = expansion.removeprefix("【扩容（选用）：").removesuffix("】").strip()
                assert len(content) >= 8
                if not line.startswith("【扩容（选用）："):
                    assert line[:line.index(expansion)].replace("**", "").strip()
            if line.startswith("【扩容（选用）："):
                assert previous_line.startswith("综上") and line == lines[-1]
            previous_line = plain_line

        for point in leaf_point_lines(block):
            chapter_keyword_counts[current_chapter][0] += 1
            if body_bold_terms(point):
                chapter_keyword_counts[current_chapter][1] += 1
            else:
                keyword_misses.append((heading, point))

        lengths = (
            visible_length(block, include_expansion=False),
            visible_length(block, include_expansion=True),
            heading,
        )
        (simple_lengths if "【简答】" in heading else essay_lengths).append(lengths)

    conflicts = {name: values for name, values in definitions.items() if len(values) > 1}
    assert not conflicts, conflicts
    assert len(definitions) == 256
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }

    # 关键词逐章检查，不能用全书平均值掩盖后半部分衰减。
    assert not keyword_misses, keyword_misses[:20]
    for chapter, (leaf_count, covered) in chapter_keyword_counts.items():
        assert leaf_count and covered == leaf_count, (chapter, leaf_count, covered)
        chapter_metrics[chapter]["keyword_leaf_coverage"] = covered / leaf_count

    assert min(item[0] for item in simple_lengths) >= 150
    assert max(item[0] for item in simple_lengths) <= 480
    assert min(item[0] for item in essay_lengths) >= 350
    assert max(item[0] for item in essay_lengths) <= 620
    simple_median = statistics.median(item[0] for item in simple_lengths)
    essay_median = statistics.median(item[0] for item in essay_lengths)
    simple_full_median = statistics.median(item[1] for item in simple_lengths)
    essay_full_median = statistics.median(item[1] for item in essay_lengths)
    assert 1.5 <= essay_median / simple_median <= 2.1
    assert 1.8 <= essay_full_median / simple_median <= 2.2

    print(
        "全本V4内容验证通过："
        f"{len(chapters)}章、{len(units)}个单元（一级84／二级33）、{len(blocks)}道押题；"
        f"{len(definitions)}个名词解释无异文；438处扩容完成位置检查；"
        f"关键词逐章叶子采分点覆盖率均为100%；"
        f"简答基础／含扩容中位数{simple_median:.0f}/{simple_full_median:.0f}字，"
        f"论述{essay_median:.0f}/{essay_full_median:.0f}字；"
        f"逐章指标={dict(chapter_metrics)}。"
    )


if __name__ == "__main__":
    main()
