from __future__ import annotations

from pathlib import Path

import audit_shenzhen_baoming_v9_sources as base
from rebuild_shenzhen_baoming_v10_semantic import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
)


ROOT = Path(__file__).resolve().parents[1]

base.base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源审计报告V10.md"
base.base.LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V10.tsv"
base.base.SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": base.base.SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": base.base.SOURCE_ROOT / "普通心理学/一本通.md",
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": base.base.SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": base.base.SOURCE_ROOT / "实验心理学/一本通.md",
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": base.base.SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": base.base.SOURCE_ROOT / "心理与教育测量/一本通.md",
    },
}

base.base.STRUCTURAL_TERMS |= {
    "肌肉线索（生理线索）主要包括",
    "单眼线索是只用一只眼睛就能感受的深度线索，主要包括",
    "双眼线索主要是双眼视差",
    "记忆的主要生理机制包括",
    "记忆的主要脑机制观点包括",
    "遗忘的主要规律和影响因素及相应减少方法如下",
    "发展量表的主要形式如下",
    "发展量表的主要解释限制如下",
}

base.base.CORRECTED_FRAGMENTS |= {
    "深度知觉的主要线索",
    "催眠的含义及其主要理论",
    "记忆的主要生理机制和脑机制观点",
    "遗忘的原因，并说明如何减少遗忘",
    "发展量表的主要形式及解释限制",
}


def main() -> None:
    base.base.main()
    report = base.base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V8", "审计报告V10", 1)
    report = report.replace(
        "## 与V7审计的关键区别",
        "## V10语义层级重组后的来源复核",
    )
    report = report.replace(
        "1. 禁止空清单：每道题必须有非空来源点记录。",
        "1. 语义层级重组不改变来源边界：每道题仍须有非空来源点记录。",
    )
    base.base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
