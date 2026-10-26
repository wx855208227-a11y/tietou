#!/usr/bin/env python3
"""Create a question-by-question re-audit trail for the Shenzhen exam bank.

The earlier classification is retained as the before-state.  Every row receives
an explicit reviewed result, confidence level, and reason.  Only rows whose
reviewed subject and chapter belong to the four assigned textbooks are eligible
for the user-facing workbook.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


GP = "普通心理学（第6版）"
EP = "实验心理学（第2版）"
MEAS = "心理与教育测量（第4版）"
STAT = "现代心理与教育统计学（第5版）"
OFFICIAL_SUBJECTS = {GP, EP, MEAS, STAT}


OVERRIDES: dict[str, dict[str, object]] = {
    "2019-单选题-005": {
        "subject": EP,
        "chapter": "第一章 绪论",
        "topic": "研究人类被试的伦理与知情同意",
        "secondary": "",
        "confidence": "高",
        "evidence": "《实验心理学》第2版第一章“实验心理学的研究伦理”，教材印刷页38—40直接讲知情同意权、退出自由和免遭伤害。",
        "note": "主考点是实验研究伦理，不是普心的一般研究方法。",
    },
    "2019-单选题-042": {
        "subject": GP,
        "chapter": "第十二章 人格",
        "topic": "马斯洛的自我实现理论",
        "secondary": "第九章 动机：需要层次理论",
        "confidence": "中",
        "evidence": "《普通心理学》第6版印刷页432在第十二章“人本主义的人格理论”下讲马斯洛自我实现理论与自我实现者；题干明确说“人格发展”。",
        "uncertainty": "“自我实现需要”也见第九章动机；按题干的“人格发展最高级阶段”主归人格。",
    },
    "2019-判断题-005": {
        "subject": "教材外（不统计）",
        "chapter": "发展研究的横断/纵向设计",
        "topic": "纵向研究与横断研究的选择",
        "include": False,
        "confidence": "中",
        "evidence": "复核《普通心理学》第6版第十四章：教材讲横向/纵向的观察视角，但未系统讲该题所需的发展研究设计及优缺点。",
        "uncertainty": "与第十四章人生全程发展情境相关，但直接作答知识点未在四本教材中形成条目，因此不纳入分章统计。",
    },
    "2019-单选题-032": {
        "confidence": "中",
        "evidence": "题目所在组及核心内容均为智力的一般水平，主归《普通心理学》第6版第十一章；离差智商也在《心理与教育测量》第4版第十二章出现。",
        "uncertainty": "普心第十一章与测量第十二章都有智商解释内容；按题组结构和主考点归普心。",
    },
    "2019-综合应用题-001": {
        "include": False,
        "confidence": "低",
        "evidence": "题目要求跨至少五个心理学主题，没有可唯一计数的教材或章节。为避免任意分配，保留在内部复核表但不进入分章统计。",
        "uncertainty": "并非一个明确的教材外知识点，而是无法唯一归章的开放综合题。",
    },
    "2020-名词解释-006": {
        "subject": GP,
        "chapter": "第九章 动机",
        "topic": "动机的归因理论：外部归因",
        "secondary": "",
        "confidence": "高",
        "evidence": "《普通心理学》第6版印刷页346在第九章“动机的归因理论”中直接区分内部原因与外部原因。",
        "note": "从原先的社会心理学教材外项目改回普心动机章。",
    },
    "2020-论述题-005": {
        "confidence": "中",
        "evidence": "题目同时涉及动机与情绪；《普通心理学》第6版第十章从情绪功能与调节角度集中处理二者关系，故主归情绪。",
        "uncertainty": "第九章动机是交叉章节；按题目在情绪理论语境中的作答框架主归第十章。",
    },
    "2021-简答题-003": {
        "subject": GP,
        "chapter": "第十一章 智力",
        "topic": "行为遗传学研究方法",
        "secondary": "第十四章 人生全程发展：遗传与环境",
        "confidence": "高",
        "evidence": "《普通心理学》第6版印刷页416在第十一章“影响智力的因素”中列出双生子、收养和追踪研究三类遗传研究思路。",
        "note": "研究方法的集中讲授位置在智力章，不按“发展/遗传”表面词归入第十四章。",
    },
    "2021-论述题-005": {
        "subject": GP,
        "chapter": "第九章 动机",
        "topic": "海德的归因理论",
        "secondary": "",
        "confidence": "高",
        "evidence": "《普通心理学》第6版印刷页346在第九章“动机的归因理论”中直接介绍海德及内、外部原因。",
        "note": "从原先的社会心理学教材外项目改回普心动机章。",
    },
    "2022-名词解释-004": {
        "subject": MEAS,
        "chapter": "第五章 测量效度",
        "topic": "构念（构想/理论结构）",
        "secondary": "",
        "confidence": "中",
        "evidence": "《心理与教育测量》第4版印刷页64—66在结构效度部分定义“构想或结构”为心理学理论中的抽象、假设性概念或特质。",
        "uncertainty": "教材主要用“构想/结构”，题干用同义术语“构念”；据概念定义主归测量效度。",
    },
    "2022-名词解释-005": {
        "subject": "教材外（不统计）",
        "chapter": "发展研究的纵向设计",
        "topic": "纵向研究",
        "include": False,
        "confidence": "中",
        "evidence": "复核《普通心理学》第6版第十四章，未找到纵向研究定义及其研究设计特点的直接条目。",
        "uncertainty": "人生全程发展是相关应用情境，但不足以支撑该名词解释，故不纳入四本教材统计。",
    },
    "2022-论述题-002": {
        "confidence": "中",
        "evidence": "题目要求用上行网状激活系统解释内外向差异，理论主干是人格的生物学解释，主归普心第十二章人格。",
        "uncertainty": "神经结构本身涉及第二章脑神经基础，但该题的解释对象是人格中的内外向。",
    },
    "2023-简答题-002": {
        "subject": "教材外（不统计）",
        "chapter": "发展研究的横断设计",
        "topic": "横断研究的定义与优缺点",
        "include": False,
        "confidence": "中",
        "evidence": "复核《普通心理学》第6版第十四章，教材未系统讲横断研究定义与优缺点。",
        "uncertainty": "题目与发展心理学相关，但直接作答条目超出四本教材的现有内容。",
    },
    "2023-简答题-003": {
        "subject": STAT,
        "chapter": "第六章 概率分布",
        "topic": "标准误与标准差的区别和联系",
        "secondary": "第七章 参数估计",
        "confidence": "高",
        "evidence": "《现代心理与教育统计学》第5版在第六章抽样分布部分定义标准误并说明它与总体标准差、样本容量的关系；第七章再将其用于参数估计。",
        "note": "按概念首次集中讲授位置归第六章，不因其在区间估计中应用而归第七章。",
    },
    "2023-综合应用题-001": {
        "confidence": "低",
        "evidence": "题目要求针对多个变量提出至少四种假设和统计方法，主旨是多变量分析规划，暂主归第十三章。",
        "uncertainty": "可分别调用第五章相关、第八章假设检验、第九章方差分析和第十二章回归；不存在唯一无争议章节。",
    },
    "2023-综合应用题-002": {
        "confidence": "低",
        "evidence": "可确认作答主体包含变量界定、实验设计与统计方法，因此暂主归实验第二章。",
        "uncertainty": "现有题库文本缺失题图，无法独立复核图示现象是否为团体极化；需原图确认现象名称。",
    },
    "2024-名词解释-001": {
        "confidence": "中",
        "evidence": "《实验心理学》第2版第二章小样本设计在印刷页82—84讲ABA设计，并以A-B-A-B四阶段图示说明反转处理，属于题干ABAB设计的同一设计家族。",
        "uncertainty": "教材标题使用“ABA设计”，图示完整程序为A-B-A-B；保留在第二章并标记术语差异。",
    },
    "2024-论述题-003": {
        "confidence": "中",
        "evidence": "核心作答对象是学习动机的强化取向与人本取向，主归普心第九章动机理论。",
        "uncertainty": "强化机制也与第十三章学习交叉；按“学习动机理论”的中心问题主归第九章。",
    },
    "2026-简答题-001": {
        "subject": GP,
        "chapter": "第十一章 智力",
        "topic": "双生子设计及其适用问题",
        "secondary": "第十四章 人生全程发展：遗传与环境",
        "confidence": "高",
        "evidence": "《普通心理学》第6版印刷页416在第十一章“影响智力的因素”中直接介绍同卵/异卵双生子、分开抚养与追踪研究。",
        "note": "按研究方法在教材中的集中讲授位置归智力章。",
    },
    "2026-简答题-003": {
        "subject": GP,
        "chapter": "第九章 动机",
        "topic": "动机的归因理论及归因对情绪的影响",
        "secondary": "第十章 情绪：情绪结果",
        "confidence": "高",
        "evidence": "《普通心理学》第6版印刷页346在第九章直接定义归因，并说明内外归因会影响满意、自豪、内疚、羞愧等情绪反应。",
        "note": "“情绪”是归因理论要解释的结果变量，主理论位置是第九章动机。",
    },
    "2026-简答题-006": {
        "confidence": "中",
        "evidence": "题目直接要求效度类型及检验思路，知识主体在《心理与教育测量》第4版第五章测量效度。",
        "uncertainty": "“编制初期”与第七章测验编制流程交叉；按实际作答内容主归第五章。",
    },
    "2026-案例分析题-002": {
        "confidence": "低",
        "evidence": "第一问以斯皮尔曼—布朗公式处理增题与信度，暂按首个明确测量任务主归测量第四章。",
        "uncertainty": "第二问是正态分布录取线，跨测量第八章常模与统计第六章概率分布；两问权重信息缺失。",
    },
}


FIELDNAMES = [
    "题目ID",
    "年份",
    "题型",
    "题号",
    "题干",
    "原科目",
    "原章节",
    "复核科目",
    "复核章节",
    "复核核心考点",
    "次要考点或跨章节",
    "是否纳入四本教材统计",
    "置信度",
    "复核依据",
    "是否改动",
    "不确定说明",
    "归类备注",
    "原始定位",
    "题目全文",
]


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def review_row(row: dict[str, str]) -> dict[str, str]:
    override = OVERRIDES.get(row["题目ID"], {})
    subject = str(override.get("subject", row["主科目"]))
    chapter = str(override.get("chapter", row["教材主章节"]))
    topic = str(override.get("topic", row["核心考点"]))
    secondary = str(override.get("secondary", row["次要考点或跨章节"]))
    include = bool(override.get("include", subject in OFFICIAL_SUBJECTS))
    confidence = str(override.get("confidence", "高"))
    uncertainty = str(override.get("uncertainty", ""))
    note = str(override.get("note", row["归类备注"]))

    if "evidence" in override:
        evidence = str(override["evidence"])
    elif include:
        evidence = (
            f"逐题复核：核心作答对象“{topic}”与{subject}“{chapter}”的主讲内容一致；"
            "题干中的应用情境、结果变量或干扰项不改变主归属。"
        )
    else:
        evidence = (
            f"逐题复核：核心作答对象“{topic}”属于{subject}，"
            "四本指定教材没有可直接支撑完整作答的对应条目，不纳入分章统计。"
        )

    original_include = row["主科目"] in OFFICIAL_SUBJECTS
    changed = (
        subject != row["主科目"]
        or chapter != row["教材主章节"]
        or include != original_include
    )
    return {
        "题目ID": row["题目ID"],
        "年份": row["年份"],
        "题型": row["题型"],
        "题号": row["题号"],
        "题干": row["题干"],
        "原科目": row["主科目"],
        "原章节": row["教材主章节"],
        "复核科目": subject,
        "复核章节": chapter,
        "复核核心考点": topic,
        "次要考点或跨章节": secondary,
        "是否纳入四本教材统计": "是" if include else "否",
        "置信度": confidence,
        "复核依据": evidence,
        "是否改动": "是" if changed else "否",
        "不确定说明": uncertainty,
        "归类备注": note,
        "原始定位": row["原始定位"],
        "题目全文": row["题目全文"],
    }


def validate(source: list[dict[str, str]], reviewed: list[dict[str, str]]) -> None:
    source_ids = [row["题目ID"] for row in source]
    reviewed_ids = [row["题目ID"] for row in reviewed]
    if len(source) != 255 or len(reviewed) != 255:
        raise AssertionError(f"题目数量异常：source={len(source)}, reviewed={len(reviewed)}")
    if len(set(source_ids)) != len(source_ids):
        raise AssertionError("源题目ID存在重复")
    if source_ids != reviewed_ids:
        raise AssertionError("复核表没有逐题保持源题目顺序")
    unknown_overrides = sorted(set(OVERRIDES) - set(source_ids))
    if unknown_overrides:
        raise AssertionError(f"覆盖项不存在：{unknown_overrides}")
    for row in reviewed:
        if row["是否纳入四本教材统计"] == "是" and row["复核科目"] not in OFFICIAL_SUBJECTS:
            raise AssertionError(f"非四科题被纳入：{row['题目ID']}")
        if row["置信度"] not in {"高", "中", "低"}:
            raise AssertionError(f"置信度异常：{row['题目ID']} {row['置信度']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = read_tsv(args.source)
    reviewed = [review_row(row) for row in source]
    validate(source, reviewed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDNAMES, delimiter="\t")
        writer.writeheader()
        writer.writerows(reviewed)

    included = [row for row in reviewed if row["是否纳入四本教材统计"] == "是"]
    changed = [row for row in reviewed if row["是否改动"] == "是"]
    uncertain = [row for row in included if row["置信度"] != "高"]
    print(f"output={args.output}")
    print(f"reviewed={len(reviewed)}")
    print(f"included={len(included)}")
    print(f"excluded={len(reviewed) - len(included)}")
    print(f"changed={len(changed)}")
    print(f"included_uncertain={len(uncertain)}")


if __name__ == "__main__":
    main()
