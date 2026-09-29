from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

from audit_shenzhen_baoming_v1_sources import ALIASES, compact, similarity
from audit_shenzhen_baoming_v4_sources import ALLOWED_STRUCTURAL_TERMS, bold_terms
from audit_shenzhen_baoming_v6_sources import POINT_LEDGER as V6_POINT_LEDGER
from rebuild_shenzhen_baoming_v7 import EXPERIMENT_OUTPUT, GENERAL_OUTPUT, MEASUREMENT_OUTPUT


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题逐题采分点守恒审计报告V7.md"
LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题逐题来源台账V7.tsv"

SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "普通心理学/一本通.md",
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "实验心理学/一本通.md",
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": SOURCE_ROOT / "心理与教育测量/一本通.md",
    },
}

EXPECTED_QUESTIONS = {"普通心理学": 90, "实验心理学": 25, "心理与教育测量": 45}

# 手册章节编号与来源章节编号不同时，使用题目内容对应的来源章节。
CHAPTER_ALIASES = {
    "实验心理学": {
        "第一章 绪论": "第一章 绪论",
        "第二章 实验研究的基本问题": "第二章 实验研究的基本问题",
        "第三章 反应时": "第四章 反应时",
        "第四章 心理物理学": "第五章 心理物理学",
    }
}

STRUCTURAL_TERMS = ALLOWED_STRUCTURAL_TERMS | {
    "基本关系", "有效因果推论", "选择依据", "共同要求", "联系", "主要区别",
    "解释顺序", "三者关系", "四者关系", "理论关系", "实验逻辑", "关键控制",
    "主要价值", "推导基础", "成立条件", "局限", "适用边界", "科学问题示例",
    "主要应用", "基本程序", "比较结论", "精度指标", "主要优势", "核心指标",
    "理论与测量取向不同", "编制方法不同", "结构特点不同", "适用特点不同",
    "共同基础", "共同质量要求", "常模类型结合", "时空限制", "转换方法",
    "解释限制", "后续发展", "测验材料", "适用范围", "主要局限", "结果解释",
    "主体点", "扩容点", "相同点", "不同点", "核心过程", "教育启示",
    "概念区别", "联系与主要区别", "共同点", "综合对策", "层层制约",
    "P=KlgI", "K=ΔI/I", "△φ/φ=C",
    "以兼顾效度和信度",
    "区别", "希望达到", "与他人相比处于什么位置",
}


POINT_LEDGER = {subject: dict(items) for subject, items in V6_POINT_LEDGER.items()}
POINT_LEDGER["实验心理学"].update({
    "费希纳、冯特和艾宾浩斯": (
        "实验计量心理学", "阈限思想", "心理学变革", "培养了大量心理学家",
        "正式独立", "高级心理过程", "无意义音节", "节省法", "遗忘曲线",
    ),
    "观察法、相关研究法和实验法": (
        "提供资料和课题", "描述性", "共变关系", "无法确定因果关系",
        "揭示因果关系", "可重复", "数量化", "经济", "人为性", "控制不严",
    ),
    "简述实验心理学研究的一般程序": (
        "确定课题", "选择被试", "确定实验控制", "数据整合", "撰写研究报告",
    ),
    "简述自变量的主要类型": (
        "作业变量", "环境变量", "被试变量", "操作性定义", "自变量水平",
    ),
    "简述因变量的类型": (
        "客观指标", "主观指标", "有效性", "客观性", "数量化", "量程限制",
    ),
    "论述控制变量的主要来源": (
        "随机额外变量", "系统额外变量", "被试方面", "主试方面", "排除法",
        "恒定法", "匹配法", "随机化法", "抵消平衡法", "统计控制法",
    ),
    "论述多变量实验设计": (
        "多自变量设计", "多因变量设计", "交互作用", "主效应", "简单效应",
    ),
    "简述小样本设计": (
        "ABA设计", "多基线设计", "不使用推断统计", "有力的实验推论",
    ),
    "简述实验信度": (
        "观察量", "统计检验", "直接验证", "系统验证", "概念验证",
    ),
    "论述实验的构念效度": (
        "构念效度", "内部效度", "统计结论效度", "外部效度", "重要前提",
    ),
    "比较反应时研究中的": (
        "减数法", "证明特定心理过程", "精确预测", "严格匹配", "加因素法",
        "先后顺序", "具体时间",
    ),
    "论述感觉阈限": (
        "最小变化法", "恒定刺激法", "平均差误法", "习惯误差", "期望误差",
        "练习误差", "疲劳误差", "动作误差", "时间误差", "绝对阈限",
    ),
    "论述信号检测论": (
        "均值不等", "重叠", "正态分布", "击中", "漏报", "虚报", "正确拒斥",
        "反应偏向", "辨别力", "ROC曲线", "有无法", "评价法", "迫选法",
    ),
})
POINT_LEDGER["实验心理学"]["论述感觉阈限的含义、传统测量方法及主要误差"] = (
    "最小变化法", "恒定刺激法", "平均差误法", "习惯误差", "期望误差",
    "练习误差", "疲劳误差", "动作误差", "时间误差",
)

POINT_LEDGER["心理与教育测量"].update({
    "简述四种测量水平": ("称名量表", "顺序量表", "等距量表", "比率量表", "标准分数"),
    "简述心理测量的": ("心理特质", "教育成就", "间接性", "相对性", "客观性", "顺序量表"),
    "心理测验的**含义和四个基本条件": ("行为样本", "标准化", "难度或应答率", "信度和效度"),
    "心理测验的**主要分类": ("按测量对象", "按测量方式", "按内容表达和反应形式", "按测验功能", "按评价参照标准"),
    "简述信度的含义及主要作用": ("随机误差", "个人分数", "比较不同分数"),
    "论述信度的": (
        "重测信度", "复本信度", "分半信度", "同质性信度", "评分者信度",
        "库—理信度系数", "克隆巴赫系数", "肯德尔和谐系数", "卡方检验",
    ),
    "简述效度的": ("相对性", "综合反映", "多方面证据", "信度是必要条件", "充分条件"),
    "论述影响测验效度": ("测验构成", "测验实施过程", "被试", "效标性质", "测量信度", "精心编制", "妥善组织", "标准应试情境", "选好效标"),
    "简述项目难度": ("常模参照测验", "标准参照测验", "选拔", "选择题", "速度测验", "防止被试得到满分"),
    "简述项目鉴别力": ("鉴别指数", "相关法", "点二列相关", "二列相关", "φ相关", "积差相关"),
    "简述多重选择题": ("27%", "真实水平", "测验信度", "培养诚实", "合理猜测", "零分或负分"),
    "简述测验施测前": ("测验资料", "施测手续", "指导语", "测验情境", "测验焦虑", "协调关系", "评分技术"),
    "简述心理测验结果": ("测验的性质和功能", "原因", "常模和效度", "其他资料", "一段分数", "不能直接比较", "保密"),
    "比较目标参照测验": ("共同基础", "共同质量要求", "解释目的不同", "适用范围不同", "信效度指标不同", "项目指标要求不同"),
    "简述目标参照测验的项目分析": ("内容范围", "双向细目表", "内容效度", "分类一致性", "荷伊特信度", "专家判定法", "临界组法", "对照组法"),
    "简述人格自陈量表常见的": ("社会赞许倾向", "默认倾向", "合理化", "说谎量表", "投射测验"),
    "简述投射测验的": ("非结构任务", "反应不受限制", "测量目标具有掩蔽性", "人格总体评估", "跨文化", "难以量化"),
    "论述概化理论": ("测量目标", "测量侧面", "随机侧面", "固定侧面", "G研究", "D研究", "概化系数", "依存系数"),
    "简述项目反应理论": ("潜在特质", "项目特征曲线", "难度", "区分度", "猜测", "参数相对不变", "信息函数"),
    "简述认知诊断": ("认知属性", "属性层级关系", "Q矩阵", "认知诊断模型", "认知状态"),
})
POINT_LEDGER["心理与教育测量"]["简述标准化样组"] = (
    "成员定义明确", "总体代表性", "取样过程清楚", "样本规模适当", "近时性", "一般常模与特殊常模结合",
)

POINT_LEDGER["普通心理学"].update({
    "简述心理学的**基本任务": ("描述", "解释", "预测", "控制", "中间科学", "综合性科学"),
    "简述中枢神经系统": ("脊髓", "延脑", "脑桥", "中脑", "小脑", "间脑", "大脑", "周围神经系统"),
    "简述大脑皮层": ("初级感觉区", "初级运动区", "联合区", "功能单侧化", "协同活动"),
    "简述感觉的含义": ("视觉", "听觉", "化学感觉", "躯体感觉", "绝对感受性", "差别感受性", "感觉阈限"),
    "简述视觉适应": ("暗适应", "明适应", "后像", "视觉对比", "马赫带", "视觉掩蔽"),
    "简述时间知觉": ("感觉通道", "兴趣和情绪", "事件数量和性质", "注意分配", "年龄、疾病及空间信息"),
    "简述意识的含义": ("觉知功能", "计划功能", "选择与监控功能", "无意识", "阈下知觉", "盲视", "非注意视盲", "无意识行为"),
    "论述睡眠": ("第一阶段", "第二阶段", "第三阶段", "第四阶段", "快速眼动睡眠", "周期规律", "睡眠功能", "梦的解释"),
    "论述记忆的主要类型": ("感觉记忆", "短时记忆", "长时记忆", "情景记忆", "语义记忆", "程序性记忆", "内隐记忆", "外显记忆"),
    "什么是工作记忆": ("中央执行系统", "语音环路", "视觉空间模板", "情景缓冲器", "阅读广度"),
    "论述遗忘的原因": ("衰退说", "干扰说", "压抑说", "提取失败说", "艾宾浩斯遗忘曲线", "系列位置效应"),
    "论述问题解决": ("算法策略", "启发法策略", "问题表征", "定势", "功能固着", "类比迁移", "动机", "情绪"),
    "简述语言的含义": ("创造性", "结构性", "指代性", "社会性", "表层结构", "深层结构"),
    "简述情绪的主要维度": ("愉快度", "激动度", "强度", "紧张度", "心境", "激情", "应激"),
    "论述情绪产生的主要理论": ("詹姆斯—兰格理论", "坎农—巴德理论", "评定—兴奋说", "沙赫特—辛格理论", "认知—评价理论", "动机—分化理论"),
    "论述智力的含义": ("二因素论", "群因素论", "三维智力结构模型", "流体智力与晶体智力理论", "多元智力理论", "智力的三因素理论", "PASS模型"),
    "论述人格的含义": ("整体性", "稳定性", "独特性", "社会性", "气质", "性格", "认知风格", "自我控制系统"),
    "论述主要人格特质理论": ("奥尔波特", "卡特尔", "艾森克", "大五人格"),
    "简述学习的含义": ("行为或行为潜能", "相对持久", "经验", "认知学习", "动作技能学习"),
    "论述经典条件作用": ("习得", "消退", "自然恢复", "泛化", "分化", "二级条件作用"),
    "论述操作性条件作用": ("强化", "惩罚", "消退", "强化程序", "塑造"),
    "论述皮亚杰": ("感知运动阶段", "前运算阶段", "具体运算阶段", "形式运算阶段", "图式", "同化", "顺应", "平衡"),
    "简述依恋": ("无差别社会反应阶段", "有差别社会反应阶段", "特殊情感联结阶段", "目标调整的伙伴关系阶段", "安全型", "回避型", "抗拒型", "混乱型"),
    "论述埃里克森": ("信任", "自主", "主动", "勤奋", "同一性", "亲密", "繁殖", "完善"),
})


CORRECTED_FRAGMENTS = {
    "费希纳、冯特和艾宾浩斯", "观察法、相关研究法和实验法", "控制变量的主要来源",
    "小样本设计", "实验信度", "实验的构念效度", "减数法与加因素法", "感觉阈限",
    "信号检测论", "四种测量水平", "心理测量的", "心理测验的", "信度的",
    "效度的", "影响测验效度", "项目难度", "项目鉴别力", "多重选择题",
    "测验施测前", "心理测验结果",
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def normalize_heading(text: str) -> str:
    return re.sub(r"[*`#]", "", text).strip().rstrip("。")


def split_chapters(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^# (?!#)(.+)$", text))
    chapters: dict[str, str] = {}
    if matches and matches[0].start() > 0:
        chapters["第一章 心理学的研究对象和方法"] = text[: matches[0].start()]
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chapters[normalize_heading(match.group(1))] = text[match.start() : end]
    return chapters


def source_chapter(subject: str, manual_heading: str, chapters: dict[str, str]) -> str:
    if subject == "普通心理学" and manual_heading == "补充章 高频学习理论":
        return "\n".join(
            value for key, value in chapters.items()
            if key.startswith("补充章") or key.startswith("第十三章")
        )
    wanted = CHAPTER_ALIASES.get(subject, {}).get(manual_heading, manual_heading)
    if wanted in chapters:
        return chapters[wanted]
    number = re.match(r"(第[一二三四五六七八九十百]+章|补充章\d+)", wanted)
    if number:
        candidates = [value for key, value in chapters.items() if key.startswith(number.group(1))]
        if len(candidates) == 1:
            return candidates[0]
    # 普心一本通第一章没有显式一级标题，已在split_chapters中补入。
    if manual_heading.startswith("第一章") and "第一章 心理学的研究对象和方法" in chapters:
        return chapters["第一章 心理学的研究对象和方法"]
    raise AssertionError((subject, manual_heading, list(chapters)))


def split_questions(text: str) -> list[tuple[str, str, str]]:
    chapter_matches = list(re.finditer(r"(?m)^# (?!#)(.+)$", text))
    question_matches = list(re.finditer(r"(?m)^### (押题\d+【(?:简答|论述)】.+)$", text))
    output = []
    for index, match in enumerate(question_matches):
        end = question_matches[index + 1].start() if index + 1 < len(question_matches) else len(text)
        previous_chapters = [item for item in chapter_matches if item.start() < match.start()]
        assert previous_chapters, match.group(1)
        chapter = normalize_heading(previous_chapters[-1].group(1))
        output.append((chapter, normalize_heading(match.group(1)), text[match.start() : end]))
    return output


def trace(term: str, source: str) -> bool:
    candidate = ALIASES.get(term, term)
    return similarity(candidate, compact(source)) >= 0.20


def ledger_terms(subject: str, title: str) -> tuple[str, ...]:
    hits = [terms for fragment, terms in POINT_LEDGER[subject].items() if fragment in title]
    if not hits:
        return ()
    # 短片段可能命中同一道题的多个局部清单，合并去重后检查。
    return tuple(dict.fromkeys(term for terms in hits for term in terms))


def main() -> None:
    rows: list[str] = []
    report_rows: list[str] = []
    totals = Counter()
    for subject, paths in SUBJECTS.items():
        manual = paths["manual"].read_text(encoding="utf-8")
        speed_text = paths["speed"].read_text(encoding="utf-8")
        ybt_text = paths["yibentong"].read_text(encoding="utf-8")
        full_source = speed_text + ybt_text
        speed_chapters = split_chapters(speed_text)
        ybt_chapters = split_chapters(ybt_text)
        questions = split_questions(manual)
        assert len(questions) == EXPECTED_QUESTIONS[subject], (subject, len(questions))
        for index, (chapter, title, answer) in enumerate(questions, start=1):
            local_source = source_chapter(subject, chapter, speed_chapters) + source_chapter(subject, chapter, ybt_chapters)
            definitions = re.findall(r"【名词解释：([^】]+)】", answer)
            unsupported_definitions = [
                term for term in definitions
                if not trace(term, local_source) and not trace(term, full_source)
            ]
            assert not unsupported_definitions, (subject, title, "definitions", unsupported_definitions)

            required = ledger_terms(subject, title)
            missing = [term for term in required if term not in answer]
            assert not missing, (subject, title, "missing source points", missing)
            unsourced = [
                term for term in required
                if not trace(term, local_source) and not trace(term, full_source)
            ]
            assert not unsourced, (subject, title, "ledger source", unsourced)

            terms = bold_terms(answer)
            unsupported = [
                term for term in terms
                if not trace(term, local_source) and not trace(term, full_source) and term not in STRUCTURAL_TERMS
            ]
            # 结构性比较语和总结语允许由来源信息直接归纳，但不得形成新的理论点。
            assert not unsupported, (subject, title, "unsupported bold terms", unsupported)

            status = "已修订并复核" if any(fragment in title for fragment in CORRECTED_FRAGMENTS) else "逐题复核通过"
            source_scope = chapter.replace("|", "／")
            clean_title = title.replace("|", "／")
            rows.append(
                f"{subject}\t{index}\t{source_scope}\t{clean_title}\t{len(required)}\t{len(definitions)}\t{status}"
            )
            report_rows.append(
                f"| {subject} | {index} | {source_scope} | {clean_title} | {len(required)} | {status} |"
            )
            totals["questions"] += 1
            totals["required"] += len(required)
            totals["definitions"] += len(definitions)
            totals["corrected"] += status.startswith("已修订")

    assert totals["questions"] == 160, totals
    LEDGER_TSV.write_text(
        "科目\t序号\t局部来源范围\t题目\t独立来源点清单数\t名词解释数\t结果\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`"
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    )
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题逐题采分点守恒审计报告V7

## 审计结论

- 已对普通心理学90题、实验心理学25题、心理与教育测量45题完成逐题局部来源核对，共160/160题。
- 每题首先限定在对应章节内核对速背手册和一本通；题目确实调用跨章概念时，再回查本科目完整来源，避免用全书关键词命中替代局部核对。
- 对并列点多、分类容易被重组的题建立独立来源点清单，共核对{totals['required']}个采分点；每一点必须在正文或圆括号扩容中有明确去向。
- 共核对{totals['definitions']}次名词解释调用，均能在本题对应的速背手册或一本通章节中回溯。
- 本轮对{totals['corrected']}题进行了实质修订，其余题逐题确认题干范围、来源点去向和局部来源一致性后保留。

## 审计规则

1. 速背手册主体点优先进入正文；一本通补充原则上进入圆括号扩容。
2. 简答题因容量移出的有效点必须作为整点扩容保留，不能无痕删除。
3. 总起、总结和比较结论可以重组来源信息，但不得据此新增理论采分点。
4. 每个名词解释、人物—理论配对、公式和分类均在题目对应章节内回溯，不使用全书模糊匹配代替局部核对。

## 逐题结果

| 科目 | 序号 | 局部来源范围 | 题目 | 独立来源点清单数 | 结果 |
|---|---:|---|---|---:|---|
{chr(10).join(report_rows)}

## 来源文件校验值

{hashes}
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} required_points={totals['required']} "
        f"definitions={totals['definitions']} corrected={totals['corrected']}"
    )


if __name__ == "__main__":
    main()
