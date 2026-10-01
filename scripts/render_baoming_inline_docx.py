from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from render_baoming_docx import (
    BLACK,
    LIGHT_GRAY_FILL,
    add_cover,
    add_heading,
    add_table,
    configure_body_header_footer,
    configure_page,
    configure_styles,
    markdown_tokens,
    set_paragraph_border,
    set_run_font,
    set_update_fields,
    shade_paragraph,
)
from render_baoming_mother_docx import COMPACT_UNIT_PREFIXES


TAG_GRAY = RGBColor(89, 89, 89)
OPTIONAL_GRAY = RGBColor(96, 96, 96)
BODY_TEXT_SIZE = 12
DEFINITION_TAG_RE = re.compile(r"【名词解释：[^】]+】")
INLINE_EXPANSION_RE = re.compile(r"【扩容（选(?:用|背)）：.*?】")
BARE_EXPANSION_RE = re.compile(r"【(?!(?:名词解释：[^】]+|简答|论述|★{1,3})】).*?】")
ACTIVE_BARE_EXPANSION_RE = BARE_EXPANSION_RE
INLINE_COMPACT_UNIT_PREFIXES = COMPACT_UNIT_PREFIXES + (
    "十三、心理学的主要分支",
    "四、影响信度系数的因素",
    "五、测量的标准误差",
    "六、概化理论",
)

# LibreOffice does not consistently honor keep-with-next when a task-module
# heading is followed by a long, keep-together child paragraph. These V7
# pagination locks are derived from the first compact-layout PDF pass and keep
# the module heading from becoming the last line of a page.
MEASUREMENT_V7_PAGE_BREAK_MODULES = {
    "1. 两类测验的基本含义如下：",
    "3. 人格评定量表的编制使用要求包括：",
    "3. 各种信度估计方法的主要区别如下：",
    "2. 项目难度的分布特点和选择要求如下：",
}

MEASUREMENT_V7_PAGE_BREAK_BODY = {
    "难度、项目间相关和鉴别力既相互联系，也会使信度与预测效度出现需要平衡的关系。",
}
MEASUREMENT_V8_PAGE_BREAK_MODULES = {
    "1. 投射测验的理论原理主要包括：",
}
MEASUREMENT_V8_PAGE_BREAK_BODY: set[str] = set()
MEASUREMENT_V9_PAGE_BREAK_MODULES = {
    "1. 人格自陈量表常见的反应偏差包括：",
    "3. 两类测验的主要区别如下：",
    "3. 概化理论的研究阶段和基本设计如下：",
    "1. 效标效度验证涉及的基本概念和类型包括：",
    "1. 项目鉴别力的主要估计方法及解释标准如下：",
    "3. 常模与标准的区别如下：",
    "1. 发展量表的主要优点包括：",
    "2. 组内常模的应用实例及解释限制如下：",
}
MEASUREMENT_V9_PAGE_BREAK_BODY: set[str] = set()
EXPERIMENT_V2_PAGE_BREAK_MODULES = {
    "1. 韦伯定律的主要内容包括：",
    "2. 无觉察知觉的实验逻辑与控制要求包括：",
}
EXPERIMENT_V2_PAGE_BREAK_BODY: set[str] = set()
ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES = MEASUREMENT_V7_PAGE_BREAK_MODULES
ACTIVE_MEASUREMENT_PAGE_BREAK_BODY = MEASUREMENT_V7_PAGE_BREAK_BODY

CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 2,
    "五、格式塔心理学": 3,
    "六、精神分析学派": 3,
    "七、人本主义心理学": 4,
    "八、认知心理学": 4,
    "九、观察法、相关研究法与实验法": 5,
    "十、实验变量": 6,
    "十一、测验法与信效度": 6,
    "十二、投射法与投射测验": 7,
    "十三、心理学的主要分支": 7,
    "第二章 心理和行为的生物学基础": 8,
    "一、神经元": 8,
    "二、神经冲动与突触传递": 8,
    "三、神经系统的构成与功能": 9,
    "四、大脑皮层的感觉区与运动区": 10,
    "五、大脑皮层的言语区与联合区": 10,
    "六、大脑两半球的功能分工": 11,
    "七、丘脑与下丘脑": 11,
    "八、边缘系统、海马与杏仁核": 12,
    "九、脑功能的主要学说": 12,
    "第三章 条件反射和学习": 14,
    "一、学习的含义与特征": 14,
    "二、反射、反射弧与反射类型": 14,
    "三、经典条件反射": 15,
    "四、经典条件反射的基本规律": 15,
    "五、信号系统与高级神经活动": 16,
    "六、操作条件反射与行为调控": 17,
    "七、经典条件反射与操作条件反射的比较": 17,
    "八、顿悟学习": 18,
    "九、目的行为学习理论": 19,
    "十、观察学习": 19,
    "十一、格雷的强化敏感性理论": 20,
}

V3_CATALOG_OVERRIDES = {
    "七、经典条件反射与操作条件反射的比较": 18,
}

V6_CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 2,
    "五、格式塔心理学": 2,
    "六、精神分析学派": 3,
    "七、人本主义心理学": 3,
    "八、认知心理学": 4,
    "九、观察法、相关研究法与实验法": 4,
    "十、实验变量": 5,
    "十一、测验法与信效度": 5,
    "十二、投射法与投射测验": 6,
    "十三、心理学的主要分支": 6,
    "第二章 心理和行为的生物学基础": 7,
    "一、神经元": 7,
    "二、神经冲动与突触传递": 7,
    "三、神经系统的构成与功能": 8,
    "四、大脑皮层的感觉区与运动区": 8,
    "五、大脑皮层的言语区与联合区": 9,
    "六、大脑两半球的功能分工": 9,
    "七、丘脑与下丘脑": 10,
    "八、边缘系统、海马与杏仁核": 10,
    "九、脑功能的主要学说": 11,
    "第三章 条件反射和学习": 12,
    "一、学习的含义与特征": 12,
    "二、反射、反射弧与反射类型": 12,
    "三、经典条件反射": 13,
    "四、经典条件反射的基本规律": 13,
    "五、信号系统与高级神经活动": 14,
    "六、操作条件反射与行为调控": 14,
    "七、经典条件反射与操作条件反射的比较": 15,
    "八、顿悟学习": 15,
    "九、目的行为学习理论": 16,
    "十、观察学习": 16,
    "十一、格雷的强化敏感性理论": 17,
}

# The verified V7 body pagination is unchanged from V6: 17 body pages after
# the cover and catalog.
V7_CATALOG_PAGE_MAP = V6_CATALOG_PAGE_MAP.copy()

V8_CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 2,
    "五、格式塔心理学": 3,
    "六、精神分析学派": 3,
    "七、人本主义心理学": 4,
    "八、认知心理学": 4,
    "九、观察法、相关研究法与实验法": 4,
    "十、实验变量": 5,
    "十一、测验法与信效度": 6,
    "十二、投射法与投射测验": 6,
    "十三、心理学的主要分支": 7,
    "第二章 心理和行为的生物学基础": 8,
    "一、神经元": 8,
    "二、神经冲动与突触传递": 8,
    "三、神经系统的构成与功能": 9,
    "四、大脑皮层的感觉区与运动区": 10,
    "五、大脑皮层的言语区与联合区": 10,
    "六、大脑两半球的功能分工": 11,
    "七、丘脑与下丘脑": 11,
    "八、边缘系统、海马与杏仁核": 12,
    "九、脑功能的主要学说": 12,
    "第三章 条件反射和学习": 14,
    "一、学习的含义与特征": 14,
    "二、反射、反射弧与反射类型": 14,
    "三、经典条件反射": 15,
    "四、经典条件反射的基本规律": 15,
    "五、信号系统与高级神经活动": 16,
    "六、操作条件反射与行为调控": 17,
    "七、经典条件反射与操作条件反射的比较": 18,
    "八、顿悟学习": 19,
    "九、目的行为学习理论": 19,
    "十、观察学习": 20,
    "十一、格雷的强化敏感性理论": 21,
}

# Replaced with the verified V9 body pagination after the first render.
V9_CATALOG_PAGE_MAP = V8_CATALOG_PAGE_MAP.copy()

V10_CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 2,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 3,
    "五、格式塔心理学": 3,
    "六、精神分析学派": 3,
    "七、人本主义心理学": 4,
    "八、认知心理学": 5,
    "九、观察法、相关研究法与实验法": 5,
    "十、实验变量": 6,
    "十一、测验法与信效度": 6,
    "十二、投射法与投射测验": 7,
    "十三、心理学的主要分支": 7,
    "第二章 心理和行为的生物学基础": 9,
    "一、神经元": 9,
    "二、神经冲动与突触传递": 9,
    "三、神经系统的构成与功能": 10,
    "四、大脑皮层的感觉区与运动区": 11,
    "五、大脑皮层的言语区与联合区": 11,
    "六、大脑两半球的功能分工": 12,
    "七、丘脑与下丘脑": 12,
    "八、边缘系统、海马与杏仁核": 13,
    "九、脑功能的主要学说": 14,
    "第三章 条件反射和学习": 15,
    "一、学习的含义与特征": 15,
    "二、反射、反射弧与反射类型": 15,
    "三、经典条件反射": 16,
    "四、经典条件反射的基本规律": 16,
    "五、信号系统与高级神经活动": 17,
    "六、操作条件反射与行为调控": 18,
    "七、经典条件反射与操作条件反射的比较": 19,
    "八、顿悟学习": 20,
    "九、目的行为学习理论": 20,
    "十、观察学习": 21,
    "十一、格雷的强化敏感性理论": 22,
}

# V11实际PDF为22页正文；斜体字形使“脑功能的主要学说”前移一页。
V11_CATALOG_PAGE_MAP = V10_CATALOG_PAGE_MAP | {"九、脑功能的主要学说": 13}

V12_CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 2,
    "五、格式塔心理学": 2,
    "六、精神分析学派": 3,
    "七、人本主义心理学": 4,
    "八、认知心理学": 4,
    "九、观察法、相关研究法与实验法": 4,
    "十、实验变量": 5,
    "十一、测验法与信效度": 5,
    "十二、投射法与投射测验": 6,
    "十三、心理学的主要分支": 6,
    "第二章 心理和行为的生物学基础": 8,
    "一、神经元": 8,
    "二、神经冲动与突触传递": 8,
    "三、神经系统的构成与功能": 9,
    "四、大脑皮层的感觉区与运动区": 9,
    "五、大脑皮层的言语区与联合区": 10,
    "六、大脑两半球的功能分工": 10,
    "七、丘脑与下丘脑": 11,
    "八、边缘系统、海马与杏仁核": 11,
    "九、脑功能的主要学说": 12,
    "第三章 条件反射和学习": 13,
    "一、学习的含义与特征": 13,
    "二、反射、反射弧与反射类型": 13,
    "三、经典条件反射": 14,
    "四、经典条件反射的基本规律": 14,
    "五、信号系统与高级神经活动": 15,
    "六、操作条件反射与行为调控": 15,
    "七、经典条件反射与操作条件反射的比较": 16,
    "八、顿悟学习": 17,
    "九、目的行为学习理论": 17,
    "十、观察学习": 18,
    "十一、格雷的强化敏感性理论": 19,
}

# V13经PDF正文逐页复核，仅“人本主义心理学”因扩容分行前移一页。
V13_CATALOG_PAGE_MAP = V12_CATALOG_PAGE_MAP | {"七、人本主义心理学": 3}

# V14经PDF正文逐页复核，共20个正文起始页（末题续至正文第21页）。
V14_CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 1,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 2,
    "五、格式塔心理学": 3,
    "六、精神分析学派": 3,
    "七、人本主义心理学": 4,
    "八、认知心理学": 4,
    "九、观察法、相关研究法与实验法": 4,
    "十、实验变量": 5,
    "十一、测验法与信效度": 6,
    "十二、投射法与投射测验": 6,
    "十三、心理学的主要分支": 7,
    "第二章 心理和行为的生物学基础": 8,
    "一、神经元": 8,
    "二、神经冲动与突触传递": 8,
    "三、神经系统的构成与功能": 9,
    "四、大脑皮层的感觉区与运动区": 10,
    "五、大脑皮层的言语区与联合区": 10,
    "六、大脑两半球的功能分工": 11,
    "七、丘脑与下丘脑": 11,
    "八、边缘系统、海马与杏仁核": 11,
    "九、脑功能的主要学说": 12,
    "第三章 条件反射和学习": 14,
    "一、学习的含义与特征": 14,
    "二、反射、反射弧与反射类型": 14,
    "三、经典条件反射": 15,
    "四、经典条件反射的基本规律": 15,
    "五、信号系统与高级神经活动": 16,
    "六、操作条件反射与行为调控": 16,
    "七、经典条件反射与操作条件反射的比较": 17,
    "八、顿悟学习": 18,
    "九、目的行为学习理论": 18,
    "十、观察学习": 19,
    "十一、格雷的强化敏感性理论": 20,
}

# V15经首轮PDF正文逐页校准，共28页正文。
V15_CATALOG_PAGE_MAP = {
    "第一章 心理学研究的对象、方法及其学科发展": 1,
    "一、心理学的含义与研究对象": 1,
    "二、科学心理学的诞生": 2,
    "三、构造主义与机能主义": 2,
    "四、行为主义": 3,
    "五、格式塔心理学": 4,
    "六、精神分析学派": 4,
    "七、人本主义心理学": 5,
    "八、认知心理学": 5,
    "九、观察法、相关研究法与实验法": 6,
    "十、实验变量": 7,
    "十一、测验法与信效度": 8,
    "十二、投射法与投射测验": 8,
    "十三、心理学的主要分支": 9,
    "第二章 心理和行为的生物学基础": 10,
    "一、神经元": 10,
    "二、神经冲动与突触传递": 10,
    "三、神经系统的构成与功能": 11,
    "四、大脑皮层的感觉区与运动区": 12,
    "五、大脑皮层的言语区与联合区": 13,
    "六、大脑两半球的功能分工": 14,
    "七、丘脑与下丘脑": 14,
    "八、边缘系统、海马与杏仁核": 15,
    "九、脑功能的主要学说": 16,
    "第三章 条件反射和学习": 18,
    "一、学习的含义与特征": 18,
    "二、反射、反射弧与反射类型": 18,
    "三、经典条件反射": 19,
    "四、经典条件反射的基本规律": 20,
    "五、信号系统与高级神经活动": 21,
    "六、操作条件反射与行为调控": 22,
    "七、经典条件反射与操作条件反射的比较": 23,
    "八、顿悟学习": 25,
    "九、目的行为学习理论": 25,
    "十、观察学习": 26,
    "十一、格雷的强化敏感性理论": 27,
}

# V16删除无可复核来源的格雷单元及三处材料外扩题；首次渲染前沿用
# V15中此前各单元的已核定页码，渲染后再按实际PDF逐页回填。
V16_CATALOG_PAGE_MAP = {
    title: page
    for title, page in V15_CATALOG_PAGE_MAP.items()
    if title != "十一、格雷的强化敏感性理论"
} | {
    "十一、测验法与信效度": 7,
    "十三、心理学的主要分支": 8,
    "六、操作条件反射的强化、惩罚与强化程序": V15_CATALOG_PAGE_MAP[
        "六、操作条件反射与行为调控"
    ]
}
V16_CATALOG_PAGE_MAP.pop("六、操作条件反射与行为调控")


def force_monochrome_title_style(document: Document) -> None:
    """Remove the built-in theme accent from the cover title rule."""
    properties = document.styles["Title"]._element.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is None:
        return
    for edge in borders:
        edge.set(qn("w:color"), "000000")
        edge.attrib.pop(qn("w:themeColor"), None)


def add_inline_runs(
    paragraph,
    content: str,
    size: float = 12,
    optional: bool = False,
    monochrome: bool = False,
    bare_expansions: bool = False,
) -> None:
    def add_expansion_runs(expansion_content: str) -> None:
        prefix_match = re.match(r"【扩容（选(?:用|背)）：", expansion_content)
        round_expansion = expansion_content.startswith("（") and expansion_content.endswith("）")
        expansion_prefix = prefix_match.group(0) if prefix_match else "（" if round_expansion else "【"
        expansion_closing = "）" if round_expansion else "】"
        prefix_run = paragraph.add_run(expansion_prefix)
        set_run_font(
            prefix_run,
            "宋体",
            size if bare_expansions else 9.2 if prefix_match else 10.5,
            True,
        )
        inner = expansion_content[len(expansion_prefix) : -1]
        for text, is_bold, is_underlined, is_italic in markdown_tokens(inner):
            if not text:
                continue
            run = paragraph.add_run(text.replace("—", "\u2060—\u2060"))
            set_run_font(run, "宋体", size if bare_expansions else 10.2, is_bold)
            run.italic = is_italic
            if is_underlined:
                run.underline = True
        closing_run = paragraph.add_run(expansion_closing)
        set_run_font(
            closing_run,
            "宋体",
            size if bare_expansions else 9.2 if prefix_match else 10.5,
            True,
        )

    def add_regular_runs(regular_content: str) -> None:
        for text, is_bold, is_underlined, is_italic in markdown_tokens(regular_content):
            if not text:
                continue
            for part in re.split(r"(【[^】]+】)", text):
                if not part:
                    continue
                if DEFINITION_TAG_RE.fullmatch(part):
                    run = paragraph.add_run(part)
                    set_run_font(run, "宋体", size if bare_expansions else 9.5, True)
                    run.italic = is_italic
                    if not monochrome:
                        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
                elif re.fullmatch(r"【[^】]+】", part):
                    run = paragraph.add_run(part)
                    set_run_font(run, "宋体", size if bare_expansions else 9.5, True)
                    run.italic = is_italic
                    run.font.color.rgb = BLACK if monochrome else TAG_GRAY
                else:
                    run = paragraph.add_run(part.replace("—", "\u2060—\u2060"))
                    set_run_font(
                        run,
                        "宋体",
                        size if bare_expansions else 9.5 if optional else size,
                        is_bold,
                    )
                    run.italic = is_italic
                    if is_underlined:
                        run.underline = True
                    if optional:
                        run.font.color.rgb = BLACK if monochrome else OPTIONAL_GRAY

    expansion_pattern = ACTIVE_BARE_EXPANSION_RE if bare_expansions else INLINE_EXPANSION_RE
    cursor = 0
    for match in expansion_pattern.finditer(content):
        add_regular_runs(content[cursor : match.start()])
        add_expansion_runs(match.group(0))
        cursor = match.end()
    add_regular_runs(content[cursor:])


def add_catalog(
    document: Document,
    lines: list[str],
    page_map: dict[str, int],
    monochrome: bool = False,
    question_specific: bool = False,
    study_labels: bool = False,
    study_typography: bool = False,
    direct_without_answer_label: bool = False,
    selective_expansion: bool = False,
    bare_expansions: bool = False,
) -> None:
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(18)
    set_run_font(title.add_run("目录"), "宋体", 26, True)

    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            heading = line[2:].strip()
            if heading.startswith("华东师范大学"):
                continue
            is_chapter = True
        elif line.startswith("## "):
            heading = line[3:].strip().split("【", 1)[0]
            is_chapter = False
        else:
            continue
        if heading not in page_map:
            continue
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0 if is_chapter else 0.74)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.space_after = Pt(5 if is_chapter else 1)
        paragraph.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        set_run_font(
            paragraph.add_run(f"{heading}\t{page_map[heading]}"),
            size=11,
            bold=is_chapter,
        )

    note = document.add_paragraph()
    note.paragraph_format.first_line_indent = Cm(0)
    note.paragraph_format.space_before = Pt(8)
    note.paragraph_format.space_after = Pt(0)
    if monochrome:
        set_paragraph_border(note, "000000", size="8")
    else:
        shade_paragraph(note, LIGHT_GRAY_FILL)
    if direct_without_answer_label:
        if bare_expansions:
            note_text = (
                "直接用法｜每道押题下方内容可直接背诵和作答；圆括号外是背诵主体，"
                "（）内是可选扩容，例子可按题目灵活替换。"
            )
        elif selective_expansion:
            note_text = (
                "直接用法｜每道押题下方内容可直接背诵和作答；【名词解释】前是可独立提取的完整定义；"
                "【扩容（选背）】中的内容可选择背诵，作答时按题目分值和时间选写。"
            )
        else:
            note_text = "直接用法｜每道押题下方内容可直接背诵和作答；【名词解释】是可独立提取的完整定义；【加分项】按题干和时间灵活选写。"
    elif study_typography:
        note_text = (
            "直接用法｜每题答案均完整呈现；正文中的正体表示多题重复内容，斜体表示只在本题新增的内容；"
            "【采分点加分】紧跟对应点选写，【整体加分】位于答案末尾选写。"
        )
    elif study_labels:
        note_text = (
            "直接用法｜每题答案均完整呈现；【共用】会在别题原样出现，【本题补充】是本题新增；"
            "【采分点加分】紧跟对应点选写，【整体加分】位于答案末尾选写。"
        )
    elif question_specific:
        note_text = "直接用法｜每道押题下方答案可直接背诵和作答；【名词解释】是可独立提取的完整定义；【加分项】按题干和时间灵活选写。"
    else:
        note_text = "直接用法｜题目问什么，就写综合答案中的同名小标题；名词解释提取【名词解释】标注前的定义；【加分项】按题干和时间灵活选写。"
    set_run_font(
        note.add_run(note_text),
        size=9 if study_labels or study_typography else 9.5,
        bold=True,
    )


def set_bottom_border(paragraph, color: str = "000000", size: str = "6") -> None:
    properties = paragraph._p.get_or_add_pPr()
    borders = properties.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        properties.append(borders)
    bottom = borders.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        borders.append(bottom)
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)


def add_student_guide(document: Document) -> None:
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(16)
    set_run_font(title.add_run("使用说明"), "宋体", 22, True)

    lead = document.add_paragraph()
    lead.paragraph_format.first_line_indent = Cm(0)
    lead.paragraph_format.line_spacing = 1.45
    lead.paragraph_format.space_after = Pt(10)
    set_run_font(lead.add_run("先按星级确定背诵顺序，再按题目分值决定是否调用选背扩容。"), size=11.5, bold=True)

    levels = (
        ("★★★  核心优先", "速背手册原一级中综合优先度最高的内容。时间有限时先完整背诵。"),
        ("★★  重点掌握", "同样属于速背手册原一级。完成三星后继续掌握，不能把二星理解为不重要。"),
        ("★  基础覆盖", "对应速背手册原二级。用于补足范围，时间紧张时至少熟悉题目与基础采分点。"),
    )
    for label, explanation in levels:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.right_indent = Cm(0.3)
        paragraph.paragraph_format.line_spacing = 1.45
        paragraph.paragraph_format.space_after = Pt(9)
        set_run_font(paragraph.add_run(label + "｜"), size=12, bold=True)
        set_run_font(paragraph.add_run(explanation), size=11.5)

    caution = document.add_paragraph()
    caution.paragraph_format.first_line_indent = Cm(0)
    caution.paragraph_format.line_spacing = 1.4
    caution.paragraph_format.space_before = Pt(4)
    caution.paragraph_format.space_after = Pt(14)
    set_bottom_border(caution, size="8")
    set_run_font(
        caution.add_run("注意｜星级只表示背诵先后顺序，不代表必考概率，也不表示低星内容绝对不会考。"),
        size=10.5,
        bold=True,
    )

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(8)
    set_run_font(heading.add_run("答案怎么用"), size=14, bold=True)
    uses = (
        "1. 每道押题下方就是一份可直接背写的答案；先背方括号外的基础采分点。",
        "2. 【扩容（选背）】按题目分值和作答时间选写，不必机械全部写入。",
        "3. 名词解释提取核心定义和紧邻的标准扩容；简答、论述按题干选取相应分点。",
        "4. 正文仅用加粗标记采分关键词，黑白打印时无需依赖颜色或底纹。",
    )
    for value in uses:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.line_spacing = 1.4
        paragraph.paragraph_format.space_after = Pt(5)
        set_run_font(paragraph.add_run(value), size=10.8)

    source = document.add_paragraph()
    source.paragraph_format.first_line_indent = Cm(0)
    source.paragraph_format.line_spacing = 1.35
    source.paragraph_format.space_before = Pt(11)
    set_run_font(source.add_run("内容边界｜"), size=10, bold=True)
    set_run_font(
        source.add_run(
            "知识结论均以速背手册或一本通为依据；答案可以应试化重组，标明可灵活替换的例子不作为新的理论或结论。"
        ),
        size=10,
    )
    document.add_page_break()


def add_student_guide_v9(document: Document) -> None:
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Cm(0)
    title.paragraph_format.space_after = Pt(16)
    set_run_font(title.add_run("使用说明"), "宋体", 22, True)

    level_heading = document.add_paragraph()
    level_heading.paragraph_format.first_line_indent = Cm(0)
    level_heading.paragraph_format.space_after = Pt(7)
    set_run_font(level_heading.add_run("星级"), size=14, bold=True)
    levels = (
        (
            "★★★  核心优先｜",
            "速背手册原一级；一本通与考纲中的核心内容，华东或相关真题信号强，主观题可考性和答案复用价值最高。优先完整背诵。",
        ),
        (
            "★★  重点掌握｜",
            "同属速背手册原一级；一本通与考纲依据明确，具有稳定可考性，但真题信号或综合优先度略低于三星。完成三星后继续掌握。",
        ),
        (
            "★  基础覆盖｜",
            "速背手册原二级；速背手册或一本通有收录且属于考纲范围，但真题信号和主观题可考性相对较弱。用于补足范围。",
        ),
    )
    for label, explanation in levels:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.right_indent = Cm(0.3)
        paragraph.paragraph_format.line_spacing = 1.42
        paragraph.paragraph_format.space_after = Pt(8)
        set_run_font(paragraph.add_run(label), size=11.5, bold=True)
        set_run_font(paragraph.add_run(explanation), size=11)

    use_heading = document.add_paragraph()
    use_heading.paragraph_format.first_line_indent = Cm(0)
    use_heading.paragraph_format.space_after = Pt(7)
    set_run_font(use_heading.add_run("怎么用"), size=14, bold=True)
    uses = (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数。",
        "2. （）内是扩容项，选背；用于丰富答题角度、锦上添花，追求更高分数。如果其中是例子，可以根据题目灵活替换。",
    )
    for value in uses:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.left_indent = Cm(0.45)
        paragraph.paragraph_format.line_spacing = 1.4
        paragraph.paragraph_format.space_after = Pt(5)
        set_run_font(paragraph.add_run(value), size=10.8)
    document.add_page_break()


def add_answer_heading(document: Document, text: str = "综合答案") -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.line_spacing = 1.0
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.keep_with_next = True
    set_run_font(paragraph.add_run(text), "宋体", 11, True)


def add_question_heading(
    document: Document,
    content: str,
    monochrome: bool = False,
    large_between_question_gap: bool = False,
    comfortable: bool = False,
    bare_expansions: bool = False,
    tight_layout: bool = False,
):
    paragraph = document.add_paragraph(style="Heading 3")
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_after = Pt(4.5 if tight_layout else 6 if comfortable else 2)
    match = re.match(r"(押题\d+)(【[^】]+】)(.*)", content)
    if match is None:
        paragraph.paragraph_format.space_before = Pt(8 if comfortable else 5)
        add_inline_runs(
            paragraph,
            content,
            size=11.5,
            monochrome=monochrome,
            bare_expansions=bare_expansions,
        )
        return paragraph
    paragraph.paragraph_format.space_before = Pt(
        16 if comfortable and match.group(1) != "押题1"
        else 9 if comfortable
        else 10 if large_between_question_gap and match.group(1) != "押题1"
        else 5
    )
    set_run_font(paragraph.add_run(match.group(1)), "宋体", BODY_TEXT_SIZE, True)
    # 题型标记是题干正文的一部分，不再通过缩小字号制造视觉层级。
    set_run_font(paragraph.add_run(match.group(2)), "宋体", BODY_TEXT_SIZE, True)
    add_inline_runs(
        paragraph,
        match.group(3),
        size=12,
        monochrome=monochrome,
        bare_expansions=bare_expansions,
    )
    if comfortable:
        set_bottom_border(paragraph, size="5")
    return paragraph


def add_list_paragraph(
    document: Document,
    raw_line: str,
    answer_mode: bool,
    compact: bool,
    monochrome: bool = False,
    comfortable: bool = False,
    bare_expansions: bool = False,
    tight_layout: bool = False,
) -> None:
    stripped = raw_line.strip()
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.75)
    paragraph.paragraph_format.first_line_indent = Cm(-0.48)
    paragraph.paragraph_format.line_spacing = (
        1.4 if tight_layout else 1.48 if comfortable else 1.2 if compact else 1.35
    )
    paragraph.paragraph_format.space_after = Pt(
        2 if tight_layout else 4.5 if comfortable else 0 if answer_mode else 1
    )
    paragraph.paragraph_format.widow_control = True
    plain_stripped = stripped.replace("**", "")
    if tight_layout and plain_stripped in ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES:
        paragraph.paragraph_format.page_break_before = True
    # In task-module answers, a numbered line ending in a colon is the parent
    # module heading and must stay with its first child point.
    paragraph.paragraph_format.keep_with_next = not answer_mode or stripped.endswith("：")
    if stripped.endswith("："):
        if tight_layout:
            paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.keep_together = True
    if (
        any(tag in stripped for tag in ("【采分点加分】", "【加分项】", "【扩容（选用）：", "【扩容（选背）：", "【名词解释："))
        or bare_expansions and ACTIVE_BARE_EXPANSION_RE.search(stripped)
    ):
        paragraph.paragraph_format.keep_together = True
    add_inline_runs(
        paragraph,
        stripped,
        size=10.5 if not answer_mode else BODY_TEXT_SIZE if comfortable else 11.5,
        monochrome=monochrome,
        bare_expansions=bare_expansions,
    )


def add_secondary_list_paragraph(
    document: Document,
    raw_line: str,
    answer_mode: bool,
    compact: bool,
    monochrome: bool = False,
    comfortable: bool = False,
    bare_expansions: bool = False,
    tight_layout: bool = False,
) -> None:
    """Render （1） child points one level below their parent scoring angle."""
    stripped = raw_line.strip()
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(1.22)
    paragraph.paragraph_format.first_line_indent = Cm(-0.47)
    paragraph.paragraph_format.line_spacing = (
        1.4 if tight_layout else 1.46 if comfortable else 1.2 if compact else 1.3
    )
    paragraph.paragraph_format.space_after = Pt(
        2 if tight_layout else 4 if comfortable else 0 if answer_mode else 1
    )
    paragraph.paragraph_format.widow_control = True
    paragraph.paragraph_format.keep_with_next = stripped.endswith("：")
    if stripped.endswith("："):
        paragraph.paragraph_format.keep_together = True
    if (
        "【扩容（选用）：" in stripped
        or "【扩容（选背）：" in stripped
        or "【名词解释：" in stripped
        or bare_expansions and ACTIVE_BARE_EXPANSION_RE.search(stripped)
    ):
        paragraph.paragraph_format.keep_together = True
    add_inline_runs(
        paragraph,
        stripped,
        size=10.5 if not answer_mode else BODY_TEXT_SIZE if comfortable else 11.3,
        monochrome=monochrome,
        bare_expansions=bare_expansions,
    )


def add_deep_list_paragraph(
    document: Document,
    raw_line: str,
    answer_mode: bool,
    compact: bool,
    level: int,
    monochrome: bool = False,
    comfortable: bool = False,
    bare_expansions: bool = False,
    tight_layout: bool = False,
) -> None:
    """Render ① and a. as the third and fourth real answer levels."""
    stripped = raw_line.strip()
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(1.68 if level == 3 else 2.12)
    paragraph.paragraph_format.first_line_indent = Cm(-0.43)
    paragraph.paragraph_format.line_spacing = (
        1.4 if tight_layout else 1.46 if comfortable else 1.2 if compact else 1.3
    )
    paragraph.paragraph_format.space_after = Pt(
        2 if tight_layout else 4 if comfortable else 0 if answer_mode else 1
    )
    paragraph.paragraph_format.widow_control = True
    if (
        "【名词解释：" in stripped
        or bare_expansions and ACTIVE_BARE_EXPANSION_RE.search(stripped)
    ):
        paragraph.paragraph_format.keep_together = True
    add_inline_runs(
        paragraph,
        stripped,
        size=10.5 if not answer_mode else BODY_TEXT_SIZE if comfortable else 11.3,
        monochrome=monochrome,
        bare_expansions=bare_expansions,
    )


def add_body_paragraph(
    document: Document,
    content: str,
    compact: bool,
    monochrome: bool = False,
    comfortable: bool = False,
    bare_expansions: bool = False,
    tight_layout: bool = False,
) -> None:
    optional = (
        content.startswith("（加分项：")
        or content.startswith(("【扩容（选用）：", "【扩容（选背）："))
        or bare_expansions and ACTIVE_BARE_EXPANSION_RE.fullmatch(content) is not None
    )
    summary = content.startswith("综上")
    module_intro = content.endswith("：") and not optional
    # 扩容项和总结段只约束自身不拆段，不再反向给前文设置 keep-with-next。
    # 反向绑定会把“末尾若干采分点—多个扩容段—总结”串成长链，Word 为了
    # 整链同页会在上一页留下大块空白。父模块标题仍通过 module_intro 与
    # 首个子项同页，单个采分点内的定义、扩容和名解标签本来就在同一段中。
    paragraph = document.add_paragraph()
    plain_content = content.replace("**", "")
    if tight_layout and plain_content in ACTIVE_MEASUREMENT_PAGE_BREAK_BODY:
        paragraph.paragraph_format.page_break_before = True
    paragraph.paragraph_format.line_spacing = (
        1.32 if tight_layout and optional
        else 1.42 if tight_layout
        else 1.36 if comfortable and optional
        else 1.5 if comfortable
        else 1.18 if optional
        else 1.25 if compact
        else 1.4
    )
    paragraph.paragraph_format.space_after = Pt(
        2.5 if tight_layout else 5 if comfortable else 1
    )
    paragraph.paragraph_format.widow_control = True
    if (
        "【名词解释：" in content
        or "【采分点加分】" in content
        or "【加分项】" in content
        or "【扩容（选用）：" in content
        or "【扩容（选背）：" in content
        or bare_expansions and ACTIVE_BARE_EXPANSION_RE.search(content)
    ):
        paragraph.paragraph_format.keep_together = True
    if summary:
        paragraph.paragraph_format.space_before = Pt(
            3 if tight_layout else 4 if comfortable else 0
        )
        paragraph.paragraph_format.space_after = Pt(
            4 if tight_layout else 6 if comfortable else 1
        )
        paragraph.paragraph_format.keep_together = True
    if module_intro:
        paragraph.paragraph_format.space_before = Pt(
            2 if tight_layout else 3 if comfortable else 1
        )
        paragraph.paragraph_format.space_after = Pt(
            2 if tight_layout else 3 if comfortable else 1
        )
        paragraph.paragraph_format.keep_with_next = True
        paragraph.paragraph_format.keep_together = True
    if content == "**【整体加分】**":
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.space_after = Pt(1)
        paragraph.paragraph_format.keep_with_next = True
    if optional:
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.space_before = Pt(1)
    add_inline_runs(
        paragraph,
        content,
        size=BODY_TEXT_SIZE if comfortable else 11.5,
        optional=optional,
        monochrome=monochrome,
        bare_expansions=bare_expansions,
    )


def render_markdown(
    markdown_path: Path,
    output_path: Path,
    page_map_override: dict[str, int] | None = None,
) -> None:
    global ACTIVE_BARE_EXPANSION_RE
    global ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES
    global ACTIVE_MEASUREMENT_PAGE_BREAK_BODY
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    subtitle = lines[2].removeprefix("## ").strip()
    # 全本各迭代版都应使用全本封面、目录和逐题直背版式；版本名不应
    # 成为版式识别条件。
    full_book = subtitle.startswith("全本·")
    minimal_v9 = subtitle.startswith("全本·极简直背版")
    comfortable = subtitle.startswith("全本·三星分级舒适阅读版V8") or minimal_v9
    # 测量V7及其内容精校续版沿用紧凑排版，压缩答案内部无意义段后距，
    # 但保留题间留白、12磅正文和原有内容层级。V9恢复逐章分页。
    task_aligned_rebuild = (
        "心理学导论" in title and subtitle.endswith("V10")
        or "实验心理学" in title and subtitle.endswith("V2")
    )
    tight_layout = (
        "心理测量" in title and subtitle.endswith(("V7", "V8", "V9"))
    ) or task_aligned_rebuild
    chapter_page_breaks = (
        "心理测量" in title and subtitle.endswith("V9")
    ) or task_aligned_rebuild
    if "实验心理学" in title and subtitle.endswith("V2"):
        ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES = EXPERIMENT_V2_PAGE_BREAK_MODULES
        ACTIVE_MEASUREMENT_PAGE_BREAK_BODY = EXPERIMENT_V2_PAGE_BREAK_BODY
    elif subtitle.endswith("V7"):
        ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES = MEASUREMENT_V7_PAGE_BREAK_MODULES
        ACTIVE_MEASUREMENT_PAGE_BREAK_BODY = MEASUREMENT_V7_PAGE_BREAK_BODY
    elif subtitle.endswith("V8"):
        ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES = MEASUREMENT_V8_PAGE_BREAK_MODULES
        ACTIVE_MEASUREMENT_PAGE_BREAK_BODY = MEASUREMENT_V8_PAGE_BREAK_BODY
    elif subtitle.endswith("V9"):
        ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES = MEASUREMENT_V9_PAGE_BREAK_MODULES
        ACTIVE_MEASUREMENT_PAGE_BREAK_BODY = MEASUREMENT_V9_PAGE_BREAK_BODY
    else:
        ACTIVE_MEASUREMENT_PAGE_BREAK_MODULES = set()
        ACTIVE_MEASUREMENT_PAGE_BREAK_BODY = set()
    bare_expansions = minimal_v9
    if bare_expansions:
        if "心理测量" in title:
            from build_measurement_baoming_v3 import SOURCE, source_expansion_contents
        elif "实验心理学" in title:
            from build_experiment_baoming_v1 import SOURCE, source_expansion_contents
        else:
            from build_baoming_full_v9 import SOURCE, source_expansion_contents

        wrapped_expansions = sorted(
            {f"（{value}）" for value in source_expansion_contents(SOURCE.read_text(encoding="utf-8"))},
            key=len,
            reverse=True,
        )
        ACTIVE_BARE_EXPANSION_RE = re.compile(
            "|".join(re.escape(value) for value in wrapped_expansions)
        )
    else:
        ACTIVE_BARE_EXPANSION_RE = BARE_EXPANSION_RE
    question_specific = full_book or subtitle.endswith(("V8", "V9", "V10", "V11", "V12", "V13", "V14", "V15", "V16"))
    monochrome = full_book or subtitle.endswith(("V7", "V8", "V9", "V10", "V11", "V12", "V13", "V14", "V15", "V16"))
    if page_map_override is not None:
        page_map = page_map_override
    elif full_book:
        page_map = {
            line.lstrip("# ").strip().split("【", 1)[0]: 0
            for line in lines
            if line.startswith("# 第") or re.match(r"^## [一二三四五六七八九十]+、", line)
        }
    elif subtitle.endswith("V16"):
        page_map = V16_CATALOG_PAGE_MAP
    elif subtitle.endswith("V15"):
        page_map = V15_CATALOG_PAGE_MAP
    elif subtitle.endswith("V14"):
        page_map = V14_CATALOG_PAGE_MAP
    elif subtitle.endswith("V13"):
        page_map = V13_CATALOG_PAGE_MAP
    elif subtitle.endswith("V12"):
        page_map = V12_CATALOG_PAGE_MAP
    elif subtitle.endswith("V11"):
        page_map = V11_CATALOG_PAGE_MAP
    elif subtitle.endswith("V10"):
        page_map = V10_CATALOG_PAGE_MAP
    elif subtitle.endswith("V9"):
        page_map = V9_CATALOG_PAGE_MAP
    elif question_specific:
        page_map = V8_CATALOG_PAGE_MAP
    elif monochrome:
        page_map = V7_CATALOG_PAGE_MAP
    elif subtitle.endswith("V6"):
        page_map = V6_CATALOG_PAGE_MAP
    else:
        page_map = CATALOG_PAGE_MAP | (V3_CATALOG_OVERRIDES if subtitle.endswith("V3") else {})
    document = Document()
    configure_styles(document)
    if monochrome:
        force_monochrome_title_style(document)
    configure_page(document.sections[0])
    set_update_fields(document)
    document.core_properties.title = title
    if "心理测量" in title:
        subject_name = "心理测量"
    elif "实验心理学" in title:
        subject_name = "实验心理学"
    else:
        subject_name = "心理学导论"
    document.core_properties.subject = (
        f"华东师范大学347{subject_name}逐题直背答案版"
        if question_specific
        else f"华东师范大学347{subject_name}直背综合答案版"
    )
    document.core_properties.author = "铁头心理学考研"
    if minimal_v9:
        add_cover(document, title, "", edition="")
    else:
        add_cover(
            document,
            title,
            subtitle,
            edition="全本｜2026" if full_book else "前三章｜2026",
        )
    if minimal_v9:
        add_student_guide_v9(document)
    elif comfortable:
        add_student_guide(document)
    first_chapter_index = next(
        index for index, line in enumerate(lines) if line.startswith("# 第一章 ")
    )
    add_catalog(
        document,
        lines,
        page_map,
        monochrome=monochrome,
        question_specific=question_specific,
        study_labels=subtitle.endswith("V10"),
        study_typography=subtitle.endswith("V11"),
        direct_without_answer_label=full_book or subtitle.endswith(("V12", "V13", "V14", "V15", "V16")),
        selective_expansion=full_book or subtitle.endswith(("V13", "V14", "V15", "V16")),
        bare_expansions=bare_expansions,
    )

    body_section = document.add_section(WD_SECTION.NEW_PAGE)
    configure_page(body_section)
    configure_body_header_footer(
        body_section,
        f"华东师范大学347｜{subject_name}保命手册",
    )

    answer_mode = False
    compact_unit = False
    first_chapter = True
    line_index = first_chapter_index
    while line_index < len(lines):
        raw_line = lines[line_index]
        stripped = raw_line.strip()
        if not stripped or stripped == "---":
            line_index += 1
            continue
        if stripped.startswith("# "):
            heading = add_heading(
                document,
                1,
                stripped[2:].strip(),
                page_break_before=(
                    not first_chapter and (not tight_layout or chapter_page_breaks)
                ),
            )
            if tight_layout and not first_chapter:
                heading.paragraph_format.space_before = Pt(0 if chapter_page_breaks else 14)
                heading.paragraph_format.space_after = Pt(4)
            first_chapter = False
            answer_mode = False
        elif stripped.startswith("## "):
            heading_text = stripped[3:].strip()
            heading = add_heading(document, 2, heading_text)
            compact_unit = not comfortable and heading_text.startswith(INLINE_COMPACT_UNIT_PREFIXES)
            if compact_unit:
                heading.paragraph_format.space_before = Pt(7)
                heading.paragraph_format.space_after = Pt(3)
            elif comfortable:
                heading.paragraph_format.space_before = Pt(9 if tight_layout else 13)
                heading.paragraph_format.space_after = Pt(5 if tight_layout else 7)
            answer_mode = False
        elif stripped.startswith("#### "):
            heading_text = stripped[5:].strip()
            if heading_text == "答案":
                add_answer_heading(document, "答案")
                answer_mode = True
            else:
                heading = add_heading(document, 3, heading_text)
                heading.paragraph_format.space_before = Pt(4)
                heading.paragraph_format.space_after = Pt(2)
                answer_mode = False
        elif stripped.startswith("### "):
            heading_text = stripped[4:].strip()
            if heading_text == "综合答案":
                add_answer_heading(document)
                answer_mode = True
            else:
                displayed = "押题题目" if heading_text == "押题题目" else heading_text
                if question_specific and displayed.startswith("押题"):
                    heading = add_question_heading(
                        document,
                        displayed,
                        monochrome=monochrome,
                        large_between_question_gap=full_book or subtitle.endswith(("V9", "V10", "V11", "V12", "V13", "V14", "V15", "V16")),
                        comfortable=comfortable,
                        bare_expansions=bare_expansions,
                        tight_layout=tight_layout,
                    )
                else:
                    heading = add_heading(document, 3, displayed)
                    heading.paragraph_format.space_before = Pt(5)
                    heading.paragraph_format.space_after = Pt(2)
                answer_mode = (full_book or subtitle.endswith(("V12", "V13", "V14", "V15", "V16"))) and displayed.startswith("押题")
        elif stripped.startswith("|"):
            table_lines: list[str] = []
            while line_index < len(lines) and lines[line_index].strip().startswith("|"):
                table_lines.append(lines[line_index].strip())
                line_index += 1
            add_table(document, table_lines)
            continue
        elif re.match(r"^\d+\.\s", stripped):
            add_list_paragraph(
                document,
                raw_line,
                answer_mode,
                compact_unit,
                monochrome=monochrome,
                comfortable=comfortable,
                bare_expansions=bare_expansions,
                tight_layout=tight_layout,
            )
        elif re.match(r"^（\d+）", stripped):
            add_secondary_list_paragraph(
                document,
                raw_line,
                answer_mode,
                compact_unit,
                monochrome=monochrome,
                comfortable=comfortable,
                bare_expansions=bare_expansions,
                tight_layout=tight_layout,
            )
        elif re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", stripped):
            add_deep_list_paragraph(
                document,
                raw_line,
                answer_mode,
                compact_unit,
                level=3,
                monochrome=monochrome,
                comfortable=comfortable,
                bare_expansions=bare_expansions,
                tight_layout=tight_layout,
            )
        elif re.match(r"^[a-z]\.\s", stripped):
            add_deep_list_paragraph(
                document,
                raw_line,
                answer_mode,
                compact_unit,
                level=4,
                monochrome=monochrome,
                comfortable=comfortable,
                bare_expansions=bare_expansions,
                tight_layout=tight_layout,
            )
        else:
            add_body_paragraph(
                document,
                stripped,
                compact_unit,
                monochrome=monochrome,
                comfortable=comfortable,
                bare_expansions=bare_expansions,
                tight_layout=tight_layout,
            )
        line_index += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-map", type=Path)
    arguments = parser.parse_args()
    page_map = None
    if arguments.page_map:
        page_map = json.loads(arguments.page_map.read_text(encoding="utf-8"))
    render_markdown(arguments.input, arguments.output, page_map)


if __name__ == "__main__":
    main()
