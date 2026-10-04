from __future__ import annotations

from pathlib import Path
import re

import validate_shenzhen_baoming_v14_full as previous
from rebuild_shenzhen_baoming_v15_source_keywords import (
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
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题结构容量审校报告V15.md"
base.LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题结构容量审校台账V15.tsv"
base.EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}


def validate_definitions_v15(path: Path, text: str) -> dict[str, str]:
    definitions = previous.validate_definitions_v14(path, text)
    return {term: value.replace("**", "") for term, value in definitions.items()}


base.validate_definitions = validate_definitions_v15


def semantic_assertions_v15(general: str, experiment: str, measurement: str) -> None:
    general = general.replace("**", "")
    experiment = experiment.replace("**", "")
    measurement = measurement.replace("**", "")

    attention = block_with(general, "简述选择性注意的经典现象")
    require_order(attention, "1. 负启动", "2. 返回抑制", "3. 注意瞬脱")
    assert "三种现象的主要区别" not in attention

    visual = block_with(general, "简述视觉的主要现象")
    require_order(visual, "1. 视觉适应", "2. 后像", "3. 视觉对比", "4. 马赫带", "5. 视觉掩蔽")

    motion = block_with(general, "简述运动知觉的含义和主要类型")
    require_order(
        motion, "1. 真动知觉", "2. 似动知觉", "（1）动景运动", "（2）诱发运动", "（3）自主运动", "（4）运动后效"
    )

    depth = block_with(general, "简述深度知觉的主要线索")
    require_order(depth, "1. 肌肉线索（生理线索）", "（1）调节", "（2）辐合", "2. 单眼线索", "3. 双眼线索")

    working = block_with(general, "比较工作记忆与短时记忆")
    require_order(working, "1. 短时记忆的基本内容如下：", "2. 工作记忆的基本内容如下：", "3. 二者的联系如下：", "4. 二者的区别如下：")

    perception = block_with(general, "知觉组织的主要原则")
    for term in ("邻近性", "相似性", "对称性", "良好连续", "共同命运", "封闭性", "线条朝向", "简单性", "均质连接性"):
        assert term in perception, ("知觉组织原则缺失", term)

    memory = block_with(general, "比较内隐记忆和外显记忆")
    assert "意识参与不同" not in re.sub(r"（(?!\d+）)[^（）]*）", "", memory)
    require_order(memory, "（1）加工深度", "（2）两者的保持时间", "（3）记忆负荷量", "（4）呈现方式", "（5）干扰因素")

    causality = block_with(general, "简述研究中的因果关系和相关关系")
    require_order(causality, "1. 因果关系", "2. 相关关系", "3. 解释相关结果时应注意：")

    long_term = block_with(general, "长时记忆的编码、存储和提取")
    require_order(long_term, "1. 长时记忆的编码及影响因素如下：", "2. 长时记忆的存储变化如下：", "3. 长时记忆的提取方式及影响因素如下：")
    for forbidden in ("编码—提取匹配", "编码⁠—⁠提取匹配", "编码特异性原则", "恢复学习时的环境"):
        assert forbidden not in long_term

    implicit = block_with(experiment, "两种经典内隐研究范式")
    require_order(implicit, "1. 序列反应时任务的基本内容如下：", "2. 内隐联想测验的基本内容如下：")
    assert "3. 联系与主要区别" not in implicit

    threshold = block_with(experiment, "感觉阈限的含义、传统测量方法")
    for term in ("绝对阈限", "差别阈限", "最小变化法", "恒定刺激法", "平均差误法", "习惯误差", "期望误差", "练习误差", "疲劳误差", "动作误差", "时间误差"):
        assert term in threshold, ("感觉阈限题缺失", term)

    norms = block_with(measurement, "比较目标参照测验与常模参照测验")
    require_order(norms, "1. 两种测验的基本含义如下：", "2. 两种测验的联系如下：", "3. 两种测验的主要区别如下：")

    for text in (general, experiment, measurement):
        assert "区别一——" not in text
        assert "\u2060" not in text
        assert not re.search(r"\n{3,}", text)


base.semantic_assertions = semantic_assertions_v15


def main() -> None:
    previous.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("结构容量审校报告V14", "结构容量审校报告V15", 1)
    report += (
        "\n## V15新增硬校验\n\n"
        "- 题干不再混用正文关键词加粗，关键词只在答案内标注。\n"
        "- 内隐记忆与外显记忆的正文区别恢复为速背手册明列的五项；意识参与角度仅作扩容。\n"
        "- 正文关键词按对应速背知识块的分点标题、加粗和下划线重新生成并覆盖校验。\n"
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
