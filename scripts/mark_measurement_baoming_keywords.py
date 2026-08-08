from __future__ import annotations

import argparse
import re
from pathlib import Path

from build_baoming_full_v5 import mark_answer_line, parse_markdown_bold


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "content/measurement_baoming_ch1_3.md",
    ROOT / "content/measurement_baoming_ch4_5.md",
    ROOT / "content/measurement_baoming_ch6_8.md",
    ROOT / "content/measurement_baoming_ch9_11.md",
)


# 自动标注后只修正会切断固定词或遗漏比较方向的少量句子。替换前后去除
# Markdown 粗体标记后必须完全一致，因而不会改写知识正文。
MANUAL_REPLACEMENTS = {
    "心理**测量的完整实践需要肯定心理的可测性、确定测量内容**，并在阐明心理内容的特性或差异性的基础上形成具体测量方法。":
        "心理测量的完整实践需要**肯定心理的可测性、确定测量内容**，并在阐明心理内容的特性或差异性的基础上**形成具体测量方法**。",
    "“**陆军A式量表**”是文字测验，“陆军B式量表”是非文字测验，二者推动心理测验由个别施测走向团体施测。":
        "“**陆军A式量表**”是**文字测验**，“**陆军B式量表**”是**非文字测验**，二者**推动心理测验由个别施测走向团体施测**。",
    "测验结果不受主观因素**影响，并具有重复性**。":
        "测验结果**不受主观因素影响**，并**具有重复性**。",
    "以及自**由反应题评分不客观**，都会影响结果。":
        "以及**自由反应题评分不客观**，都会影响结果。",
    "让受测者自**由反应**，":
        "让受测者**自由反应**，",
    "平衡“是”**和“否”题目的数量与方向**，并通过题目编排和统计方法控制回答误差。":
        "平衡“是”和“否”题目的**数量与方向**，并通过**题目编排和统计方法控制回答误差**。",
    "可通过平衡“是”“**否”题目和控制回答误差加以改善**。":
        "可通过平衡“是”“否”题目和**控制回答误差**加以改善。",
    "效度不是简单的“**有效**”或“无效”":
        "效度不是简单的“**有效**”或“**无效**”",
    "每个被试面对相同**测量条件时**，侧面与被试交叉；每个被试面对不同**测量条件时**，侧面嵌套于被试。":
        "每个被试面对**相同测量条件**时，侧面与被试交叉；每个被试面对**不同测量条件**时，侧面嵌套于被试。",
    "内容效度回答“**测题是否代表应测内容**”，结构效度回答“测验是否反映预定心理结构”，效标效度回答“测验能否预测或估计外部行为表现”。":
        "内容效度回答“**测题是否代表应测内容**”，结构效度回答“**测验是否反映预定心理结构**”，效标效度回答“**测验能否预测或估计外部行为表现**”。",
    "常模回答“**与他人相比处于什么位置**”，标准回答“是否达到预定要求”。":
        "常模回答“**与他人相比处于什么位置**”，标准回答“**是否达到预定要求**”。",
    "施测更具弹性，主试可根据受测者表现分阶段进行施测和计分。":
        "**施测更具弹性**，主试可根据受测者表现**分阶段进行施测和计分**。",
    "瑞文测验发展出标准型、彩色型、高级型和联合型四种形式。":
        "瑞文测验发展出**标准型、彩色型、高级型和联合型**四种形式。",
    "包括疑病、抑郁、癔症、精神病态偏执、男性化—女性化、妄想狂、精神衰弱、精神分裂、轻躁狂和社会内向等量表。":
        "包括**疑病、抑郁、癔症、精神病态偏执、男性化—女性化**、**妄想狂、精神衰弱、精神分裂、轻躁狂和社会内向**等量表。",
    "效度系数同时受测验信度、效标测量信度以及预测变量与效标变量真实相关程度的影响。":
        "效度系数同时受**测验信度、效标测量信度以及预测变量与效标变量真实相关程度**的影响。",
    "效度系数受测验信度、效标测量信度及二者真实相关程度影响；效标应有效、可靠并独立于原测验，防止效标污染。":
        "效度系数受**测验信度、效标测量信度及二者真实相关程度**影响；效标应**有效、可靠并独立于原测验**，防止效标污染。",
    "项目难度、鉴别力等参数会随取样团体改变。":
        "项目难度、鉴别力等参数会**随取样团体改变**。",
    "规定测验适用人群及其年龄、教育和其他重要特征。":
        "规定**测验适用人群及其年龄、教育和其他重要特征**。",
    "检查题目的技术性问题、有效性和可信度，进行初步修改。":
        "检查题目的**技术性问题、有效性和可信度**，进行初步修改。",
    "简洁说明测验内容、分数含义、可能误解及运用方式。":
        "简洁说明**测验内容、分数含义、可能误解及运用方式**。",
}


def semantic(text: str) -> str:
    return text.replace("**", "")


def mark_line(raw: str) -> str:
    if not raw or raw.startswith("#") or raw == "---":
        return raw
    plain, intervals = parse_markdown_bold(raw)
    marked = mark_answer_line(plain, intervals)
    for old, new in MANUAL_REPLACEMENTS.items():
        if old in marked:
            assert semantic(old) == semantic(new)
            marked = marked.replace(old, new)
    return marked


def transform(text: str) -> str:
    return "\n".join(mark_line(line) for line in text.splitlines()) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    changed = []
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        result = transform(source)
        assert semantic(source) == semantic(result), path
        if result != source:
            changed.append(path)
            if arguments.write:
                path.write_text(result, encoding="utf-8")
    action = "已写入" if arguments.write else "待写入"
    print(f"关键词标注{action}：{len(changed)}个文件。")


if __name__ == "__main__":
    main()
