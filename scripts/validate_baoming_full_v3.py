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


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_现行范围重编版V3.md")
CHAPTERS = (
    "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章",
    "第九章", "第十章", "第十一章", "第十二章", "第十三章", "第十四章", "第十五章",
    "第十六章", "第十八章",
)
NUMERALS = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
    "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13,
}
FORBIDDEN_BODY = (
    "XXXX", "待补充", "答题思路", "到此停笔", "【共用】", "【本题补充】",
    "人本主义人格理论", "耶鲁态度改变模型", "社会抑制", "旁观者效应",
    "利他行为", "偏见", "格雷", "强化敏感性理论", "行为趋近系统",
    "行为抑制系统", "BAS", "BIS",
)


def chapter_sections(body: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^# (第[^\s]+章)[^\n]*$", body, re.MULTILINE))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result.append((match.group(1), body[match.start():end]))
    return result


def main() -> None:
    text = MARKDOWN.read_text(encoding="utf-8")
    body = text[text.index("# 第一章 "):]
    chapters = chapter_sections(body)
    assert tuple(name for name, _ in chapters) == CHAPTERS
    assert "第十七章" not in body

    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(units) == 117, len(units)
    assert Counter(level for _, level in units) == {"一级": 22, "二级": 95}
    assert not any(token in body for token in FORBIDDEN_BODY), {
        token for token in FORBIDDEN_BODY if token in body
    }
    assert "<u>" not in body and "==" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body), "正文存在斜体标记"
    assert not re.search(r"^####\s+答案", body, re.MULTILINE)

    chapter_metrics: dict[str, dict[str, int]] = {}
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

        current_unit = ""
        question_numbers: list[int] = []
        for line in section.splitlines() + ["## END"]:
            if line.startswith("## "):
                if current_unit:
                    assert question_numbers == list(range(1, len(question_numbers) + 1)), (
                        chapter, current_unit, question_numbers,
                    )
                current_unit = line
                question_numbers = []
            elif line.startswith("### 押题"):
                question_numbers.append(int(re.match(r"### 押题(\d+)", line).group(1)))

    blocks = question_blocks(body)
    kinds = Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks)
    assert len(blocks) == 145, len(blocks)
    assert kinds == {"简答": 107, "论述": 38}, kinds
    expansion_count = body.count("【扩容（选用）：")
    assert expansion_count == 438, expansion_count

    # 同一知识单元内、范围相近的同题型答案不得出现两倍以上的容量悬殊。
    unit_matches = list(re.finditer(r"^## [^\n]+$", body, re.MULTILINE))
    for index, unit_match in enumerate(unit_matches):
        unit_end = unit_matches[index + 1].start() if index + 1 < len(unit_matches) else len(body)
        unit_blocks = question_blocks(body[unit_match.start():unit_end])
        for kind in ("简答", "论述"):
            lengths = [
                visible_length(block, include_expansion=False)
                for heading, block in unit_blocks if f"【{kind}】" in heading
            ]
            if len(lengths) >= 2:
                assert max(lengths) / min(lengths) <= 2.0, (unit_match.group(0), kind, lengths)

    definitions: dict[str, set[str]] = defaultdict(set)
    simple_lengths: list[tuple[int, int, str]] = []
    essay_lengths: list[tuple[int, int, str]] = []
    for heading, block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and line.strip() != "---"]
        assert lines, heading
        assert not re.match(r"^(?:\d+\.\s|（\d+）)", plain(lines[0])), f"缺少总起：{heading}"
        assert any(re.match(r"^1\.\s", plain(line)) for line in lines), f"缺少一级分点：{heading}"
        summary_positions = [index for index, line in enumerate(lines) if plain(line).startswith("综上")]
        assert summary_positions, f"缺少总结：{heading}"
        assert summary_positions[-1] in {len(lines) - 1, len(lines) - 2}, f"总结位置异常：{heading}"
        if summary_positions[-1] == len(lines) - 2:
            assert lines[-1].startswith("【扩容（选用）："), f"总结后存在非整题扩容：{heading}"

        previous_line = ""
        for line in lines:
            plain_line = plain(line)
            previous_tag_end = 0
            for match in TAG_RE.finditer(plain_line):
                definition = normalized_definition(plain_line, previous_tag_end, match.start())
                assert definition.endswith("。"), (heading, match.group(1), definition)
                definitions[match.group(1)].add(definition)
                previous_tag_end = match.end()

            expansions = EXPANSION_RE.findall(line)
            if line.startswith("【扩容（选用）："):
                assert previous_line.startswith("综上"), f"局部扩容被另起一行：{heading}｜{line}"
                assert line == lines[-1], f"整题扩容未置于末尾：{heading}"
            for expansion in expansions:
                assert expansion.endswith(("。】", "！】", "？】")), expansion
                content = expansion.removeprefix("【扩容（选用）：").removesuffix("】").strip()
                assert len(content) >= 8, (heading, expansion)
                if not line.startswith("【扩容（选用）："):
                    before = line[:line.index(expansion)].replace("**", "").strip()
                    assert before, f"扩容前缺少对应采分点：{heading}｜{line}"
            previous_line = plain_line

        lengths = (
            visible_length(block, include_expansion=False),
            visible_length(block, include_expansion=True),
            heading,
        )
        (simple_lengths if "【简答】" in heading else essay_lengths).append(lengths)

    conflicts = {name: values for name, values in definitions.items() if len(values) > 1}
    assert not conflicts, conflicts
    assert len(definitions) == 256, len(definitions)
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }

    assert min(item[0] for item in simple_lengths) >= 150
    assert max(item[0] for item in simple_lengths) <= 480
    assert min(item[0] for item in essay_lengths) >= 350
    assert max(item[0] for item in essay_lengths) <= 620
    simple_median = statistics.median(item[0] for item in simple_lengths)
    essay_median = statistics.median(item[0] for item in essay_lengths)
    simple_full_median = statistics.median(item[1] for item in simple_lengths)
    essay_full_median = statistics.median(item[1] for item in essay_lengths)
    assert 1.5 <= essay_median / simple_median <= 2.1
    essay_call_ratio = essay_full_median / simple_median
    assert 1.8 <= essay_call_ratio <= 2.2

    print(
        "全本V3内容与格式验证通过："
        f"{len(chapters)}章、{len(units)}个单元、{len(blocks)}道押题；"
        f"{len(definitions)}个名词解释无异文；{expansion_count}处扩容完成位置检查；"
        f"简答基础容量中位数{simple_median:.0f}字，论述{essay_median:.0f}字，"
        f"简答含扩容中位数{simple_full_median:.0f}字，论述含扩容{essay_full_median:.0f}字；"
        f"论述完整调用／简答基础比{essay_call_ratio:.2f}；"
        f"逐章指标={chapter_metrics}。"
    )


if __name__ == "__main__":
    main()
