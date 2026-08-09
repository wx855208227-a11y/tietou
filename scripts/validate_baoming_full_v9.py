from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

from build_baoming_full_v9 import transform
from validate_baoming_full_v1 import question_blocks
from validate_baoming_full_v3 import CHAPTERS, chapter_sections
from validate_baoming_full_v4 import leaf_point_lines
from validate_baoming_full_v5 import body_keyword_terms


V8 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_三星分级舒适阅读版V8.md")
V9 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_极简直背版V9.md")
RESERVED = {"简答", "论述", "★★★", "★★", "★"}


def body(text: str) -> str:
    return text[text.index("# 第一章 ") :]


def expansion_contents(content: str) -> list[str]:
    result = []
    for value in re.findall(r"【(.*?)】", content):
        plain = value.replace("**", "")
        if plain in RESERVED or plain.startswith("名词解释："):
            continue
        result.append(value)
    return result


def main() -> None:
    v8 = V8.read_text(encoding="utf-8")
    text = V9.read_text(encoding="utf-8")
    assert text == transform(v8), "V9不是V8的纯呈现规则转换"
    front = text[: text.index("# 第一章 ")]
    for phrase in (
        "速背手册原一级",
        "一本通与考纲",
        "华东或相关真题信号强",
        "主观题可考性",
        "答案复用价值",
        "方括号外是背诵主体",
        "可以拿到主要分数",
        "【】`内是扩容项，选背",
        "丰富答题角度、锦上添花",
        "例子，可以根据题目灵活替换",
    ):
        assert phrase in front, phrase
    assert front.count("### ") == 2

    content = body(text)
    assert "扩容（选背）" not in content
    assert "扩容（选用）" not in content
    assert "例子可灵活替换" not in content
    assert "固定例子可选用" not in content
    assert content.count("【名词解释：") == 296
    expansions = expansion_contents(content)
    assert len(expansions) == 596

    units = re.findall(r"^## .+【(★★★|★★|★)】$", content, re.MULTILINE)
    assert Counter(units) == {"★★★": 44, "★★": 40, "★": 33}
    blocks = question_blocks(content)
    assert len(blocks) == 145
    assert Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks) == {
        "简答": 107,
        "论述": 38,
    }

    chapters = chapter_sections(content)
    assert tuple(name for name, _ in chapters) == CHAPTERS
    leaf_total = 0
    chapter_stats = {}
    for chapter, section in chapters:
        leaf_count = covered = 0
        for _, block in question_blocks(section):
            for line in leaf_point_lines(block):
                leaf_count += 1
                if body_keyword_terms(line):
                    covered += 1
        assert leaf_count == covered
        leaf_total += leaf_count
        chapter_stats[chapter] = (leaf_count, covered)
    assert leaf_total == 789

    print(
        "全本V9内容验证通过："
        "V8知识内容零漂移；17章、117单元（★★★44／★★40／★33）、"
        "145题（简答107／论述38）；296处名解、596处纯方括号扩容；"
        f"789个叶子采分点关键词覆盖={chapter_stats}。"
    )


if __name__ == "__main__":
    main()
