from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics


MARKDOWN = Path("deliverables/华东师范大学347心理测量保命手册_全本_逐题直背版V1.md")
CHAPTERS = tuple(f"第{name}章" for name in "一二三四五六七八九十") + ("第十一章",)
TAG_RE = re.compile(r"【名词解释：([^】]+)】")
EXPANSION_RE = re.compile(r"【扩容（选用）：.*?】")
FORBIDDEN = (
    "XXXX", "待补充", "答题思路", "到此停笔", "【共用】", "【本题补充】",
    "【加分项】", "【采分点加分】", "答案\n",
)


def plain(text: str) -> str:
    return text.replace("**", "")


def question_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^### (押题\d+【(简答|论述)】[^\n]+)$", text, re.MULTILINE))
    result = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = re.split(r"(?=^#{1,2} )", text[match.end():end], 1, flags=re.MULTILINE)[0]
        result.append((match.group(1), block.strip()))
    return result


def normalize_definition(markdown_segment: str) -> str:
    value = plain(markdown_segment).strip()
    value = re.sub(r"^(?:\d+\.\s*|（\d+）\s*)", "", value)
    if "：" in value:
        label, definition = value.split("：", 1)
        if len(label) <= 24 and definition:
            value = definition.strip()
    return value


def visible_length(text: str, include_expansion: bool) -> int:
    if not include_expansion:
        text = EXPANSION_RE.sub("", text)
    text = TAG_RE.sub("", text)
    text = text.replace("【扩容（选用）：", "").replace("】", "").replace("**", "")
    return len(re.sub(r"\s+|---", "", text))


def main() -> None:
    text = MARKDOWN.read_text(encoding="utf-8")
    body = text[text.index("# 第一章 "):]
    chapters = tuple(match.group(1) for match in re.finditer(r"^# (第[^\s]+章)", body, re.MULTILINE))
    assert chapters == CHAPTERS, chapters

    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(units) == 39
    assert Counter(level for _, level in units) == {"一级": 29, "二级": 10}
    blocks = question_blocks(body)
    assert len(blocks) == 45
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 41,
        "论述": 4,
    }

    assert not any(token in body for token in FORBIDDEN)
    assert "<u>" not in body and "==" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body), "正文存在斜体标记"
    assert not re.search(r"^####\s+答案", body, re.MULTILINE)
    assert not any(line.startswith("【扩容（选用）：") for line in body.splitlines())

    definitions: dict[str, set[str]] = defaultdict(set)
    formatted_definitions: dict[str, set[str]] = defaultdict(set)
    simple_lengths = []
    essay_lengths = []
    shared_lines: dict[str, set[str]] = defaultdict(set)

    for line in body.splitlines():
        if line and not line.startswith("#") and line != "---":
            shared_lines[plain(line)].add(line)
        plain_line = plain(line)
        previous = 0
        for match in TAG_RE.finditer(plain_line):
            definition = normalize_definition(plain_line[previous:match.start()])
            assert definition.endswith("。"), (match.group(1), definition)
            definitions[match.group(1)].add(definition)
            previous = match.end()

        previous = 0
        for match in TAG_RE.finditer(line):
            segment = line[previous:match.start()].strip()
            plain_segment = plain(segment)
            if re.match(r"^(?:\d+\.\s*|（\d+）\s*)", plain_segment):
                colon = segment.find("：")
                if 0 <= colon < 60:
                    segment = segment[colon + 1:].strip()
            formatted_definitions[match.group(1)].add(segment)
            previous = match.end()

        for expansion in EXPANSION_RE.findall(line):
            assert expansion.endswith(("。】", "！】", "？】")), expansion

    assert len(definitions) == 60
    assert sum(len(TAG_RE.findall(line)) for line in body.splitlines()) == 81
    assert not {name: values for name, values in definitions.items() if len(values) > 1}
    assert not {name: values for name, values in formatted_definitions.items() if len(values) > 1}
    assert not {line: variants for line, variants in shared_lines.items() if len(variants) > 1}
    assert body.count("【扩容（选用）：") == 103

    assert definitions["标准化"] == {"指测验的内容、实施、记分和分数解释的一致性。"}
    assert definitions["智龄"] == {
        "测题按年龄分组，儿童通过相应测题所得分数代表其智力年龄；"
        "智龄可以与实龄比较以衡量智力水平，但只能表示智力的绝对水平，"
        "不能比较不同实龄儿童的智力高低。"
    }
    assert definitions["投射测验"] == {
        "投射测验是通过提供未经组织的刺激情境，让受测者自由反应，以推断其人格情况的测验。"
    }

    for heading, block in blocks:
        lines = [line for line in block.splitlines() if line.strip() and line.strip() != "---"]
        assert lines and not re.match(r"^(?:\d+\.\s|（\d+）)", plain(lines[0])), heading
        assert any(re.match(r"^1\.\s", plain(line)) for line in lines), heading
        summaries = [index for index, line in enumerate(lines) if plain(line).startswith("综上")]
        assert summaries and summaries[-1] == len(lines) - 1, heading
        values = (visible_length(block, False), visible_length(block, True), heading)
        (simple_lengths if "【简答】" in heading else essay_lengths).append(values)

    assert min(item[0] for item in simple_lengths) >= 220
    assert max(item[0] for item in simple_lengths) <= 540
    assert min(item[0] for item in essay_lengths) >= 570
    assert max(item[0] for item in essay_lengths) <= 780
    simple_median = statistics.median(item[0] for item in simple_lengths)
    essay_median = statistics.median(item[0] for item in essay_lengths)
    assert 1.75 <= essay_median / simple_median <= 2.1

    lines = body.splitlines()
    leaf_count = 0
    for index, line in enumerate(lines):
        if not re.match(r"^(?:\d+\.\s|（\d+）)", line):
            continue
        level = 1 if re.match(r"^\d+\.", line) else 2
        next_level = 0
        for following in lines[index + 1:]:
            if not following.strip():
                continue
            if re.match(r"^\d+\.", following):
                next_level = 1
            elif re.match(r"^（\d+）", following):
                next_level = 2
            break
        if next_level > level:
            continue
        leaf_count += 1
        main = line.split("【扩容（选用）：", 1)[0]
        plain_main = plain(main)
        colon = plain_main.find("：")
        content = main[main.find("：") + 1:] if 0 <= colon < 45 else main
        assert re.search(r"\*\*.+?\*\*", content), line

    print(
        "测量保命手册V1内容验证通过："
        f"11章、39单元（一级29／二级10）、45题（简答41／论述4）；"
        f"60个名词解释、81处调用零异文，103处同行扩容；"
        f"{leaf_count}个叶子采分点均有正文关键词；"
        f"简答基础容量中位数{simple_median:.0f}字，论述{essay_median:.0f}字，"
        f"容量比{essay_median / simple_median:.2f}。"
    )


if __name__ == "__main__":
    main()
