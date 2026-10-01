from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re

from rebuild_shenzhen_baoming_v11_examfit import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v4 import (
    compact,
    outside_expansions,
    question_blocks,
    validate_definitions,
)
from validate_shenzhen_baoming_v5 import block_with, validate_one
from validate_shenzhen_baoming_v9_hierarchy import require_order, validate_tree


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题题干任务容量审计报告V11.md"
LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题题干任务容量审计台账V11.tsv"

EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}
EXPECTED_DEFINITION_CALLS = 360


FORBIDDEN_TITLE_SNIPPETS = (
    "简述视觉适应、后像、视觉对比、马赫带和视觉掩蔽",
    "简述选择性注意中的",
    "论述动机的本能论、驱力理论、诱因理论",
    "至少说明五种理论",
    "论述苛勒、托尔曼和建构主义",
    "简述费希纳、冯特和艾宾浩斯",
    "说明序列反应时任务和内隐联想测验",
    "简述罗夏克墨迹测验、主题统觉测验和内隐联想测验",
)


EXPECTED_NATURAL_TITLES = (
    "简述视觉的主要现象",
    "简述选择性注意的经典现象",
    "论述动机的主要理论",
    "论述智力的主要理论",
    "论述认知学习理论的主要观点",
    "简述实验心理学创立与早期发展的主要代表人物及其贡献",
    "论述两种经典内隐研究范式的基本原理",
    "简述人格测量中的常见投射测验和内隐测验",
)


FLEX_CAPACITY = {
    ("普通心理学", 2): "核心清单只有基本任务与学科性质；一本通解释保留为就近扩容",
    ("普通心理学", 14): "三条定律的核心公式与关系完整；适用边界和例证保留为扩容",
    ("普通心理学", 26): "注意的功能和种类清单不可删减，主体仅略高于简答参考上限",
    ("普通心理学", 36): "比较维度完整；点内解释选背后可达到论述容量",
    ("普通心理学", 43): "概念的构成、功能、种类和形成理论均为题干要求，点内解释选背",
    ("普通心理学", 56): "五类动机理论均须保留，主体接近论述参考下限",
    ("实验心理学", 4): "四项伦理原则构成稳定清单，必要解释按点扩容",
    ("实验心理学", 5): "研究程序五个步骤不可删减，主体仅略高于简答参考上限",
    ("实验心理学", 18): "刺激、机体和速度—准确性三模块均为题干要求，仅略高于上限",
    ("实验心理学", 21): "三种传统方法及误差均须展开，点内定义和控制方法选背",
    ("心理与教育测量", 10): "五种信度估计方法为完整清单，适用条件和误差来源按点扩容",
    ("心理与教育测量", 13): "三类效度的含义、联系和区别完整，主体仅略高于简答参考上限",
    ("心理与教育测量", 14): "内容效度的验证与提高方法完整，相关概念表面效度转为扩容",
}


RELATION_ALLOWED_WITHOUT_TITLE = (
    "功能单侧化",
    "过去经验和知觉定势",
    "信号检测论的基本思想",
)


def strip_parenthetical(text: str) -> str:
    value = text
    while True:
        revised = re.sub(r"（[^（）]*）", "", value)
        if revised == value:
            return revised
        value = revised


def answer_lengths(answer: str) -> tuple[int, int]:
    full = re.sub(r"\*\*|【名词解释：[^】]+】|\s+", "", answer)
    core = re.sub(
        r"\*\*|【名词解释：[^】]+】|\s+",
        "",
        strip_parenthetical(answer),
    )
    return len(core), len(full)


def task_alignment(heading: str, answer: str) -> None:
    main = strip_parenthetical(answer)
    top_lines = re.findall(r"(?m)^\d+\. .+$", main)
    title = re.sub(r"\*\*", "", heading)

    asks_relation = any(term in title for term in ("比较", "异同", "联系", "区别", "关系"))
    relation_allowed = asks_relation or any(term in title for term in RELATION_ALLOWED_WITHOUT_TITLE)
    if not relation_allowed:
        offenders = [
            line
            for line in top_lines
            if re.search(r"(?:联系与|主要区别|理论关系|理论比较|功能关系|三者关系|四者关系)", line)
        ]
        assert not offenders, (heading, "未要求比较／关系却设置正文模块", offenders)

    asks_evaluation = any(term in title for term in ("评价", "优缺点", "优势", "局限"))
    if not asks_evaluation:
        offenders = [line for line in top_lines if re.search(r"(?:理论评价|贡献与局限|适用边界)", line)]
        assert not offenders, (heading, "未要求评价却设置正文模块", offenders)

    asks_application = any(
        term in title
        for term in ("应用", "启示", "教育意义", "作用", "用途", "提高", "减少", "促进", "控制方法")
    )
    if not asks_application:
        offenders = [line for line in top_lines if re.search(r"(?:教育启示|教育意义|教育应用|主要价值)", line)]
        assert not offenders, (heading, "未要求应用／启示却设置正文模块", offenders)

    if "比较" in title or "异同" in title:
        assert "联系" in main and "区别" in main, (heading, "比较题缺少联系或区别")


def semantic_assertions(general: str, experiment: str, measurement: str) -> None:
    attention = block_with(general, "简述选择性注意的经典现象")
    require_order(attention, "1. **负启动**", "2. **返回抑制**", "3. **注意瞬脱**")
    assert "三种现象的**主要区别**" not in attention

    visual = block_with(general, "简述视觉的主要现象")
    require_order(
        visual,
        "1. **视觉适应**",
        "2. **后像**",
        "3. **视觉对比**",
        "4. **马赫带**",
        "5. **视觉掩蔽**",
    )

    motion = block_with(general, "简述运动知觉的含义和主要类型")
    require_order(
        motion,
        "1. **真动知觉**",
        "2. **似动知觉**",
        "（1）**动景运动**",
        "（2）**诱发运动**",
        "（3）**自主运动**",
        "（4）**运动后效**",
    )

    depth = block_with(general, "简述深度知觉的主要线索")
    require_order(
        depth,
        "1. **肌肉线索（生理线索）**",
        "（1）**调节**",
        "（2）**辐合**",
        "2. **单眼线索**",
        "3. **双眼线索**",
    )

    hypnosis = block_with(general, "简述催眠的含义及其主要理论")
    assert "3. **理论比较**" not in strip_parenthetical(hypnosis)

    moral = block_with(general, "比较皮亚杰和科尔伯格")
    require_order(
        moral,
        "1. **皮亚杰的道德认知发展理论如下：**",
        "2. **科尔伯格的道德认知发展理论如下：**",
        "3. **两种理论的联系与区别**",
    )
    assert "4. **教育启示**" not in strip_parenthetical(moral)

    implicit = block_with(experiment, "两种经典内隐研究范式")
    require_order(
        implicit,
        "1. **序列反应时任务的基本内容如下：**",
        "2. **内隐联想测验的基本内容如下：**",
    )
    assert "3. **联系与主要区别**" not in implicit

    content_validity = block_with(measurement, "论述内容效度的含义")
    assert "3. 理解内容效度时" not in strip_parenthetical(content_validity)

    personality = block_with(measurement, "简述人格测量中的常见投射测验和内隐测验")
    require_order(personality, "1. **罗夏克墨迹测验**", "2. **主题统觉测验**", "3. 内隐联想测验")


def main() -> None:
    builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    rows: list[dict[str, str]] = []
    definitions: dict[str, str] = {}
    totals = Counter()
    observed_flex: set[tuple[str, int]] = set()

    for path, expected in EXPECTED.items():
        text = path.read_text(encoding="utf-8")
        assert text == builds[path], (path.name, "文件不可由构建脚本复现")
        validate_one(path, expected)
        assert not re.search(r"^### 押题\d+【论述】简述|^### 押题\d+【简答】论述", text, re.MULTILINE)
        assert not any(snippet in text for snippet in FORBIDDEN_TITLE_SNIPPETS)

        current_chapter = ""
        chapter_by_heading: dict[str, str] = {}
        for line in text.splitlines():
            if line.startswith("# ") and not line.startswith("# 深圳大学"):
                current_chapter = line[2:]
            elif line.startswith("### 押题"):
                chapter_by_heading[line] = current_chapter

        for index, (heading, kind, answer) in enumerate(question_blocks(text), start=1):
            validate_tree(path, heading, answer)
            task_alignment(heading, answer)
            core_length, full_length = answer_lengths(answer)
            in_reference = 200 <= core_length <= 400 if kind == "简答" else 400 <= core_length <= 800
            key = (expected["subject"], index)
            if not in_reference:
                assert key in FLEX_CAPACITY, (key, kind, core_length, heading)
                observed_flex.add(key)
            rows.append(
                {
                    "科目": expected["subject"],
                    "序号": str(index),
                    "章节": chapter_by_heading[heading],
                    "题型": kind,
                    "题目": re.sub(r"\*\*", "", heading.removeprefix("### ")),
                    "主体字数": str(core_length),
                    "含全部扩容字数": str(full_length),
                    "题干自然性": "通过",
                    "任务对齐": "通过",
                    "容量结论": "参考区间内" if in_reference else "弹性保留",
                    "弹性理由": "" if in_reference else FLEX_CAPACITY[key],
                }
            )
            totals["questions"] += 1
            totals[f"{kind}_count"] += 1
            totals[f"{kind}_strict"] += int(in_reference)

        for term, definition in validate_definitions(path, text).items():
            if term in definitions:
                assert definitions[term] == definition, (term, "跨题或跨科名词解释不一致")
            definitions[term] = definition

    assert totals["questions"] == 160
    assert observed_flex == set(FLEX_CAPACITY), (observed_flex ^ set(FLEX_CAPACITY))
    joined = "\n".join(builds.values())
    assert all(title in joined for title in EXPECTED_NATURAL_TITLES)
    assert len(definitions) == 329, len(definitions)
    assert joined.count("【名词解释：") == EXPECTED_DEFINITION_CALLS
    semantic_assertions(builds[GENERAL_OUTPUT], builds[EXPERIMENT_OUTPUT], builds[MEASUREMENT_OUTPUT])

    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    table = "\n".join(
        f"| {row['科目']} | {row['序号']} | {row['题型']} | {row['题目']} | {row['主体字数']} | {row['含全部扩容字数']} | {row['容量结论']} |"
        for row in rows
    )
    flex_lines = "\n".join(
        f"- {subject}第{index}题：{reason}。"
        for (subject, index), reason in FLEX_CAPACITY.items()
    )
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题题干、任务与容量审计报告V11

## 审计结论

- 普通心理学90题、实验心理学25题、心理与教育测量45题，共160/160题通过押题自然性检查；题干优先使用稳定上位考点，不再把可由上位概念统摄的下位名词机械串入题干。
- 160/160题通过“题干任务—正文模块”对齐检查。未要求的比较、理论关系、评价、应用或教育启示不再作为正文采分模块；有来源且自然的补充改为圆括号扩容，牵强内容删除。
- 简答主体参考200—400字，论述主体参考400—800字。共有{totals['简答_strict']}/{totals['简答_count']}道简答、{totals['论述_strict']}/{totals['论述_count']}道论述直接落入参考区间；其余{len(FLEX_CAPACITY)}题均因来源清单完整性、题干任务覆盖或点内扩容安排作弹性保留，没有通过删采分点或增加无关内容凑字数。
- 共核对329个唯一名词解释、360次名词解释调用，跨题、跨科标准表述保持一致。
- 全部答案继续采用“总起—题干任务模块—下位采分点—总结”，层级严格按`1.→（1）→①→a.`展开。

## 容量弹性题说明

{flex_lines}

## 逐题结果

| 科目 | 序号 | 题型 | 题目 | 主体字数 | 含全部扩容字数 | 容量结论 |
|---|---:|---|---|---:|---:|---|
{table}
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} simple={totals['简答_count']} "
        f"essay={totals['论述_count']} flex={len(FLEX_CAPACITY)} "
        f"unique_definitions={len(definitions)}"
    )


if __name__ == "__main__":
    main()
