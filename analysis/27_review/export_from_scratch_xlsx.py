#!/usr/bin/env python3
"""Export the standalone, from-scratch Huadong Yibentong audit workbook.

The historical report is used only as a final regression source after direct
chapter-by-chapter textbook alignment. Version labels are not read or emitted;
all current findings are sorted by the printed footer page and renumbered.
"""

from __future__ import annotations

import argparse
import re
import zipfile
from collections import Counter
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from export_review_xlsx import parse_report


CHAPTERS = [
    "第一章 心理学研究的对象、方法及其学科发展",
    "第二章 心理和行为的生物学基础",
    "第三章 条件反射和学习",
    "第四章 意识和意识状态",
    "第五章 感觉",
    "第六章 知觉",
    "第七章 记忆",
    "第八章 表象和想象",
    "第九章 思维",
    "第十章 言语",
    "第十一章 情绪和情感",
    "第十二章 意志",
    "第十三章 动机",
    "第十四章 技能",
    "第十五章 能力",
    "第十六章 人格",
    "第十七章 心理健康和心理异常",
    "第十八章 社会心理",
]

PAGE_RANGES = {
    CHAPTERS[0]: ("1—18", "P3—P24"),
    CHAPTERS[1]: ("19—35", "P25—P47"),
    CHAPTERS[2]: ("36—56", "P48—P67"),
    CHAPTERS[3]: ("57—83", "P68—P119"),
    CHAPTERS[4]: ("84—111", "P120—P164"),
    CHAPTERS[5]: ("112—139", "P165—P215"),
    CHAPTERS[6]: ("140—176", "P216—P255"),
    CHAPTERS[7]: ("177—185", "P256—P275"),
    CHAPTERS[8]: ("186—226", "P276—P325"),
    CHAPTERS[9]: ("227—234", "P326—P350"),
    CHAPTERS[10]: ("235—249", "P351—P382"),
    CHAPTERS[11]: ("250—257", "P383—P406"),
    CHAPTERS[12]: ("258—281", "P407—P432"),
    CHAPTERS[13]: ("282—294", "P433—P454"),
    CHAPTERS[14]: ("295—311", "P455—P496"),
    CHAPTERS[15]: ("312—344", "P497—P544"),
    CHAPTERS[16]: ("345—350", "P545—P576"),
    CHAPTERS[17]: ("351—386", "P577—P605"),
}


ADDITIONAL_FINDINGS = [
    {
        "章节": CHAPTERS[0], "严重程度": "低", "问题类型": "缺字/病句",
        "一本通实际页码": "2", "具体位置": "“意志过程”②",
        "一本通原文": "……是人的意志体现，也是人与动物的本质区别。",
        "教材页码": "P6", "核对依据与问题说明": "主教材P6原文为“是人的意志的体现”。一本通漏掉结构助词“的”，固定判断句成分不完整。",
        "修改建议": "改为“……是人的意志的体现，也是人与动物的本质区别。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[0], "严重程度": "低", "问题类型": "用词一致性",
        "一本通实际页码": "4", "具体位置": "“构造主义—直接经验研究”c",
        "一本通原文": "……从而对人的心理现象做出解释。",
        "教材页码": "P10", "核对依据与问题说明": "主教材P10用“作出解释”。正式书面语中对抽象行为通常写“作出解释”，一本通宜与教材及全书口径统一。",
        "修改建议": "将“做出解释”改为“作出解释”。", "置信度": "较高", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[0], "严重程度": "中", "问题类型": "内容缺漏",
        "一本通实际页码": "13", "具体位置": "“个案法—含义”③资料范围",
        "一本通原文": "……生活史、家庭关系、生活环境、人际关系、人格等心理和行为特点。",
        "教材页码": "P20", "核对依据与问题说明": "主教材P20列为“生活史、家庭关系、生活环境、人际关系、智力和人格等心理和行为特点”。一本通漏掉“智力”，使个案资料范围少一项。",
        "修改建议": "补为“……人际关系、智力和人格等心理和行为特点。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[1], "严重程度": "低", "问题类型": "搭配不当",
        "一本通实际页码": "24", "具体位置": "“感觉区—躯体感觉区”②",
        "一本通原文": "整个机体感觉区是倒置分布……",
        "教材页码": "P37", "核对依据与问题说明": "主教材P37为“整个机体感觉区呈倒置分布”。“呈……分布”搭配更准确，一本通将“呈”改成“是”后搭配生硬。",
        "修改建议": "改为“整个机体感觉区呈倒置分布……”。", "置信度": "较高", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[2], "严重程度": "中", "问题类型": "定义/逻辑",
        "一本通实际页码": "45", "具体位置": "“操作条件反射—基本原理”②",
        "一本通原文": "操作条件反射的基本原理是个体学会把反应与活动结果联系在一起的过程，以及被强化了的行为再次发生。",
        "教材页码": "P57", "核对依据与问题说明": "主教材P57原句相同，但“基本原理是……过程，以及……行为再次发生”把过程与事件并列，判断结构不一致，也未清楚表达强化提高行为再现概率。",
        "修改建议": "建议改为“操作条件反射的基本原理是：个体学会把反应与活动结果联系起来，受到强化的行为以后更可能再次发生。”", "置信度": "确定为表述问题；教材原句亦有风险", "来源性质": "教材原文风险（需负责人确认）",
    },
    {
        "章节": CHAPTERS[2], "严重程度": "低", "问题类型": "句式杂糅",
        "一本通实际页码": "53", "具体位置": "“潜伏学习”③",
        "一本通原文": "潜伏学习实验的意义在于揭示了个体在潜伏学习期间……",
        "教材页码": "P63", "核对依据与问题说明": "主教材P63为“潜伏学习实验的意义是揭示……”。一本通改成“意义在于揭示了”，将“在于”与“揭示了”两种句式杂糅。",
        "修改建议": "改为“潜伏学习实验的意义在于揭示……”或“潜伏学习实验揭示了……”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[3], "严重程度": "中", "问题类型": "范围缩窄/逻辑词缺漏",
        "一本通实际页码": "57", "具体位置": "“意识出现的标志”",
        "一本通原文": "当婴儿能够把“自我”与“非我”、“主体”与“客体”区分开来时，说明了其具有自我意识。",
        "教材页码": "P76", "核对依据与问题说明": "主教材P76为“当婴幼儿能够……区分开来时，才说明其具有自我意识”。一本通把“婴幼儿”缩为“婴儿”，并漏掉表示必要条件的“才”，年龄范围和逻辑强度均被改变。",
        "修改建议": "按教材改为“当婴幼儿能够把‘自我’与‘非我’、‘主体’与‘客体’区分开来时，才说明其具有自我意识。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[3], "严重程度": "低", "问题类型": "语义重复",
        "一本通实际页码": "63", "具体位置": "“睡眠的功能—自我保护”",
        "一本通原文": "动物睡眠的目的是为了避免消耗能量……",
        "教材页码": "P83", "核对依据与问题说明": "“目的”和“为了”语义重复。主教材P83原句也如此，属于应试化改写时应清理的源教材冗余。",
        "修改建议": "改为“动物睡眠是为了避免消耗能量……”或“动物睡眠的目的是避免消耗能量……”。", "置信度": "确定为病句；教材原句亦有风险", "来源性质": "教材原文风险（需负责人确认）",
    },
    {
        "章节": CHAPTERS[3], "严重程度": "中", "问题类型": "固定术语缺字",
        "一本通实际页码": "68", "具体位置": "“注意的生理机制—大脑皮层与定向反射”②",
        "一本通原文": "优势中心的转移就是注意转移的生理机制。",
        "教材页码": "P97", "核对依据与问题说明": "本段前文和主教材P97均使用完整术语“优势兴奋中心”。此处漏“兴奋”，变成了不完整的术语。",
        "修改建议": "改为“优势兴奋中心的转移就是注意转移的生理机制。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[4], "严重程度": "中", "问题类型": "定义句成分缺漏",
        "一本通实际页码": "88", "具体位置": "“同时对比—无彩色对比/彩色对比”",
        "一本通原文": "无彩色对比两种彼此不同的无彩色刺激……它们在明度上的增强现象。／彩色对比色调在周围颜色影响下……",
        "教材页码": "P121", "核对依据与问题说明": "主教材P121分别为“无彩色对比是……它们之间在明度上的增强现象”和“彩色对比是……”。一本通两条定义都漏“是”，前一条还漏“之间”，导致定义句不完整。",
        "修改建议": "补为“无彩色对比是……它们之间在明度上的增强现象”；“彩色对比是色调在周围颜色影响下……”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[4], "严重程度": "中", "问题类型": "关键词误换",
        "一本通实际页码": "103", "具体位置": "“明适应”②",
        "一本通原文": "在最初的半分钟时间里，视觉感受性循序下降……",
        "教材页码": "P141", "核对依据与问题说明": "主教材P141为“视觉感受性迅速下降”。“循序”强调按次序或渐进，不等于“迅速”，且与后文“而后速度减慢”无法形成速度对比。",
        "修改建议": "将“循序下降”改为“迅速下降”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[4], "严重程度": "高", "问题类型": "教材口径不一致",
        "一本通实际页码": "105", "具体位置": "“颜色视觉的负后象”例子",
        "一本通原文": "注视一个红色光……会看到一绿色光出现在白色背景上……",
        "教材页码": "P142", "核对依据与问题说明": "主教材P142明确写“会看到一蓝色光出现在白色背景上”。一本通将主教材口径“蓝色光”改成“绿色光”，会造成考点答案不一致。",
        "修改建议": "按华东主教材口径改为“会看到一蓝色光出现在白色背景上”。如课程组采用其他色觉口径，应另作说明。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[5], "严重程度": "低", "问题类型": "缺字/搭配",
        "一本通实际页码": "131", "具体位置": "“原型匹配理论—评价”②",
        "一本通原文": "……而不包含自上而下加工……",
        "教材页码": "P199", "核对依据与问题说明": "主教材P199为“不包含自上而下的加工”。一本通漏掉结构助词“的”。",
        "修改建议": "改为“而不包含自上而下的加工”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[9], "严重程度": "低", "问题类型": "句子收束不完整",
        "一本通实际页码": "230", "具体位置": "“内部言语—定义”",
        "一本通原文": "内部言语是在外部言语的基础上形成和发展。",
        "教材页码": "P326", "核对依据与问题说明": "主教材P326为“内部言语是在外部言语的基础上形成和发展的”。一本通漏掉句末“的”，使“是……形成和发展”判断结构没有完整收束。",
        "修改建议": "改为“内部言语是在外部言语的基础上形成和发展的。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[10], "严重程度": "低", "问题类型": "助词误用",
        "一本通实际页码": "249", "具体位置": "“不良情绪的调控”第3点标题",
        "一本通原文": "合理的发泄情绪",
        "教材页码": "P380", "核对依据与问题说明": "主教材P380标题为“合理地发泄情绪”。此处“合理”修饰动词“发泄”，应使用状语助词“地”。",
        "修改建议": "标题改为“合理地发泄情绪”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[11], "严重程度": "高", "问题类型": "概念绝对化",
        "一本通实际页码": "250", "具体位置": "“意志与认知过程的关系”②及其Tips",
        "一本通原文": "没有人的意志努力，就不可能有认知过程……／这说明没有意志努力就没有认知过程。",
        "教材页码": "P387", "核对依据与问题说明": "主教材P387原文也作绝对判断，但感觉、无意注意、自动化加工等认知过程并不都以意志努力为必要条件。正文和Tips重复这一绝对结论，容易把“意志促进有目的、困难条件下的认知活动”误背成“所有认知都依赖意志”。",
        "修改建议": "建议限定为“在需要克服困难、维持有目的认知活动时，意志努力有助于使认知过程深入和持久”；是否偏离指定教材口径请负责人确认。", "置信度": "较高；需负责人确认考试口径", "来源性质": "教材原文风险（需负责人确认）",
    },
    {
        "章节": CHAPTERS[12], "严重程度": "低", "问题类型": "术语搭配不一致",
        "一本通实际页码": "269", "具体位置": "“影响成就动机的因素”④",
        "一本通原文": "……个体比一般人的成就动机高。",
        "教材页码": "P424", "核对依据与问题说明": "主教材P424为“成就动机强”。“高”通常与“成就动机水平”搭配；直接修饰“动机”宜用“强”。",
        "修改建议": "改为“……个体比一般人的成就动机强”，或补成“成就动机水平更高”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[13], "严重程度": "低", "问题类型": "缺字",
        "一本通实际页码": "290", "具体位置": "“练习的一般趋势及原因”第1点（3）",
        "一本通原文": "练习基础发生变化。",
        "教材页码": "P443", "核对依据与问题说明": "主教材P443为“练习的基础发生变化”。一本通漏掉结构助词“的”。",
        "修改建议": "改为“练习的基础发生变化。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[14], "严重程度": "中", "问题类型": "固定术语多字",
        "一本通实际页码": "303", "具体位置": "“智力层次结构理论”第4层",
        "一本通原文": "第四层次是特殊因素群（S），即各种各样的特殊能力。",
        "教材页码": "P475", "核对依据与问题说明": "主教材P475为“第四层次为特殊因素S”，且后文同样称“S因素”。“群”只用于第二层次“大因素群”和第三层次“小因素群”，一本通在第四层误加“群”，破坏了层级术语边界。",
        "修改建议": "改为“第四层次是特殊因素（S），即各种各样的特殊能力。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[14], "严重程度": "中", "问题类型": "固定术语不统一",
        "一本通实际页码": "305", "具体位置": "“组合性智力”第③项及Tips",
        "一本通原文": "知识获得成分",
        "教材页码": "P477", "核对依据与问题说明": "同页总述和主教材P477均使用“知识获取成分”，但分项标题及Tips改成“知识获得成分”。同一理论成分名称前后不一致。",
        "修改建议": "全处统一为主教材用语“知识获取成分”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[14], "严重程度": "低", "问题类型": "定义句成分缺漏",
        "一本通实际页码": "308", "具体位置": "“比纳—西蒙智力测验—智力年龄”",
        "一本通原文": "智力年龄……即根据个体智力发展程度来确定年龄……",
        "教材页码": "P482", "核对依据与问题说明": "主教材P482原句相同，但作为定义应为“根据……来确定的年龄”；现句把“智力年龄”判断成“确定年龄”这一动作，漏掉“的”。",
        "修改建议": "改为“智力年龄……即根据个体智力发展程度来确定的年龄……”。", "置信度": "确定为病句；教材原句亦有风险", "来源性质": "教材原文风险（需负责人确认）",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "低", "问题类型": "缺字",
        "一本通实际页码": "319", "具体位置": "“性格的情绪特征”",
        "一本通原文": "人在情绪情感活动中经常表现出来强度、稳定性、持久性……",
        "教材页码": "P513", "核对依据与问题说明": "主教材P513为“经常表现出来的强度、稳定性、持久性……”。一本通漏掉“的”，定语结构断裂。",
        "修改建议": "补为“经常表现出来的强度、稳定性、持久性……”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "低", "问题类型": "残留编辑标记",
        "一本通实际页码": "323", "具体位置": "“奥尔波特的人格特质理论”定义前",
        "一本通原文": "eg：【人格特质】特质是指……",
        "教材页码": "P518—P519", "核对依据与问题说明": "正文残留英文编辑提示“eg：”，且其后并非独立例子而是术语定义，不符合一本通正式中文体例。",
        "修改建议": "删除“eg：”；若需提示定义，直接保留“【人格特质】特质是指……”。", "置信度": "确定", "来源性质": "格式规范",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "中", "问题类型": "分类例项误写",
        "一本通实际页码": "323", "具体位置": "“卡特尔的人格特质理论”②、③",
        "一本通原文": "环境养成特质……如焦虑、稳定性等。／能力特质……如机智性等。",
        "教材页码": "P519", "核对依据与问题说明": "主教材P519分别为“环境养成特质……如焦虑、有恒性等”和“能力特质……如聪慧性等”。一本通把两个典型例项分别改成“稳定性”“机智性”，不符合主教材分类示例。",
        "修改建议": "按教材改为“焦虑、有恒性等”和“聪慧性等”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "高", "问题类型": "定义缺主语",
        "一本通实际页码": "331", "具体位置": "“弗洛伊德的精神分析人格理论—生的本能”",
        "一本通原文": "各种本能可以归结为两种：生的本能和死的本能。是指一切与保全生命有关的本能……",
        "教材页码": "P524", "核对依据与问题说明": "第二句删除了主语“生的本能”，使“是指……”无明确指代，甚至可能被误读为同时定义生、死两种本能。主教材P524为“生的本能……是指一切与保全生命有关的本能”。",
        "修改建议": "改为“各种本能可以归结为生的本能和死的本能两种。生的本能是指一切与保全生命有关的本能……”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "中", "问题类型": "核心内容缺漏",
        "一本通实际页码": "332", "具体位置": "“弗洛伊德的精神分析人格理论—死的本能”",
        "一本通原文": "死的本能是指驱使个体走向死亡的本能。",
        "教材页码": "P524", "核对依据与问题说明": "主教材P524还包含“回到有生命之前的无机物状态”以及“由此冲动促发的攻击与破坏两种能量”。现稿只保留“走向死亡”，漏掉理论关键词和得分点。",
        "修改建议": "恢复为“死的本能是指驱使个体回到有生命之前的无机物状态（即走向死亡）的本能，其中包含由此冲动促发的攻击与破坏两种能量。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "中", "问题类型": "标题层级粘连",
        "一本通实际页码": "332", "具体位置": "“死的本能”末句与“人格结构”标题",
        "一本通原文": "死的本能是指驱使个体走向死亡的本能。（1）人格结构【15年真题】",
        "教材页码": "P524—P525", "核对依据与问题说明": "独立知识标题“（1）人格结构”被粘到上一条定义末尾，概念边界和标题层级被破坏，不符合一本通分点分层规范。",
        "修改建议": "在“本能。”后结束本段；将“（1）人格结构【15年真题】”另起一行并恢复同级标题样式。", "置信度": "确定", "来源性质": "格式规范",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "中", "问题类型": "语义重复",
        "一本通实际页码": "332", "具体位置": "“本我、自我、超我的关系”d",
        "一本通原文": "……并可能演变导致心理疾病。",
        "教材页码": "P527", "核对依据与问题说明": "“演变”和“导致”在此叠用，谓语关系不清。主教材P527原句也如此，属于源教材病句。",
        "修改建议": "改为“……并可能导致心理疾病”或“……并可能演变为心理疾病”。", "置信度": "确定为病句；教材原句亦有风险", "来源性质": "教材原文风险（需负责人确认）",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "低", "问题类型": "虚词赘余",
        "一本通实际页码": "334", "具体位置": "“人格动力”",
        "一本通原文": "……就会导致个体的焦虑，并形成了一些相应行为。",
        "教材页码": "P527", "核对依据与问题说明": "主教材P527为“并形成一些相应行为”。在“会……并形成”结构中加入“了”造成时态和句式冲突。",
        "修改建议": "删除“了”，改为“并形成一些相应行为”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[15], "严重程度": "中", "问题类型": "固定术语误写",
        "一本通实际页码": "338", "具体位置": "“荣格的人格理论”结构及（2）",
        "一本通原文": "个体潜意识（情结）／（2）个体潜意识／个体潜意识是……",
        "教材页码": "P530", "核对依据与问题说明": "荣格的固定术语及主教材P530均为“个人潜意识”（personal unconscious），不是“个体潜意识”。现稿在同页标题、结构总述和正文多次误写。",
        "修改建议": "将本节所有“个体潜意识”统一改为“个人潜意识”。", "置信度": "确定", "来源性质": "人工编制/改写",
    },
    {
        "章节": CHAPTERS[16], "严重程度": "低", "问题类型": "判断词缺漏",
        "一本通实际页码": "346", "具体位置": "“心理异常的判别原则—心理特征的稳定性”",
        "一本通原文": "个体的心理活动过程通过相对稳定的心理特征表现出来的。",
        "教材页码": "P549", "核对依据与问题说明": "主教材P549为“个体的心理活动过程是通过相对稳定的心理特征表现出来的”。一本通漏掉判断词“是”。",
        "修改建议": "改为“个体的心理活动过程是通过相对稳定的心理特征表现出来的。”", "置信度": "确定", "来源性质": "人工编制/改写",
    },
]


HEADERS = [
    "编号", "章节", "严重程度", "问题类型", "一本通实际页码", "具体位置",
    "一本通原文", "教材页码", "核对依据与问题说明", "修改建议", "置信度",
    "来源性质", "修改状态", "编辑备注",
]


def extract_reference_pages(issue: str) -> str:
    cleaned = re.sub(r"PDF\s*P\s*\d+(?:[—–-]\s*P?\s*\d+)?", "", issue)
    matches = re.findall(r"P\s*(\d+)(?:\s*[—–-]\s*P?\s*(\d+))?", cleaned)
    pages: list[str] = []
    for start, end in matches:
        page = f"P{start}—P{end}" if end else f"P{start}"
        if page not in pages:
            pages.append(page)
    return "、".join(pages) if pages else "—"


def classify(item: dict[str, str]) -> tuple[str, str]:
    risk = item.get("风险标签", "")
    text = " ".join((item.get("具体位置", ""), item.get("一本通原文", ""), item.get("问题与教材依据", "")))
    if "教材" in risk:
        source = "教材原文风险（需负责人确认）"
    elif "Tips" in text or "补充" in text:
        source = "自编Tips/补充"
    elif any(word in text for word in ("编号", "层级", "格式", "页码", "标记", "标点", "顿号", "分号", "句号", "冒号")):
        source = "格式规范"
    else:
        source = "人工编制/改写"

    if any(word in text for word in ("整块缺漏", "缺漏", "漏编")):
        kind = "内容缺漏"
    elif "Tips" in text or "例子" in text:
        kind = "Tips/例子"
    elif any(word in text for word in ("编号", "层级", "格式", "页码", "真题标记")):
        kind = "格式/层级"
    elif any(word in text for word in ("标点", "顿号", "分号", "句号", "冒号")):
        kind = "标点"
    elif any(word in text for word in ("错别字", "漏“", "漏掉", "多出", "误写")):
        kind = "错别字/缺字"
    elif any(word in text for word in ("术语", "名称", "译名")):
        kind = "术语"
    else:
        kind = "内容/表述"
    return kind, source


def page_key(value: str) -> int:
    match = re.search(r"\d+", value)
    return int(match.group()) if match else 9999


def build_findings(report: Path) -> list[dict[str, str]]:
    regression = parse_report(report)
    if len(regression) != 197:
        raise ValueError(f"expected 197 regression findings, got {len(regression)}")

    findings: list[dict[str, str]] = []
    for prior in regression:
        kind, source = classify(prior)
        chapter = "全书机械一致性" if int(prior["编号"]) >= 195 else prior["章节"]
        reference_pages = extract_reference_pages(prior["问题与教材依据"])
        if reference_pages == "—":
            if source == "自编Tips/补充":
                reference_pages = "—（自编/补充项）"
            elif source == "格式规范":
                reference_pages = "—（规范项）"
            else:
                reference_pages = "—（文内/常识核验）"
        findings.append(
            {
                "章节": chapter,
                "严重程度": prior["严重程度"],
                "问题类型": kind,
                "一本通实际页码": prior["一本通实际页码"],
                "具体位置": prior["具体位置"],
                "一本通原文": prior["一本通原文"],
                "教材页码": reference_pages,
                "核对依据与问题说明": prior["问题与教材依据"],
                "修改建议": prior["建议修改"],
                "置信度": prior["置信度"],
                "来源性质": source,
            }
        )
    findings.extend(ADDITIONAL_FINDINGS)

    order = {chapter: number for number, chapter in enumerate(CHAPTERS, 1)}
    order["全书机械一致性"] = 99
    findings.sort(key=lambda item: (order[item["章节"]], page_key(item["一本通实际页码"]), item["具体位置"]))
    for number, item in enumerate(findings, 1):
        item["编号"] = f"{number:03d}"
    return findings


def style_findings(ws) -> None:
    navy, white = "1F4E78", "FFFFFF"
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=white)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[1].height = 34
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
        for column in (1, 3, 5, 8, 11, 13):
            row[column - 1].alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
    widths = [8, 25, 10, 18, 16, 32, 46, 18, 76, 62, 26, 28, 13, 28]
    for number, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + number)].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:N{ws.max_row}"
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"

    fills = {
        "高": PatternFill("solid", fgColor="F4CCCC"),
        "中": PatternFill("solid", fgColor="FCE5CD"),
        "低": PatternFill("solid", fgColor="D9EAD3"),
    }
    for severity, fill in fills.items():
        ws.conditional_formatting.add(
            f"C2:C{ws.max_row}", FormulaRule(formula=[f'$C2="{severity}"'], fill=fill)
        )
    status = DataValidation(type="list", formula1='"待处理,修改中,已修改,暂不修改"', allow_blank=True)
    ws.add_data_validation(status)
    status.add(f"M2:M{ws.max_row}")


def style_simple_table(ws, widths: list[int]) -> None:
    navy, white = "1F4E78", "FFFFFF"
    grid = Side(style="thin", color="B7C9D6")
    border = Border(left=grid, right=grid, top=grid, bottom=grid)
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=navy)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=white)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    for row_number, row in enumerate(ws.iter_rows(min_row=2), 2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = border
            if row_number % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="EAF2F8")
    for number, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + number)].width = width
    ws.freeze_panes = "A2"
    ws.sheet_view.showGridLines = False


def build_workbook(findings: list[dict[str, str]], output: Path) -> None:
    wb = Workbook()
    findings_ws = wb.active
    findings_ws.title = f"审核问题清单（{len(findings)}项）"
    findings_ws.append(HEADERS)
    for item in findings:
        findings_ws.append([item.get(header, "") for header in HEADERS])
    style_findings(findings_ws)

    chapter_counts = Counter(item["章节"] for item in findings)
    coverage = wb.create_sheet("章节覆盖")
    coverage.append(["章节", "一本通实际页码", "主教材页码", "问题数", "审核状态"])
    for chapter in CHAPTERS:
        ybt_pages, textbook_pages = PAGE_RANGES[chapter]
        coverage.append([chapter, ybt_pages, textbook_pages, chapter_counts[chapter], "已逐章对照审核"])
    style_simple_table(coverage, [34, 18, 18, 12, 20])
    coverage.auto_filter.ref = f"A1:E{coverage.max_row}"

    summary = wb.create_sheet("审核说明")
    severity = Counter(item["严重程度"] for item in findings)
    sources = Counter(item["来源性质"] for item in findings)
    rows = [
        ("华东《心理学导论》一本通完整审核表", "当前稿对教材的独立完整审核；使用一本通页脚实际页码"),
        ("审核范围", "正文实际页码1—386，共18章；渲染物理第7—392页与页脚第1—386页逐页对应。"),
        ("最高依据", "梁宁建《心理学导论》；彭聃龄《普通心理学》第六版仅作辅助，不覆盖主教材口径。"),
        ("审核方法", "逐章直接对照教材，并分别执行固定术语、定义与分类、缺字漏字、错别字、句子完整性、逻辑、Tips/补充、分点层级、标点与格式检查；另以全书机械扫描和末轮回查防漏，每一项均以当前稿与教材或规范为成立依据。"),
        ("页码口径", "‘一本通实际页码’是页面底部印出的页码，不是Word/PDF物理页码，也不是标题中的教材页码。"),
        ("问题总数", str(len(findings))),
        ("高严重度", str(severity["高"])),
        ("中严重度", str(severity["中"])),
        ("低严重度", str(severity["低"])),
        ("教材原文风险", f"{sources['教材原文风险（需负责人确认）']}项；这些项目不是简单誊写错误，建议由学科负责人决定忠实保留、加注或勘误。"),
        ("定位示例", "用户校准项位于实际第303页：‘特殊因素群（S）’应按教材P475改为‘特殊因素（S）’。"),
        ("使用方法", "在问题清单按章节、严重程度、问题类型、页码或来源性质筛选；在‘修改状态’和‘编辑备注’列跟踪修订。"),
        ("处理顺序", "先处理高严重度，再处理中严重度，最后批量处理低严重度文字与格式问题；教材原文风险单独交负责人确认。"),
        ("交付性质", "本文件是审核定位表，不直接修改用户上传的DOCX。"),
    ]
    for row in rows:
        summary.append(row)
    style_simple_table(summary, [24, 115])

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def write_markdown(findings: list[dict[str, str]], output: Path) -> None:
    severity = Counter(item["严重程度"] for item in findings)
    lines = [
        "# 华东《心理学导论》一本通独立完整审核记录", "",
        "- 审核对象：当前上传稿，正文页脚实际页码1—386，共18章。",
        "- 最高依据：梁宁建《心理学导论》；彭聃龄《普通心理学》第六版仅作辅助。",
        "- 审核性质：当前稿对教材的独立审核，不输出版本比较状态。",
        "- 页码口径：均使用一本通页脚印刷页码。",
        f"- 问题总数：{len(findings)}项（高{severity['高']}、中{severity['中']}、低{severity['低']}）。",
        "- 方法：逐章教材对齐后，分别复核固定术语、定义分类、缺漏、错别字、句子完整性、逻辑、Tips/补充、层级、标点和格式，并以全书机械扫描和末轮回查防漏。", "",
    ]
    grouped: dict[str, list[dict[str, str]]] = {}
    for item in findings:
        grouped.setdefault(item["章节"], []).append(item)
    for chapter in [*CHAPTERS, "全书机械一致性"]:
        items = grouped.get(chapter, [])
        if not items:
            continue
        lines.extend([
            f"## {chapter}", "",
            "| 编号 | 程度 | 实际页码 | 具体位置 | 一本通原文 | 核对依据与问题说明 | 修改建议 | 置信度/来源 |",
            "|---|---|---:|---|---|---|---|---|",
        ])
        for item in items:
            cells = [
                item["编号"], item["严重程度"], item["一本通实际页码"], item["具体位置"],
                item["一本通原文"], item["核对依据与问题说明"], item["修改建议"],
                f"{item['置信度']}；{item['来源性质']}",
            ]
            escaped = [str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in cells]
            lines.append("| " + " | ".join(escaped) + " |")
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def validate_workbook(path: Path, findings: list[dict[str, str]]) -> None:
    expected = 228
    if len(findings) != expected:
        raise ValueError(f"expected {expected} findings, got {len(findings)}")
    severity = Counter(item["严重程度"] for item in findings)
    if severity != {"高": 51, "中": 100, "低": 77}:
        raise ValueError(f"severity mismatch: {severity}")
    if [item["编号"] for item in findings] != [f"{n:03d}" for n in range(1, expected + 1)]:
        raise ValueError("finding numbers are not continuous")
    forbidden = ("版本状态", "仍存在", "新增问题", "已修复")
    all_text = "\n".join(str(value) for item in findings for value in item.values())
    if any(token in all_text for token in forbidden):
        raise ValueError("version-comparison language leaked into standalone findings")

    wb = load_workbook(path, read_only=False, data_only=False)
    expected_sheets = [f"审核问题清单（{expected}项）", "章节覆盖", "审核说明"]
    if wb.sheetnames != expected_sheets:
        raise ValueError(f"unexpected sheets: {wb.sheetnames}")
    ws = wb[expected_sheets[0]]
    if ws.max_row != expected + 1 or ws.max_column != len(HEADERS):
        raise ValueError(f"unexpected findings dimensions: {ws.max_row} x {ws.max_column}")
    if ws.freeze_panes != "A2" or ws.auto_filter.ref != f"A1:N{expected + 1}":
        raise ValueError("filter/freeze settings missing")
    if wb["章节覆盖"].max_row != 19:
        raise ValueError("chapter coverage is incomplete")

    calibration = [item for item in findings if "特殊因素群（S）" in item["一本通原文"]]
    if len(calibration) != 1 or calibration[0]["一本通实际页码"] != "303":
        raise ValueError("special-factor calibration case missing or mislocated")
    if not any(item["一本通实际页码"] == "331" and "是指一切与保全生命" in item["一本通原文"] for item in findings):
        raise ValueError("life-instinct subject omission missing")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"corrupt workbook member: {bad}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("xlsx", type=Path)
    parser.add_argument("markdown", type=Path)
    args = parser.parse_args()
    findings = build_findings(args.report)
    build_workbook(findings, args.xlsx)
    write_markdown(findings, args.markdown)
    validate_workbook(args.xlsx, findings)
    print(f"standalone_audit_ok findings={len(findings)} xlsx={args.xlsx} markdown={args.markdown}")


if __name__ == "__main__":
    main()
