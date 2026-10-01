from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import re

from rebuild_shenzhen_baoming_v9_hierarchy import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v4 import question_blocks, validate_definitions
from validate_shenzhen_baoming_v5 import block_with, validate_one


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题逻辑层级审计报告V9.md"
LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题逻辑层级审计台账V9.tsv"

EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}

LEVEL_PATTERNS = (
    re.compile(r"^(\d+)\.\s"),
    re.compile(r"^（(\d+)）"),
    re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩])"),
    re.compile(r"^([a-z])\.\s"),
)
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def require_order(block: str, *values: str) -> None:
    positions = [block.find(value) for value in values]
    assert all(position >= 0 for position in positions), (values, positions)
    assert positions == sorted(positions), (values, positions)


def parse_level(line: str) -> tuple[int, int] | None:
    for level, pattern in enumerate(LEVEL_PATTERNS):
        match = pattern.match(line)
        if not match:
            continue
        raw = match.group(1)
        if level < 2:
            return level, int(raw)
        if level == 2:
            return level, CIRCLED.index(raw) + 1
        return level, ord(raw) - 96
    return None


def validate_tree(path: Path, heading: str, answer: str) -> tuple[int, int]:
    active = [False, False, False, False]
    sequence = [0, 0, 0, 0]
    levels: list[int] = []
    started = False

    for line in answer.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parsed = parse_level(stripped)
        if parsed is None:
            if started and not stripped.startswith("（") and not stripped.startswith("综上"):
                raise AssertionError((path.name, heading, "编号后出现未归层理论段", stripped))
            continue

        level, number = parsed
        started = True
        if level > 0:
            assert active[level - 1], (path.name, heading, "层级跳跃", stripped)
        assert number == sequence[level] + 1, (
            path.name,
            heading,
            "同级序号不连续",
            stripped,
            sequence,
        )
        sequence[level] = number
        active[level] = True
        levels.append(level)
        for child in range(level + 1, 4):
            active[child] = False
            sequence[child] = 0

    assert levels and levels[0] == 0, (path.name, heading, "缺少一级答案模块")
    return sequence[0], max(levels) + 1


def semantic_assertions(general: str, experiment: str, measurement: str) -> None:
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
    assert not re.search(r"^[3-6]\. .*?(?:动景运动|诱发运动|自主运动|运动后效)", motion, re.MULTILINE)

    sleep = block_with(general, "论述睡眠的主要阶段")
    require_order(
        sleep,
        "1. **睡眠的主要阶段如下：**",
        "（1）**第一阶段**",
        "（5）**快速眼动睡眠**",
        "2. **周期规律**",
        "3. **睡眠功能**",
        "4. **梦的解释**",
    )

    memory = block_with(general, "论述记忆的主要类型及其特点")
    require_order(
        memory,
        "1. **按保持时间分类：**",
        "（3）**长时记忆**",
        "①**程序性记忆**",
        "②**陈述性记忆**",
        "a. **情景记忆**",
        "b. **语义记忆**",
        "2. **按意识参与分类：**",
        "3. **按时间指向分类：**",
        "（1）**前瞻性记忆**",
        "（2）**回溯性记忆**",
    )

    for fragment, parents in {
        "简述感觉的含义、种类和意义": ("1. **感觉种类**", "2. **感觉意义**", "3. **感受性与感觉阈限的关系如下：**"),
        "什么是工作记忆": ("1. **工作记忆的核心成分如下：**", "2. **主要作用**", "3. **常用测量任务**"),
        "简述情绪智力的含义": ("1. **情绪知觉、评价和表达**", "4. **调节情绪**"),
        "比较个体发展中的": ("1. **关键期与敏感期的基本含义如下：**", "2. **二者的联系与区别如下：**", "3. **教育意义**"),
    }.items():
        require_order(block_with(general, fragment), *parents)

    experiment_checks = {
        "比较**观察法、相关研究法和实验法**": (
            "1. **观察法的含义、优点和局限如下：**",
            "2. **相关研究法的含义、优点和局限如下：**",
            "3. **实验法的含义、优点和局限如下：**",
            "4. **三者关系与主要区别**",
        ),
        "简述自变量的主要类型": ("1. 自变量的**主要类型**包括：", "2. 自变量的**操纵方法**主要包括："),
        "简述因变量的类型": ("1. 因变量的**指标类型**包括：", "2. 因变量的**指标选择标准**包括：", "3. 因变量的**控制要求**主要包括："),
        "比较**被试间设计、被试内设计和混合设计**": ("1. **被试间设计", "2. **被试内设计", "3. **混合设计**", "4. **三种设计的联系与主要区别如下：**"),
        "论述多变量实验设计": ("1. 多变量实验设计的**主要类型**包括：", "2. 多变量实验设计的**优缺点**如下：", "3. 多变量实验结果的**解释要点**包括："),
        "简述小样本设计": ("1. **ABA设计：**", "2. **多基线设计：**"),
        "比较反应时研究中的": ("1. **减数法的基本内容如下：**", "2. **加因素法的基本内容如下：**", "3. **两种方法的联系与主要区别如下：**"),
        "说明**序列反应时任务和内隐联想测验**": ("1. **序列反应时任务的基本内容如下：**", "2. **内隐联想测验的基本内容如下：**", "3. **联系与主要区别**"),
        "论述信号检测论": ("1. 信号检测论的**基本思想**包括：", "2. 信号检测论的**核心指标及其关系如下：**", "3. 信号检测论的**实验方法**包括：", "4. 信号检测论的**主要价值**"),
    }
    for fragment, parents in experiment_checks.items():
        require_order(block_with(experiment, fragment), *parents)

    measurement_checks = {
        "简述测量的**含义和基本要素**": ("1. 测量是", "2. 测量的**基本要素**包括："),
        "比较智龄、年级当量和比率智商": ("1. **智龄：**", "2. **年级当量：**", "3. **比率智商：**", "4. 三者的**主要区别**"),
        "简述**罗夏克墨迹测验": ("1. **罗夏克墨迹测验**", "2. **主题统觉测验**", "3. 内隐联想测验"),
        "论述概化理论": ("1. **概化理论的基本思想如下：**", "2. **概化分析包括两个阶段：**", "3. **精度指标**", "4. **相对于经典测验理论的优势**"),
    }
    for fragment, parents in measurement_checks.items():
        require_order(block_with(measurement, fragment), *parents)

    validity = block_with(measurement, "比较内容效度、结构效度和效标效度")
    assert validity.count("①**考察重点**") == 3
    content = block_with(measurement, "简述内容效度的")
    require_order(content, "3. 理解内容效度时", "（1）**表面效度**", "①**作用与使用要求**")
    equivalence = block_with(measurement, "简述测验等值的含义")
    assert "\n锚测验是" not in equivalence
    assert "（锚测验是等值设计中" in equivalence


def main() -> None:
    builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    rows: list[dict[str, str]] = []
    all_definitions: dict[str, str] = {}
    totals = Counter()

    for path, expected in EXPECTED.items():
        text = path.read_text(encoding="utf-8")
        assert text == builds[path], (path.name, "文件不可由构建脚本复现")
        validate_one(path, expected)
        assert not re.search(r"^### 押题\d+【论述】简述|^### 押题\d+【简答】论述", text, re.MULTILINE)

        current_chapter = ""
        chapter_by_heading: dict[str, str] = {}
        for line in text.splitlines():
            if line.startswith("# ") and not line.startswith("# 深圳大学"):
                current_chapter = line[2:]
            elif line.startswith("### 押题"):
                chapter_by_heading[line] = current_chapter

        for index, (heading, kind, answer) in enumerate(question_blocks(text), start=1):
            top_count, depth = validate_tree(path, heading, answer)
            rows.append(
                {
                    "科目": expected["subject"],
                    "序号": str(index),
                    "章节": chapter_by_heading[heading],
                    "题型": kind,
                    "题目": re.sub(r"\*\*", "", heading.removeprefix("### ")),
                    "一级模块数": str(top_count),
                    "最深层级": str(depth),
                    "结果": "层级复核通过",
                }
            )
            totals["questions"] += 1
            totals["max_depth"] = max(totals["max_depth"], depth)

        for term, definition in validate_definitions(path, text).items():
            if term in all_definitions:
                assert all_definitions[term] == definition, (term, "跨科名词解释不一致")
            all_definitions[term] = definition

    assert totals["questions"] == 160, totals
    semantic_assertions(builds[GENERAL_OUTPUT], builds[EXPERIMENT_OUTPUT], builds[MEASUREMENT_OUTPUT])

    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    report_rows = [
        f"| {row['科目']} | {row['序号']} | {row['章节']} | {row['题目']} | {row['一级模块数']} | {row['最深层级']} | {row['结果']} |"
        for row in rows
    ]
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题逻辑层级审计报告V9

## 审计结论

- 普通心理学90题、实验心理学25题、心理与教育测量45题，共160/160题完成题干模块与答案层级复核。
- 所有答案均按“1. →（1）→①→a.”逐级展开，未发现跳级、同级序号中断或编号后理论段落游离。
- 总起和总结不编号；分类、构成、阶段、类型、方法及指标等下位项均置于对应上位模块之下。
- 对运动知觉、睡眠阶段、记忆类型、小样本设计、反应时方法、信号检测论、测量要素、发展分数、概化理论等高风险题设置了父子关系断言。
- 共核对{len(all_definitions)}个唯一名词解释，跨题、跨科表述保持一致。

## 逐题台账

| 科目 | 序号 | 章节 | 题目 | 一级模块数 | 最深层级 | 结果 |
|---|---:|---|---|---:|---:|---|
{chr(10).join(report_rows)}
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} unique_definitions={len(all_definitions)} "
        f"max_depth={totals['max_depth']}"
    )


if __name__ == "__main__":
    main()
