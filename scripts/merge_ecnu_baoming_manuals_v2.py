from __future__ import annotations

from pathlib import Path

import merge_ecnu_baoming_manuals as base


ROOT = Path(__file__).resolve().parents[1]
base.OUTPUT = ROOT / "deliverables/华东师范大学347保命手册_导论实验测量合订精校版V2.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/ecnu_baoming_combined_v2_page_map.json"
base.STRIP_NON_CHAPTER_PAGE_BREAKS = True
base.COMBINED_NON_CHAPTER_PAGE_BREAK_TEXTS = {
    "1. 人格自陈量表常见的反应偏差包括：",
    "2. 两类测验的联系在于：二者都以人格为测量对象，都需要根据受测者的反应推断人格，并受到测验信度、效度和解释规范的制约。",
    "3. 概化理论的研究阶段和基本设计如下：",
    "效标效度指测验分数对某一行为表现的预测能力高低。（按收集效标资料的时间，可分为同时效度和预测效度。）【名词解释：效标效度】",
    "1. 项目鉴别力的主要估计方法及解释标准如下：",
    "3. 常模与标准的区别如下：",
    "发展量表以年龄或年级等发展水平解释个体测验成绩，便于说明儿童在发展序列中的位置。",
}
base.SOURCES = (
    (
        "第一部分 心理学导论",
        "心理学导论",
        "华东师范大学347｜心理学导论保命手册",
        ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_任务适配精校版V10.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "华东师范大学347｜实验心理学保命手册",
        ROOT / "deliverables/华东师范大学347实验心理学保命手册_全本_任务适配精校版V2.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "华东师范大学347｜心理测量保命手册",
        ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_逐章分页精校版V9.docx",
    ),
)


if __name__ == "__main__":
    base.main()
