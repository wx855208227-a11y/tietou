from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_现行范围重编版V3.md"
V4 = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_综合证据重编版V4.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_采分关键词精校版V5.md"


# 这些词单独加粗时无法还原采分点。它们只有进入完整术语、关系或结果短语后
# 才能成为关键词。
FRAGMENT_WORDS = {
    "一般", "不能", "不同", "主要", "基本", "直接", "间接", "相对", "整体",
    "简单", "复杂", "准确", "典型", "重要", "高级", "积极", "主动", "容易",
    "所有", "有限", "无限", "全部", "两个", "三对", "最后", "最先", "后续",
    "研究", "分析", "说明", "解释", "认为", "主张", "强调", "表现", "形成",
    "发展", "发生", "产生", "获得", "保持", "进行", "推动", "排斥", "参与",
    "促进", "降低", "提高", "减少", "增加", "增强", "引起", "恢复", "控制",
    "调节", "完成", "实现", "依据", "确认", "选择", "推断", "输入", "加工",
    "提取", "整合", "组织", "联系", "结构", "功能", "方式", "内容", "对象",
    "过程", "结果", "条件", "问题", "方法", "理论", "观点", "特点", "特征",
    "分类", "类型", "阶段", "作用", "意义", "性质", "程度", "方向", "范围",
    "关系", "机制", "因素", "评价", "贡献", "局限", "优点", "缺点", "含义",
    "影响", "反映", "基础", "事物", "核心", "现象", "倾向", "意义", "区别",
    "规律", "特性", "时间", "名字", "协调", "总和", "吃亏",
    "自己", "他人", "个体", "活动", "行为", "心理", "信息", "系统", "社会",
    "生理", "经验", "环境", "任务", "目标", "实例", "反馈", "成功", "失败",
    "刺激", "反应", "认知", "情绪", "情感", "人格", "需要", "动机", "意志",
    "感觉", "知觉", "记忆", "思维", "想象", "学习", "群体", "态度", "能力",
}

LEADING_FILLERS = (
    "一般而言，", "具体而言，", "由此，", "因此，", "同时，", "其中，", "综上，", "即",
    "指的是", "指", "是指", "表现为", "体现为", "主要是", "主要指",
)

PREDICATES = (
    "反映", "表现为", "体现为", "主张", "强调", "认为", "说明", "解释", "揭示",
    "使", "导致", "引起", "促进", "抑制", "决定", "影响", "提高", "降低", "增强",
    "减少", "增加", "形成", "获得", "产生", "实现", "建立", "帮助", "依赖", "关注",
    "重视", "支持", "控制", "调节", "保持", "避免", "预测", "检验", "操纵", "测量",
    "记录", "加工", "提取", "储存", "编码", "输入", "输出", "趋近", "回避", "选择",
    "分为", "包括", "由", "经历", "遵循", "属于", "具有", "采用", "运用", "利用",
)

LIST_PATTERNS = (
    r"(?:主要)?包括(?P<value>[^；。】]+)",
    r"(?:可|可以)?分为(?P<value>[^；。】]+)",
    r"主要有(?P<value>[^；。】]+)",
    r"由(?P<value>[^；。】]{2,36}?)(?:组成|构成)",
    r"经历(?P<value>[^；。】]{2,30})",
    r"通过(?P<value>[^；。】]{2,30}?)(?:获得|形成|实现|完成)",
    r"(?:还|也)受到(?P<value>[^；。】]{2,30}?)(?:影响|制约)",
)

TAIL_NOUNS = (
    "本质特征", "内在联系", "适用范围", "心理准备状态", "人格倾向", "中介因素",
    "态度体验", "准备状态和意图", "动力性的成分", "共同属性", "关键属性",
    "无关特征", "初始假设", "概念规则", "行为模式", "认知过程", "心理过程",
    "心理活动规律", "基本动力", "稳定而独特的心理面貌", "发生和变化",
    "实验研究道路", "因果关系", "变量关系", "自然科学", "主观经验",
    "内部心理活动", "行为与人格", "无意识冲突", "研究范围", "实验检验",
    "一般特征和内在联系", "共同本质属性和内在联系", "高级阶段",
    "外显长时记忆", "情绪记忆", "威胁和恐惧信息", "事件的情绪意义",
)


# 自动结构识别后仍需人工裁定的复杂句。这里只登记原句中已经存在的连续短语，
# 不改正文、不新增知识，用于保证比较双方、长分类和条件—结果链不会被截成碎片。
MANUAL_LINE_KEYWORDS = {
    "大脑两半球单侧化不是绝对的，正常情况下两半球通过胼胝体联系并协同活动。":
        ("单侧化不是绝对的", "通过胼胝体联系并协同活动"),
    "经典条件反射的反应是反射性、非随意的；操作条件反射的反应是自主性、随意的。":
        ("反射性、非随意的", "自主性、随意的"),
    "学习者把分散的条件重新组织成有意义的整体。":
        ("重新组织成有意义的整体",),
    "进入轻度睡眠，身体放松、呼吸变慢，主要出现α波。":
        ("轻度睡眠", "α波"),
    "处于沉睡状态，脑电活动几乎完全呈现δ波。":
        ("沉睡状态", "δ波"),
    "δ波消失，出现高频率、低波幅脑电波、不规则眼动和梦境，肌肉仍然松软。":
        ("δ波消失", "高频率、低波幅脑电波、不规则眼动和梦境"),
    "睡眠具有恢复精力、保护机体、促进身体发育、巩固和重建记忆以及激发灵感和创造性思维等作用。":
        ("恢复精力、保护机体、促进身体发育", "巩固和重建记忆", "激发灵感和创造性思维"),
    "梦通过压缩、转移、象征化和再度修饰等方式进行加工。":
        ("压缩、转移、象征化和再度修饰",),
    "使心理活动指向有意义、符合需要并与当前活动一致的刺激。":
        ("有意义、符合需要并与当前活动一致的刺激",),
    "间断闪光达到一定频率后被知觉为连续光的现象。":
        ("达到一定频率后被知觉为连续光",),
    "恒常性有助于个体在变化环境中稳定地认识事物。":
        ("在变化环境中稳定地认识事物",),
    "但它可能低估整体结构和情境在识别中的作用。":
        ("低估整体结构和情境在识别中的作用",),
    "刺激的结构、背景、参照物和空间关系会改变知觉判断。":
        ("结构、背景、参照物和空间关系", "改变知觉判断"),
    "信息可按语义类别、层级关系和事件联系组织。":
        ("语义类别、层级关系和事件联系",),
    "最后呈现的材料遗忘最少、最容易回忆，称为近因效应；最先呈现的材料遗忘也较少、比较容易回忆，称为首因效应。":
        ("最后呈现的材料遗忘最少、最容易回忆", "近因效应", "最先呈现的材料遗忘也较少、比较容易回忆", "首因效应"),
    "积累一般知识，并围绕特定目标收集资料、明确问题。":
        ("积累一般知识", "收集资料、明确问题"),
    "巴甫洛夫认为，语词声音与事物形象、语词与语词之间通过条件作用建立联系。":
        ("通过条件作用建立联系",),
    "个体通过表情、语调和姿态传递内部状态与社会信息。":
        ("表情、语调和姿态", "传递内部状态与社会信息"),
    "通过积极自我暗示、重新评价情境和调整不合理认识，改变情绪体验。":
        ("积极自我暗示、重新评价情境和调整不合理认识", "改变情绪体验"),
    "实际行为通常由内部需要、当前唤醒状态和外部诱因共同决定。":
        ("内部需要、当前唤醒状态和外部诱因共同决定",),
    "练习成绩会因环境干扰、态度变化、工具和训练方式变化以及新旧经验相互干扰而波动。":
        ("环境干扰、态度变化、工具和训练方式变化", "新旧经验相互干扰"),
    "及时、具体的结果反馈和过程反馈有助于发现错误、调整动作。":
        ("及时、具体的结果反馈和过程反馈", "发现错误、调整动作"),
    "项目应符合可行性、有效性、全面性、公平性、发展性和整体性要求。":
        ("可行性、有效性、全面性、公平性、发展性和整体性",),
    "测验需要标准化施测和计分程序、适当常模以及良好信度和效度。":
        ("标准化施测和计分程序、适当常模以及良好信度和效度",),
    "他还区分体质特质、环境养成特质、能力特质、气质特质和动力特质等。":
        ("体质特质、环境养成特质、能力特质、气质特质和动力特质",),
    "人格可由开放性、责任心、外向性、宜人性和神经质五个维度加以描述。":
        ("开放性、责任心、外向性、宜人性和神经质",),
    "八阶段依次为信任对不信任、自主对羞怯怀疑、主动对内疚、勤奋对自卑、同一性对角色混乱、亲密对孤独、繁殖对停滞、自我完善对绝望。":
        ("信任对不信任、自主对羞怯怀疑、主动对内疚、勤奋对自卑", "同一性对角色混乱、亲密对孤独、繁殖对停滞、自我完善对绝望"),
    "局限是容易受到社会赞许、作假、反应定势和自我认识水平影响。":
        ("社会赞许、作假、反应定势和自我认识水平",),
    "自陈量表结构明确、客观性较高但易受自我报告偏差影响；投射测验反应开放、材料丰富但标准化和客观性较弱。":
        ("结构明确、客观性较高但易受自我报告偏差影响", "反应开放、材料丰富但标准化和客观性较弱"),
    "联结学习使原本中性的对象因与积极或消极刺激反复配对而获得评价意义。":
        ("积极或消极刺激反复配对", "获得评价意义"),
    "群体规模扩大后，每个成员感受到的责任和外部影响被分散。":
        ("群体规模扩大后", "责任和外部影响被分散"),
    "主要负责内脏和腺体的信息交换，控制不由主观意志决定的不随意运动。":
        ("内脏和腺体的信息交换", "不由主观意志决定的不随意运动"),
    "观察学习又称替代学习，由班杜拉提出，是指个体不直接参与学习活动，而是通过观察榜样的行为及其结果，并仿照榜样行为，从而习得该行为的过程。":
        ("通过观察榜样的行为及其结果", "仿照榜样行为", "习得该行为"),
    "指在一瞬间内意识能够觉察或知觉到的对象数量。":
        ("一瞬间内", "能够觉察或知觉到的对象数量"),
    "指注意在同一对象或同一活动上所能持续的时间。":
        ("同一对象或同一活动", "所能持续的时间"),
    "指根据一定目的，主动把注意从一个对象或活动转向另一个对象或活动。":
        ("根据一定目的", "从一个对象或活动转向另一个对象或活动"),
    "个体把事物的各种属性和部分知觉为一个有组织整体的特性。":
        ("把事物的各种属性和部分知觉为一个有组织整体",),
    "刺激停止后，感觉信息在感觉通道中极短暂保存的记忆。":
        ("刺激停止后", "在感觉通道中极短暂保存"),
    "过去经历过的事物重新出现时能够确认其熟悉性的过程。":
        ("过去经历过的事物重新出现", "确认其熟悉性"),
    "过去经历过的事物不在眼前时，能够在头脑中重新呈现的过程。":
        ("过去经历过的事物不在眼前", "在头脑中重新呈现"),
    "短串高频刺激传入后，使海马对新信息进行长期加工并传递到大脑皮层进行长期储存的现象。":
        ("短串高频刺激传入后", "海马对新信息进行长期加工", "传递到大脑皮层进行长期储存"),
    "对解决问题的各种方案进行评估和比较后作出最终选择的过程。":
        ("对解决问题的各种方案进行评估和比较", "作出最终选择"),
    "以新颖、独特的方式解决问题并产生首创且有价值成果的认知活动过程。":
        ("以新颖、独特的方式解决问题", "产生首创且有价值成果"),
    "个体受到威胁或面临超出当前应对能力的情境时产生的非特异性身心紧张状态。":
        ("受到威胁或面临超出当前应对能力的情境时", "非特异性身心紧张状态"),
    "同一目标对个体既具有吸引力又具有排斥力时产生的冲突。":
        ("同一目标对个体既具有吸引力又具有排斥力",),
    "多个目标各自同时具有吸引力和排斥力时产生的复杂冲突。":
        ("多个目标各自同时具有吸引力和排斥力",),
    "海德用P—O—X模型说明个体、人际对象和态度对象之间的关系；三条关系符号乘积为正时平衡，为负时不平衡。":
        ("P—O—X模型", "符号乘积为正时平衡，为负时不平衡"),
    "由认知对象某一突出特征泛化推断其其他特征，形成整体印象。":
        ("由认知对象某一突出特征泛化推断其其他特征", "形成整体印象"),
    "个人绩效不能被单独评估时，个体在群体任务中的努力程度低于独自完成任务时的现象。":
        ("个人绩效不能被单独评估时", "努力程度低于独自完成任务时"),
    "群体决策比个体决策更容易表现出冒险倾向的现象。":
        ("群体决策比个体决策更容易表现出冒险倾向",),
    "杨和赫尔姆霍兹认为，视网膜上存在对红、绿、蓝三种波长敏感的视锥细胞，各种颜色由三类视锥细胞按不同比例活动产生。":
        ("对红、绿、蓝三种波长敏感的视锥细胞", "三类视锥细胞按不同比例活动产生"),
    "黑林认为，视觉系统存在红—绿、黄—蓝、黑—白三对对立过程，一方活动会抑制另一方。":
        ("红—绿、黄—蓝、黑—白三对对立过程", "一方活动会抑制另一方"),
    "个体即使没有立即获得强化，也可能已经形成认知地图；强化主要影响学习结果是否表现出来。":
        ("即使没有立即获得强化", "已经形成认知地图", "强化主要影响学习结果是否表现"),
    "个体即使对活动本身缺乏直接兴趣，也可借助对活动结果的兴趣维持注意。":
        ("即使对活动本身缺乏直接兴趣", "对活动结果的兴趣维持注意"),
    "即使部分信息缺失，个体也可能依据已有结构把对象知觉为完整整体。":
        ("即使部分信息缺失", "依据已有结构把对象知觉为完整整体"),
}


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    score: int
    source: str

    @property
    def length(self) -> int:
        return self.end - self.start


def parse_markdown_bold(line: str) -> tuple[str, list[tuple[int, int]]]:
    plain: list[str] = []
    intervals: list[tuple[int, int]] = []
    start: int | None = None
    index = 0
    while index < len(line):
        if line.startswith("**", index):
            if start is None:
                start = len(plain)
            else:
                intervals.append((start, len(plain)))
                start = None
            index += 2
        else:
            plain.append(line[index])
            index += 1
    if start is not None:
        raise AssertionError(f"未闭合加粗：{line}")
    return "".join(plain), intervals


def render_bold(plain: str, intervals: list[tuple[int, int]]) -> str:
    intervals = sorted(intervals)
    result: list[str] = []
    cursor = 0
    for start, end in intervals:
        if start < cursor:
            continue
        result.append(plain[cursor:start])
        result.append("**")
        result.append(plain[start:end])
        result.append("**")
        cursor = end
    result.append(plain[cursor:])
    return "".join(result)


def v3_line_map() -> dict[str, list[tuple[int, int]]]:
    variants: dict[str, list[tuple[tuple[int, int], ...]]] = defaultdict(list)
    for line in V3.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or line.startswith(">"):
            continue
        plain, intervals = parse_markdown_bold(line)
        variants[plain].append(tuple(intervals))
    result = {}
    for plain, options in variants.items():
        result[plain] = list(Counter(options).most_common(1)[0][0])
    return result


def overlaps(left: tuple[int, int], right: tuple[int, int]) -> bool:
    return left[0] < right[1] and right[0] < left[1]


def protected_ranges(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in re.finditer(r"【(?:名词解释|扩容（选用）)：.*?】", text)]


def point_content_start(text: str) -> tuple[int, tuple[int, int] | None]:
    match = re.match(r"^(?:\d+\.\s*|（\d+）\s*)", text)
    if not match:
        return 0, None
    colon = text.find("：", match.end())
    first_tag = min([position for position in (text.find("【名词解释："), text.find("【扩容（选用）：")) if position >= 0] or [len(text)])
    if colon < 0 or colon > 42 or colon >= first_tag:
        return match.end(), None
    return colon + 1, (match.end(), colon)


def trim_candidate(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start] in " ，；。：、‘’“”\"'（）()":
        start += 1
    while end > start and text[end - 1] in " ，；。：、‘’“”\"'（）()":
        end -= 1
    changed = True
    while changed:
        changed = False
        value = text[start:end]
        for filler in LEADING_FILLERS:
            if value.startswith(filler) and len(value) - len(filler) >= 3:
                start += len(filler)
                changed = True
                break
    for filler in ("并且", "而且", "以及", "并", "而"):
        if text[start:end].startswith(filler) and end - start - len(filler) >= 3:
            start += len(filler)
            break
    if text[start:end].startswith("的") and end - start >= 4:
        start += 1
    return start, end


def add_candidate(
    candidates: list[Span], text: str, start: int, end: int, score: int, source: str,
    *, max_len: int = 28,
) -> None:
    start, end = trim_candidate(text, start, end)
    if end - start < 2 or end - start > max_len:
        return
    value = text[start:end]
    if value in FRAGMENT_WORDS or re.fullmatch(r"[A-Za-z0-9—－-]+", value):
        return
    if value.startswith(("的", "过的")) or value.endswith("的") or value.endswith(("认为", "主张", "强调", "说明", "解释")):
        return
    if value.startswith("例如") and len(value) > 18:
        return
    candidates.append(Span(start, end, score, source))


def split_list_value(text: str, start: int, end: int) -> list[tuple[int, int]]:
    value = text[start:end]
    trailing = re.search(r"，(?:前者|后者|二者|其中|其|从而|并且|并|同时|但|而|负责|主要|它)", value)
    if trailing:
        end = start + trailing.start()
        value = text[start:end]
    # 分类项目总长适中则整组标记，便于一次还原完整分类；太长时按分号或逗号拆成
    # 2—4组，避免整句加粗。
    if len(value) <= 24:
        return [(start, end)]
    pieces = []
    cursor = start
    for match in re.finditer(r"[；]", value):
        stop = start + match.start()
        if stop - cursor >= 2:
            pieces.append((cursor, stop))
        cursor = start + match.end()
    if end - cursor >= 2:
        pieces.append((cursor, end))
    return pieces if 1 < len(pieces) <= 4 else [(start, end)]


def trusted_v3_candidates(text: str, intervals: list[tuple[int, int]], content_start: int) -> list[Span]:
    result = []
    protected = protected_ranges(text)
    definition = "【名词解释：" in text
    for start, end in intervals:
        value = text[start:end].strip()
        if not value or any(overlaps((start, end), item) for item in protected):
            continue
        if start < content_start:
            # 分点标题稍后统一按完整标题标记。
            continue
        if definition:
            prior_tags = [match.end() for match in re.finditer(r"【名词解释：.*?】", text[:start])]
            segment_start = prior_tags[-1] if prior_tags else content_start
            copula = text.find("是", segment_start)
            if start == segment_start and copula >= 0 and end <= copula:
                # 定义句不机械加粗被定义词，突出对象、上位概念和必要限定。
                continue
        if len(value) == 1 or value in FRAGMENT_WORDS:
            continue
        if value.startswith(("的", "过的")) or value.endswith("的") or value.endswith(("认为", "主张", "强调", "说明", "解释")):
            continue
        if definition and start == content_start and end - start <= 15:
            # 行首被定义词不承担采分功能；定义标签已经明确概念名称。
            continue
        result.append(Span(start, end, 96, "v3"))
    return result


def semantic_candidates(text: str, start: int, end: int, *, expansion: bool) -> list[Span]:
    candidates: list[Span] = []
    segment = text[start:end]

    # 分类与构成必须能一次还原全部项目。
    for pattern in LIST_PATTERNS:
        for match in re.finditer(pattern, segment):
            value_start = start + match.start("value")
            value_end = start + match.end("value")
            if re.search(r"什么|哪些|何种", text[value_start:value_end]):
                continue
            for left, right in split_list_value(text, value_start, value_end):
                add_candidate(candidates, text, left, right, 105, "list", max_len=40)

    # 越……越……、必要非充分、正负方向等关系本身就是采分点，整体保留。
    for match in re.finditer(r"[^，；。]{0,10}越[^，；。]{1,16}越[^，；。]{1,16}", segment):
        add_candidate(candidates, text, start + match.start(), start + match.end(), 108, "relation")
    for marker in ("必要而非充分条件", "呈反向关系", "相互依存并相互转化", "共同构成", "共同作用", "并非完全一致"):
        marker_at = segment.find(marker)
        while marker_at >= 0:
            clause_left = max(segment.rfind("；", 0, marker_at), segment.rfind("，", 0, marker_at)) + 1
            clause_right_candidates = [position for position in (segment.find("；", marker_at), segment.find("。", marker_at), segment.find("，", marker_at + len(marker))) if position >= 0]
            clause_right = min(clause_right_candidates) if clause_right_candidates else len(segment)
            add_candidate(candidates, text, start + clause_left, start + clause_right, 106, "relation")
            marker_at = segment.find(marker, marker_at + 1)

    # 书面定义中的“本质特征／适用范围”等稳定上位属性。
    for noun in TAIL_NOUNS:
        cursor = segment.find(noun)
        while cursor >= 0:
            # 句首的概念名称只是主语，不单独当作采分关键词。
            if cursor != 0 or cursor + len(noun) == len(segment):
                add_candidate(candidates, text, start + cursor, start + cursor + len(noun), 101, "tail")
            cursor = segment.find(noun, cursor + 1)

    # 引号中的完整判断比“什么／作用”等碎片更能复述比较维度。
    for match in re.finditer(r"[“\"](?P<value>[^”\"]{2,14})[”\"]", segment):
        add_candidate(candidates, text, start + match.start("value"), start + match.end("value"), 104, "quoted")

    for match in re.finditer(r"[^，；。]{2,14}是[^，；。]{2,14}的(?:基础|前提|条件|结果|原因)", segment):
        add_candidate(candidates, text, start + match.start(), start + match.end(), 107, "relation")

    # 按分号／句号划分独立采分关系；逗号仅在两侧都较完整时再拆。
    clause_bounds: list[tuple[int, int]] = []
    cursor = start
    for match in re.finditer(r"[；。]", text[start:end]):
        stop = start + match.start()
        if stop > cursor:
            clause_bounds.append((cursor, stop))
        cursor = start + match.end()
    if cursor < end:
        clause_bounds.append((cursor, end))

    for left, right in clause_bounds:
        clause = text[left:right]
        sub_bounds = [(left, right)]
        commas = list(re.finditer(r"，", clause))
        if commas:
            pieces = []
            local = left
            for comma in commas:
                stop = left + comma.start()
                if stop - local >= 7:
                    pieces.append((local, stop))
                    local = left + comma.end()
            if right - local >= 7:
                pieces.append((local, right))
            if 2 <= len(pieces) <= 4:
                sub_bounds = pieces

        for sub_left, sub_right in sub_bounds:
            sub_left, sub_right = trim_candidate(text, sub_left, sub_right)
            if sub_right - sub_left < 3:
                continue
            value = text[sub_left:sub_right]

            # “X是Y／X指Y”：优先取最后一层“的＋上位概念”前的核心限定，
            # 同时保留上位概念；不把整句都变成粗体。
            copulas: list[tuple[re.Match[str], int]] = []
            opening = re.match(r"(?:是指|指|是(?!否))", value)
            if opening:
                copulas.append((opening, 0))
            copulas.extend((match, 1) for match in re.finditer(r"(?<!但)是(?!否)", value[1:]))
            if copulas:
                copula, offset = copulas[-1]
                comp_left = sub_left + offset + copula.end()
                comp_right = sub_right
                complement = text[comp_left:comp_right]
                last_de = complement.rfind("的")
                if 2 <= last_de <= len(complement) - 2:
                    modifier_left = comp_left
                    # 去掉“个体／人们／心理学”等泛化主语式开头。
                    modifier = complement[:last_de]
                    for lead in ("个体", "人们", "心理学", "概念所", "对", "把"):
                        if modifier.startswith(lead) and len(modifier) - len(lead) >= 4:
                            modifier_left += len(lead)
                            break
                    add_candidate(candidates, text, modifier_left, comp_left + last_de, 91, "definition-modifier", max_len=22)
                    add_candidate(candidates, text, comp_left + last_de + 1, comp_right, 94, "definition-head", max_len=16)
                else:
                    add_candidate(candidates, text, comp_left, comp_right, 90, "definition", max_len=22)

            # 谓词—结果短语保留完整方向，不再把“促进／降低”单独加粗。
            for predicate in PREDICATES:
                position = value.find(predicate)
                if position < 0:
                    continue
                if predicate == "使" and position > 0 and value[position - 1] == "即":
                    continue
                pred_left = sub_left + position
                pred_right = sub_right
                if pred_right - pred_left > 24:
                    # 长句先截到下一个逗号或并列连接处。
                    tail = text[pred_left:pred_right]
                    cut = re.search(r"，|并且|同时|而且", tail[4:])
                    if cut:
                        pred_right = pred_left + 4 + cut.start()
                if pred_right - pred_left >= len(predicate) + 2:
                    add_candidate(candidates, text, pred_left, pred_right, 86, "predicate", max_len=24)
                break

            # 若本小句仍没有结构候选，提取末端完整名词／结果短语。扩容只保留
            # 新增角度，例子本身不机械满句加粗。
            local_candidates = [item for item in candidates if item.start < sub_right and sub_left < item.end]
            if not local_candidates and not (expansion and value.startswith("例如")):
                stripped_left, stripped_right = trim_candidate(text, sub_left, sub_right)
                value = text[stripped_left:stripped_right]
                if 4 <= len(value) <= 18:
                    add_candidate(candidates, text, stripped_left, stripped_right, 72, "fallback")
                elif len(value) > 18:
                    de = value.rfind("的")
                    if 3 <= de <= len(value) - 3:
                        add_candidate(candidates, text, stripped_left + de + 1, stripped_right, 70, "fallback-tail", max_len=16)

    return candidates


def merge_close_spans(text: str, spans: list[Span]) -> list[Span]:
    if not spans:
        return []
    spans = sorted(spans, key=lambda item: (item.start, item.end))
    merged = [spans[0]]
    for current in spans[1:]:
        previous = merged[-1]
        gap = text[previous.end:current.start]
        if current.start <= previous.end:
            winner = previous if (previous.score, previous.length) >= (current.score, current.length) else current
            # 若一个短语完整包含另一个，保留信息更充分且分数不低的项。
            if previous.start <= current.start and current.end <= previous.end:
                winner = previous
            elif current.start <= previous.start and previous.end <= current.end:
                winner = current
            merged[-1] = winner
        elif len(gap) <= 2 and re.fullmatch(r"(?:和|与|及|、|并|或|而|的)?", gap) and current.end - previous.start <= 24:
            merged[-1] = Span(previous.start, current.end, max(previous.score, current.score), "merged")
        else:
            merged.append(current)
    return merged


def select_spans(
    text: str, candidates: list[Span], content_start: int, segment_end: int, *, max_other: int = 3,
) -> list[Span]:
    selected: list[Span] = []
    # 先按来源质量与长度选取，定义／分类／关系优先于一般谓词。
    for candidate in sorted(candidates, key=lambda item: (-item.score, -item.length, item.start)):
        if candidate.start < content_start or candidate.end > segment_end:
            continue
        if any(overlaps((candidate.start, candidate.end), (item.start, item.end)) for item in selected):
            continue
        selected.append(candidate)
    selected = merge_close_spans(text, selected)

    # 每个独立采分句通常保留1—3组关键词；较长分类可例外。上限防止退回
    # “整段到处加粗”的旧问题。
    lists = [item for item in selected if item.source == "list"]
    others = [item for item in selected if item.source != "list"]
    if len(others) > max_other:
        others = sorted(others, key=lambda item: (-item.score, item.start))[:max_other]
    return sorted(lists + others, key=lambda item: item.start)


def mark_answer_line(text: str, v3_intervals: list[tuple[int, int]]) -> str:
    content_start, label = point_content_start(text)
    expansion_tag = text.find("【扩容（选用）：")
    main_end = expansion_tag if expansion_tag >= 0 else len(text)

    intervals: list[tuple[int, int]] = []
    if label:
        intervals.append(label)

    manual_applied = False
    for source_text, phrases in MANUAL_LINE_KEYWORDS.items():
        source_at = text.find(source_text, content_start, main_end)
        if source_at < 0:
            continue
        manual_applied = True
        for phrase in phrases:
            phrase_at = text.find(phrase, source_at, source_at + len(source_text))
            if phrase_at < 0:
                raise AssertionError((source_text, phrase, text))
            intervals.append((phrase_at, phrase_at + len(phrase)))

    # 用户确认的标杆定义，作为全书定义标注的密度与颗粒度基准。
    psychology = "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    if text.startswith(psychology):
        for phrase in ("行为和心理活动规律", "中间科学", "自然科学和社会科学"):
            start = text.index(phrase)
            intervals.append((start, start + len(phrase)))
    elif not manual_applied:
        trusted_candidates = trusted_v3_candidates(text, v3_intervals, content_start)
        definition_ranges = [match.span() for match in re.finditer(r"【名词解释：.*?】", text[:main_end])]
        semantic_ranges = []
        cursor = content_start
        for left, right in definition_ranges:
            if cursor < left:
                semantic_ranges.append((cursor, left))
            cursor = right
        if cursor < main_end:
            semantic_ranges.append((cursor, main_end))
        is_leaf = bool(re.match(r"^(?:\d+\.\s*|（\d+）\s*)", text))
        for left, right in semantic_ranges:
            trusted_here = [item for item in trusted_candidates if left <= item.start and item.end <= right]
            semantic_here = semantic_candidates(text, left, right, expansion=False)
            if definition_ranges:
                # 每个定义段保留2—3组最小充分关键词；若V3已有成熟标注则优先沿用。
                chosen = select_spans(
                    text, trusted_here + semantic_here, left, right, max_other=3,
                )
            elif is_leaf:
                if trusted_here:
                    chosen = select_spans(text, trusted_here, left, right, max_other=2)
                else:
                    # V3未标出的叶子采分点补1组可还原短语；比较句含分号时
                    # 可保留双方各1组。这里按采分需要补，不追求机械密度。
                    max_other = 2 if "；" in text[left:right] else 1
                    chosen = select_spans(text, semantic_here, left, right, max_other=max_other)
            else:
                # 总起与总结只沿用已有成熟关键词，避免把整段变成粗体。
                chosen = select_spans(text, trusted_here, left, right, max_other=2)
            intervals.extend((item.start, item.end) for item in chosen)

    # 扩容单独选取“新增角度”的关键词，绝不跨过标签或回头重复基础定义。
    if expansion_tag >= 0:
        expansion_start = expansion_tag + len("【扩容（选用）：")
        expansion_end = text.rfind("】")
        expansion_text = text[expansion_start:expansion_end]
        expansion_candidates = [] if expansion_text.startswith("例如") else semantic_candidates(text, expansion_start, expansion_end, expansion=True)
        picked = select_spans(text, expansion_candidates, expansion_start, expansion_end)
        # 扩容原则上只突出1组新增角度；完整分类可保留整组。
        if picked:
            best = max(picked, key=lambda item: (item.source == "list", item.score, item.length))
            intervals.append((best.start, best.end))

    # 名词解释标签本身不加粗；扩容内部允许标出新增角度。相邻／重叠标记统一收口。
    definition_ranges = [match.span() for match in re.finditer(r"【名词解释：.*?】", text)]
    cleaned = []
    for start, end in sorted(set(intervals)):
        if any(overlaps((start, end), item) for item in definition_ranges):
            continue
        value = text[start:end]
        if "例子可灵活替换" in value:
            continue
        if cleaned and start == cleaned[-1][1] and end - cleaned[-1][0] <= 30:
            cleaned[-1] = (cleaned[-1][0], end)
        elif cleaned and start < cleaned[-1][1]:
            previous = cleaned[-1]
            if end <= previous[1]:
                continue
            cleaned[-1] = (previous[0], end)
        else:
            cleaned.append((start, end))
    return render_bold(text, cleaned)


def build() -> str:
    source = V4.read_text(encoding="utf-8")
    source = source.replace("## 全本·综合证据重编版V4", "## 全本·采分关键词精校版V5", 1)
    source = source.replace(
        "> 全书按“不可替换性—可还原性—最小充分”标记关键词：每个独立采分点至少保留一组能够还原对象、条件／机制、关系方向或结果判断的关键词。全书采用黑白打印版式，不使用颜色、底纹、下划线或斜体。",
        "> 全书按“采分功能—最小充分—可独立还原”标记关键词：定义突出研究对象、上位概念、核心属性与必要限定；分类突出完整项目；机制突出条件、作用方式与结果；比较突出双方、维度与差异方向；评价突出贡献与局限。关键词只用于还原采分点，不追求机械覆盖率。全书采用黑白打印版式，不使用颜色、底纹、下划线或斜体。",
        1,
    )
    trusted = v3_line_map()
    output = []
    in_body = False
    for raw in source.splitlines():
        if raw.startswith("# 第一章 "):
            in_body = True
        if not in_body or not raw or raw.startswith("#") or raw.startswith(">") or raw == "---":
            output.append(raw)
            continue
        plain, _ = parse_markdown_bold(raw)
        output.append(mark_answer_line(plain, trusted.get(plain, [])))
    return "\n".join(output) + "\n"


def main() -> None:
    markdown = build()
    OUTPUT.write_text(markdown, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
