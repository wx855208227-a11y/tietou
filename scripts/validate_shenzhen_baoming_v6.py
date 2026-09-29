from __future__ import annotations

from pathlib import Path

from rebuild_shenzhen_baoming_v6 import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)
from validate_shenzhen_baoming_v4 import outside_expansions, validate_definitions
from validate_shenzhen_baoming_v5 import block_with, validate_one


EXPECTED = {
    GENERAL_OUTPUT: {"chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"chapters": 13, "units": 39, "questions": 45},
}


def assert_terms(answer: str, terms: tuple[str, ...]) -> None:
    missing = [term for term in terms if term not in answer]
    assert not missing, missing


def main() -> None:
    builds = {
        GENERAL_OUTPUT: build_general(),
        EXPERIMENT_OUTPUT: build_experiment(),
        MEASUREMENT_OUTPUT: build_measurement(),
    }
    results: dict[str, object] = {}
    definitions: dict[str, str] = {}
    for path, expected in EXPECTED.items():
        text = path.read_text(encoding="utf-8")
        assert text == builds[path], path.name
        results[path.name] = validate_one(path, expected)
        assert "S=KlgI" not in text, path.name
        for term, definition in validate_definitions(path, text).items():
            if term in definitions:
                assert definitions[term] == definition, term
            definitions[term] = definition

    general = builds[GENERAL_OUTPUT]
    experiment = builds[EXPERIMENT_OUTPUT]

    laws = block_with(general, "韦伯定律、费希纳定律和斯蒂文斯幂定律")
    assert "K=ΔI/I" in laws and "P=KlgI" in laws and "P=KIⁿ" in laws
    assert experiment.count("P=KlgI") == 2

    color = block_with(general, "比较颜色视觉的")
    assert "托马斯·杨" in color and "杨和赫尔姆霍茨" in color

    hearing = block_with(general, "简述声音的心理维度和声音掩蔽")
    assert_terms(
        hearing,
        (
            "音高", "响度", "音色", "频率", "振幅", "波形", "声音掩蔽",
            "赫尔姆霍茨", "共鸣理论", "冯·贝克西", "行波理论",
            "拉瑟福德", "频率理论", "韦弗尔", "神经齐射理论",
        ),
    )

    organization = block_with(general, "简述知觉组织的主要原则")
    principles = (
        "邻近性", "相似性", "对称性", "良好连续", "共同命运",
        "封闭性", "线条朝向", "简单性", "均质连接性",
    )
    assert_terms(organization, principles)
    body = outside_expansions(organization)
    assert all(term in body for term in principles[:6])
    assert "简单性" in body
    assert "线条朝向" not in body and "均质连接性" not in body
    assert_terms(organization, ("特征分析", "轮廓与边界检测", "知觉系统的整合和完善", "经验作用"))

    for name, result in results.items():
        print(name, result)
    print("PASS：V6内容结构、公式一致性、人物—理论配对及知觉组织9/9采分点检查通过。")


if __name__ == "__main__":
    main()
