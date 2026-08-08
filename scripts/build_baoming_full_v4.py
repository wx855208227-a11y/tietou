from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import re
import zipfile

from docx import Document
from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_现行范围重编版V3.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_综合证据重编版V4.md"
EVIDENCE = ROOT / "analysis/华东心理学导论保命手册V4_押题证据矩阵.md"
SPEED = ROOT.parent / "inbox/feishu/om_x100b690fde5974a0b10d419cacda419/27_.docx"
YIBENTONG = Path("/tmp/tietou_hf_sources_20260725/ecnu_yibentong.docx")
PUBLIC_347 = Path("/tmp/tietou_hf_sources_20260725/public_347_questions.docx")
PUBLIC_312 = Path("/tmp/tietou_hf_sources_20260725/public_312_questions.docx")


# 二级并非按配额倒推，而是逐单元复核后保留的相对次重点。其余现行范围
# 单元满足“章节骨干／稳定采分结构／辅助题库或学校风格支持”中的组合条件。
SECONDARY_UNITS = {
    "第一章 心理学研究的对象、方法及其学科发展｜二、科学心理学的诞生",
    "第一章 心理学研究的对象、方法及其学科发展｜三、构造主义与机能主义",
    "第一章 心理学研究的对象、方法及其学科发展｜五、格式塔心理学",
    "第一章 心理学研究的对象、方法及其学科发展｜十一、测验法与信效度",
    "第二章 心理和行为的生物学基础｜一、神经元",
    "第二章 心理和行为的生物学基础｜二、神经冲动与突触传递",
    "第二章 心理和行为的生物学基础｜七、丘脑与下丘脑",
    "第三章 条件反射和学习｜一、学习的含义与特征",
    "第三章 条件反射和学习｜二、反射、反射弧与反射类型",
    "第三章 条件反射和学习｜五、信号系统与高级神经活动",
    "第三章 条件反射和学习｜八、顿悟学习",
    "第四章 意识和意识状态｜一、意识的含义、内容与功能",
    "第四章 意识和意识状态｜三、梦及其理论解释",
    "第四章 意识和意识状态｜八、注意分配的认知理论",
    "第五章 感觉｜二、常见感觉现象",
    "第五章 感觉｜五、主要视觉现象",
    "第六章 知觉｜三、时间知觉及其影响因素",
    "第六章 知觉｜四、运动知觉",
    "第六章 知觉｜八、错觉及其成因",
    "第七章 记忆｜三、记忆的神经生理机制",
    "第八章 表象和想象｜一、表象",
    "第八章 表象和想象｜二、想象",
    "第九章 思维｜三、概念组织理论",
    "第十章 言语｜二、言语活动的中枢机制",
    "第十一章 情绪和情感｜三、早期情绪理论",
    "第十二章 意志｜四、意志品质",
    "第十三章 动机｜五、动机的早期理论",
    "第十四章 技能｜一、技能及其与知识、习惯的关系",
    "第十五章 能力｜一、能力及其与知识、技能的关系",
    "第十五章 能力｜五、智力测验",
    "第十六章 人格｜八、影响人格形成与发展的因素",
    "第十八章 社会心理｜六、群体与群体规范",
    "第十八章 社会心理｜九、群体决策与去个性化",
}


GENERIC_BOLD = {
    "定义", "含义", "特点", "特征", "分类", "种类", "作用", "功能", "评价",
    "关系", "理论", "基本", "主要", "方面", "过程", "内容", "研究", "分析",
    "问题", "方法", "意义", "形成", "发展", "影响", "因素", "阶段", "类型",
    "表现", "提出", "包括", "比较", "说明", "例如", "综上", "心理学", "个体",
    "活动", "行为", "心理", "信息", "不同", "可以", "认为", "系统", "进行",
    "产生", "具有", "一个", "一种", "对象", "观点", "机制", "结果", "条件",
}


MANUAL_KEYWORDS = {
    "相关系数", "强度和方向", "安排、控制和操纵", "因变量变化", "观察、测量和记录",
    "自变量作用的结果", "脑和脊髓之外", "躯体神经系统和自主神经系统", "信息交换",
    "脑和脊髓", "分析和综合", "动作指令", "优势半球颞叶后部", "口头言语理解",
    "听觉性失语症", "胼胝体被切断", "大脑两半球功能分工", "高度专门化且相对独立",
    "认知功能的完整", "音高、响度和音色", "机体节律", "外部标尺", "有效记忆策略",
    "问题解决过程", "情绪与情感的区别", "需要层次", "教育与创造力启示",
    "加工处理", "不同阶段的经验", "较真实的资料", "成为条件刺激", "引起条件反应",
    "主体觉知", "没有意识到", "睡眠锭", "深度睡眠", "δ波", "头脑中重新呈现",
    "抽取事物的特征和属性", "归入同类", "多个部分假设", "同时进行验证",
    "逐一进行验证", "主要矛盾和关键因素", "常用功能", "其他可能用途",
    "激发并维持活动", "支持原立场的论据", "信息性影响",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    return "".join(node.text or "" for node in root.findall(f".//{{{namespace}}}t"))


def source_bold_phrases() -> list[str]:
    document = Document(SPEED)
    phrases: set[str] = set(MANUAL_KEYWORDS)
    for paragraph in document.paragraphs:
        buffer = ""
        for run in paragraph.runs:
            if run.bold:
                buffer += run.text
            elif buffer:
                phrases.add(buffer.strip())
                buffer = ""
        if buffer:
            phrases.add(buffer.strip())
    cleaned = set()
    for phrase in phrases:
        phrase = re.sub(r"^[（(]?\d+[.、）)]?", "", phrase).strip(" ：:；;，,。.（）()【】")
        if phrase in GENERIC_BOLD or not 2 <= len(phrase) <= 18:
            continue
        if "\n" in phrase or re.search(r"[：:；;。！？!?【】]", phrase):
            continue
        if re.fullmatch(r"[一二三四五六七八九十]+", phrase):
            continue
        cleaned.add(phrase)
    return sorted(cleaned, key=lambda item: (-len(item), item))


def parse_bold(line: str) -> tuple[str, list[tuple[int, int]]]:
    plain: list[str] = []
    intervals: list[tuple[int, int]] = []
    index = 0
    bold_start: int | None = None
    while index < len(line):
        if line.startswith("**", index):
            if bold_start is None:
                bold_start = len(plain)
            else:
                intervals.append((bold_start, len(plain)))
                bold_start = None
            index += 2
            continue
        plain.append(line[index])
        index += 1
    if bold_start is not None:
        raise AssertionError(f"未闭合的加粗标记：{line}")
    return "".join(plain), intervals


def render_bold(plain: str, intervals: list[tuple[int, int]]) -> str:
    intervals = sorted(set(intervals))
    for left, right in zip(intervals, intervals[1:]):
        assert left[1] <= right[0], (plain, left, right)
    starts: dict[int, int] = defaultdict(int)
    ends: dict[int, int] = defaultdict(int)
    for start, end in intervals:
        if start < end:
            starts[start] += 1
            ends[end] += 1
    result: list[str] = []
    for index, character in enumerate(plain):
        if starts[index]:
            result.append("**")
        result.append(character)
        if ends[index + 1]:
            result.append("**")
    return "".join(result)


def overlaps(interval: tuple[int, int], others: list[tuple[int, int]]) -> bool:
    return any(interval[0] < other[1] and other[0] < interval[1] for other in others)


def mark_keywords(line: str, candidates: list[str]) -> str:
    plain, intervals = parse_bold(line)
    expansion = plain.find("【扩容（选用）：")
    main_end = expansion if expansion >= 0 else len(plain)
    if re.match(r"^(?:\d+\.\s*|（\d+）\s*)", plain):
        colon = plain.find("：")
        content_start = colon + 1 if 0 <= colon < main_end else plain.find(" ") + 1
    else:
        content_start = 0
    if content_start >= main_end:
        return line

    clauses = []
    start = content_start
    for match in re.finditer(r"[；。]", plain[content_start:main_end]):
        end = content_start + match.end()
        clauses.append((start, end))
        start = end
    if start < main_end:
        clauses.append((start, main_end))

    chosen = list(intervals)
    definition_line = "【名词解释：" in plain[:main_end]
    for clause_start, clause_end in clauses:
        visible = re.sub(r"\s+", "", plain[clause_start:clause_end]).strip("，；。；：")
        if len(visible) < 5:
            continue
        existing = [item for item in chosen if item[0] < clause_end and clause_start < item[1]]
        desired = 1 if len(visible) <= 26 else 2 if len(visible) <= 65 else 3
        if definition_line and len(visible) >= 12:
            desired = max(desired, 2)
        needed = max(0, desired - len(existing))
        if not needed:
            continue
        options: list[tuple[int, int, str]] = []
        for phrase in candidates:
            search_at = clause_start
            while True:
                position = plain.find(phrase, search_at, clause_end)
                if position < 0:
                    break
                item = (position, position + len(phrase), phrase)
                if not overlaps((item[0], item[1]), chosen):
                    options.append(item)
                search_at = position + 1
        options.sort(key=lambda item: (-len(item[2]), item[0]))
        for start_at, end_at, _ in options:
            interval = (start_at, end_at)
            if overlaps(interval, chosen):
                continue
            chosen.append(interval)
            needed -= 1
            if not needed:
                break
    return render_bold(plain, chosen)


def relevel(text: str) -> str:
    chapter = ""
    output = []
    seen = set()
    for line in text.splitlines():
        if line.startswith("# 第"):
            chapter = line[2:].strip()
        match = re.match(r"^(## )(.+)【(?:一级|二级)】$", line)
        if match:
            key = f"{chapter}｜{match.group(2)}"
            level = "二级" if key in SECONDARY_UNITS else "一级"
            line = f"{match.group(1)}{match.group(2)}【{level}】"
            seen.add(key)
        output.append(line)
    assert SECONDARY_UNITS <= seen, sorted(SECONDARY_UNITS - seen)
    assert len(seen) == 117, len(seen)
    return "\n".join(output) + "\n"


def build_markdown() -> str:
    original = SOURCE.read_text(encoding="utf-8")
    body = original[original.index("# 第一章 "):]
    header = """# 华东师范大学347心理学导论保命手册

## 全本·综合证据重编版V4

> 每道押题均配置一份可直接背写的独立答案，按“总起—分点—总结”组织。括号外是必须优先掌握的基础采分点；`【名词解释：……】`标在完整定义句末；`【扩容（选用）：……】`紧跟所扩充的采分点，可按题目分值和时间选写。

> 一级、二级由华东历年命题信号、现行考纲与教材核心度、知识点可考性、其他347与312真题支持、华东命题风格和答案复用价值综合判断。既往题型不是未来题型上限；最终比例只用于检查分布是否异常，不作为强制配额。

> 押题依据华东的命题思路和侧重点设计，再用现行范围、稳定采分结构及辅助题库交叉验证。学生版不展示内部证据矩阵；没有可核实原题的年份和题型不作直接考过声明。

> 全书按“不可替换性—可还原性—最小充分”标记关键词：每个独立采分点至少保留一组能够还原对象、条件／机制、关系方向或结果判断的关键词。全书采用黑白打印版式，不使用颜色、底纹、下划线或斜体。

> 容量依据现有题型进行理论校准，尚未完成真实学员15—20分钟计时手写测试；正式印刷前仍需结合学员手写结果微调。

> 本手册沿用速背手册原章节序号；原速背手册未收录第十七章，因此正文由第一至第十六章及第十八章构成。现行考纲与教材范围是内容准入门槛，旧真题只用于范围内分级和命题，不据此恢复速背手册与一本通已经筛除的内容。

---

"""
    text = relevel(header + body)
    candidates = source_bold_phrases()
    lines = []
    in_body = False
    for line in text.splitlines():
        if line.startswith("# 第一章 "):
            in_body = True
        if (
            in_body
            and line
            and not line.startswith("#")
            and line != "---"
            and not line.startswith(">")
        ):
            line = mark_keywords(line, candidates)
        lines.append(line)
    return "\n".join(lines) + "\n"


def question_records(markdown: str) -> list[dict[str, str]]:
    records = []
    chapter = unit = level = ""
    for line in markdown.splitlines():
        if line.startswith("# 第"):
            chapter = line[2:].strip()
        unit_match = re.match(r"^## (.+)【(一级|二级)】$", line)
        if unit_match:
            unit, level = unit_match.groups()
        question_match = re.match(r"^### 押题(\d+)【([^】]+)】(.+)$", line)
        if question_match:
            number, question_type, stem = question_match.groups()
            records.append({
                "chapter": chapter,
                "unit": unit,
                "level": level,
                "number": number,
                "type": question_type,
                "stem": stem.strip(),
            })
    return records


def stem_terms(stem: str) -> list[str]:
    terms = []
    for group in re.findall(r"\*\*(.+?)\*\*", stem):
        for term in re.split(r"[、，。及与和]", group):
            term = term.strip()
            if len(term) >= 2 and term not in GENERIC_BOLD:
                terms.append(term)
    if not terms:
        plain = stem.replace("**", "")
        terms.extend(re.findall(r"[\u4e00-\u9fffA-Za-z—]{3,12}", plain)[:2])
    return list(dict.fromkeys(terms))


def examability(stem: str, question_type: str) -> str:
    plain = stem.replace("**", "")
    if "比较" in plain or "关系" in plain:
        return "比较双方、维度与关系方向明确，可形成稳定的并列采分点"
    if any(word in plain for word in ("结合实例", "如何", "应用")) or plain.startswith("分析"):
        return "概念、机制与应用对象明确，可按“理论—对应—结论”稳定评分"
    if question_type == "论述":
        return "核心理论可分为定义、主要观点、关系／评价等多角度采分模块"
    return "题干对象和分点边界明确，可由定义、构成／机制和结论直接评分"


def school_style(stem: str, question_type: str) -> str:
    plain = stem.replace("**", "")
    if any(word in plain for word in ("结合实例", "如何", "应用")) or plain.startswith("分析"):
        return "概念与情境应用结合，符合华东重视迁移和解释的设问方式"
    if "比较" in plain or "关系" in plain:
        return "围绕易混概念作多维辨析，符合华东的关系型设问方式"
    if question_type == "论述":
        return "以章节骨干理论组织多角度展开，符合高分主观题的结构要求"
    return "以核心概念带出组成、规律或机制，符合基础主观题的直接设问方式"


def evidence_matrix(markdown: str) -> str:
    public_347 = docx_text(PUBLIC_347)
    public_312 = docx_text(PUBLIC_312)
    target_2018_2020 = "\n".join(Document(PUBLIC_347).paragraphs[index].text for index in range(1065, 1401))
    records = question_records(markdown)
    rows = []
    for index, record in enumerate(records, start=1):
        terms = stem_terms(record["stem"])
        target_hits = [term for term in terms if term in target_2018_2020][:3]
        hits_347 = [term for term in terms if term in public_347][:3]
        hits_312 = [term for term in terms if term in public_312][:3]
        if target_hits:
            target = "可核实2018—2020华东题册检出相关术语：" + "、".join(target_hits)
        else:
            target = "可核实2018—2020华东题册未直接检出题干核心术语；其他年份本轮未逐条核实"
        auxiliary_parts = []
        if hits_347:
            auxiliary_parts.append("347题库检出：" + "、".join(hits_347))
        if hits_312:
            auxiliary_parts.append("312题库检出：" + "、".join(hits_312))
        auxiliary = "；".join(auxiliary_parts) if auxiliary_parts else "两套辅助题库未按题干核心术语直接检出"
        core = (
            "速背与一本通现行正文范围内的章节骨干"
            if record["level"] == "一级"
            else "速背与一本通现行正文范围内的局部或补充模块"
        )
        conclusion = (
            f"保留为{record['level']}；预测为{record['type']}。"
            + ("综合核心度、采分结构和风格证据优先掌握" if record["level"] == "一级" else "现行范围内保留，但直接信号或复用价值相对较弱")
        )
        stem = record["stem"].replace("**", "").replace("|", "／")
        rows.append(
            f"| {index} | {record['chapter']} | {record['unit']}·押题{record['number']}【{record['type']}】{stem} | "
            f"{target} | {core} | {examability(record['stem'], record['type'])} | {auxiliary}（术语检出只作可考性支持） | "
            f"{school_style(record['stem'], record['type'])} | {conclusion} |"
        )
    hashes = {
        "速背手册": digest(SPEED),
        "一本通": digest(YIBENTONG),
        "347题库": digest(PUBLIC_347),
        "312题库": digest(PUBLIC_312),
    }
    header = """# 华东心理学导论保命手册V4押题证据矩阵

## 使用边界

- 本表是编制端证据账本，不进入学生版。
- 目标院校直接信号只使用本轮可在题库正文中逐条检索的2018—2020华东题目；其他年份没有原题可逐条核实时，不补造年份或题型。
- “术语检出”只能证明题库存在相关考查线索，不能等同于同题、同题型或目标院校直接考过；最终题型还须结合现行核心度、采分结构和华东风格判断。
- 既往题型不是预测上限，但辅助题库的大题也不会被无条件移植。

## 输入文件哈希

""" + "\n".join(f"- {name}：`{value}`" for name, value in hashes.items()) + """

## 逐题证据

| 序号 | 章节 | 押题 | 华东命题信号 | 考纲／教材核心度 | 知识点可考性 | 其他347／312支持 | 华东风格 | 预测题型与结论 |
|---:|---|---|---|---|---|---|---|---|
"""
    return header + "\n".join(rows) + "\n"


def main() -> None:
    assert len(SECONDARY_UNITS) == 33
    for path in (SOURCE, SPEED, YIBENTONG, PUBLIC_347, PUBLIC_312):
        assert path.is_file(), path
    markdown = build_markdown()
    OUTPUT.write_text(markdown, encoding="utf-8")
    EVIDENCE.write_text(evidence_matrix(markdown), encoding="utf-8")
    print(OUTPUT)
    print(EVIDENCE)


if __name__ == "__main__":
    main()
