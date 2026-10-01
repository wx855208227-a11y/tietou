from __future__ import annotations

from pathlib import Path

import audit_shenzhen_baoming_v8_sources as base
from rebuild_shenzhen_baoming_v9_hierarchy import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
)


ROOT = Path(__file__).resolve().parents[1]

base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源审计报告V9.md"
base.LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V9.tsv"
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

# 这些词只承担答案模块或层级连接作用，不是新增理论采分点。
base.STRUCTURAL_TERMS |= {
    "含义",
    "优点",
    "基本内容",
    "基本含义",
    "基本观点",
    "主要作用",
    "常用测量任务",
    "基本程序",
    "实验逻辑",
    "关键控制",
    "指标关系",
    "精度指标",
    "相对于经典测验理论的优势",
    "考察重点",
    "作用与使用要求",
    "睡眠的主要阶段如下",
    "按时间指向分类",
    "测量的基本要素包括",
}

base.CORRECTED_FRAGMENTS |= {
    "感觉的含义、种类和意义",
    "韦伯定律、费希纳定律和斯蒂文斯幂定律",
    "运动知觉的含义和主要类型",
    "睡眠的主要阶段",
    "记忆的主要类型",
    "工作记忆",
    "情绪智力",
    "关键期与敏感期",
    "观察法、相关研究法和实验法",
    "自变量的主要类型",
    "因变量的类型",
    "被试间设计、被试内设计和混合设计",
    "多变量实验设计",
    "小样本设计",
    "准实验设计与真实验设计",
    "A、B、C三类反应时",
    "减数法与加因素法",
    "序列反应时任务和内隐联想测验",
    "韦伯定律和费希纳定律",
    "信号检测论",
    "测量的含义和基本要素",
    "内容效度、结构效度和效标效度",
    "智龄、年级当量和比率智商",
    "罗夏克墨迹测验、主题统觉测验和内隐联想测验",
    "概化理论",
}


def main() -> None:
    base.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V8", "审计报告V9", 1)
    report = report.replace(
        "## 与V7审计的关键区别",
        "## V9层级重组后的来源复核",
    )
    report = report.replace(
        "1. 禁止空清单：每道题必须有非空来源点记录。",
        "1. 层级重组不改变来源边界：每道题仍须有非空来源点记录。",
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
