from __future__ import annotations

from pathlib import Path

import audit_shenzhen_baoming_v12_sources as previous
from rebuild_shenzhen_baoming_v13_source_scope import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
)


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源审计报告V13.md"
base.LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V13.tsv"
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
        "简述研究中的因果关系和相关关系": (
            "有可能揭示因果关系", "相关系数", "相关本身不能提供因果信息", "唯一方法",
        ),
        "什么是工作记忆": (
            "语音环路", "视觉空间模板", "情景缓冲器", "中央执行系统",
            "语言理解", "词汇习得", "阅读广度测试", "操作广度测试",
        ),
        "长时记忆的编码、存储和提取": (
            "语义编码", "视觉编码", "听觉编码", "觉醒水平", "加工深度",
            "逐渐减少", "概括", "完整", "具体", "出现错误", "再认", "回忆",
        ),
    }
)
base.CORRECTED_FRAGMENTS |= {
    "简述研究中的因果关系和相关关系",
    "什么是工作记忆",
    "长时记忆的编码、存储和提取",
    "比较语言发展的学习观",
}


def main() -> None:
    previous.main()
    report = base.REPORT.read_text(encoding="utf-8")
    report = report.replace("审计报告V12", "审计报告V13", 1)
    report = report.replace(
        "每题均限定在对应章节的速背手册与一本通内核对，不再用全科关键词回查掩盖跨章错配。",
        "每题先在对应章节建立完整清单，再对题干任务模块做本题知识块复核；同章相邻小节不得自动成为正文来源。",
    )
    report += (
        "\n## 本题知识块专项复核\n\n"
        "- 因果与相关题：删除方向性、第三变量、非线性和时间先后等资料未直接提供的扩写，并由论述题校准为简答题。\n"
        "- 工作记忆题：主要作用和测量任务改回速背手册／一本通的语音环路、中央执行系统、阅读广度和操作广度表述，删除双任务及宽泛作用扩写。\n"
        "- 长时记忆题：编码只调用编码小节，存储只调用动态存储小节，提取只调用再认和回忆小节；未再借用遗忘规律或提高记忆效果策略。\n"
        "- 语言发展理论题：总起只界定三种理论的解释侧重，删除与比较任务无关的发展阶段铺垫。\n"
    )
    base.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
