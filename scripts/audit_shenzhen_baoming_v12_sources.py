from __future__ import annotations

from pathlib import Path

import audit_shenzhen_baoming_v11_sources as audit_v11
from rebuild_shenzhen_baoming_v12_global import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
)


ROOT = Path(__file__).resolve().parents[1]
base = audit_v11.base

base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源审计报告V12.md"
base.LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V12.tsv"
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


base.EXHAUSTIVE_ADDITIONS["普通心理学"].update(
    {
        "论述感觉的基本现象": (
            "感觉适应", "感觉对比", "感觉的相互作用", "感觉补偿",
        ),
        "比较工作记忆与短时记忆": (
            "短时记忆", "7±2个组块", "听觉编码", "组块化", "复述",
            "工作记忆", "语音环路", "视觉空间模板", "情景缓冲器",
            "中央执行系统", "暂时保持", "容量有限", "成分不同",
            "主动性不同", "侧重点不同",
        ),
        "比较内隐记忆和外显记忆": (
            "外显记忆", "内隐记忆", "意识参与不同", "加工深度影响不同",
            "保持时间不同", "记忆负荷影响不同", "呈现方式影响不同", "干扰影响不同",
        ),
        "论述概念的含义": (
            "内涵", "外延", "分类和范畴化功能", "合取概念", "析取概念",
            "关系概念", "人工概念", "自然概念", "共同要素说", "假设检验说", "原型理论",
        ),
    }
)
base.EXHAUSTIVE_ADDITIONS["实验心理学"].update(
    {
        "自变量、因变量和控制变量": (
            "自变量", "因变量", "控制变量", "操纵", "观察和测量", "控制额外变量",
        ),
        "比较准实验设计与真实验设计": (
            "准实验设计", "真实验设计", "控制程度不同", "因果推论能力不同", "适用范围不同",
        ),
        "比较费希纳定律和史蒂文斯定律": (
            "费希纳定律", "史蒂文斯定律", "函数形式不同", "增长特点不同",
            "测量基础不同", "量表性质不同", "适用范围不同",
        ),
    }
)
base.EXHAUSTIVE_ADDITIONS["心理与教育测量"].update(
    {
        "比较智龄、年级当量和比率智商": (
            "智龄", "年级当量", "比率智商", "不适用于成人",
        ),
        "比较目标参照测验与常模参照测验": (
            "目标参照测验", "常模参照测验", "共同基础", "共同质量要求",
            "解释目的不同", "适用范围不同", "信效度指标不同", "项目指标要求不同",
        ),
    }
)

base.CORRECTED_FRAGMENTS |= {
    "论述感觉的基本现象",
    "比较工作记忆与短时记忆",
    "比较内隐记忆和外显记忆",
    "论述概念的含义",
    "自变量、因变量和控制变量",
    "比较准实验设计与真实验设计",
    "比较费希纳定律和史蒂文斯定律",
    "比较智龄、年级当量和比率智商",
    "比较目标参照测验与常模参照测验",
}
base.STRUCTURAL_TERMS |= {"三者的联系与区别如下"}


def main() -> None:
    base.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V8", "审计报告V12", 1)
    report = report.replace("## 与V7审计的关键区别", "## V12全局语义重编后的来源复核")
    report = report.replace(
        "1. 禁止空清单：每道题必须有非空来源点记录。",
        "1. 160道题逐题建立非空来源清单；速背主体优先，一本通仅作辅助。",
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
