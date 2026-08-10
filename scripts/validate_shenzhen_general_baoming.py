from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.md"
TITLE = "# 深圳大学347普通心理学保命手册"
ALLOWED_BRACKETS = {"简答", "论述", "★★★", "★★", "★"}


def compact(text: str) -> str:
    return re.sub(r"[\s*`]", "", text)


def question_blocks(lines: list[str]) -> list[tuple[int, str, str]]:
    headings = [(index, line) for index, line in enumerate(lines) if line.startswith("### 押题")]
    result: list[tuple[int, str, str]] = []
    for offset, (index, heading) in enumerate(headings):
        stop = next(
            (
                cursor
                for cursor in range(index + 1, len(lines))
                if lines[cursor].startswith(("### 押题", "## ", "# "))
            ),
            len(lines),
        )
        result.append((index + 1, heading, "\n".join(lines[index + 1 : stop]).replace("---", "")))
    return result


def normalized_definition_line(line: str) -> str:
    return re.sub(r"^\d+\.\s*", "", line)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0] == TITLE
    first_chapter = next(index for index, line in enumerate(lines) if line.startswith("# 第一章 "))
    front = "\n".join(lines[:first_chapter])
    body = "\n".join(lines[first_chapter:])

    assert front.count("## 星级") == 1 and front.count("## 怎么用") == 1
    assert "圆括号外是背诵主体" in front and "`（）`内是扩容项，选背" in front
    for phrase in ("答题思路", "到此停笔", "共用", "本题补充", "可灵活替换", "【扩容"):
        assert phrase not in body, phrase
    assert "选背" not in body and "选用" not in body
    assert "_" not in body, "正文存在斜体或下划线Markdown标记"
    assert text.count("（") == text.count("）")

    chapters = [line for line in lines if re.match(r"^# 第[一二三四五六七八九十]+章 ", line)]
    assert len(chapters) == 14, len(chapters)
    assert sum(line.startswith("# 补充章 ") for line in lines) == 1
    units = re.findall(r"^## .+【(★★★|★★|★)】$", body, re.MULTILINE)
    assert units and len(units) == sum(line.startswith("## ") for line in lines[first_chapter:])

    blocks = question_blocks(lines)
    assert blocks
    types = Counter("简答" if "【简答】" in heading else "论述" for _, heading, _ in blocks)
    assert sum(types.values()) == len(blocks)
    assert all(re.fullmatch(r"### 押题\d+【(?:简答|论述)】.+", heading) for _, heading, _ in blocks)

    simple_lengths: list[int] = []
    essay_lengths: list[int] = []
    for line_number, heading, answer in blocks:
        length = len(compact(answer))
        assert answer.strip().endswith("。"), (line_number, heading)
        if "【简答】" in heading:
            assert 350 <= length <= 750, ("简答容量", line_number, length, heading)
            simple_lengths.append(length)
        else:
            assert 500 <= length <= 1250, ("论述容量", line_number, length, heading)
            essay_lengths.append(length)
    assert statistics.median(essay_lengths) >= statistics.median(simple_lengths) * 1.4

    definitions: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for line_number, line in enumerate(lines, 1):
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        assert len(tags) <= 1, ("同段堆放多个名解", line_number)
        if not tags:
            continue
        assert line.endswith(f"【名词解释：{tags[0]}】"), ("名解标签不在句末", line_number)
        definition = line[: line.rfind("【名词解释：")]
        assert len(compact(definition)) >= 25, ("名解容量不足", line_number, tags[0])
        definitions[tags[0]].append((line_number, line))
    assert definitions
    for term, occurrences in definitions.items():
        variants = {normalized_definition_line(line) for _, line in occurrences}
        assert len(variants) == 1, ("重复名解表述不一致", term, occurrences)

    for bracket in re.findall(r"【([^】]+)】", body):
        assert bracket in ALLOWED_BRACKETS or bracket.startswith("名词解释："), bracket

    quarter_ratios: list[float] = []
    for quarter in range(4):
        chunk = "\n".join(
            lines[len(lines) * quarter // 4 : len(lines) * (quarter + 1) // 4]
        )
        total = len(re.sub(r"\s", "", chunk))
        bold = sum(len(value) for value in re.findall(r"\*\*([^*]+)\*\*", chunk))
        ratio = bold / total
        assert ratio >= 0.055, ("分段关键词密度过低", quarter + 1, ratio)
        quarter_ratios.append(ratio)

    long_scoring_lines = [
        (index, line)
        for index, line in enumerate(lines, 1)
        if re.match(r"^\d+\.\s", line) and len(compact(line)) >= 35
    ]
    assert all(re.search(r"\*\*[^*]+\*\*", line) for _, line in long_scoring_lines)

    print(
        "PASS "
        f"chapters={len(chapters)} units={len(units)} stars={dict(Counter(units))} "
        f"questions={len(blocks)} types={dict(types)} definitions={len(definitions)} "
        f"simple_median={statistics.median(simple_lengths):.0f} "
        f"essay_median={statistics.median(essay_lengths):.0f} "
        f"keyword_quarters={[round(value, 3) for value in quarter_ratios]}"
    )


if __name__ == "__main__":
    main()
