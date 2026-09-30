from __future__ import annotations

from rebuild_shenzhen_baoming_v8 import (
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
        block_with(general, "负启动、返回抑制和注意瞬脱"),
        "选择性注意", "负启动", "返回抑制", "注意瞬脱", "主要区别",
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
        block_with(measurement, "项目难度对测验的影响"),
        "正偏态", "负偏态", "缩小分数全距", "潜在区分度越大", "分布广一些", "区分度具有**相对性**",
    )
    require(
        block_with(measurement, "比较智龄、年级当量和比率智商"),
        "智龄", "年级当量", "比率智商", "施特恩", "不适用于成人",
    )
    require(
        block_with(measurement, "简述组内常模的含义"),
        "百分等级常模", "标准分数常模", "剖析图", "顺序量数", "相等单位",
    )
    require(
        block_with(measurement, "比内智力量表的发展"),
        "1905年", "1908年", "1911年", "1916年", "1937年", "1960年", "离差智商",
    )
    require(
        block_with(measurement, "简述瑞文测验的"),
        "团体智力测验", "非文字图形测验", "标准推理测验", "彩图推理测验", "高级推理测验",
    )
    require(
        block_with(measurement, "简述项目反应理论"),
        "潜在特质", "项目特征曲线", "跨群体不变性", "可选择性", "信息函数", "计算机化自适应测验",
    )

    for name, result in results.items():
        print(name, result)
    print(f"PASS: V8 structure, source-point conservation and definition consistency; unique_definitions={len(definitions)}")


if __name__ == "__main__":
    main()
