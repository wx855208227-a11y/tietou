from __future__ import annotations

from rebuild_shenzhen_baoming_v7 import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v4 import validate_definitions
from validate_shenzhen_baoming_v5 import block_with, validate_one


EXPECTED = {
    GENERAL_OUTPUT: {"chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"chapters": 13, "units": 39, "questions": 45},
}


def require(block: str, *terms: str) -> None:
    missing = [term for term in terms if term not in block]
    assert not missing, missing


def main() -> None:
    builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    definitions: dict[str, str] = {}
    results = {}
    for path, expected in EXPECTED.items():
        text = path.read_text(encoding="utf-8")
        assert text == builds[path], path
        results[path.name] = validate_one(path, expected)
        assert "空间误差" not in text
        assert "内在一致性信度" not in text
        for term, definition in validate_definitions(path, text).items():
            if term in definitions:
                assert definitions[term] == definition, term
            definitions[term] = definition

    general = builds[GENERAL_OUTPUT]
    experiment = builds[EXPERIMENT_OUTPUT]
    measurement = builds[MEASUREMENT_OUTPUT]

    require(
        block_with(general, "简述知觉组织的主要原则"),
        "邻近性", "相似性", "对称性", "良好连续", "共同命运", "封闭性",
        "线条朝向", "简单性", "均质连接性",
    )
    require(
        block_with(experiment, "论述控制变量的主要来源"),
        "随机额外变量", "系统额外变量", "排除法", "恒定法", "匹配法",
        "随机化法", "抵消平衡法", "统计控制法",
    )
    require(
        block_with(experiment, "论述感觉阈限"),
        "动作误差", "时间误差", "平均差误法最适合测量绝对阈限",
    )
    require(
        block_with(experiment, "论述信号检测论"),
        "均值不等", "重叠的正态分布", "同一曲线上各点的感受性相同",
    )
    require(
        block_with(measurement, "简述心理测验的**含义和四个基本条件"),
        "行为样本", "标准化", "难度或应答率", "信度和效度",
    )
    require(
        block_with(measurement, "论述信度的"),
        "重测信度", "复本信度", "分半信度", "同质性信度", "评分者信度",
        "库—理信度系数", "克隆巴赫系数", "卡方检验",
    )
    require(
        block_with(measurement, "简述效度的"),
        "相对性", "综合反映", "多方面证据",
    )
    require(
        block_with(measurement, "简述项目难度"),
        "标准参照测验", "速度测验", "防止被试得到满分",
    )
    require(
        block_with(measurement, "简述项目鉴别力"),
        "鉴别指数法", "相关法", "点二列相关", "二列相关", "φ相关", "积差相关",
    )

    for name, result in results.items():
        print(name, result)
    print(f"PASS: V7 structure and corrected source-point checks; unique_definitions={len(definitions)}")


if __name__ == "__main__":
    main()
