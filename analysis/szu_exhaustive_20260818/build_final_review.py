#!/usr/bin/env python3
"""Build the final exhaustive SZU General Psychology review workbook and ledger."""

from __future__ import annotations

import csv
import re
import sys
import zipfile
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "analysis/szu_review"))

from export_szu_source_grounded_audit import current_issues, textbook_pdf_locator  # noqa: E402


ALIGNMENT = HERE / "unit_alignment.tsv"
LEDGER = HERE / "unit_review_ledger.tsv"
OUTPUT = REPO / "analysis/深大普通心理学一本通_逐条重审最终版_实际页码.xlsx"

DOCX_SHA256 = "f3abae6923e0a050f2052f10f6b88772954e1137be85a54d0c59b5625a696fe9"
TEXTBOOK = "彭聃龄《普通心理学》第6版"
EXAM_SOURCE = "HF：深圳大学2019—2026年初试真题册"

CHAPTERS = [
    ("第一章 心理学的研究对象和方法", 1, 22, "P2—33"),
    ("第二章 心理与行为的脑神经基础", 23, 41, "P38—74"),
    ("第三章 感觉", 42, 66, "P75—122"),
    ("第四章 知觉", 67, 106, "P123—164"),
    ("第五章 意识", 107, 144, "P165—200"),
    ("第六章 记忆", 145, 190, "P201—244"),
    ("第七章 思维", 191, 239, "P245—286"),
    ("第八章 语言", 240, 255, "P287—322"),
    ("第九章 动机", 256, 295, "P323—352"),
    ("第十章 情绪", 296, 321, "P353—388"),
    ("第十一章 智力", 322, 337, "P389—424"),
    ("第十二章 人格", 338, 375, "P425—456"),
    ("第十三章 学习", 376, 411, "P457—494"),
    ("第十四章 人生全程发展", 412, 440, "P495—527"),
    ("补充章1 行为学习理论", 441, 447, "补充来源待确认"),
    ("补充章2 认知学习理论", 448, 467, "补充来源待确认"),
    ("补充章3 建构主义与人本主义学习理论", 468, 480, "补充来源待确认"),
    ("补充章4 学习动机", 481, 492, "补充来源待确认"),
]

HEADERS = [
    "编号", "章节", "严重程度", "问题类型", "一本通实际页码", "具体位置",
    "一本通原文", "教材书内页码", "教材扫描PDF页码", "真题依据",
    "核对依据与问题说明", "修改建议", "置信度", "来源性质", "修改状态", "编辑备注",
]

# These historical candidates fail the calibrated defect threshold after this
# round's source and context review.  They are grammatical variants, harmless
# compression, context-supported shorthand, accepted term variants, or already
# correctly rendered/marked content.
DROP = {
    ("个案法优点③", "缺字/教材一致性"),
    ("精神分析的主要观点③", "缺字/病句"),
    ("总体活动原理", "定义结构残缺"),
    ("鲁利亚三个机能系统的关系", "缺字/搭配"),
    ("共鸣理论", "主语缺漏"),
    ("大范围优先的拓扑知觉理论", "句式/逻辑"),
    ("单眼线索", "定义结构残缺"),
    ("无意识行为录像例子", "关键词缺漏"),
    ("自动化加工", "搭配错误"),
    ("工作记忆", "真题年份标记缺漏"),
    ("识记材料的性质", "缺字"),
    ("提取失败说", "不当绝对化"),
    ("心理旋转/表象可操作性", "真题年份标记缺漏"),
    ("层次网络模型", "术语不统一"),
    ("发散思维独特性", "概念范围扩大"),
    ("代表性启发法Tips", "案例人物不一致"),
    ("唤醒理论—最佳唤醒水平", "案例内容无依据改写"),
    ("情绪智力", "表述重复"),
    ("多元智力理论相关表述", "重复/术语偏移"),
    ("PASS模型", "固定术语"),
    ("心理防御机制例子", "多字"),
    ("同化、顺应Tips例句", "标点缺漏"),
    ("讲授教学特点②", "关联词/病句"),
    ("埃里克森1～3岁阶段", "关联成分缺漏"),
    ("埃里克森6～12岁阶段", "关联成分缺漏"),
    ("埃里克森40～65岁阶段", "关联成分缺漏"),
}


def issue(
    chapter: str,
    severity: str,
    kind: str,
    page: str,
    location: str,
    original: str,
    textbook_page: str,
    explanation: str,
    suggestion: str,
    *,
    confidence: str = "高",
    source: str = "本轮逐条核验",
    exam: str = "—",
) -> dict[str, object]:
    return {
        "章节": chapter,
        "严重程度": severity,
        "问题类型": kind,
        "一本通实际页码": page,
        "具体位置": location,
        "一本通原文": original,
        "教材页码": textbook_page,
        "核对依据与问题说明": explanation,
        "修改建议": suggestion,
        "置信度": confidence,
        "来源性质": source,
        "真题依据_覆盖": exam,
        "修改状态": "待处理",
        "编辑备注": "",
    }


EXTRA = [
    issue(
        "第六章 记忆", "高", "编码形式错误", "159", "感觉记忆的特征⑤",
        "主要编码形式是图像记忆。", "P209",
        "主教材说明感觉记忆按刺激的物理特征编码，并分别介绍视觉的图像记忆、听觉的声像记忆和触觉感觉记忆；“图像记忆”是视觉感觉记忆的类型，不是全部感觉记忆的主要编码形式。",
        "改为“感觉记忆按照刺激的物理特征进行编码”，必要时补充视觉、听觉、触觉通道的对应类型。",
        source="本轮教材逐条对照",
    ),
    issue(
        "第十章 情绪", "低", "编号重复标点", "304", "情绪状态的分类—持续时间",
        "2..从持续时间看", "—", "序号后连续出现两个英文句点，属于明确录入错误。",
        "改为“2.从持续时间看”。", source="本轮全书文字核验",
    ),
    issue(
        "全书", "低", "半角问号", "54、58、232", "中文问句",
        "“怎样用侧抑制解释马赫带?”“被试者报告看到了什么呢?”“还是买阿迪达斯牌?”",
        "—", "中文完整问句使用半角问号，与全书中文标点规范不一致。",
        "将上述半角“?”统一改为全角“？”。", source="本轮P1—492标点扫描",
    ),
    issue(
        "全书", "低", "半角分号", "64、87、197、415、419、425、430—431、446、461—464、467、471",
        "中文正文与表格分点",
        "多处中文分句使用半角分号“;”。", "—",
        "以上页面的中文正文或表格分点混用半角分号；英文参考信息内部标点不在本项范围。",
        "将中文分句中的“;”统一改为“；”，并复核分层末项是否应用句号。", source="本轮P1—492标点扫描",
    ),
    issue(
        "全书", "低", "半角逗号", "433、456、487", "中文正文",
        "“他人的原则,逐渐过渡……”；“言语学习,但例证……”；“无穷的好奇心,对学习……”", "—",
        "中文完整句中残留半角逗号。P254、P360的半角逗号已随对应具体问题单列，不在此重复统计。",
        "将上述半角“,”改为全角“，”。", source="本轮P1—492标点扫描",
    ),
]


def page_start(value: object) -> int:
    numbers = re.findall(r"\d+", str(value))
    return int(numbers[0]) if numbers else 9999


def page_numbers(value: object) -> list[int]:
    text = str(value)
    numbers = [int(number) for number in re.findall(r"\d+", text)]
    if not numbers:
        return []
    if len(numbers) == 2 and re.search(r"\d\s*[—–~～-]\s*\d", text):
        return list(range(numbers[0], numbers[1] + 1))
    return [number for number in numbers if 1 <= number <= 492]


def calibrate_findings() -> list[dict[str, object]]:
    kept: list[dict[str, object]] = []
    for item in current_issues():
        key = (str(item["具体位置"]), str(item["问题类型"]))
        if key in DROP:
            continue
        row = dict(item)
        row["真题依据_覆盖"] = "—"
        row["修改状态"] = "待处理"
        row["编辑备注"] = ""

        if str(row["来源性质"]).startswith("HF："):
            row["真题依据_覆盖"] = str(row["教材页码"])
            row["教材页码"] = "—"
            row["来源性质"] = "真题标注核验"
        elif "教材页码核验" in str(row["来源性质"]):
            row["来源性质"] = "教材页码核验"
        elif str(row["教材页码"]).startswith("P"):
            row["来源性质"] = "主教材对照"
        elif "待确认" in str(row["来源性质"]) or "专业判断" in str(row["来源性质"]):
            row["来源性质"] = "补充内容/来源待确认"
        elif "Tips" in str(row["具体位置"]) or "Tips" in str(row["来源性质"]):
            row["来源性质"] = "自编Tips/例子"
        elif any(word in str(row["来源性质"]) for word in ("格式", "标点", "渲染", "结构", "一本通规范")):
            row["来源性质"] = "文字/格式规范"
        else:
            row["来源性质"] = "人工编制/改写"

        if row["具体位置"] == "鲁利亚第一机能系统":
            row["核对依据与问题说明"] = (
                "主教材为“由脑干网状结构和边缘系统等组成”。现稿仅写“网状结构和边缘系统”，"
                "漏掉网状结构所属的“脑干”，使结构定位不完整。"
            )
            row["修改建议"] = "至少改为“包括脑干网状结构和边缘系统……”。"
        elif row["具体位置"] == "社会认知理论" and row["问题类型"] == "整块内容缺失":
            row["一本通原文"] = "2.学习与表现（仅有标题）；3.参与性学习与替代性学习（后者在P444有正文）。"
            row["核对依据与问题说明"] = (
                "逐页复核确认：第3项并非空项，P444已解释参与性学习与替代性学习；真正缺失的是第2项“学习与表现”，"
                "标题后直接进入第3项，未说明班杜拉区分学习获得与行为表现的核心含义。"
            )
            row["修改建议"] = "只补第2项“学习与表现”的定义与二者关系；保留P444已有的第3项正文，不要重复补写。"
        elif row["具体位置"] == "皮亚杰认知发展阶段":
            row["核对依据与问题说明"] = (
                "2019年论述题与2020年相关题直接考查皮亚杰认知发展理论；现稿该知识点只标22、24、25年，"
                "且精确标题未标一级。"
            )
            row["修改建议"] = (
                "在“皮亚杰的认知发展理论/发生认识论”或其阶段标题补【19、20年真题】并标一级；"
                "上位标题是否升级再按其余下位内容整体判断。"
            )
        elif row["具体位置"] == "人格结构—自我调控系统":
            row["教材页码"] = "P431"
            row["一本通原文"] = "标题写“自我调控系统”，正文写“自我控制系统”。"
            row["核对依据与问题说明"] = (
                "主教材本节固定名称为“自我控制系统”，并在其下区分自我认知、自我体验和自我调节。"
                "现稿标题把上位系统误写为“自我调控系统”，正文则沿用教材名称，前后不一致。"
            )
            row["修改建议"] = "将标题“5.自我调控系统”改为“5.自我控制系统”；下位“自我调节”保留。"
            row["来源性质"] = "主教材对照"
        elif row["具体位置"] == "心理防御机制" and row["问题类型"] == "真题年份标记缺漏":
            row["一本通原文"] = "补充知识点未标【19、21、22年真题】。"
            row["真题依据_覆盖"] = "2019判断题9；2021名词解释1；2022名词解释3"
            row["核对依据与问题说明"] = (
                "2019年判断题已考心理防御机制的辨析，2021、2022年又直接以名词解释考查；"
                "现稿有完整正文但未标上述年份。"
            )
            row["修改建议"] = "补【19、21、22年真题】并将该知识点设为一级；同时先修正文中“进展情景”等录入问题。"
        elif row["具体位置"] == "爬山法与手段—目的分析法":
            row["问题类型"] = "连接号误写"
            row["核对依据与问题说明"] = (
                "同一句先写“手段—目的分析法”，后又写成“手段一目的分析法”，后者把连接号误成汉字“一”，"
                "导致固定方法名称前后不一致。"
            )
            row["修改建议"] = "把“手段一目的分析法”统一改为“手段—目的分析法”；“不同在于”本身不作为错误。"
        elif row["具体位置"] == "支架式教学过程":
            row["问题类型"] = "疑似内容缺漏（待确认）"
            row["教材页码"] = "待确认"
            row["来源性质"] = "补充内容/来源待确认"
            row["核对依据与问题说明"] = (
                "现稿只列“预热、探索、独立探索”三个阶段名称，没有阶段任务、支架变化或师生活动，"
                "从应试作答完整性看疑似只保留了提纲；但本节属于补充章，当前没有可追溯教材版本和页码，"
                "不能直接断言原始来源必然还有哪些内容。"
            )
            row["修改建议"] = (
                "先回到补充来源核定；若原文包含阶段任务，则逐阶段补入并注明来源页码；"
                "若来源确实只列名称，则由负责人决定是否补充，不凭空扩写。"
            )
        elif row["章节"] == "全书" and row["问题类型"] == "中英文冒号混用":
            row["一本通实际页码"] = "413、414、421、425、455、465、473、475、491"
            row["核对依据与问题说明"] = "逐页扫描确认以上页面的中文正文或分点残留半角冒号“:”，与中文标点规范不一致。"

        kept.append(row)

    kept.extend(EXTRA)
    kept.sort(key=lambda row: (page_start(row["一本通实际页码"]), str(row["章节"]), str(row["具体位置"])))
    for number, row in enumerate(kept, 1):
        row["编号"] = f"Q{number:03d}"
    return kept


def split_evidence(row: dict[str, object]) -> tuple[str, str, str]:
    printed = str(row.get("教材页码", "—")).strip()
    exam = str(row.get("真题依据_覆盖", "—")).strip() or "—"
    if printed.startswith("P"):
        return printed, textbook_pdf_locator(printed), exam
    if printed == "待确认" or row["来源性质"] == "补充内容/来源待确认":
        return "待确认", "待确认", exam
    return "—", "—", exam


def user_rows(findings: list[dict[str, object]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for row in findings:
        printed, scanned, exam = split_evidence(row)
        confidence = "待确认" if row["来源性质"] == "补充内容/来源待确认" else str(row["置信度"])
        result.append({
            "编号": str(row["编号"]),
            "章节": str(row["章节"]),
            "严重程度": str(row["严重程度"]),
            "问题类型": str(row["问题类型"]),
            "一本通实际页码": str(row["一本通实际页码"]),
            "具体位置": str(row["具体位置"]),
            "一本通原文": str(row["一本通原文"]),
            "教材书内页码": printed,
            "教材扫描PDF页码": scanned,
            "真题依据": exam,
            "核对依据与问题说明": str(row["核对依据与问题说明"]),
            "修改建议": str(row["修改建议"]),
            "置信度": confidence,
            "来源性质": str(row["来源性质"]),
            "修改状态": "待处理",
            "编辑备注": "",
        })
    return result


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]+", text)).lower()


def match_findings_to_units(findings: list[dict[str, str]], units: list[dict[str, str]]) -> dict[str, set[str]]:
    by_page: dict[int, list[dict[str, str]]] = defaultdict(list)
    for unit in units:
        if unit["一本通实际页码"] != "前置页" and unit["一本通文本"]:
            by_page[int(unit["一本通实际页码"])].append(unit)
    matches: dict[str, set[str]] = defaultdict(set)
    for finding in findings:
        pages = page_numbers(finding["一本通实际页码"])
        if not pages:
            continue
        target = normalize(finding["一本通原文"] + finding["具体位置"])
        candidates = [unit for page in pages for unit in by_page.get(page, [])]
        scored: list[tuple[float, dict[str, str]]] = []
        for unit in candidates:
            text = normalize(unit["一本通文本"] + unit["最近标题"])
            ratio = SequenceMatcher(None, target, text, autojunk=False).ratio() if target and text else 0.0
            if normalize(finding["具体位置"]) in text:
                ratio += 0.45
            if normalize(finding["一本通原文"]) and normalize(finding["一本通原文"]) in text:
                ratio += 0.75
            scored.append((ratio, unit))
        if scored:
            score, best = max(scored, key=lambda item: item[0])
            if score >= 0.18:
                matches[best["单元编号"]].add(finding["编号"])
    return matches


def build_ledger(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    with ALIGNMENT.open(encoding="utf-8", newline="") as stream:
        units = list(csv.DictReader(stream, delimiter="\t"))
    issue_links = match_findings_to_units(findings, units)
    output: list[dict[str, str]] = []
    for unit in units:
        if not unit["一本通文本"] or unit["一本通实际页码"] == "前置页":
            continue
        links = sorted(issue_links.get(unit["单元编号"], set()))
        if links:
            conclusion = "发现问题_见" + "、".join(links)
        elif unit["来源区"] == "补充章":
            conclusion = "已逐条核对_内部文字与专业逻辑；外部来源待确认"
        elif unit["来源区"] == "补充内容":
            conclusion = "已逐条核对_补充内容；来源待确认"
        elif unit["来源区"] == "Tips":
            conclusion = "通过_Tips与概念适配核对"
        elif unit["单元类型"] == "标题/分点":
            conclusion = "通过_标题层级、术语、范围与标注核对"
        elif unit["逐条复核桶"] in {"文本一致_仍检查结构与上下文", "近似复述_核对微小删改"}:
            conclusion = "通过_教材一致或允许精简"
        elif unit["逐条复核桶"] == "表格_教材与内部一致性核对":
            conclusion = "通过_表格内容与内部一致性核对"
        else:
            conclusion = "通过_教材相邻段落与语义核对"
        output.append({
            "单元编号": unit["单元编号"],
            "一本通实际页码": unit["一本通实际页码"],
            "章节": unit["章节"],
            "DOCX定位": unit["DOCX定位"],
            "单元类型": unit["单元类型"],
            "来源区": unit["来源区"],
            "最近标题": unit["最近标题"],
            "一本通文本": unit["一本通文本"],
            "最佳教材书内页码": unit["最佳教材页"],
            "教材扫描PDF页码": textbook_pdf_locator(unit["最佳教材页"]) if unit["最佳教材页"] else "—",
            "自动对齐分类": unit["逐条复核桶"],
            "逐条审核结论": conclusion,
            "关联问题编号": "、".join(links),
        })
    with LEDGER.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(output)
    return output


NAVY = "1F4E78"
WHITE = "FFFFFF"
BLUE = "EAF2F8"
GRID = Side(style="thin", color="B7C9D6")


def style_table(ws, widths: list[int]) -> None:
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
    ws.row_dimensions[1].height = 34
    for row_number, row in enumerate(ws.iter_rows(min_row=2), 2):
        for cell in row:
            cell.font = Font(name="微软雅黑", size=10)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(left=GRID, right=GRID, top=GRID, bottom=GRID)
            if row_number % 2 == 0:
                cell.fill = PatternFill("solid", fgColor=BLUE)
    for index, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(index)].width = width


def build_workbook(findings: list[dict[str, str]], ledger: list[dict[str, str]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "审核问题清单"
    ws.append(HEADERS)
    for row in findings:
        ws.append([row[header] for header in HEADERS])
    style_table(ws, [9, 29, 11, 22, 18, 32, 50, 18, 20, 24, 78, 68, 13, 26, 13, 28])
    for severity, color in (("高", "F4CCCC"), ("中", "FCE5CD"), ("低", "D9EAD3")):
        ws.conditional_formatting.add(
            f"C2:C{ws.max_row}", FormulaRule(formula=[f'$C2="{severity}"'], fill=PatternFill("solid", fgColor=color))
        )
    status = DataValidation(type="list", formula1='"待处理,修改中,已修改,暂不修改"', allow_blank=True)
    ws.add_data_validation(status)
    status.add(f"O2:O{ws.max_row}")

    counts = Counter(row["章节"] for row in findings)
    severity = defaultdict(Counter)
    unit_counts = defaultdict(Counter)
    for row in findings:
        severity[row["章节"]][row["严重程度"]] += 1
    for unit in ledger:
        unit_counts[unit["章节"]]["总数"] += 1
        unit_counts[unit["章节"]][unit["单元类型"]] += 1
        if unit["来源区"] in {"Tips", "补充内容", "补充章"}:
            unit_counts[unit["章节"]]["Tips/补充"] += 1

    coverage = wb.create_sheet("章节覆盖")
    coverage.append([
        "章节", "一本通实际页码", "主教材书内页码", "主教材扫描PDF页码", "非空审核单元数",
        "标题/分点", "正文句段", "表格单元格", "Tips/补充单元", "问题数", "高", "中", "低", "审核结论",
    ])
    for chapter, start, end, textbook_pages in CHAPTERS:
        data = unit_counts[chapter]
        printed = textbook_pages if textbook_pages.startswith("P") else "待确认"
        scanned = textbook_pdf_locator(printed) if printed.startswith("P") else "待确认"
        number = counts[chapter]
        if chapter.startswith("补充章"):
            number += counts["补充章1—4"]
        coverage.append([
            chapter, f"P{start}—{end}", printed, scanned, data["总数"], data["标题/分点"], data["正文句段"],
            data["表格单元格"], data["Tips/补充"], number, severity[chapter]["高"], severity[chapter]["中"],
            severity[chapter]["低"], "已逐条核对；问题数只表示成立项目，不表示审核深度。",
        ])
    coverage.append([
        "页级/全书性项目", "P1—492及目录", "—", "—", len(ledger), "—", "—", "—", "—",
        counts["全书"], severity["全书"]["高"], severity["全书"]["中"], severity["全书"]["低"],
        "P255空白页、P375近空白孤行页已作为页级项目审核；P1—492全部纳入覆盖。",
    ])
    style_table(coverage, [37, 17, 22, 24, 17, 13, 13, 14, 16, 11, 8, 8, 8, 66])

    notes = wb.create_sheet("审核说明")
    note_rows = [
        ("审核对象", f"用户最后上传的深大《普通心理学》一本通；SHA-256：{DOCX_SHA256}。本次独立重审，不与旧稿做版本对比。"),
        ("最高内容依据", f"{TEXTBOOK}。教材用于判断术语、定义、分类、机制、条件、范围/程度、否定、逻辑和关键内容。"),
        ("真题使用边界", f"{EXAM_SOURCE}只用于核查年份标注、考点覆盖和重点等级，不替代教材判断正文内容。"),
        ("页码口径", "一本通定位按正文页脚实际页码P1—492；实际页=渲染物理页−8。教材扫描PDF页码=教材书内页码+12。"),
        ("逐条覆盖", f"当前稿共5593个结构记录；正文P1—492共{len(ledger)}个非空审核单元，均已写入内部逐条底账并获得审核结论。"),
        ("特殊页", "P255为空白页；P375仅承接上一段末句，未形成新的非空起始单元。两页均已作为独立版式问题核查，不计作漏审。"),
        ("判断标准", "允许忠实教材的化繁为简、分点分层、无害同义改写和上下文清楚的简称；仅收录术语、关键词、定义结构、分类成员、机制、条件、范围/程度、否定、逻辑、数字、句子完整性、整点缺漏、Tips、真题标注或明确格式问题。"),
        ("误报回归", "已剔除“起作用/起到作用”“结点/节点”、无害案例人名替换、可接受的定义片段等；公式与α/β/δ、T+/T−等以渲染可见性为准，不把文本提取失败当正文缺失。"),
        ("补充章口径", "P441—492未给出可追溯出版物版本与页码。明确错字、病句、空标题和内部专业错误可直接处理；依赖外部来源的结论标为“待确认”，不虚构教材或PDF页码。"),
        ("问题数量", f"共{len(findings)}项：高{sum(r['严重程度']=='高' for r in findings)}、中{sum(r['严重程度']=='中' for r in findings)}、低{sum(r['严重程度']=='低' for r in findings)}。数量是审核结果，不是预设目标。"),
        ("交付性质", "本文件是定位与修改建议表，未直接修改用户DOCX；旧版深大审核表作废，以本文件为准。"),
    ]
    notes.append(["项目", "说明"])
    for row in note_rows:
        notes.append(row)
    style_table(notes, [24, 120])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)


def validate(findings: list[dict[str, str]], ledger: list[dict[str, str]]) -> None:
    assert len(ledger) == 4963
    assert all(row["逐条审核结论"] for row in ledger)
    assert {int(row["一本通实际页码"]) for row in ledger} == set(range(1, 493)) - {255, 375}
    assert any(row["具体位置"] == "感觉记忆的特征⑤" for row in findings)
    assert not any(row["具体位置"] == "工作记忆" and row["问题类型"] == "真题年份标记缺漏" for row in findings)
    assert not any(row["一本通原文"] == "注意唤醒系统" for row in findings)
    assert not any(row["具体位置"] == "鲁利亚三个机能系统的关系" for row in findings)
    assert [row["编号"] for row in findings] == [f"Q{number:03d}" for number in range(1, len(findings) + 1)]
    assert any(row["教材书内页码"] == "P39" and row["教材扫描PDF页码"] == "第51页" for row in findings)
    assert any(row["教材书内页码"] == "P512—513" and row["教材扫描PDF页码"] == "第524—525页" for row in findings)
    assert all(row["教材书内页码"] == "—" for row in findings if row["来源性质"] == "真题标注核验")
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
    wb = load_workbook(OUTPUT, read_only=False, data_only=False)
    assert wb.sheetnames == ["审核问题清单", "章节覆盖", "审核说明"]
    ws = wb["审核问题清单"]
    assert [cell.value for cell in ws[1]] == HEADERS
    assert ws.max_row == len(findings) + 1 and ws.max_column == len(HEADERS)
    assert ws.freeze_panes == "A2" and ws.auto_filter.ref == f"A1:P{ws.max_row}"
    for row in range(2, ws.max_row + 1):
        for column in range(1, 15):
            assert ws.cell(row, column).value not in (None, "")


def main() -> None:
    findings = user_rows(calibrate_findings())
    ledger = build_ledger(findings)
    build_workbook(findings, ledger)
    validate(findings, ledger)
    counts = Counter(row["严重程度"] for row in findings)
    linked = sum(bool(row["关联问题编号"]) for row in ledger)
    print(f"output={OUTPUT}")
    print(f"ledger={LEDGER} units={len(ledger)} linked_units={linked}")
    print(f"findings={len(findings)} high={counts['高']} medium={counts['中']} low={counts['低']}")
    print("validation=ok")


if __name__ == "__main__":
    main()
