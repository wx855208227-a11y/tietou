from __future__ import annotations

from pathlib import Path

import audit_shenzhen_baoming_v13_sources as previous
from rebuild_shenzhen_baoming_v14_point_integrity import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
)


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源审计报告V14.md"
base.LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V14.tsv"
base.SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": base.SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": base.SOURCE_ROOT / "普通心理学/一本通.md",
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": base.SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": base.SOURCE_ROOT / "实验心理学/一本通.md",
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": base.SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": base.SOURCE_ROOT / "心理与教育测量/一本通.md",
    },
}


def main() -> None:
    previous.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V13", "审计报告V14", 1)
    report += (
        "\n## V14完整性复核\n\n"
        "- 独立采分点反向覆盖以《160题采分点完整性台账V14》为准；本报告继续承担答案理论关键词、名词解释和局部来源的正向回溯。\n"
        "- 两套校验分别回答‘答案有没有无来源新增’和‘来源合法采分点有没有遗漏’，不得以答案已有关键词替代反向清单。\n"
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
