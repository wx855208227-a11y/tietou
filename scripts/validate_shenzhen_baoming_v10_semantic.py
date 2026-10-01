from __future__ import annotations

from pathlib import Path
import re

import validate_shenzhen_baoming_v9_hierarchy as base
from rebuild_shenzhen_baoming_v10_semantic import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v5 import block_with


ROOT = Path(__file__).resolve().parents[1]

base.GENERAL_OUTPUT = GENERAL_OUTPUT
base.EXPERIMENT_OUTPUT = EXPERIMENT_OUTPUT
base.MEASUREMENT_OUTPUT = MEASUREMENT_OUTPUT
base.build_general = build_general
base.build_experiment = build_experiment
base.build_measurement = build_measurement
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题语义层级审计报告V10.md"
base.LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题语义层级审计台账V10.tsv"
base.EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}


previous_semantic_assertions = base.semantic_assertions


def semantic_assertions(general: str, experiment: str, measurement: str) -> None:
    previous_semantic_assertions(general, experiment, measurement)

    depth = block_with(general, "简述深度知觉的主要线索")
    base.require_order(
        depth,
        "1. **肌肉线索（生理线索）**主要包括：",
        "（1）**调节**",
        "（2）**辐合**",
        "2. **单眼线索**",
        "（1）**遮挡、线条透视和空气透视**",
        "（2）**相对高度、相对大小和纹理梯度**",
        "3. **双眼线索**",
    )
    assert not re.search(r"^[1-9]\. .*?(?:调节|辐合|遮挡、线条透视|相对高度、相对大小)", depth, re.MULTILINE)

    hypnosis = block_with(general, "简述催眠的含义及其主要理论")
    base.require_order(
        hypnosis,
        "1. **特殊状态理论**",
        "2. **非特殊状态理论**",
        "（1）**角色扮演理论**",
        "3. **理论比较**",
    )
    assert "3. **角色扮演理论**" not in hypnosis

    memory = block_with(general, "简述记忆的主要生理机制和脑机制观点")
    base.require_order(
        memory,
        "1. 记忆的主要**生理机制**包括：",
        "（1）**突触结构变化**",
        "（2）**长时程增强**",
        "（3）**反响回路**",
        "2. 记忆的主要**脑机制观点**包括：",
        "（1）**整合论**",
        "（2）**定位说**",
    )
    assert not re.search(r"^[1-9]\. .*?(?:突触结构变化|长时程增强|反响回路|整合论|定位说)", memory, re.MULTILINE)

    forgetting = block_with(general, "论述遗忘的原因，并说明如何减少遗忘")
    base.require_order(
        forgetting,
        "1. 遗忘的主要**原因及相应减少方法**如下：",
        "（4）**提取失败说**",
        "2. 遗忘的主要**规律和影响因素及相应减少方法**如下：",
        "（1）**艾宾浩斯遗忘曲线**",
        "（3）**系列位置效应**",
        "3. **综合对策**",
    )
    assert "（5）**艾宾浩斯遗忘曲线**" not in forgetting

    development = block_with(measurement, "简述发展量表的**主要形式及解释限制**")
    base.require_order(
        development,
        "1. 发展量表的**主要形式**如下：",
        "（1）**年龄常模**",
        "（2）年级当量",
        "2. 发展量表的**主要解释限制**如下：",
        "（1）年级单位不相等",
        "（3）年级常模容易被误用",
    )
    assert not re.search(r"^[12]\. (?:\*\*年龄常模|年级当量)", development, re.MULTILINE)


base.semantic_assertions = semantic_assertions


if __name__ == "__main__":
    base.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V9", "审计报告V10", 1)
    report = report.replace(
        "所有答案均按“1. →（1）→①→a.”逐级展开，未发现跳级、同级序号中断或编号后理论段落游离。",
        "所有答案均按“1. →（1）→①→a.”逐级展开；同时逐题复核题干任务模块与来源材料中的上位类别、下位分类和项目说明，未发现跳级、并列误判或编号后理论段落游离。",
    )
    report = report.replace(
        "对运动知觉、睡眠阶段、记忆类型、小样本设计、反应时方法、信号检测论、测量要素、发展分数、概化理论等高风险题设置了父子关系断言。",
        "对深度知觉、运动知觉、催眠理论、记忆机制、遗忘、睡眠阶段、记忆类型、小样本设计、反应时方法、信号检测论、测量要素、发展量表和概化理论等高风险题设置了父子关系断言。",
    )
    base.REPORT.write_text(report, encoding="utf-8")
