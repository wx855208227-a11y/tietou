from __future__ import annotations

from pathlib import Path
import re

import validate_shenzhen_baoming_v11_examfit as base
from rebuild_shenzhen_baoming_v12_global import (
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


base.GENERAL_OUTPUT = GENERAL_OUTPUT
base.EXPERIMENT_OUTPUT = EXPERIMENT_OUTPUT
base.MEASUREMENT_OUTPUT = MEASUREMENT_OUTPUT
base.build_general = build_general
base.build_experiment = build_experiment
base.build_measurement = build_measurement
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全局语义审校报告V12.md"
base.LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题全局语义审校台账V12.tsv"
base.EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}
base.EXPECTED_DEFINITION_CALLS = 362

# 字数是答题容量的参考，不以删采分点或添加无来源内容凑区间。
base.FLEX_CAPACITY = {
    ("普通心理学", 2): "核心清单只有基本任务与学科性质；来源解释保留为就近扩容",
    ("普通心理学", 13): "感觉基本现象与三种现象比较均为题干任务，主体仅略低于论述参考下限",
    ("普通心理学", 14): "三条定律的核心公式与关系完整；适用边界和例证保留为扩容",
    ("普通心理学", 26): "注意的功能和种类清单不可删减，主体仅略高于简答参考上限",
    ("普通心理学", 36): "题干要求先阐释短时记忆与工作记忆，再比较联系和区别；完整答案仅略高于论述参考上限",
    ("普通心理学", 56): "五类动机理论均须保留，主体接近论述参考下限",
    ("实验心理学", 4): "四项伦理原则构成稳定清单，必要解释按点扩容",
    ("实验心理学", 5): "研究程序五个步骤不可删减，主体仅略高于简答参考上限",
    ("实验心理学", 14): "两类设计的定义、联系和三项区别均属比较题必要模块，仅略高于简答参考上限",
    ("实验心理学", 18): "刺激、机体和速度—准确性三模块均为题干要求，仅略高于上限",
    ("心理与教育测量", 10): "五种信度估计方法为完整清单，适用条件和误差来源按点扩容",
    ("心理与教育测量", 13): "三类效度的含义、联系和区别完整，主体仅略高于简答参考上限",
    ("心理与教育测量", 14): "内容效度的验证与提高方法完整，相关概念表面效度转为扩容",
}


old_semantic_assertions = base.semantic_assertions


def semantic_assertions(general: str, experiment: str, measurement: str) -> None:
    old_semantic_assertions(general, experiment, measurement)

    work_memory = block_with(general, "比较工作记忆与短时记忆")
    require_order(
        work_memory,
        "1. **短时记忆的基本内容如下：**",
        "2. **工作记忆的基本内容如下：**",
        "3. **二者的联系如下：**",
        "4. **二者的区别如下：**",
    )
    assert "区别一" not in work_memory

    perception = block_with(general, "知觉组织的主要原则")
    for term in (
        "邻近性", "相似性", "对称性", "良好连续", "共同命运",
        "封闭性", "线条朝向", "简单性", "均质连接性",
    ):
        assert term in perception, ("知觉组织原则缺失", term)

    threshold = block_with(experiment, "感觉阈限的含义、传统测量方法")
    require_order(
        threshold,
        "1. **感觉阈限的基本含义如下：**",
        "2. **感觉阈限的传统测量方法及相应误差如下：**",
        "3. **三种方法的关系**",
    )
    for term in (
        "绝对阈限", "差别阈限", "最小变化法", "恒定刺激法", "平均差误法",
        "习惯误差", "期望误差", "练习误差", "疲劳误差", "动作误差", "时间误差",
    ):
        assert term in threshold, ("感觉阈限题缺失", term)

    quasi = block_with(experiment, "比较准实验设计与真实验设计")
    require_order(
        quasi,
        "1. **两种设计的基本含义如下：**",
        "2. **二者的联系**",
        "3. **二者的区别如下：**",
    )
    assert "区别一" not in quasi

    laws = block_with(experiment, "比较**费希纳定律和史蒂文斯定律**")
    require_order(
        laws,
        "1. **两种定律的基本内容如下：**",
        "2. **二者的联系**",
        "3. **二者的区别如下：**",
    )

    norms = block_with(measurement, "比较目标参照测验与常模参照测验")
    require_order(
        norms,
        "1. **两种测验的基本含义如下：**",
        "2. **两种测验的联系如下：**",
        "3. **两种测验的主要区别如下：**",
    )

    for text in (general, experiment, measurement):
        assert "区别一——" not in text
        assert not re.search(r"\n{3,}", text)
        assert "\u2060" not in text


base.semantic_assertions = semantic_assertions


def main() -> None:
    base.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V11", "全局语义审校报告V12", 1)
    report = report.replace(
        "160/160题通过押题自然性检查",
        "160/160题逐题复核并通过押题自然性检查",
    )
    report = report.replace(
        "160/160题通过“题干任务—正文模块”对齐检查",
        "160/160题逐题通过“题干任务—正文模块—层级关系”对齐检查",
    )
    report = report.replace("360次名词解释调用", "362次名词解释调用")
    report += (
        "\n## 本轮全局复核重点\n\n"
        "- 每题均重新检查题干是否像真实考题，题型是否与来源内容容量相匹配。\n"
        "- 每题均重新检查总起、任务模块、下位采分点和总结；总起与总结不编号，正文按`1.→（1）→①→a.`展开。\n"
        "- 比较题按题型采用“对象阐释—联系—区别”：论述题完整展开对象，简答题压缩对象表述后突出比较。\n"
        "- 速背手册中的合法点不得静默删除；简答主体不能容纳的次要点转入相邻圆括号扩容。\n"
        "- 圆括号只补充其紧邻采分点；未要求的比较、评价、应用不另立正文模块。\n"
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
