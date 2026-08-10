from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from build_experiment_baoming_v1 import GUIDE, OUTPUT, render_body, source_expansion_contents


TAG_RE = re.compile(r"【名词解释：([^】]+)】")
QUESTION_RE = re.compile(r"^### 押题\d+【(简答|论述)】.+$", re.MULTILINE)
RESERVED = {"简答", "论述", "★★★", "★★", "★"}
CHAPTERS = (
    "第一章 绪论",
    "第二章 实验研究的基本问题",
    "第四章 反应时",
    "第五章 心理物理学",
    "第六章 注意",
    "第七章 知觉",
    "第八章 记忆与学习",
    "第九章 思维",
    "第十章 情绪",
    "常见的心理学实验",
    "心理学研究中的新技术",
)


def plain(value: str) -> str:
    return re.sub(r"\*\*|__|`|\s+", "", value)


def question_blocks(text: str) -> list[tuple[str, str, str]]:
    matches = list(QUESTION_RE.finditer(text))
    result: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end() : end]
        block = re.sub(r"^#{1,2} .*$", "", block, flags=re.MULTILINE)
        result.append((match.group(0), match.group(1), block.strip()))
    return result


def answer_length(block: str) -> int:
    return len(re.sub(r"[\s*`#]", "", block))


def main() -> None:
    text = OUTPUT.read_text(encoding="utf-8")
    expected = (
        "# 华东师范大学347实验心理学保命手册\n\n"
        "## 全本·极简直背版V1\n\n"
        + GUIDE
        + "---\n\n"
        + render_body()
    )
    assert text == expected, "成品Markdown不是构建脚本的确定性输出"

    front, body = text.split("# 第一章 绪论", 1)
    body = "# 第一章 绪论" + body
    for phrase in (
        "★★★ 核心优先",
        "★★ 重点掌握",
        "★ 基础覆盖",
        "速背手册原一级",
        "速背手册原二级",
        "一本通与考纲",
        "华东或相关真题信号强",
        "圆括号外是背诵主体",
        "`（）`内是扩容项，选背",
        "例子，可以根据题目灵活替换",
    ):
        assert phrase in front, phrase
    for forbidden in (
        "星级只表示背诵顺序，不代表必考概率",
        "扩容（选背）",
        "扩容（选用）",
        "例子可灵活替换",
        "答题思路",
        "到此停笔",
    ):
        assert forbidden not in body, forbidden

    chapters = tuple(
        match.group(1)
        for match in re.finditer(r"^# (.+)$", body, re.MULTILINE)
    )
    assert chapters == CHAPTERS, chapters
    units = re.findall(r"^## (.+)【(★★★|★★|★)】$", body, re.MULTILINE)
    assert len(units) == 49
    assert Counter(level for _, level in units) == {"★★★": 18, "★★": 17, "★": 14}

    blocks = question_blocks(body)
    assert len(blocks) == 49
    assert Counter(question_type for _, question_type, _ in blocks) == {
        "简答": 35,
        "论述": 14,
    }
    simple_lengths: list[int] = []
    essay_lengths: list[int] = []
    for heading, question_type, block in blocks:
        assert "综上" in block, heading
        point_count = len(re.findall(r"^\d+\. ", block, re.MULTILINE))
        definition_count = block.count("【名词解释：")
        scoring_units = point_count + definition_count
        assert point_count >= 3, (heading, point_count)
        assert scoring_units >= (6 if question_type == "论述" else 3), (
            heading,
            scoring_units,
        )
        first_point = re.search(r"^1\. ", block, re.MULTILINE)
        assert first_point is not None and block[: first_point.start()].strip(), heading
        for line in block.splitlines():
            if re.match(r"^\d+\. ", line):
                assert "**" in line, (heading, line)
        length = answer_length(block)
        if question_type == "简答":
            assert 280 <= length <= 530, (heading, length)
            simple_lengths.append(length)
        else:
            assert 500 <= length <= 820, (heading, length)
            essay_lengths.append(length)
    assert statistics.median(essay_lengths) / statistics.median(simple_lengths) >= 1.4

    assert "[[" not in body and "]]" not in body
    expansions = source_expansion_contents("")
    assert len(expansions) == 116
    for wrapped, count in Counter(f"（{value}）" for value in expansions).items():
        assert body.count(wrapped) >= count, wrapped
    assert not re.search(r"^（(?!\d+）)", body, re.MULTILINE), "扩容项被错误拆成独立段落"

    assert body.count("【名词解释：") == 73
    assert "\u2060" not in body
    definition_modules: dict[str, set[str]] = defaultdict(set)
    for line in body.splitlines():
        tags = TAG_RE.findall(line)
        assert len(tags) <= 1, line
        if not tags:
            continue
        assert TAG_RE.search(line) is not None
        assert TAG_RE.search(line).end() == len(line), line
        assert re.search(r"（[^（）]+）【名词解释：[^】]+】$", line), line
        assert "**" in line, "名解核心句没有关键词标注：" + line
        name = tags[0]
        definition_modules[name].add(plain(line[: line.index("【名词解释：")]))
    assert len(definition_modules) == 69
    assert not {
        name: values for name, values in definition_modules.items() if len(values) != 1
    }, "重复名解存在异文"
    assert all(
        value in RESERVED or value.startswith("名词解释：")
        for value in re.findall(r"【(.*?)】", body)
    ), "正文仍有非名解方括号扩容"

    print(
        "实验心理学保命手册V1内容验证通过："
        "11个一级章节、49单元（★★★18／★★17／★14）、"
        "49题（简答35／论述14）；69个唯一名解、73处调用、"
        f"116处圆括号扩容；简答中位{statistics.median(simple_lengths):.0f}字，"
        f"论述中位{statistics.median(essay_lengths):.0f}字。"
    )


if __name__ == "__main__":
    main()
