#!/usr/bin/env python3
"""Apply a deterministic, reviewable primary classification to every question."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


GP = "普通心理学（第6版）"
EP = "实验心理学（第2版）"
MEAS = "心理与教育测量（第4版）"
STAT = "现代心理与教育统计学（第5版）"
SOC = "社会心理学（跨教材拓展）"
ABN = "变态与咨询心理学（跨教材拓展）"
ORG = "管理与组织心理学（跨教材拓展）"
MIX = "跨科目综合"

GP_CH = {
    1: "第一章 心理学的研究对象和方法",
    2: "第二章 心理与行为的脑神经基础",
    3: "第三章 感觉",
    4: "第四章 知觉",
    5: "第五章 意识",
    6: "第六章 记忆",
    7: "第七章 思维",
    8: "第八章 语言",
    9: "第九章 动机",
    10: "第十章 情绪",
    11: "第十一章 智力",
    12: "第十二章 人格",
    13: "第十三章 学习",
    14: "第十四章 人生全程发展",
}
EP_CH = {
    1: "第一章 绪论",
    2: "第二章 实验研究的基本问题",
    3: "第三章 如何读和写心理学实验报告",
    4: "第四章 反应时",
    5: "第五章 心理物理学",
    6: "第六章 注意",
    7: "第七章 感知觉",
    8: "第八章 记忆与学习",
    9: "第九章 思维",
    10: "第十章 情绪",
    11: "第十一章 实验研究技术在社会认知领域的应用",
}
MEAS_CH = {
    1: "第一章 心理与教育测量概论",
    2: "第二章 心理与教育测量简史",
    3: "第三章 经典测验理论的基本假设",
    4: "第四章 测量信度",
    5: "第五章 测量效度",
    6: "第六章 测验的项目分析",
    7: "第七章 心理与教育测验的编制与实施",
    8: "第八章 常模参照测验",
    9: "第九章 目标参照测验",
    10: "第十章 测验等值",
    11: "第十一章 学绩测验",
    12: "第十二章 能力测验（上）",
    13: "第十三章 能力测验（下）",
    14: "第十四章 人格测量",
    15: "第十五章 其他心理与教育测验",
    16: "第十六章 测量应用实务",
    17: "第十七章 测量理论与应用的新发展",
}
STAT_CH = {
    1: "第一章 绪论",
    2: "第二章 统计图表",
    3: "第三章 集中量数",
    4: "第四章 差异量数",
    5: "第五章 相关关系",
    6: "第六章 概率分布",
    7: "第七章 参数估计",
    8: "第八章 假设检验",
    9: "第九章 方差分析",
    10: "第十章 χ²检验",
    11: "第十一章 非参数检验",
    12: "第十二章 线性回归",
    13: "第十三章 多变量统计分析简介",
    14: "第十四章 抽样原理及方法",
}

CATALOGS = {GP: GP_CH, EP: EP_CH, MEAS: MEAS_CH, STAT: STAT_CH}


def qid(year: int, kind: str, number: int) -> str:
    return f"{year}-{kind}-{number:03d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--catalog-output", type=Path, required=True)
    args = parser.parse_args()

    with args.source.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))

    mapping: dict[str, dict[str, str]] = {}

    def assign(
        year: int,
        kind: str,
        numbers: int | range | list[int] | tuple[int, ...],
        subject: str,
        chapter: str,
        topic: str,
        secondary: str = "",
        note: str = "",
    ) -> None:
        if isinstance(numbers, int):
            iterable = [numbers]
        else:
            iterable = numbers
        for number in iterable:
            key = qid(year, kind, number)
            if key in mapping:
                raise ValueError(f"duplicate mapping: {key}")
            mapping[key] = {
                "主科目": subject,
                "教材主章节": chapter,
                "核心考点": topic,
                "次要考点或跨章节": secondary,
                "归类备注": note,
            }

    # 2019 单选题
    assign(2019, "单选题", range(1, 4), GP, GP_CH[1], "心理学流派与学科发展")
    assign(2019, "单选题", 4, EP, EP_CH[4], "心理旋转实验中的反应时", "普通心理学第七章 思维")
    assign(2019, "单选题", 5, GP, GP_CH[1], "研究伦理与知情同意")
    assign(2019, "单选题", range(6, 9), EP, EP_CH[2], "额外变量与实验效应")
    assign(2019, "单选题", range(9, 13), GP, GP_CH[3], "感觉现象与感觉规律")
    assign(2019, "单选题", range(13, 18), GP, GP_CH[4], "运动、空间、时间与组织知觉")
    assign(2019, "单选题", range(18, 22), GP, GP_CH[5], "睡眠、梦与注意")
    assign(2019, "单选题", range(22, 25), GP, GP_CH[13], "观察学习与条件作用")
    assign(2019, "单选题", 25, GP, GP_CH[6], "遗忘规律")
    assign(2019, "单选题", range(26, 28), GP, GP_CH[14], "心理社会发展与依恋")
    assign(2019, "单选题", range(28, 32), GP, GP_CH[7], "概念、思维类型与问题解决")
    assign(2019, "单选题", range(32, 34), GP, GP_CH[11], "智力测量与影响因素")
    assign(2019, "单选题", range(34, 39), GP, GP_CH[9], "成就动机、需要与归因")
    assign(2019, "单选题", range(39, 44), GP, GP_CH[10], "基本情绪、应激与表情")
    assign(2019, "单选题", 44, MEAS, MEAS_CH[14], "投射测验与人格测验")
    assign(2019, "单选题", 45, SOC, "社会影响：服从、从众与依从", "服从")
    assign(2019, "单选题", 46, SOC, "社会认知与归因", "归因与认知失调")
    assign(2019, "单选题", 47, EP, EP_CH[11], "内隐社会认知研究方法", "社会心理学：内隐社会认知")
    assign(2019, "单选题", 48, SOC, "攻击与冲突", "挫折—攻击理论")
    assign(2019, "单选题", 49, SOC, "群体过程", "社会促进")
    assign(2019, "单选题", 50, ORG, "人性假设", "经济人假设")
    assign(2019, "单选题", 51, ABN, "心理咨询与治疗", "心理咨询师的工作边界")
    assign(2019, "单选题", 52, ABN, "人格障碍", "反社会型人格障碍")
    assign(2019, "单选题", 53, ABN, "情绪障碍", "双相情感障碍")
    assign(2019, "单选题", 54, ABN, "精神病性障碍", "精神分裂症阳性症状")
    assign(2019, "单选题", 55, MEAS, MEAS_CH[12], "离差智商与比率智商")
    assign(2019, "单选题", 56, MEAS, MEAS_CH[1], "测量量表类型")
    assign(2019, "单选题", 57, MEAS, MEAS_CH[5], "效标关联效度")
    assign(2019, "单选题", 58, MEAS, MEAS_CH[6], "测验难度与分数分布")
    assign(2019, "单选题", 59, MEAS, MEAS_CH[4], "重测信度")
    assign(2019, "单选题", 60, MEAS, MEAS_CH[3], "测量误差")
    assign(2019, "单选题", 61, STAT, STAT_CH[2], "数据分布形态")
    assign(2019, "单选题", 62, STAT, STAT_CH[3], "偏态分布中的集中量数")
    assign(2019, "单选题", 63, STAT, STAT_CH[6], "正态分布")
    assign(2019, "单选题", 64, STAT, STAT_CH[9], "方差分析自由度")
    assign(2019, "单选题", 65, STAT, STAT_CH[7], "置信区间与样本容量")

    # 2019 判断题
    assign(2019, "判断题", 1, GP, GP_CH[4], "深度知觉与视崖实验")
    assign(2019, "判断题", 2, GP, GP_CH[5], "睡眠脑电")
    assign(2019, "判断题", range(3, 5), GP, GP_CH[3], "听觉理论与感觉阈限")
    assign(2019, "判断题", range(5, 7), GP, GP_CH[14], "发展研究与道德发展")
    assign(2019, "判断题", 7, GP, GP_CH[9], "动机的产生条件")
    assign(2019, "判断题", 8, SOC, "态度与人际吸引", "曝光效应")
    assign(2019, "判断题", 9, GP, GP_CH[12], "心理防御机制")
    assign(2019, "判断题", 10, ORG, "领导理论", "领导权变理论")
    assign(2019, "判断题", 11, ORG, "组织变革", "勒温组织变革模型")
    assign(2019, "判断题", 12, ABN, "焦虑、创伤与强迫相关障碍", "创伤后应激障碍")
    assign(2019, "判断题", 13, ABN, "心理咨询与治疗", "双重关系")
    assign(2019, "判断题", 14, ABN, "心理咨询伦理", "隐私、保密与自主决定")
    assign(2019, "判断题", 15, ABN, "物质使用与成瘾", "耐受与戒断")
    assign(2019, "判断题", 16, ABN, "神经发育障碍", "孤独症病因")
    assign(2019, "判断题", 17, STAT, STAT_CH[5], "正相关")
    assign(2019, "判断题", 18, MEAS, MEAS_CH[1], "心理测量的基本要素", "第四章信度；第五章效度")
    assign(2019, "判断题", 19, MEAS, MEAS_CH[5], "信度与效度的关系", "第四章 测量信度")
    assign(2019, "判断题", 20, STAT, STAT_CH[2], "线形图")

    # 2019 主观题
    assign(2019, "名词解释", 1, GP, GP_CH[4], "知觉")
    assign(2019, "名词解释", 2, GP, GP_CH[13], "学习")
    assign(2019, "名词解释", 3, GP, GP_CH[5], "注意")
    assign(2019, "名词解释", range(4, 6), GP, GP_CH[14], "最近发展区与顺应")
    assign(2019, "名词解释", 6, GP, GP_CH[7], "思维")
    assign(2019, "名词解释", 7, GP, GP_CH[9], "动机")
    assign(2019, "名词解释", 8, GP, GP_CH[10], "情绪")
    assign(2019, "名词解释", 9, ABN, "心理障碍概述", "精神疾病")
    assign(2019, "名词解释", 10, MEAS, MEAS_CH[3], "真分数理论")
    assign(2019, "简答题", 1, GP, GP_CH[1], "心理学研究方法")
    assign(2019, "简答题", 2, GP, GP_CH[11], "智力理论")
    assign(2019, "简答题", 3, STAT, STAT_CH[5], "积差相关的适用条件")
    assign(2019, "论述题", 1, GP, GP_CH[6], "记忆系统及其转换")
    assign(2019, "论述题", 2, GP, GP_CH[14], "皮亚杰认知发展阶段")
    assign(2019, "论述题", 3, GP, GP_CH[12], "精神分析人格理论")
    assign(2019, "论述题", 4, ORG, "激励理论", "员工激励")
    assign(2019, "综合应用题", 1, MIX, "多主题综合应用", "至少五个心理学主题", note="题目明确要求跨五个主题，不宜归入单一教材章；作为独立综合类唯一计数。")

    # 2020
    assign(2020, "名词解释", range(1, 3), EP, EP_CH[2], "实验者效应与安慰剂效应")
    assign(2020, "名词解释", 3, GP, GP_CH[4], "知觉恒常性")
    assign(2020, "名词解释", 4, GP, GP_CH[7], "思维定势")
    assign(2020, "名词解释", 5, EP, EP_CH[5], "心理量")
    assign(2020, "名词解释", 6, SOC, "社会认知与归因", "外部归因")
    assign(2020, "名词解释", 7, GP, GP_CH[9], "动机")
    assign(2020, "名词解释", 8, GP, GP_CH[6], "内隐记忆")
    assign(2020, "名词解释", 9, GP, GP_CH[10], "基本情绪")
    assign(2020, "名词解释", 10, GP, GP_CH[9], "需要层次理论")
    assign(2020, "简答题", 1, EP, EP_CH[4], "唐德斯减数法")
    assign(2020, "简答题", 2, GP, GP_CH[14], "皮亚杰认知发展理论")
    assign(2020, "简答题", 3, GP, GP_CH[5], "注意过滤器理论")
    assign(2020, "简答题", 4, EP, EP_CH[5], "信号检测论")
    assign(2020, "简答题", 5, EP, EP_CH[5], "心理量与物理量的关系")
    assign(2020, "论述题", 1, GP, GP_CH[1], "自然观察法与实验法")
    assign(2020, "论述题", 2, GP, GP_CH[6], "内隐记忆与外显记忆")
    assign(2020, "论述题", 3, GP, GP_CH[10], "情绪产生机制")
    assign(2020, "论述题", 4, GP, GP_CH[4], "经验和思维定势对知觉的影响", "第七章 思维")
    assign(2020, "论述题", 5, GP, GP_CH[10], "情绪与动机的关系", "第九章 动机")
    assign(2020, "实验设计题", range(1, 3), EP, EP_CH[2], "实验设计", "社会心理/记忆情境；统计方法")

    # 2021
    assign(2021, "名词解释", range(1, 3), GP, GP_CH[12], "心理防御机制与大五人格")
    assign(2021, "名词解释", 3, GP, GP_CH[11], "晶体智力")
    assign(2021, "名词解释", 4, GP, GP_CH[3], "感觉后效")
    assign(2021, "名词解释", 5, GP, GP_CH[12], "气质")
    assign(2021, "名词解释", 6, MEAS, MEAS_CH[14], "投射测验")
    assign(2021, "名词解释", 7, SOC, "社会认知与归因", "基本归因偏差")
    assign(2021, "名词解释", 8, GP, GP_CH[6], "陈述性记忆")
    assign(2021, "名词解释", 9, GP, GP_CH[7], "概念")
    assign(2021, "名词解释", 10, GP, GP_CH[13], "桑代克效果律")
    assign(2021, "简答题", 1, SOC, "社会影响：服从、从众与依从", "规范性从众与信息性从众")
    assign(2021, "简答题", 2, SOC, "攻击与冲突", "挫折—攻击理论")
    assign(2021, "简答题", 3, GP, GP_CH[14], "行为遗传学研究方法", "第十一章智力；第十二章人格")
    assign(2021, "简答题", 4, GP, GP_CH[11], "多元智力理论")
    assign(2021, "简答题", 5, GP, GP_CH[12], "人格的定义与特征")
    assign(2021, "论述题", 1, GP, GP_CH[12], "弗洛伊德人格发展阶段")
    assign(2021, "论述题", 2, GP, GP_CH[6], "提高记忆效率")
    assign(2021, "论述题", 3, GP, GP_CH[13], "操作性条件作用规律")
    assign(2021, "论述题", 4, GP, GP_CH[7], "演绎推理与归纳推理")
    assign(2021, "论述题", 5, SOC, "社会认知与归因", "海德归因理论")
    assign(2021, "实验设计题", range(1, 3), EP, EP_CH[2], "实验设计", "态度改变/言语与推理；统计方法")

    # 2022
    assign(2022, "名词解释", 1, SOC, "社会认知与自我", "自我妨碍")
    assign(2022, "名词解释", 2, SOC, "社会化与社会行为", "社会化")
    assign(2022, "名词解释", range(3, 5), GP, GP_CH[12], "防御机制与人格构念")
    assign(2022, "名词解释", 5, GP, GP_CH[14], "纵向研究")
    assign(2022, "名词解释", 6, GP, GP_CH[5], "有意后注意")
    assign(2022, "名词解释", 7, GP, GP_CH[7], "线性推理")
    assign(2022, "名词解释", 8, GP, GP_CH[3], "感觉适应")
    assign(2022, "名词解释", range(9, 11), GP, GP_CH[6], "前摄抑制与工作记忆")
    assign(2022, "简答题", 1, GP, GP_CH[4], "知觉的基本特性")
    assign(2022, "简答题", 2, GP, GP_CH[10], "情绪调节策略")
    assign(2022, "简答题", 3, GP, GP_CH[5], "鸡尾酒效应与注意理论")
    assign(2022, "简答题", 4, SOC, "态度与说服", "说服的途径")
    assign(2022, "简答题", 5, ABN, "情绪障碍", "双相情感障碍")
    assign(2022, "论述题", 1, GP, GP_CH[14], "皮亚杰儿童思维发展阶段")
    assign(2022, "论述题", 2, GP, GP_CH[12], "上行网状激活系统与内外向", "第二章 脑神经基础")
    assign(2022, "论述题", 3, GP, GP_CH[6], "遗忘理论")
    assign(2022, "论述题", 4, EP, EP_CH[2], "额外变量控制")
    assign(2022, "论述题", 5, SOC, "态度与认知一致性", "认知失调理论")
    assign(2022, "实验设计题", range(1, 3), EP, EP_CH[2], "实验设计", "社会惰化/消费者行为；统计方法")

    # 2023
    assign(2023, "名词解释", 1, EP, EP_CH[5], "信号检测论辨别力指标")
    assign(2023, "名词解释", 2, GP, GP_CH[5], "谢夫林双加工理论")
    assign(2023, "名词解释", 3, GP, GP_CH[7], "代表性启发式")
    assign(2023, "名词解释", 4, SOC, "亲社会行为", "社会责任规范")
    assign(2023, "名词解释", 5, ABN, "心理咨询与治疗", "来访者中心疗法")
    assign(2023, "名词解释", 6, MEAS, MEAS_CH[4], "信度")
    assign(2023, "简答题", 1, GP, GP_CH[5], "睡眠阶段")
    assign(2023, "简答题", 2, GP, GP_CH[14], "横断研究")
    assign(2023, "简答题", 3, STAT, STAT_CH[7], "标准误与标准差", "第四章 差异量数")
    assign(2023, "简答题", 4, GP, GP_CH[6], "工作记忆")
    assign(2023, "简答题", 5, EP, EP_CH[2], "混淆变量及其控制")
    assign(2023, "论述题", 1, GP, GP_CH[13], "学习理论的行为改变应用", "物质使用与成瘾")
    assign(2023, "论述题", 2, GP, GP_CH[14], "毕生发展与选择—优化—补偿模型")
    assign(2023, "论述题", 3, GP, GP_CH[5], "选择性注意理论")
    assign(2023, "论述题", 4, STAT, STAT_CH[8], "p值、显著性与结果解释")
    assign(2023, "综合应用题", 1, STAT, STAT_CH[13], "多变量研究假设与统计方法", "第五章相关；第九章方差分析；第十二章回归")
    assign(2023, "综合应用题", 2, EP, EP_CH[2], "团体极化的混合实验设计", "社会心理学：群体过程；统计学：重复测量方差分析")
    assign(2023, "综合应用题", 3, EP, EP_CH[2], "两因素实验设计与交互作用", "亲社会行为；统计学：方差分析与简单效应")

    # 2024
    assign(2024, "填空题", 1, EP, EP_CH[4], "唐德斯反应时")
    assign(2024, "填空题", 2, GP, GP_CH[12], "阿德勒人格理论")
    assign(2024, "填空题", 3, GP, GP_CH[6], "工作记忆容量")
    assign(2024, "填空题", 4, GP, GP_CH[14], "皮亚杰守恒任务")
    assign(2024, "填空题", 5, MEAS, MEAS_CH[12], "离差智商")
    assign(2024, "填空题", 6, EP, EP_CH[5], "差别阈限法")
    assign(2024, "填空题", 7, ORG, "人性假设", "X理论")
    assign(2024, "填空题", 8, ABN, "焦虑障碍", "广泛性焦虑障碍")
    assign(2024, "填空题", 9, GP, GP_CH[13], "经典条件作用")
    assign(2024, "填空题", 10, GP, GP_CH[4], "图形—背景与知觉选择性")
    assign(2024, "名词解释", 1, EP, EP_CH[2], "ABAB小样本设计")
    assign(2024, "名词解释", 2, ORG, "激励理论", "三重需要理论")
    assign(2024, "名词解释", 3, ORG, "领导理论", "费德勒权变理论")
    assign(2024, "名词解释", 4, GP, GP_CH[9], "耶克斯—多德森定律")
    assign(2024, "名词解释", 5, SOC, "社会认知与刻板印象", "刻板印象")
    assign(2024, "名词解释", 6, GP, GP_CH[14], "最近发展区")
    assign(2024, "简答题", 1, ABN, "心理咨询与治疗", "抑郁症治疗")
    assign(2024, "简答题", 2, GP, GP_CH[10], "情绪理论")
    assign(2024, "简答题", 3, GP, GP_CH[4], "深度知觉线索")
    assign(2024, "论述题", 1, GP, GP_CH[14], "埃里克森人格发展阶段")
    assign(2024, "论述题", 2, GP, GP_CH[6], "遗忘原因与改善")
    assign(2024, "论述题", 3, GP, GP_CH[9], "学习动机理论及应用")
    assign(2024, "实验设计题", range(1, 4), EP, EP_CH[2], "实验设计", "学习/人格/社会行为情境；统计方法")

    # 2025
    assign(2025, "名词解释", 1, GP, GP_CH[9], "需要层次理论")
    assign(2025, "名词解释", 2, GP, GP_CH[13], "操作性条件反射")
    assign(2025, "名词解释", 3, GP, GP_CH[12], "自我概念")
    assign(2025, "名词解释", 4, GP, GP_CH[11], "多元智力理论")
    assign(2025, "名词解释", 5, ABN, "神经发育障碍", "孤独症")
    assign(2025, "名词解释", 6, GP, GP_CH[6], "动机性遗忘")
    assign(2025, "名词解释", 7, GP, GP_CH[5], "阈下知觉")
    assign(2025, "名词解释", 8, GP, GP_CH[9], "期望理论")
    assign(2025, "名词解释", 9, EP, EP_CH[2], "准实验设计")
    assign(2025, "名词解释", 10, MEAS, MEAS_CH[5], "测量效度")
    assign(2025, "简答题", 1, ABN, "心理咨询与治疗", "心理障碍治疗方法")
    assign(2025, "简答题", 2, GP, GP_CH[13], "观察学习")
    assign(2025, "简答题", 3, STAT, STAT_CH[8], "假设检验原理与过程")
    assign(2025, "论述题", 1, GP, GP_CH[14], "皮亚杰发展阶段及教育启示")
    assign(2025, "论述题", 2, GP, GP_CH[6], "记忆类型")
    assign(2025, "论述题", 3, GP, GP_CH[10], "压力应对")
    assign(2025, "实验设计题", range(1, 4), EP, EP_CH[2], "实验设计", "注意/工作满意度/正念与亲社会行为；统计方法")

    # 2026
    assign(2026, "单选题", 1, EP, EP_CH[2], "自变量")
    assign(2026, "单选题", 2, GP, GP_CH[5], "注意的定义")
    assign(2026, "单选题", 3, GP, GP_CH[13], "经典条件作用中的无条件刺激")
    assign(2026, "单选题", 4, STAT, STAT_CH[4], "线性变换下的方差")
    assign(2026, "单选题", range(5, 7), GP, GP_CH[13], "正强化与观察学习")
    assign(2026, "单选题", 7, EP, EP_CH[2], "被试间设计与随机分配", note="原题括注为心理统计，但主考点是实验设计，按教材内容纠正归类。")
    assign(2026, "单选题", 8, GP, GP_CH[3], "绝对阈限")
    assign(2026, "单选题", 9, GP, GP_CH[4], "知觉组织的相似性原则")
    assign(2026, "单选题", 10, MEAS, MEAS_CH[6], "测验项目区分度")
    assign(2026, "名词解释", 1, GP, GP_CH[5], "注意瞬脱")
    assign(2026, "名词解释", 2, GP, GP_CH[6], "工作记忆")
    assign(2026, "名词解释", 3, GP, GP_CH[10], "情绪的认知评价理论")
    assign(2026, "名词解释", 4, STAT, STAT_CH[6], "标准正态分布")
    assign(2026, "名词解释", 5, MEAS, MEAS_CH[12], "心理年龄")
    assign(2026, "简答题", 1, GP, GP_CH[14], "双生子设计")
    assign(2026, "简答题", 2, EP, EP_CH[2], "实验信度")
    assign(2026, "简答题", 3, GP, GP_CH[10], "归因对情绪的影响", "第九章 动机；社会心理学归因")
    assign(2026, "简答题", 4, GP, GP_CH[10], "情绪的核心功能")
    assign(2026, "简答题", 5, STAT, STAT_CH[8], "p值与统计推断", "第六章 概率分布")
    assign(2026, "简答题", 6, MEAS, MEAS_CH[5], "量表编制初期的效度检验", "第七章 测验编制与实施")
    assign(2026, "案例分析题", 1, STAT, STAT_CH[8], "独立样本t检验与研究结论", "实验心理学：被试间设计")
    assign(2026, "案例分析题", 2, MEAS, MEAS_CH[4], "测验增题与信度", "第八章常模参照测验；统计学第六章概率分布", "题目含信度提升与正态分布录取线两个子问，按首个核心测量任务唯一计入信度章。")
    assign(2026, "实验设计题", 1, EP, EP_CH[2], "记忆方式转变的实验设计", "普通心理学第六章 记忆；统计方法")

    source_ids = {row["题目ID"] for row in rows}
    mapped_ids = set(mapping)
    missing = sorted(source_ids - mapped_ids)
    extra = sorted(mapped_ids - source_ids)
    if missing or extra:
        raise ValueError(f"mapping mismatch: missing={missing}, extra={extra}")

    output_rows: list[dict[str, str]] = []
    for row in rows:
        classified = mapping[row["题目ID"]]
        basis = (
            "四本指定教材目录与题干主考点"
            if classified["主科目"] in CATALOGS
            else "真题题干与解析；四本指定教材未覆盖，按学科拓展标注"
        )
        output_rows.append(
            {
                **{key: row[key] for key in ["题目ID", "年份", "题型", "题号", "题干"]},
                **classified,
                "归类依据": basis,
                "唯一计数": "1",
                "原始定位": row["原始定位"],
                "题目全文": row["题目全文"],
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output_rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(output_rows)

    with args.catalog_output.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = ["科目", "章节序号", "章节名称", "来源"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for subject, chapters in CATALOGS.items():
            for number, chapter in chapters.items():
                writer.writerow(
                    {
                        "科目": subject,
                        "章节序号": number,
                        "章节名称": chapter,
                        "来源": "深大指定教材目录",
                    }
                )
        for subject, chapter in sorted(
            {(item["主科目"], item["教材主章节"]) for item in mapping.values() if item["主科目"] not in CATALOGS}
        ):
            writer.writerow(
                {
                    "科目": subject,
                    "章节序号": "拓展",
                    "章节名称": chapter,
                    "来源": "旧真题超出当前四本指定教材，按学科专题归类",
                }
            )

    print(f"classified={len(output_rows)}")
    print(f"subjects={len({row['主科目'] for row in output_rows})}")
    print(f"chapters_used={len({(row['主科目'], row['教材主章节']) for row in output_rows})}")


if __name__ == "__main__":
    main()
