from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

from build_baoming_full_v5 import FRAGMENT_WORDS, MANUAL_LINE_KEYWORDS
from validate_baoming_full_v1 import normalized_definition, plain, question_blocks, TAG_RE
from validate_baoming_full_v3 import CHAPTERS, FORBIDDEN_BODY, chapter_sections
from validate_baoming_full_v4 import leaf_point_lines


V4 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_综合证据重编版V4.md")
V5 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_采分关键词精校版V5.md")


def bold_terms(text: str) -> list[str]:
    return re.findall(r"\*\*(.+?)\*\*", text)


def body_keyword_terms(line: str) -> list[str]:
    original_main = line.split("【扩容（选用）：", 1)[0]
    first_tag = original_main.find("【名词解释：")
    main = original_main
    main = re.sub(r"【名词解释：.*?】", "", main)
    plain_main = main.replace("**", "")
    colon = plain_main.find("：")
    if 0 <= colon < 42 and (first_tag < 0 or original_main.find("：") < first_tag):
        main = main[main.find("：") + 1:]
    return bold_terms(main)


def phrase_is_bold(line: str, phrase: str) -> bool:
    return any(phrase in term for term in bold_terms(line))


def main() -> None:
    v4 = V4.read_text(encoding="utf-8")
    v5 = V5.read_text(encoding="utf-8")
    body4 = v4[v4.index("# 第一章 "):]
    body5 = v5[v5.index("# 第一章 "):]

    assert "全本·采分关键词精校版V5" in v5[: v5.index("# 第一章 ")]
    assert body4.replace("**", "") == body5.replace("**", ""), "V5改动了V4正文或结构"
    assert tuple(name for name, _ in chapter_sections(body5)) == CHAPTERS
    assert len(re.findall(r"^## .+【(?:一级|二级)】$", body5, re.MULTILINE)) == 117
    assert Counter(re.findall(r"^## .+【(一级|二级)】$", body5, re.MULTILINE)) == {"一级": 84, "二级": 33}
    assert len(question_blocks(body5)) == 145
    assert body5.count("【扩容（选用）：") == 438
    assert not any(term in body5 for term in FORBIDDEN_BODY)
    assert "<u>" not in body5 and "__" not in body5 and "==" not in body5
    assert not re.search(r"(?<!\*)\*(?!\*)", body5), "正文存在斜体标记"
    assert "****" not in body5 and "即**使" not in body5

    # V5只允许完整关键词短语；标签、例子替换提示和泛化碎片不能被加粗。
    for term in bold_terms(body5):
        assert "【" not in term and "】" not in term
        assert "例子可灵活替换" not in term
        assert not term.startswith(("的", "过的", "并且", "而且")), term
    for line in body5.splitlines():
        if not line or line.startswith("#"):
            continue
        for term in bold_terms(line):
            if term not in FRAGMENT_WORDS:
                continue
            colon = line.find("：")
            # 泛化二字词只允许充当明确的分点标题，不得在正文中冒充采分关键词。
            assert colon >= 0 and f"**{term}**" in line[:colon], (term, line)

    # 同一句在多题复用时，标注必须逐字一致。
    variants: dict[str, set[str]] = defaultdict(set)
    for line in body5.splitlines():
        if line and not line.startswith("#") and line != "---":
            variants[line.replace("**", "")].add(line)
    conflicts = {line: items for line, items in variants.items() if len(items) > 1}
    assert not conflicts, list(conflicts.items())[:5]

    # 名词解释正文没有因关键词重做而产生异文，并且每条定义至少存在一组
    # 定义属性关键词（分点标题本身不计）。
    definitions: dict[str, set[str]] = defaultdict(set)
    zero_definition_keywords = []
    for line in body5.splitlines():
        if "【名词解释：" not in line:
            continue
        plain_line = plain(line)
        previous = 0
        for match in TAG_RE.finditer(plain_line):
            definition = normalized_definition(plain_line, previous, match.start())
            definitions[match.group(1)].add(definition)
            previous = match.end()
        main_line = line.split("【扩容（选用）：", 1)[0]
        without_tags = re.sub(r"【名词解释：.*?】", "", main_line)
        terms = bold_terms(without_tags)
        plain_without_tags = without_tags.replace("**", "")
        colon = plain_without_tags.find("：")
        if 0 <= colon < 35:
            title_terms = set(bold_terms(without_tags[: without_tags.find("：")]))
            terms = [term for term in terms if term not in title_terms]
        if not terms:
            zero_definition_keywords.append(line)
    assert len(definitions) == 256
    assert not {name: values for name, values in definitions.items() if len(values) > 1}
    assert not zero_definition_keywords, zero_definition_keywords[:10]

    expected_psychology = (
        "心理学是研究人的**行为和心理活动规律**的**中间科学**，兼有"
        "**自然科学和社会科学**的性质。【名词解释：心理学】"
        "【扩容（选用）：心理学的研究对象主要包括**心理过程和人格**。】"
    )
    assert expected_psychology in body5

    # 每个叶子采分点至少能从正文关键词还原一个核心关系；逐章分别检查，
    # 不能用全书平均掩盖后半部分衰减。
    chapter_stats = {}
    for chapter, section in chapter_sections(body5):
        leaf_count = covered = 0
        groups = []
        for _, block in question_blocks(section):
            for line in leaf_point_lines(block):
                leaf_count += 1
                terms = body_keyword_terms(line)
                if terms:
                    covered += 1
                    groups.append(len(terms))
        assert leaf_count and covered == leaf_count, (chapter, leaf_count, covered)
        assert 1 <= sum(groups) / len(groups) <= 4, (chapter, groups)
        chapter_stats[chapter] = (leaf_count, covered, round(sum(groups) / len(groups), 2))

    # 人工裁定的复杂句必须完整落到粗体短语中，不能再次被自动切碎。
    plain_lines = {line.replace("**", ""): line for line in body5.splitlines()}
    for source, phrases in MANUAL_LINE_KEYWORDS.items():
        matching = [marked for raw, marked in plain_lines.items() if source in raw]
        assert matching, source
        for phrase in phrases:
            assert all(phrase_is_bold(marked, phrase) for marked in matching), (source, phrase)

    required_samples = (
        "构造主义重在分析意识“**由什么构成**”；机能主义重在说明心理活动“**有什么作用**”",
        "**反射性、非随意的**；操作条件反射的反应是**自主性、随意的**",
        "**开放性、责任心、外向性、宜人性和神经质**",
        "**个人绩效不能被单独评估时**，个体在群体任务中的**努力程度低于独自完成任务时**",
    )
    assert all(sample in body5 for sample in required_samples)

    print(
        "全本V5关键词验证通过：正文与V4逐字一致；"
        "17章、117单元（一级84／二级33）、145题、256个名词解释、438处扩容；"
        "重复句标注零异文；787个叶子采分点逐章均有可还原关键词；"
        f"逐章关键词组统计={chapter_stats}。"
    )


if __name__ == "__main__":
    main()
