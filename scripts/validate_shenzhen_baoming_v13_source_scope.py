from __future__ import annotations

from pathlib import Path
import re

import validate_shenzhen_baoming_v12_global as previous
from rebuild_shenzhen_baoming_v13_source_scope import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v5 import block_with
from validate_shenzhen_baoming_v9_hierarchy import require_order


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.GENERAL_OUTPUT = GENERAL_OUTPUT
base.EXPERIMENT_OUTPUT = EXPERIMENT_OUTPUT
base.MEASUREMENT_OUTPUT = MEASUREMENT_OUTPUT
base.build_general = build_general
base.build_experiment = build_experiment
base.build_measurement = build_measurement
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题结构容量审校报告V13.md"
base.LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题结构容量审校台账V13.tsv"
base.EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}
base.EXPECTED_DEFINITION_CALLS = 362


old_semantic_assertions = base.semantic_assertions


def semantic_assertions(general: str, experiment: str, measurement: str) -> None:
    old_semantic_assertions(general, experiment, measurement)

    causality = block_with(general, "简述研究中的因果关系和相关关系")
    require_order(causality, "1. **因果关系**", "2. **相关关系**", "3. 解释相关结果时应注意：")
    assert "【论述】" not in causality.splitlines()[0]
    for forbidden in ("第三变量", "方向性问题", "非线性关系", "时间先后", "稳定共变"):
        assert forbidden not in causality

    working_memory = block_with(general, "什么是工作记忆")
    require_order(
        working_memory,
        "1. **工作记忆的核心成分如下：**",
        "2. **工作记忆的主要作用如下：**",
        "3. **工作记忆的常用测量任务如下：**",
    )
    for required in (
        "语音环路", "视觉空间模板", "情景缓冲器", "中央执行系统",
        "语言理解和词汇习得", "阅读广度测试", "操作广度测试",
    ):
        assert required in working_memory, required
    for forbidden in ("双任务", "推理、问题解决", "当前目标保持"):
        assert forbidden not in working_memory

    long_term = block_with(general, "长时记忆的编码、存储和提取")
    require_order(
        long_term,
        "1. **长时记忆的编码及影响因素如下：**",
        "2. **长时记忆的存储变化如下：**",
        "3. **长时记忆的提取方式及影响因素如下：**",
    )
    for required in (
        "语义编码", "视觉编码和听觉编码", "觉醒水平", "加工深度",
        "存储的量变", "存储的质变", "再认", "回忆",
    ):
        assert required in long_term, required
    for forbidden in (
        "编码—提取匹配", "编码⁠—⁠提取匹配", "编码特异性原则",
        "恢复学习时的环境", "保持量并非匀速下降", "精细复述和组织材料",
    ):
        assert forbidden not in long_term, forbidden

    language = block_with(general, "比较语言发展的学习观")
    intro = language.split("1. **语言发展的学习观如下：**", 1)[0]
    for forbidden in ("前语言期", "单词句期", "电报句期", "元语言意识"):
        assert forbidden not in intro

    for text in (general, experiment, measurement):
        assert "编码—提取匹配" not in text
        assert "编码⁠—⁠提取匹配" not in text
        assert not re.search(r"\n{3,}", text)


base.semantic_assertions = semantic_assertions


def main() -> None:
    previous.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("全局语义审校报告V12", "结构容量审校报告V13", 1)
    report += (
        "\n## V13新增的本题知识块约束\n\n"
        "- 来源审核不再把同章任意小节视为可互换来源；正文理论点必须直接完成题干任务，并能回溯到本题对应知识块。\n"
        "- 容量不足时先校准题型或题干，不得借相邻小节补点凑成论述题。\n"
        "- 本轮重点回查了全部160题的题干任务、一级模块和下位点；对普通心理学第6、35、37、82题作实质修订。\n"
        "- 长时记忆题已删除来自‘提高记忆效果的策略’和‘遗忘规律’小节的编码特异性、早期遗忘速度及复习策略表述，只保留编码、动态存储、再认和回忆的直接来源内容。\n"
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
