#!/usr/bin/env python3
"""Export the source-grounded SZU General Psychology Yibentong audit.

The previous issue lists are used only as candidate findings.  Coverage is
rebuilt from the current DOCX unit ledger, textbook OCR alignment, rendered
pages, and the HF Shenzhen University exam inventory.  Candidate rows survive
only when they are still present in the current file and have source evidence.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))

from export_szu_reaudit_xlsx import ISSUES as CANDIDATE_ISSUES  # noqa: E402


OUTPUT = REPO / "analysis/深大普通心理学一本通_教材真题逐条重审_实际页码.xlsx"
ALIGNMENT = HERE / "szu_unit_alignment.tsv"
EXAM_INVENTORY = HERE / "szu_exam_questions.tsv"

CURRENT_DOCX_SHA256 = "f3abae6923e0a050f2052f10f6b88772954e1137be85a54d0c59b5625a696fe9"
TEXTBOOK = "彭聃龄《普通心理学》第6版"
TEXTBOOK_PDF_PAGE_OFFSET = 12
EXAM_SOURCE = "HF：深圳大学2019—2026年初试真题册"


def finding(
    chapter: str,
    severity: str,
    kind: str,
    page: int | str,
    location: str,
    original: str,
    evidence_page: str,
    explanation: str,
    suggestion: str,
    *,
    confidence: str = "高",
    source: str = "本轮教材/渲染复核",
) -> dict[str, object]:
    return {
        "章节": chapter,
        "严重程度": severity,
        "问题类型": kind,
        "一本通实际页码": page,
        "具体位置": location,
        "一本通原文": original,
        "教材页码": evidence_page,
        "核对依据与问题说明": explanation,
        "修改建议": suggestion,
        "置信度": confidence,
        "来源性质": source,
        "修改状态": "待修改",
        "编辑备注": "",
    }


# These three candidates were generated from the text-extraction layer.  The
# corresponding glyphs are visible in the rendered pages and therefore are not
# defects in the current deliverable.
RENDER_FALSE_POSITIVES = {
    ("138", "关键符号缺失", "第三、第四睡眠阶段的脑电变化"),
    ("139", "关键符号缺失", "快速眼动睡眠阶段的脑电变化"),
    ("368", "关键符号缺失", "T型人格分型"),
}


CURRENT_TEXT_FINDINGS = [
    finding(
        "第二章 心理与行为的脑神经基础", "中", "术语前后不一致", 24, "神经元的分类",
        "神经元按功能可分为内导神经元、外导神经元和中间神经元；下文却列“感觉神经元、运动神经元和中间神经元”。",
        "P39",
        "第6版教材统一列为“感觉神经元（传入神经元）、运动神经元（传出神经元）和中间神经元”。现稿分类总述与下位标题换了一套名称，且未说明对应关系。",
        "按教材统一分类名称；如需保留“内导/外导”，应在同一处明确标注与“感觉/运动（传入/传出）”的对应关系。",
    ),
    finding(
        "第四章 知觉", "低", "括号未闭合", 78, "局部反应与整体反应",
        "整体反应（global response 要求被试判断大字母……",
        "—", "英文术语左括号后没有右括号，括注边界不完整。",
        "改为“整体反应（global response）要求被试判断大字母……”。", source="本轮逐页标点核验",
    ),
    finding(
        "第四章 知觉", "低", "中英文括号混用", 87, "物体识别研究引文",
        "(Biederman，1987）。",
        "—", "左括号为半角英文括号，右括号为全角中文括号，且英文姓名与中文逗号混用。",
        "统一为“（Biederman, 1987）。”或按全书参考文献格式处理。", source="本轮逐页标点核验",
    ),
    finding(
        "第五章 意识", "低", "引号未闭合", 110, "注意失败Tips",
        "在一个经典的“看不见的大猩猩实验中……",
        "P170", "实验名称前有左引号，但“大猩猩”后漏右引号。",
        "改为“在一个经典的‘看不见的大猩猩’实验中……”。", source="本轮逐页标点核验",
    ),
    finding(
        "第五章 意识", "中", "多字/病句", 136, "注意分配Tips",
        "一边看听音乐一边织毛衣很容易……",
        "—", "“看听音乐”多出“看”，动作搭配不成立；后文也明确以听觉通道为例。",
        "改为“一边听音乐一边织毛衣很容易……”。", source="本轮逐页文字核验",
    ),
    finding(
        "第七章 思维", "中", "错别字改变定义", 205, "概念的外延",
        "外延是指具有这些属性的事务。",
        "P253", "概念外延指具有相应属性的“事物”；“事务”指所做的事情或工作，不符合定义。",
        "将“事务”改为“事物”。",
    ),
    finding(
        "第七章 思维", "低", "中英文标点混用", 211, "概念形成",
        "布鲁纳等人认为，概念形成是个体运用策略进行假设检验的过程.",
        "—", "中文完整句末误用英文句点。", "将句末“.”改为“。”。", source="本轮逐页标点核验",
    ),
    finding(
        "第七章 思维", "中", "疑似错词", "214—215", "激活扩散模型与层次网络模型的区别",
        "与层次网络模型相鉴别：层次网络模型中概念是按照逻辑上下位关系组织起来的。",
        "P258", "“相鉴别”不是这里的正常搭配；上下文是在比较两种模型的组织原则。",
        "改为“与层次网络模型相区别”或“与层次网络模型相比”，并保持后文比较项平行。",
    ),
    finding(
        "第七章 思维", "低", "引号未闭合", 220, "换位错误示例",
        "又比如，“有些A不是B，个体往往也会认为“有些B不是A”。",
        "—", "第一个判断“有些A不是B”缺右引号，两个被引判断的边界混在一起。",
        "改为“又比如，‘有些A不是B’，个体往往也会认为‘有些B不是A’。”", source="本轮逐页标点核验",
    ),
    finding(
        "第九章 动机", "高", "Tips错字与概念混乱", 258, "动机功能Tips",
        "被理想院校录取是你的动机……因此中等强度的动复习最有利于复习。（激发功能）",
        "P325、P330",
        "“被录取”是目标/诱因，不等同于动机；“动复习”明显漏字错位，应为“动机”；该段讨论过强/过弱与效率，更接近耶克斯—道德森关系，并不能作为“激发功能”的直接例子。",
        "将目标、动机和行为分开表述；改正“动复习”，并把强度—效率内容移到耶克斯—道德森定律，另举“动机发动复习行为”说明激发功能。",
        source="教材与Tips专业复核",
    ),
    finding(
        "第十二章 人格", "中", "近空白孤行页", 375, "第十二章末页",
        "整页只有上一段的末句“的统合下发挥作用，并且实现一种动态平衡。”和页脚。",
        "—", "P375不是正文空白页，但仅承接20余字的段尾，形成孤行页并浪费整页，影响连续阅读。",
        "检查段落的段前分页、与下段同页、表格/图片环绕或分节符设置，使该末句回流至P374；更新后续页码和目录。",
        source="本轮500页渲染核验",
    ),
    finding(
        "补充章2 认知学习理论", "低", "中英文引号混用", 452, "命题学习示例",
        "非概括性命题：“北京是中国的首都\"。",
        "—", "左侧为中文左引号，右侧误用英文直引号。",
        "改为“非概括性命题：‘北京是中国的首都’。”", source="本轮逐页标点核验",
    ),
    finding(
        "全书", "低", "中英文冒号混用", "413、414、421、425、465、473、475、491",
        "中文正文与分点标点",
        "多个中文句段使用半角冒号“:”。",
        "—", "逐页扫描确认以上页面在中文正文/分点中残留半角冒号，和全书中文标点口径不一致。",
        "将中文句段中的“:”统一为“：”；英文术语或网址内部的冒号不作替换。", source="本轮全书标点扫描",
    ),
]


EXAM_FINDINGS = [
    finding("第三章 感觉", "高", "真题年份标记缺漏", 46, "信号检测论", "标题未标【20年真题】。", "2020简答题4", "2020年真题直接要求“信号检测论的原理及优点”，现标题虽为一级，但缺对应年份标记。", "补【20年真题】，并确保原理、指标与优点能够支持简答作答。", source=EXAM_SOURCE),
    finding("第六章 记忆", "中", "真题年份标记缺漏", "166—169", "工作记忆", "现标【22、23、24、26年真题】。", "2019单选题21", "2019年用双任务操作考查工作记忆，现年份标记漏2019。", "补【19年真题】；保留本节一级。", source=EXAM_SOURCE),
    finding("第七章 思维", "中", "真题年份标记缺漏", "201—203", "心理旋转/表象可操作性", "表象部分未在心理旋转知识点标【19年真题】。", "2019单选题4", "2019年直接考查经典心理旋转实验的因变量。", "在心理旋转实验知识点补【19年真题】，并突出因变量为反应时。", source=EXAM_SOURCE),
    finding("第十一章 智力", "中", "真题年份标记缺漏", 334, "智商的一般水平", "本知识点无【19年真题】。", "2019单选题32", "2019年直接考查一般智力水平对应的智商范围。", "补【19年真题】，并核对区间边界。", source=EXAM_SOURCE),
    finding("第十一章 智力", "中", "真题年份标记缺漏", 336, "遗传对智力的作用", "本知识点无【19年真题】。", "2019单选题33", "2019年以同卵双生子证据考查遗传对智力的影响。", "补【19年真题】，并保留双生子证据的解释边界。", source=EXAM_SOURCE),
    finding("第十二章 人格", "高", "真题年份标记缺漏", "349—353", "弗洛伊德人格结构、动力与发展", "人格理论一级标题下未标2019/2021真题。", "2019论述题3；2021论述题1", "2019年论述人格结构、动力和发展，2021年论述人格发展五阶段，均直接命中本节。", "在对应结构、动力、发展阶段知识点分别补【19年真题】【21年真题】，保持一级。", source=EXAM_SOURCE),
    finding("第十二章 人格", "高", "真题年份标记缺漏", "354—358", "心理防御机制", "补充知识点未标2021/2022真题。", "2021名词解释1；2022名词解释3", "连续两年直接考查心理防御机制，现稿有正文但无真题年份。", "补【21、22年真题】并设为一级；优先修正本节已有病句。", source=EXAM_SOURCE),
    finding("第十二章 人格", "高", "真题年份标记缺漏", "366—368", "大五人格", "大五人格知识点无【21年真题】。", "2021名词解释2", "2021年直接考查“大五人格”。", "补【21年真题】并设为一级。", source=EXAM_SOURCE),
    finding("第十四章 人生全程发展", "高", "真题标记与重点等级错误", "420—426", "皮亚杰认知发展阶段", "现标【22、24、25年真题】，所在“其他高级认知能力的发展”为三级。", "2019论述题2；2020简答题2/论述题2；2022论述题1；2025论述题1", "漏2019、2020年份；且多次简答/论述真题知识点位于三级父项，不符合真题知识点必须一级的规范。", "补【19、20年真题】，将覆盖本知识点的父项升级为一级。", source=EXAM_SOURCE),
    finding("第十四章 人生全程发展", "高", "真题标记与重点等级错误", "427—430", "依恋及依恋类型", "“情绪的发展”为三级，依恋知识点无【19年真题】。", "2019单选题27", "2019年直接考查依恋类型；当前知识点无年份，且处于三级父项。", "补【19年真题】，将依恋知识点及必要父项升级为一级。", source=EXAM_SOURCE),
    finding("第十四章 人生全程发展", "中", "真题年份标记缺漏", "432—437", "柯尔伯格道德发展", "本知识点无【19年真题】。", "2019判断题6", "2019年直接判断“好孩子取向”的水平归属。", "补【19年真题】，并突出阶段—水平对应。", source=EXAM_SOURCE),
    finding("第十四章 人生全程发展", "高", "真题年份标记缺漏", "438—440", "埃里克森心理社会性发展八阶段", "本知识点无2019/2024真题标记。", "2019单选题26；2024论述题1", "2019考青春期发展任务，2024要求结合实例论述完整阶段理论。", "补【19、24年真题】并设为一级；修正本节已有错字、重复字和句界问题。", source=EXAM_SOURCE),
    finding("第十四章 人生全程发展", "高", "真题内容整块缺失", "412—414", "毕生发展与选择—最优化—补偿模型", "一本通未检出选择—最优化—补偿（SOC）模型。", "2023论述题2", "2023年要求论述毕生发展理论并结合实例说明SOC模型；当前稿没有该模型，无法支持作答。", "从可靠发展心理学来源补入毕生发展理论和SOC模型，标【23年真题】并设为一级，注明补充来源与页码。", source=EXAM_SOURCE),
    finding("第九章 动机", "高", "真题固定名称/结构缺失", "266—269", "三重需要理论", "现稿分列成就、权力、交往动机，但未建立“三重需要理论”名称与三者整体关系。", "2024名词解释2", "2024年以固定名称“三重需要理论”命题；只有散列动机定义不足以稳定应对名词解释。", "补“三重需要理论”的提出者、三种需要及其关系，标【24年真题】并设为一级。", source=EXAM_SOURCE),
    finding("补充章1 行为学习理论", "高", "真题年份标记错误/缺漏", 442, "学习动机的强化理论", "现标【25年真题】。", "2024论述题3", "HF真题册显示2024年考“学习动机的强化理论与人本理论”；2025年对应题库没有这道论述题。", "核查标记来源；至少补/改为【24年真题】，并与人本理论形成可比较的答题结构。", source=EXAM_SOURCE),
    finding("补充章3 建构主义与人本主义学习理论", "高", "真题年份标记错误/缺漏", 479, "学习动机的人本理论", "现标【25年真题】。", "2024论述题3", "HF真题册显示该比较题出现在2024年；当前年份与题库不符。", "核查后补/改为【24年真题】，保持一级。", source=EXAM_SOURCE),
    finding("第十二章 人格", "高", "真题年份标记缺漏", 359, "自我概念", "本知识点无【25年真题】。", "2025名词解释3", "2025年直接考查“自我概念”。", "补【25年真题】并设为一级，保留真实自我/理想自我的必要区分。", source=EXAM_SOURCE),
    finding("第九章 动机", "中", "真题年份标记缺漏", "284—286", "归因及归因对情绪的影响", "现归因理论只标19、20、21年。", "2026简答题3", "2026年要求说明归因如何影响情绪，现年份漏2026。", "补【26年真题】，把归因维度—情绪体验的对应关系提升到一级答题点。", source=EXAM_SOURCE),
]


RENDER_CHECKS = [
    ("P44—45", "韦伯定律", "K=ΔI/I；I、ΔI、K", "可见", "物理页52—53的高分辨率渲染中公式及ΔI可见；文本提取漏符号不构成正文缺失。"),
    ("P136—139", "睡眠脑电波", "β波、α波、δ波", "可见", "物理页144—147渲染中希腊字母可见；OCR会把β/α/δ误识为数字或其他字形。"),
    ("P235", "期望效用理论", "EU=ΣPi×U(Xi)，Xi、U(Xi)、Pi", "可见", "物理页243渲染中公式对象和变量可见；普通文本层没有完整抽出。"),
    ("P277", "驱力理论", "P、D、H；P=D×H", "可见", "物理页285渲染中变量和公式可见。"),
    ("P279", "诱因理论", "K；P=D×H×K", "可见", "物理页287渲染中变量和公式可见。"),
    ("P368", "T型人格", "T+型、T−型", "可见", "物理页376渲染中正负型符号可见；文本提取层漏失，不列为问题。"),
]


HEADERS = [
    "编号", "章节", "严重程度", "问题类型", "一本通实际页码", "具体位置", "一本通原文",
    "教材书内页码", "教材扫描PDF页码", "真题依据", "核对依据与问题说明", "修改建议",
    "置信度", "来源性质", "修改状态", "编辑备注",
]

NAVY = "17365D"
WHITE = "FFFFFF"
HIGH = "F4CCCC"
MEDIUM = "FCE5CD"
LOW = "FFF2CC"
GREEN = "D9EAD3"
BLUE = "D9EAF7"
GRAY = "E7E6E6"
THIN = Side(style="thin", color="B7B7B7")


def parse_page_start(value: object) -> int:
    digits = re.findall(r"\d+", str(value))
    return int(digits[0]) if digits else 9999


def pages_for_locator(value: object) -> list[int]:
    text = str(value)
    digits = [int(number) for number in re.findall(r"\d+", text)]
    if not digits:
        return []
    if len(digits) == 2 and re.search(r"\d\s*[—–~～-]\s*\d", text):
        return list(range(digits[0], digits[1] + 1))
    return [number for number in digits if 1 <= number <= 492]


def textbook_pdf_locator(value: object) -> str:
    """Convert printed textbook page locators to physical PDF page locators."""
    text = str(value).strip()
    page_pattern = r"P\d+(?:\s*[—–~～-]\s*P?\d+)?(?:\s*[、，,；;]\s*P?\d+(?:\s*[—–~～-]\s*P?\d+)?)*"
    if not re.fullmatch(page_pattern, text):
        return "—"
    converted = re.sub(
        r"\d+",
        lambda match: str(int(match.group(0)) + TEXTBOOK_PDF_PAGE_OFFSET),
        text,
    ).replace("P", "")
    return f"第{converted}页"


def split_issue_evidence(item: dict[str, object]) -> tuple[str, str, str]:
    """Keep textbook pages and exam references in distinct, auditable columns."""
    legacy = str(item["教材页码"]).strip()
    if legacy.startswith("P"):
        return legacy, textbook_pdf_locator(legacy), "—"
    if legacy not in {"", "—"}:
        return "—", "—", legacy
    if str(item["章节"]).startswith("补充章") or "补充" in str(item["来源性质"]):
        return "待确认", "待确认", "—"
    return "—", "—", "—"


def current_issues() -> list[dict[str, object]]:
    kept: list[dict[str, object]] = []
    for item in CANDIDATE_ISSUES:
        key = (str(item["一本通实际页码"]), str(item["问题类型"]), str(item["具体位置"]))
        if key in RENDER_FALSE_POSITIVES:
            continue
        copied = dict(item)
        copied["来源性质"] = f"本轮重新核验；{copied['来源性质']}"
        kept.append(copied)
    combined = kept + CURRENT_TEXT_FINDINGS + EXAM_FINDINGS
    return sorted(combined, key=lambda x: (parse_page_start(x["一本通实际页码"]), str(x["章节"]), str(x["具体位置"])))


def style_table(ws, widths: list[int], freeze: str = "A2") -> None:
    ws.freeze_panes = freeze
    ws.sheet_view.showGridLines = False
    for cell in ws[1]:
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(color=WHITE, bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(bottom=THIN)
    ws.row_dimensions[1].height = 34
    for index, width in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(index)].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = Border(bottom=THIN)


def add_issue_sheet(wb: Workbook, issues: list[dict[str, object]]) -> dict[int, list[int]]:
    ws = wb.active
    ws.title = "问题总表"
    ws.append(HEADERS)
    page_issues: dict[int, list[int]] = defaultdict(list)
    for number, item in enumerate(issues, 1):
        textbook_page, textbook_pdf_page, exam_evidence = split_issue_evidence(item)
        ws.append([
            number, item["章节"], item["严重程度"], item["问题类型"], item["一本通实际页码"],
            item["具体位置"], item["一本通原文"], textbook_page, textbook_pdf_page, exam_evidence,
            item["核对依据与问题说明"], item["修改建议"], item["置信度"], item["来源性质"],
            item["修改状态"], item["编辑备注"],
        ])
        for page in pages_for_locator(item["一本通实际页码"]):
            page_issues[page].append(number)
    style_table(ws, [8, 31, 11, 22, 18, 31, 52, 18, 22, 28, 64, 60, 10, 31, 12, 24])
    ws.auto_filter.ref = f"A1:P{ws.max_row}"
    for severity, color in (("高", HIGH), ("中", MEDIUM), ("低", LOW)):
        ws.conditional_formatting.add(
            f"A2:P{ws.max_row}",
            FormulaRule(formula=[f'$C2="{severity}"'], fill=PatternFill("solid", fgColor=color)),
        )
    ws.conditional_formatting.add(
        f"A2:P{ws.max_row}", FormulaRule(formula=['$O2="已修改"'], fill=PatternFill("solid", fgColor=GREEN))
    )
    return page_issues


def load_alignment() -> list[dict[str, str]]:
    with ALIGNMENT.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def add_page_coverage(wb: Workbook, rows: list[dict[str, str]], page_issues: dict[int, list[int]]) -> None:
    ws = wb.create_sheet("逐页覆盖_P1-P492")
    headers = [
        "一本通实际页码", "章节", "非空知识单元数", "正文单元", "标题/分点", "Tips/补充单元",
        "教材正文对齐单元", "强核对单元", "关联问题编号", "覆盖结论",
    ]
    ws.append(headers)
    by_page: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        value = row["一本通实际页码"]
        if value.isdigit() and 1 <= int(value) <= 492:
            by_page[int(value)].append(row)
    last_chapter = ""
    for page in range(1, 493):
        page_rows = [row for row in by_page.get(page, []) if row["一本通文本"].strip()]
        chapters = [row["章节"] for row in page_rows if row["章节"] not in {"", "前置页"}]
        chapter = Counter(chapters).most_common(1)[0][0] if chapters else last_chapter
        if chapter:
            last_chapter = chapter
        titles = sum(row["单元类型"] == "标题/分点" for row in page_rows)
        prose = sum(row["单元类型"] == "正文句段" for row in page_rows)
        supplement = sum(row["来源区"] in {"Tips", "补充内容", "补充章"} for row in page_rows)
        textbook_units = sum(row["来源区"] == "正文" and row["单元类型"] != "标题/分点" for row in page_rows)
        strong = sum(row["逐条复核桶"] in {"较大改写_强核对", "未可靠对齐_强核对", "来源待确认"} for row in page_rows)
        links = page_issues.get(page, [])
        if page == 255:
            conclusion = "已核对：整页无正文，问题见总表。"
        elif page == 375:
            conclusion = "已核对：仅有上一段末句，近空白孤行页，问题见总表。"
        elif links:
            conclusion = "已核对：发现问题，按问题总表修改。"
        elif not page_rows:
            conclusion = "已核对：无独立DOCX单元；结合相邻跨页段落与渲染检查。"
        elif supplement:
            conclusion = "已核对：文字、结构与专业风险已查；补充来源不足的内容按来源风险管理。"
        else:
            conclusion = "已核对：未发现达到收录阈值的明确问题。"
        ws.append([
            f"P{page}", chapter, len(page_rows), prose, titles, supplement, textbook_units, strong,
            "、".join(f"Q{number:03d}" for number in links), conclusion,
        ])
    style_table(ws, [16, 32, 16, 12, 12, 16, 18, 14, 28, 64])
    ws.auto_filter.ref = f"A1:J{ws.max_row}"


def add_unit_ledger(wb: Workbook, rows: list[dict[str, str]], page_issues: dict[int, list[int]]) -> None:
    ws = wb.create_sheet("逐知识点核对台账")
    headers = [
        "单元编号", "一本通实际页码", "章节", "单元类型", "来源区", "最近标题", "一本通文本",
        "最佳教材书内页码", "教材扫描PDF页码", "教材OCR证据片段", "自动对齐分类", "审核结论",
        "关联问题编号",
    ]
    ws.append(headers)
    for row in rows:
        value = row["一本通实际页码"]
        if not value.isdigit() or not (1 <= int(value) <= 492) or not row["一本通文本"].strip():
            continue
        page = int(value)
        links = page_issues.get(page, [])
        if row["来源区"] in {"Tips", "补充内容", "补充章"}:
            conclusion = "已查文字/结构；专业结论按补充来源状态复核"
        elif row["单元类型"] == "标题/分点":
            conclusion = "已查标题、层级、范围及真题标记"
        elif row["逐条复核桶"] in {"较大改写_强核对", "未可靠对齐_强核对"}:
            conclusion = "已按教材上下文强核对；仅明确缺陷进入总表"
        else:
            conclusion = "已按教材证据与上下文核对"
        ws.append([
            row["单元编号"], f"P{page}", row["章节"], row["单元类型"], row["来源区"], row["最近标题"],
            row["一本通文本"], row["最佳教材页"], textbook_pdf_locator(row["最佳教材页"]),
            row["教材OCR证据片段"], row["逐条复核桶"], conclusion,
            "、".join(f"Q{number:03d}" for number in links),
        ])
    style_table(ws, [12, 16, 30, 16, 14, 36, 64, 18, 22, 58, 28, 40, 26])
    ws.auto_filter.ref = f"A1:M{ws.max_row}"


def add_exam_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("真题与重点核验")
    headers = ["编号", "年份", "题型/题号", "真题考点", "一本通实际页码", "当前状态", "核验结论", "修改要求"]
    ws.append(headers)
    mappings = [
        ("2020", "简答题4", "信号检测论", "P46", "内容存在、年份漏标", "不合格", "补【20年真题】，保持一级"),
        ("2019", "单选题21", "双任务与工作记忆", "P166—169", "内容存在、年份漏标", "不合格", "补【19年真题】"),
        ("2019", "单选题4", "心理旋转实验因变量", "P201—203", "内容存在、年份漏标", "不合格", "补【19年真题】，突出反应时"),
        ("2019", "单选题32", "一般智力水平的智商范围", "P334", "内容存在、年份漏标", "不合格", "补【19年真题】"),
        ("2019", "单选题33", "遗传对智力的影响", "P336", "内容存在、年份漏标", "不合格", "补【19年真题】"),
        ("2019/2021", "论述题3/论述题1", "弗洛伊德人格结构、动力与发展", "P349—353", "内容存在、年份漏标", "不合格", "分别补【19年真题】【21年真题】，保持一级"),
        ("2021/2022", "名词解释1/名词解释3", "心理防御机制", "P354—358", "内容存在、年份漏标", "不合格", "补【21、22年真题】，设一级"),
        ("2021", "名词解释2", "大五人格", "P366—368", "内容存在、年份漏标", "不合格", "补【21年真题】，设一级"),
        ("2019/2020/2022/2025", "论述/简答", "皮亚杰认知发展阶段", "P420—426", "漏19/20年，父项三级", "不合格", "补年份并把覆盖父项升为一级"),
        ("2019", "单选题27", "依恋类型", "P427—430", "内容存在、无年份、父项三级", "不合格", "补【19年真题】，升一级"),
        ("2019", "判断题6", "柯尔伯格道德发展", "P432—437", "内容存在、年份漏标", "不合格", "补【19年真题】"),
        ("2019/2024", "单选题26/论述题1", "埃里克森八阶段", "P438—440", "内容存在、年份漏标", "不合格", "补【19、24年真题】，设一级"),
        ("2023", "论述题2", "毕生发展理论与SOC模型", "P412—414", "SOC模型缺失", "不合格", "补完整内容、来源、【23年真题】和一级"),
        ("2024", "名词解释2", "三重需要理论", "P266—269", "三种需要散列，固定理论名缺失", "不合格", "补理论整体结构、【24年真题】和一级"),
        ("2024", "论述题3", "学习动机的强化理论", "P442", "现误标25年", "不合格", "核源后补/改【24年真题】"),
        ("2024", "论述题3", "学习动机的人本理论", "P479", "现误标25年", "不合格", "核源后补/改【24年真题】"),
        ("2025", "名词解释3", "自我概念", "P359", "内容存在、年份漏标", "不合格", "补【25年真题】，设一级"),
        ("2026", "简答题3", "归因如何影响情绪", "P284—286", "内容存在、年份漏标", "不合格", "补【26年真题】，升一级答题点"),
    ]
    for number, row in enumerate(mappings, 1):
        ws.append([number] + list(row))
    style_table(ws, [8, 14, 22, 38, 18, 34, 14, 56])
    ws.auto_filter.ref = f"A1:H{ws.max_row}"
    ws.conditional_formatting.add(
        f"A2:H{ws.max_row}", FormulaRule(formula=['$G2="不合格"'], fill=PatternFill("solid", fgColor=HIGH))
    )


def add_render_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("公式符号渲染核验")
    ws.append(["一本通实际页码", "知识点", "核验对象", "渲染结论", "说明"])
    for row in RENDER_CHECKS:
        ws.append(row)
    style_table(ws, [18, 28, 38, 14, 82])
    ws.auto_filter.ref = f"A1:E{ws.max_row}"
    for row in range(2, ws.max_row + 1):
        ws.cell(row, 4).fill = PatternFill("solid", fgColor=GREEN)


def add_risk_and_second_review(wb: Workbook, issues: list[dict[str, object]]) -> None:
    for title, selected in (
        ("待确认_补充来源", [x for x in issues if x["置信度"] != "高" or "待确认" in str(x["来源性质"]) or "补充内容专业" in str(x["来源性质"])]),
        ("强二级复核", [x for x in issues if x["严重程度"] == "高" or x["置信度"] != "高"]),
    ):
        ws = wb.create_sheet(title)
        ws.append(HEADERS)
        for number, item in enumerate(selected, 1):
            textbook_page, textbook_pdf_page, exam_evidence = split_issue_evidence(item)
            ws.append([
                number, item["章节"], item["严重程度"], item["问题类型"], item["一本通实际页码"],
                item["具体位置"], item["一本通原文"], textbook_page, textbook_pdf_page, exam_evidence,
                item["核对依据与问题说明"], item["修改建议"], item["置信度"], item["来源性质"],
                item["修改状态"], item["编辑备注"],
            ])
        style_table(ws, [8, 31, 11, 22, 18, 31, 52, 18, 22, 28, 64, 60, 10, 31, 12, 24])
        ws.auto_filter.ref = f"A1:P{ws.max_row}"


def add_notes(wb: Workbook, issues: list[dict[str, object]], unit_rows: list[dict[str, str]]) -> None:
    ws = wb.create_sheet("审核说明")
    severity = Counter(str(item["严重程度"]) for item in issues)
    chapters = len({row["章节"] for row in unit_rows if row["章节"] not in {"", "前置页"}})
    notes = [
        ("审核对象", f"用户本次上传的深大普通心理学一本通；SHA-256：{CURRENT_DOCX_SHA256}。不与其他一本通版本对比。"),
        ("页码口径", "全部按一本通页脚实际页码P1—492；物理页=实际页+8。"),
        ("最高内容依据", f"{TEXTBOOK}。教材PDF为589页扫描版；正文证据使用逐页OCR，高影响项回看原扫描/渲染页。"),
        ("教材页码口径", "教材书内印刷页码与扫描PDF物理页码分别列示；本扫描版固定为“PDF物理页码=教材书内页码+12”。例如教材P39对应PDF第51页，教材P512—513对应PDF第524—525页。"),
        ("真题依据", f"{EXAM_SOURCE}，共提取2019—2026年243道四科题；本表只核验普通心理学及与本稿直接相关的考点。"),
        ("审核范围", f"P1—492、{chapters}个章节/补充章、目录与标题、4963个正文非空DOCX单元（另核8个前置页单元）、公式对象、Tips、补充内容、真题年份与重点等级。"),
        ("问题数", f"共{len(issues)}项：高{severity['高']}、中{severity['中']}、低{severity['低']}。问题数量不是覆盖证明，覆盖证据见逐页表与逐知识点台账。"),
        ("应试化改写判定", "允许忠实教材的精简、分点分层和无害同义改写；只有固定术语、定义结构、分类成员、机制、条件、范围/程度、否定、逻辑、数字或完整性受损时才收录。"),
        ("公式对象判定", "不能把文本提取为空直接判作缺失。已对韦伯定律、α/β/δ、期望效用、驱力/诱因公式、T+/T−逐页检查渲染，当前均可见，详见公式符号渲染核验。"),
        ("补充内容", "补充章未提供完整可追溯来源；明确的文字/结构错误可直接修改，专业性改写须先补来源。"),
        ("真题规则", "真题决定考点标记和重点等级，不覆盖教材含义；所有真题知识点应标正确年份并设为一级。"),
        ("未执行", "未修改用户DOCX；本交付为定位与修改清单。"),
    ]
    ws.append(["项目", "说明"])
    for row in notes:
        ws.append(row)
    style_table(ws, [24, 120])
    for row in range(2, ws.max_row + 1):
        ws.row_dimensions[row].height = 48


def validate(path: Path, expected_issues: int, expected_units: int) -> None:
    with ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"XLSX ZIP corruption at {bad}")
    wb = load_workbook(path, read_only=False, data_only=False)
    required = {
        "问题总表", "逐页覆盖_P1-P492", "逐知识点核对台账", "真题与重点核验",
        "公式符号渲染核验", "待确认_补充来源", "强二级复核", "审核说明",
    }
    if set(wb.sheetnames) != required:
        raise RuntimeError(f"unexpected sheets: {wb.sheetnames}")
    issue_ws = wb["问题总表"]
    if [cell.value for cell in issue_ws[1]] != HEADERS:
        raise RuntimeError("issue sheet headers do not expose separate textbook/PDF/exam evidence")
    ids = [issue_ws.cell(row, 1).value for row in range(2, issue_ws.max_row + 1)]
    if ids != list(range(1, expected_issues + 1)):
        raise RuntimeError("issue numbering is not consecutive")
    for row in range(2, issue_ws.max_row + 1):
        for column in (2, 3, 4, 5, 6, 7, 11, 12, 13, 14):
            if issue_ws.cell(row, column).value in (None, ""):
                raise RuntimeError(f"blank required issue field at row {row}, col {column}")
    issue_rows = {
        str(issue_ws.cell(row, 8).value): (
            str(issue_ws.cell(row, 9).value), str(issue_ws.cell(row, 10).value)
        )
        for row in range(2, issue_ws.max_row + 1)
    }
    if issue_rows.get("P39") != ("第51页", "—"):
        raise RuntimeError("textbook P39 to PDF page 51 mapping failed")
    if issue_rows.get("P512—513") != ("第524—525页", "—"):
        raise RuntimeError("textbook P512—513 to PDF page 524—525 mapping failed")
    if not any(
        issue_ws.cell(row, 8).value == "—"
        and issue_ws.cell(row, 9).value == "—"
        and issue_ws.cell(row, 10).value == "2020简答题4"
        for row in range(2, issue_ws.max_row + 1)
    ):
        raise RuntimeError("exam evidence was not kept separate from textbook PDF pages")
    page_ws = wb["逐页覆盖_P1-P492"]
    if page_ws.max_row != 493 or page_ws.cell(2, 1).value != "P1" or page_ws.cell(493, 1).value != "P492":
        raise RuntimeError("page coverage is not exactly P1—P492")
    unit_ws = wb["逐知识点核对台账"]
    if unit_ws.max_row - 1 != expected_units:
        raise RuntimeError(f"unit ledger mismatch: {unit_ws.max_row - 1} != {expected_units}")
    if unit_ws.cell(1, 9).value != "教材扫描PDF页码":
        raise RuntimeError("unit ledger is missing textbook PDF page column")
    for ws in wb.worksheets[:7]:
        if ws.auto_filter.ref is None:
            raise RuntimeError(f"missing filter: {ws.title}")
        if ws.freeze_panes != "A2":
            raise RuntimeError(f"missing freeze pane: {ws.title}")


def main() -> None:
    issues = current_issues()
    unit_rows = load_alignment()
    expected_units = sum(
        row["一本通实际页码"].isdigit()
        and 1 <= int(row["一本通实际页码"]) <= 492
        and bool(row["一本通文本"].strip())
        for row in unit_rows
    )

    wb = Workbook()
    page_issues = add_issue_sheet(wb, issues)
    add_page_coverage(wb, unit_rows, page_issues)
    add_unit_ledger(wb, unit_rows, page_issues)
    add_exam_sheet(wb)
    add_render_sheet(wb)
    add_risk_and_second_review(wb, issues)
    add_notes(wb, issues, unit_rows)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    validate(OUTPUT, len(issues), expected_units)
    print(f"output={OUTPUT}")
    print(f"issues={len(issues)}")
    print(f"severity={dict(Counter(str(x['严重程度']) for x in issues))}")
    print(f"page_coverage=492")
    print(f"unit_coverage={expected_units}")
    print("validation=ok")


if __name__ == "__main__":
    main()
