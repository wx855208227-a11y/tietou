from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import re

import validate_shenzhen_baoming_v13_source_scope as previous
import validate_shenzhen_baoming_v11_examfit as examfit
import validate_shenzhen_baoming_v5 as validate_v5
from validate_shenzhen_baoming_v4 import PREFIX_RE
from rebuild_shenzhen_baoming_v14_point_integrity import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
)


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.GENERAL_OUTPUT = GENERAL_OUTPUT
base.EXPERIMENT_OUTPUT = EXPERIMENT_OUTPUT
base.MEASUREMENT_OUTPUT = MEASUREMENT_OUTPUT
base.build_general = build_general
base.build_experiment = build_experiment
base.build_measurement = build_measurement
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题结构容量审校报告V14.md"
base.LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题结构容量审校台账V14.tsv"
base.EXPECTED = {
    GENERAL_OUTPUT: {"subject": "普通心理学", "chapters": 15, "units": 75, "questions": 90},
    EXPERIMENT_OUTPUT: {"subject": "实验心理学", "chapters": 4, "units": 25, "questions": 25},
    MEASUREMENT_OUTPUT: {"subject": "心理与教育测量", "chapters": 13, "units": 39, "questions": 45},
}
base.EXPECTED_DEFINITION_CALLS = 362
base.FLEX_CAPACITY[("普通心理学", 39)] = (
    "题目要求至少六种方法；编码、存储和提取三个阶段的来源清单均完整，点内解释作为扩容"
)
base.FLEX_CAPACITY.pop(("心理与教育测量", 13), None)


def validate_definitions_v14(path: Path, text: str) -> dict[str, str]:
    """A reused term may carry a task-specific sentence before the final tag."""
    definitions: dict[str, list[str]] = defaultdict(list)
    for number, line in enumerate(text.splitlines(), 1):
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        assert len(tags) <= 1, (path.name, number, line)
        if not tags:
            continue
        tag = tags[0]
        assert line.endswith(f"【名词解释：{tag}】"), (path.name, number, line)
        before = line[: line.rfind("【名词解释：")]
        assert "（" in before and "）" in before, (path.name, number, tag)
        clean = PREFIX_RE.sub("", before).strip()
        first_expansion_end = clean.find("）")
        if first_expansion_end >= 0:
            clean = clean[: first_expansion_end + 1]
        definitions[tag].append(clean)
    return {term: values[0] for term, values in definitions.items()}


validate_v5.validate_definitions = validate_definitions_v14
examfit.validate_definitions = validate_definitions_v14


def main() -> None:
    previous.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("结构容量审校报告V13", "结构容量审校报告V14", 1)
    report += (
        "\n## V14新增硬校验\n\n"
        "- 下级序号只有一个同级项时必须并回父级；三科均无孤立`（1）`、`①`或`a.`。\n"
        "- 来源采分点完整性由独立清单反向核对，不再由现稿已有关键词生成清单。\n"
        "- 遗忘题完整保留四种原因、五个影响因素和三个阶段的减少遗忘策略。\n"
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
