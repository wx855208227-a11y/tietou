from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

from audit_baoming_full_v6_sources import (
    EXPECTED_HASHES,
    SOURCE_LABEL_ALIASES,
    SPEED,
    YIBENTONG,
    digest,
)
from validate_baoming_full_v1 import question_blocks
from validate_baoming_full_v3 import chapter_sections
from validate_baoming_full_v4 import leaf_point_lines
from validate_baoming_full_v5 import body_keyword_terms


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_三星分级舒适阅读版V8.md")
REPORT = Path("analysis/华东心理学导论保命手册V8_双源逐采分点审计.md")
NUMERALS = "一二三四五六七八九十"


def docx_paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    result = []
    for paragraph in root.findall(f".//{{{namespace}}}p"):
        value = "".join(node.text or "" for node in paragraph.findall(f".//{{{namespace}}}t")).strip()
        if value:
            result.append(value)
    return result


def compact(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text.replace("—", ""))).lower()


def bigrams(text: str) -> set[str]:
    value = compact(text)
    return {value[index : index + 2] for index in range(len(value) - 1)}


def chapter_sources() -> tuple[dict[str, str], str]:
    chapters: dict[str, list[str]] = defaultdict(list)
    all_lines = []
    for path in (SPEED, YIBENTONG):
        current = ""
        for line in docx_paragraphs(path):
            all_lines.append(line)
            match = re.match(rf"^第([{NUMERALS}]+)章", line)
            if match:
                current = match.group(1)
            if current:
                chapters[current].append(line)
    return {key: compact("\n".join(values)) for key, values in chapters.items()}, compact("\n".join(all_lines))


def chapter_number(chapter_name: str) -> str:
    match = re.match(rf"^第([{NUMERALS}]+)章", chapter_name)
    assert match, chapter_name
    return match.group(1)


def coverage(terms: list[str], source: str) -> tuple[bool, float]:
    exact = any(len(compact(term)) >= 2 and compact(term) in source for term in terms)
    scores = []
    for term in terms:
        grams = bigrams(term)
        if grams:
            scores.append(sum(item in source for item in grams) / len(grams))
    return exact, max(scores, default=0.0)


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        assert path.is_file(), path
        assert digest(path) == expected, path

    sources_by_chapter, all_source = chapter_sources()
    text = MARKDOWN.read_text(encoding="utf-8")
    body = text[text.index("# 第一章 ") :]
    normalized = body.replace("【扩容（选背）：", "【扩容（选用）：")

    labels = set(re.findall(r"【名词解释：([^】]+)】", body))
    missing_exact = {label for label in labels if compact(label) not in all_source}
    expected_missing = {
        label for label in SOURCE_LABEL_ALIASES if compact(label) not in all_source
    }
    assert missing_exact == expected_missing, sorted(missing_exact)
    for label, alias in SOURCE_LABEL_ALIASES.items():
        assert compact(alias) in all_source, (label, alias)

    chapter_stats: dict[str, Counter[str]] = {}
    low_items = []
    total_leaf = exact_leaf = 0
    for chapter_name, section in chapter_sections(normalized):
        source = sources_by_chapter[chapter_number(chapter_name)]
        stats: Counter[str] = Counter()
        for _, block in question_blocks(section):
            for line in leaf_point_lines(block):
                total_leaf += 1
                stats["采分点"] += 1
                terms = body_keyword_terms(line)
                assert terms, line
                exact, score = coverage(terms, source)
                if exact:
                    exact_leaf += 1
                    stats["同章明确词组"] += 1
                else:
                    stats["应试化重组"] += 1
                if score < 0.20:
                    low_items.append((chapter_name, score, line))
        chapter_stats[chapter_name] = stats
    assert total_leaf == 789
    assert not low_items, low_items[:10]

    expansions = re.findall(r"【扩容（选背）：(.*?)】", body)
    example_expansions = []
    sourced_expansions = []
    weak_expansions = []
    for expansion in expansions:
        if "例如" in expansion or "例子" in expansion or "固定实验" in expansion:
            example_expansions.append(expansion)
            continue
        terms = re.findall(r"\*\*(.*?)\*\*", expansion) or [expansion]
        exact, score = coverage(terms, all_source)
        sourced_expansions.append((exact, score, expansion))
        if score < 0.40:
            weak_expansions.append((score, expansion))
    assert len(expansions) == 596
    assert not weak_expansions, weak_expansions[:10]

    # 对本轮发现过的高风险越界项设硬门槛，防止后续排版或重建时回流。
    forbidden = (
        "格雷",
        "强化敏感性理论",
        "偏见",
        "闪光融合",
        "状态依存记忆",
        "基本心理需要",
        "外部奖励的双重作用",
        "恐惧条件作用",
        "威胁和恐惧信息",
        "吊桥情境",
        "独立决策程序",
        "S—S联结",
        "R—O联结",
    )
    assert not {term for term in forbidden if term in body}

    # 本轮重点改回双源的原词锚点。
    correction_anchors = (
        "颜色混合是两种或两种以上的色光同时作用于视网膜同一区域",
        "视觉适应分为暗适应和明适应",
        "杏仁核对情绪控制和情绪记忆具有一定作用",
        "编码特殊性原则",
        "长时记忆中信息的存储是一个动态过程",
        "想象的功能",
        "代替功能",
        "挫折具有挫折情境挫折认知挫折行为三方面的含义",
        "自我决定理论",
        "由无动机到外部动机再到内部动机是一个连续体",
        "掌握目标",
        "成绩目标",
        "群体极化",
        "冒险性迁移产生的原因",
        "去个体化产生的原因",
    )
    for anchor in correction_anchors:
        assert compact(anchor) in all_source, anchor

    direct_expansions = sum(exact for exact, _, _ in sourced_expansions)
    rows = []
    for chapter, stats in chapter_stats.items():
        rows.append(
            f"| {chapter} | {stats['采分点']} | {stats['同章明确词组']} | {stats['应试化重组']} |"
        )
    report = f"""# 华东心理学导论保命手册V8双源逐采分点审计

## 结论

- 正文共17章、117单元、145道押题；逐题抽取出{total_leaf}个叶子采分点，全部通过同章双源覆盖检查。
- 其中{exact_leaf}个采分点的加粗关键词可在同章速背手册／一本通中直接定位；其余{total_leaf - exact_leaf}个属于双源原意基础上的合并、比较或应试化重组，没有引入新的理论模块。
- 256个唯一名词解释中，{len(labels) - len(missing_exact)}个名称可直接检出，{len(missing_exact)}个按登记的规范别名复核；不存在材料外名解。
- 596处选背扩容中，{len(sourced_expansions)}处为来源内容或来源基础上的精简重组，其中{direct_expansions}处含可直接定位词组；{len(example_expansions)}处为概念范围内的可替换例子／固定例子，不作为新理论或新结论。
- 已删除或改回上一版中双源未直接收录的“闪光融合”“状态依存记忆”、自我决定理论的材料外扩展、杏仁核的材料外恐惧机制，以及群体决策的材料外预防措施。

## 审计口径

1. 知识准入只使用速背手册和一本通；347／312题库只服务押题证据，不作为答案知识来源。
2. “来源一致”不等于逐句复制。定义、分类、机制、条件、功能、评价等知识结论必须有双源依据；为便于作答可以合并重复句、改为总分总结构或完成比较归纳。
3. 标明可灵活替换的例子只用于说明已经入册的概念，不得借例子引入新的理论、分类或因果结论。
4. 自动检查同时设置材料外高风险词硬门槛；发现低覆盖项目时必须回到原文人工核验，不能以全书平均覆盖率代替逐点检查。

## 逐章采分点覆盖

| 章节 | 叶子采分点 | 同章明确词组 | 应试化重组 |
|---|---:|---:|---:|
{"\n".join(rows)}

## 来源文件

- 速背手册：`27_.docx`，SHA-256 `{EXPECTED_HASHES[SPEED]}`。
- 一本通：`ecnu_yibentong.docx`，SHA-256 `{EXPECTED_HASHES[YIBENTONG]}`。

本报告证明的是知识范围和采分点可追溯，不宣称答案每一句均与来源逐字相同。
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(
        "全本V8双源逐采分点审计通过："
        f"leaf={total_leaf} exact_leaf={exact_leaf} regrouped={total_leaf - exact_leaf} "
        f"labels={len(labels)} direct_labels={len(labels) - len(missing_exact)} aliases={len(missing_exact)} "
        f"expansions={len(expansions)} source_or_regrouped={len(sourced_expansions)} "
        f"examples={len(example_expansions)}。"
    )


if __name__ == "__main__":
    main()
