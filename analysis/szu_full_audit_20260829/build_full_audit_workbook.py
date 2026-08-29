#!/usr/bin/env python3
"""Build the final 2026-08-29 SZU General Psychology audit workbook.

The earlier workbook is used only as a library of source-rechecked findings.
This entry point binds the findings to the fresh 2026-08-29 full-document
ledger, adds omission checks that paragraph-to-paragraph alignment cannot
detect, and embeds the complete unit ledger in the deliverable.
"""

from __future__ import annotations

import importlib.util
import zipfile
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill
from openpyxl.utils import get_column_letter


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LEGACY_BUILDER = REPO / "analysis/szu_exhaustive_20260818/build_final_review.py"
OUTPUT = REPO / "analysis/深大普通心理学一本通_全量审核表_20260829_实际页码.xlsx"


def load_base():
    spec = importlib.util.spec_from_file_location("szu_audit_base", LEGACY_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LEGACY_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base()
base.ALIGNMENT = HERE / "unit_alignment.tsv"
base.LEDGER = HERE / "unit_review_ledger.tsv"
base.OUTPUT = OUTPUT


def add_issue(
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
    source: str = "本轮独立复核",
    exam: str = "—",
):
    return base.issue(
        chapter,
        severity,
        kind,
        page,
        location,
        original,
        textbook_page,
        explanation,
        suggestion,
        confidence=confidence,
        source=source,
        exam=exam,
    )


# These findings were established from the current DOCX itself, the sixth
# edition textbook pages, and/or the extracted SZU exam source.  They target
# omissions and cross-section conceptual faults that short-string mutation
# matching cannot discover reliably.
ADDITIONAL_FINDINGS = [
    add_issue(
        "第一章 心理学的研究对象和方法",
        "中",
        "补充概念定义不准确",
        "9",
        "双盲控制",
        "是指主试和被试都不知道自变量是怎样被控制的。",
        "—",
        "双盲的关键是主试与被试均不知道被试所属条件、处理或关键信息，并非笼统地“不知道自变量怎样被控制”。现定义既不准确，也没有给出补充来源。",
        "按实验设计的规范定义重写为“主试和被试均不知道被试所处的实验条件/接受的处理”，并标明所据实验心理学教材及页码。",
        confidence="中",
        source="补充内容/来源待确认",
    ),
    add_issue(
        "第一章 心理学的研究对象和方法",
        "高",
        "教材整节漏编",
        "12—13",
        "研究方法之后、心理学史之前",
        "现稿讲完“研究中的因果关系和相关关系”后，直接进入“四、心理学的过去和现在”。",
        "P20",
        "主教材在此处另有完整专节“五、心理学研究中的伦理道德”，包含知情同意、退出权、隐私保护、避免伤害、动物研究伦理及学术诚信；现稿整节未编入。",
        "在研究方法部分补入“心理学研究中的伦理道德”，按教材分点保留知情同意、退出权、隐私、无伤害、动物伦理和学术诚信等关键词，并相应调整标题序号。",
        source="主教材章节覆盖核验",
    ),
    add_issue(
        "第四章 知觉",
        "低",
        "真题标记格式不规范",
        "82",
        "知觉系统的整合和完善功能",
        "（2）知觉系统的整合和完善功能【19年、26真题】",
        "P131",
        "2019单选题16和2026单选题9均直接考“相似性”。现稿已标两个年份，并非漏标；问题是“年”位置不符合全书【xx年真题】格式。",
        "统一为“【19、26年真题】”；相似性正文保留，所在一级层级无需重复堆叠标记。",
        source="真题标注格式核验",
        exam="2019单选题16；2026单选题9",
    ),
    add_issue(
        "第九章 动机",
        "中",
        "错词/分类成员错误",
        "260",
        "自然需要",
        "包括饮食、运动、休息、睡眠、排泄、嗣后等需要。",
        "P326",
        "“嗣后”意为以后，不是需要类别；主教材列举的是“饮食、运动、休息、睡眠、性的需要等”。现稿出现无意义成员并改变教材清单。",
        "按教材改为“包括饮食、运动、休息、睡眠、性的需要等”。如需保留“排泄”，须确认补充来源后另行加入。",
        source="主教材逐条对照",
    ),
    add_issue(
        "第九章 动机",
        "中",
        "错别字改变句意",
        "286",
        "归因理论Tips—稳定性影响未来预期",
        "由于这次考得好所以他预期下次自己也会又好成绩。",
        "—",
        "“会又好成绩”句法不成立，结合上下文应为“会有好成绩”。",
        "改为“由于这次考得好，所以他预期自己下次也会有好成绩”。",
        source="本轮Tips文字核验",
    ),
    add_issue(
        "第十章 情绪",
        "高",
        "教材与真题内容整块缺失",
        "296—297",
        "情绪外部表现—面部表情",
        "现稿只说明面部、姿态、语调三类表情，未讲面部表情的跨文化一致性与文化差异。",
        "P366—367",
        "主教材明确说明基本面部表情具有跨文化一致性，同时表情识别又存在地域、种族等文化差异。2019单选题43直接考查这两方面并存，现稿不能支持作答。",
        "在面部表情后补入“基本表情具有跨文化一致性；表情识别也存在文化差异和群体内优势”，标【19年真题】并按一级真题点处理。",
        source="主教材与深大真题联合核验",
        exam="2019单选题43",
    ),
    add_issue(
        "第十章 情绪",
        "中",
        "固定用语误写",
        "296",
        "面部表情",
        "面部表情是面部肌肉变化所组成的模式，是鉴定情绪的主要依据。",
        "P355",
        "主教材固定表述为“鉴别情绪的主要依据”。“鉴定”通常指作出专业评定，不是此处对情绪类别加以辨认的用语。",
        "将“鉴定情绪”改为“鉴别情绪”。",
        source="主教材逐条对照",
    ),
    add_issue(
        "第十章 情绪",
        "低",
        "助词误用",
        "321",
        "合理宣泄策略Tips",
        "小明适当的向父母表露出自己的沮丧……",
        "—",
        "“适当”在句中修饰动词“表露”，应使用状语标志“地”。",
        "改为“小明适当地向父母表露出自己的沮丧……”。",
        source="本轮Tips文字核验",
    ),
    add_issue(
        "第十一章 智力",
        "高",
        "真题内容整块缺失",
        "334",
        "智力的测量",
        "现稿仅写“智力的测量（详见测量心理学）”，没有心理年龄/智力年龄及比率智商内容。",
        "P402—403",
        "主教材完整说明心理年龄（智力年龄）的定义、绝对水平含义及其与实际年龄、比率智商的关系。2026年深大以“心理年龄”直接命题，不能只用跨科目提示替代正文。",
        "补入心理年龄的定义和必要辨析，保留“根据受测者在各年龄水平答对题目所确定的年龄”等教材关键词；标【26年真题】并设为一级。",
        source="主教材与深大真题联合核验",
        exam="2026名词解释5",
    ),
    add_issue(
        "第十一章 智力",
        "高",
        "真题方法内容整块缺失",
        "336",
        "遗传对智力的作用",
        "现稿只有“遗传会影响生理发展、智力发展和人格特质”的结论，没有行为遗传学研究方法或双生子设计。",
        "P416—417",
        "主教材在此用同卵/异卵双生子、收养关系和分开抚养的同卵双生子说明遗传研究逻辑；2021年考行为遗传学研究方法，2026年又直接考双生子设计及适用问题。现稿缺少方法、比较逻辑与适用范围。",
        "以教材的双生子和收养研究为证据，补“家系/双生子/收养研究”的基本比较逻辑；双生子设计的完整定义与适用问题须核定可靠行为遗传学或发展心理学来源。标【21、26年真题】并设为一级。",
        source="主教材与深大真题联合核验；方法定义来源待确认",
        exam="2021简答题3；2026简答题1",
    ),
    add_issue(
        "第十三章 学习",
        "低",
        "助词误用",
        "384",
        "正迁移Tips",
        "因此他很快的学会了驾驶摩托车，这就是正迁移。",
        "—",
        "“很快”修饰动词“学会”，应使用“地”。",
        "改为“因此他很快地学会了驾驶摩托车……”。",
        source="本轮Tips文字核验",
    ),
    add_issue(
        "第十三章 学习",
        "高",
        "理论体系与例子错置",
        "395—397",
        "操作性条件作用的主要规律",
        "在“消退、维持、分化、泛化”下继续使用铃声—唾液、听脚步声等经典条件作用例子。",
        "P477—482",
        "铃声引发唾液是经典条件作用，不是由行为后果控制的操作性反应。现稿把刚在经典条件作用部分使用过的例子又放入操作性条件作用，学员会混淆两套学习机制。",
        "若保留这些操作性概念，应改用“按杆后是否得到食物”等行为—后果例子；否则将现有铃声—唾液例子移回经典条件作用，并按来源重建本节结构。",
        source="主教材机制与Tips联合核验",
    ),
    add_issue(
        "第十三章 学习",
        "高",
        "强化与强化物概念混淆",
        "397",
        "强化的定义及内部/外部强化物",
        "强化：能够增强反应率的后果。内部强化物为人们因受到内部动机的驱使而从事某种活动。",
        "P482",
        "“能够增强反应率的后果”更接近强化物，强化本身是使行为以后出现概率增加的过程；所谓“内部强化物”的句子没有定义强化物，反而把强化物与内部动机/活动混在一起。第六版本页只区分正强化和负强化，未使用这组内部/外部强化物分类。",
        "先区分“强化”与“强化物”；删除或移出这组无本教材依据且定义错误的分类。若负责人确需保留，须核定可靠来源、放入补充内容并重写定义。",
        source="主教材核心概念核验",
        exam="2019、2026年相关强化考题",
    ),
    add_issue(
        "第十三章 学习",
        "中",
        "负强化物指认错误",
        "398",
        "正负强化Tips",
        "认真写作业，就可以不用做家务。做家务就是负强化物。",
        "P482",
        "行为之后被移除的厌恶刺激才构成负强化条件。例中用于增强写作业行为的是“免除/不用做家务”，不是把“做家务”本身呈现出来。",
        "改为“认真写作业后可以免除家务；免除家务使认真写作业的频率增加，属于负强化”。",
        source="主教材概念与Tips核验",
    ),
    add_issue(
        "第十三章 学习",
        "高",
        "固定术语与分类逻辑错误",
        "398—399",
        "强化程序",
        "间隔强化：即四种延缓强化程序。表中列固定时间、固定比例、可变时间、可变比例程序。",
        "P482",
        "“间隔/间歇强化”是并非每次反应都强化；“延缓强化”是行为与强化物之间存在时间延迟，二者不是同一维度。主教材分列连续/间隔、固定/变化比例、固定/变化时间，并另讲即时/延迟强化。",
        "将“延缓强化程序”改为“间歇（部分）强化程序”，再按统一教材口径列四种程序；把即时/延迟强化另作一组，不与间歇强化混同。",
        source="主教材分类结构核验",
    ),
    add_issue(
        "第十三章 学习",
        "高",
        "固定术语错误",
        "399",
        "斯金纳箱Tips结论",
        "他称之为“操作条件性刺激”。",
        "P481—482",
        "主教材的固定名称是“操作性条件作用”；教材没有“操作条件性刺激”这一术语。现稿把行为结果影响以后反应概率的作用误命名为一种“刺激”。",
        "改为“这种由行为结果改变该行为以后出现概率的过程称为操作性条件作用”，并删除后面口语化、循环定义式的解释。",
        source="主教材固定术语核验",
    ),
    add_issue(
        "第十四章 人生全程发展",
        "高",
        "真题研究设计内容整块缺失",
        "413—414",
        "个体发展的领域与分期",
        "现稿只有按发展领域划分的“横向视角”和按年龄分期的“纵向视角”，没有横断研究、纵向研究的定义与优缺点。",
        "P497",
        "“横向/纵向视角”不是“横断/纵向研究设计”的替代内容。深大2019年已考设计选择，2022年考纵向研究，2023年考横断研究定义与优缺点；第六版只在本页讲发展领域与年龄分期，未系统提供研究设计答案。",
        "从可靠发展心理学教材补入横断研究与纵向研究的定义、优缺点和适用问题，标【19、22、23年真题】并设为一级；明确补充来源和页码。",
        source="深大真题核验；补充来源待确认",
        exam="2019判断题5；2022名词解释5；2023简答题2",
    ),
]


base.EXTRA = list(base.EXTRA) + ADDITIONAL_FINDINGS


def classification(row: dict[str, str]) -> str:
    text = " ".join(str(row.get(key, "")) for key in ("问题类型", "置信度", "来源性质", "核对依据与问题说明"))
    if "整块缺失" in row["问题类型"] or "整节漏编" in row["问题类型"]:
        return "确定错误"
    if any(token in text for token in ("疑似", "待确认", "风险")):
        return "疑似问题"
    if row["问题类型"] in {"表格跨页", "物理术语不统一"}:
        return "优化建议"
    return "确定错误"


def add_classification_and_ledger(findings: list[dict[str, str]], ledger: list[dict[str, str]]) -> None:
    workbook = load_workbook(OUTPUT)
    issues = workbook["审核问题清单"]
    issues.cell(1, 17, "判断层级")
    for row_number, finding in enumerate(findings, 2):
        issues.cell(row_number, 17, classification(finding))
    issues.column_dimensions["Q"].width = 14
    for cell in issues[1]:
        cell.fill = PatternFill("solid", fgColor=base.NAVY)
        cell.font = Font(name="微软雅黑", size=10, bold=True, color=base.WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(left=base.GRID, right=base.GRID, top=base.GRID, bottom=base.GRID)
    for row in issues.iter_rows(min_row=2, min_col=17, max_col=17):
        row[0].font = Font(name="微软雅黑", size=10)
        row[0].alignment = Alignment(vertical="top", wrap_text=True)
        row[0].border = Border(left=base.GRID, right=base.GRID, top=base.GRID, bottom=base.GRID)
    issues.auto_filter.ref = f"A1:Q{issues.max_row}"

    ledger_sheet = workbook.create_sheet("逐条覆盖底账")
    headers = [
        "单元编号", "一本通实际页码", "章节", "DOCX定位", "单元类型", "来源区", "最近标题",
        "一本通文本", "最佳教材书内页码", "教材扫描PDF页码", "自动对齐分类", "逐条审核结论", "关联问题编号",
    ]
    ledger_sheet.append(headers)
    for row in ledger:
        conclusion = row["逐条审核结论"]
        if conclusion.startswith("通过_"):
            conclusion = conclusion.replace("通过_", "已覆盖复核_", 1)
        elif conclusion.startswith("已逐条核对_"):
            conclusion = conclusion.replace("已逐条核对_", "已覆盖复核_", 1)
        ledger_sheet.append([row[header] if header != "逐条审核结论" else conclusion for header in headers])

    base.style_table(ledger_sheet, [12, 16, 32, 18, 16, 14, 42, 80, 20, 21, 29, 46, 20])
    ledger_sheet.auto_filter.ref = f"A1:M{ledger_sheet.max_row}"
    ledger_sheet.freeze_panes = "A2"
    for column in (1, 2, 4, 5, 6, 9, 10, 11, 13):
        for cells in ledger_sheet.iter_cols(min_col=column, max_col=column, min_row=2):
            for item in cells:
                item.alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)

    notes = workbook["审核说明"]
    for row in notes.iter_rows(min_row=2):
        if row[0].value == "逐条覆盖":
            row[1].value = (
                f"当前稿共5593个结构记录；正文P1—P492共{len(ledger)}个非空审核单元，"
                "全部进入‘逐条覆盖底账’。底账结合教材OCR对齐、短差异扫描、章节缺漏核对、"
                "真题命中核对与高风险原页复核；未列为问题表示未达到本表收录阈值。"
            )
        elif row[0].value == "交付性质":
            row[1].value = "本文件是对当前上传DOCX的独立定位与修改建议表，未与其他一本通版本比较，也未直接修改用户DOCX。"
    notes.append(("判断层级", "确定错误=证据明确，可直接改；疑似问题=现稿有风险但补充来源或负责人判断仍需确认；优化建议=不影响核心事实但建议改善呈现。"))
    notes.auto_filter.ref = notes.dimensions
    notes.column_dimensions[get_column_letter(2)].width = 120

    workbook.save(OUTPUT)


def validate_final(findings: list[dict[str, str]], ledger: list[dict[str, str]]) -> None:
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
    workbook = load_workbook(OUTPUT, read_only=False, data_only=False)
    assert workbook.sheetnames == ["审核问题清单", "章节覆盖", "审核说明", "逐条覆盖底账"]
    issues = workbook["审核问题清单"]
    assert issues.max_row == len(findings) + 1
    assert issues.max_column == 17
    assert issues.cell(1, 17).value == "判断层级"
    assert {issues.cell(row, 17).value for row in range(2, issues.max_row + 1)} == {"确定错误", "疑似问题", "优化建议"}
    assert workbook["逐条覆盖底账"].max_row == len(ledger) + 1 == 4964
    required = {
        "心理学研究中的伦理道德",
        "心理年龄",
        "双生子设计",
        "内部强化物",
        "操作条件性刺激",
        "横断研究",
        "跨文化一致性",
    }
    joined = "\n".join(str(cell.value or "") for row in issues.iter_rows() for cell in row)
    assert all(term in joined for term in required)
    assert all(str(issues.cell(row, 5).value or "").strip() for row in range(2, issues.max_row + 1))


def main() -> None:
    findings = base.user_rows(base.calibrate_findings())
    ledger = base.build_ledger(findings)
    base.build_workbook(findings, ledger)
    base.validate(findings, ledger)
    add_classification_and_ledger(findings, ledger)
    validate_final(findings, ledger)
    counts = Counter(row["严重程度"] for row in findings)
    classes = Counter(classification(row) for row in findings)
    print(f"output={OUTPUT}")
    print(f"ledger={base.LEDGER} units={len(ledger)}")
    print(f"findings={len(findings)} high={counts['高']} medium={counts['中']} low={counts['低']}")
    print("classification=" + ",".join(f"{key}:{value}" for key, value in sorted(classes.items())))
    print("validation=ok")


if __name__ == "__main__":
    main()
