from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import re

from audit_shenzhen_baoming_v13_sources import base as source_base
from audit_shenzhen_baoming_v7_sources import (
    EXPECTED_QUESTIONS,
    normalize_heading,
    source_chapter,
    split_chapters,
    split_questions,
    trace,
)
from rebuild_shenzhen_baoming_v14_point_integrity import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    build_experiment,
    build_general,
    build_measurement,
    numbered_groups,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题采分点完整性复核报告V14.md"
LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题采分点完整性台账V14.tsv"


SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": source_base.SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": source_base.SOURCE_ROOT / "普通心理学/一本通.md",
        "build": build_general,
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": source_base.SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": source_base.SOURCE_ROOT / "实验心理学/一本通.md",
        "build": build_experiment,
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": source_base.SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": source_base.SOURCE_ROOT / "心理与教育测量/一本通.md",
        "build": build_measurement,
    },
}


# V13以前的台账只为部分“容易漏点题”手工列点，其余题以答案已有关键词
# 代替来源清单，无法发现来源有而答案无的情况。这里为原来没有独立清单的题
# 补齐题干对应的来源采分点；所有题都必须由显式清单命中，禁止用答案反推清单。
ADDITIONAL_POINT_LEDGER = {
    "普通心理学": {
        "简述心理学的研究对象": (
            "人的心理和行为", "认知", "动机和情绪", "心理特征", "行为", "心理与行为的关系",
        ),
        "比较自然观察法和实验法": (
            "观察法", "自然条件", "有系统、有计划", "第一手资料", "实验法", "控制条件", "有可能揭示因果关系",
        ),
        "简述神经元的结构、功能和分类": (
            "胞体、树突和轴突", "接收刺激、产生冲动和传导冲动", "内导神经元", "外导神经元", "中间神经元", "电传导", "化学传导",
        ),
        "论述大脑皮层的主要机能分区": (
            "初级感觉区", "初级运动区", "联合区", "语言联合区", "大脑半球单侧化", "分工与联合",
        ),
        "论述听觉的基本现象": (
            "音高", "响度", "音色", "声音掩蔽", "共鸣理论", "行波理论", "频率理论", "神经齐射理论",
        ),
        "结合实验论述选择性注意理论": (
            "过滤器理论", "衰减理论", "后期选择理论", "多阶段选择模型", "双耳分听", "鸡尾酒效应",
        ),
        "比较注意分配的主要理论": (
            "认知资源理论", "资源调节", "双加工理论", "自动化加工", "意识控制加工",
        ),
        "简述催眠的含义及其主要理论": (
            "催眠", "特殊状态理论", "非特殊状态理论", "角色扮演理论",
        ),
        "比较感觉记忆、短时记忆和长时记忆": (
            "感觉记忆", "图像记忆", "声像记忆", "短时记忆", "7±2个组块", "长时记忆", "注意", "复述", "提取",
        ),
        "如何提高记忆效率": (
            "清醒状态", "集中注意", "深层次", "形象化", "韵律化", "及时", "经常", "精细复述", "正确分配复习的时间", "阅读与回忆", "过度学习", "编码特异性", "测试效应",
        ),
        "简述思维的含义": (
            "概括性", "间接性", "直观动作思维", "形象思维", "抽象思维", "辐合思维", "发散思维", "常规性思维", "创造性思维", "分析和综合", "比较", "归类", "抽象和概括",
        ),
        "简述表象的含义": (
            "表象", "直观性", "概括性", "可操作性", "双重编码理论",
        ),
        "论述演绎推理和归纳推理": (
            "演绎推理", "三段论推理", "条件推理", "线性推理", "归纳推理",
        ),
        "论述语言的含义": (
            "结构性", "指代性", "创造性", "社会性", "转换生成语法理论", "表层结构", "深层结构",
        ),
        "简述语言加工的主要脑区": (
            "布洛卡区", "威尔尼克区", "弓形束", "威尔尼克—格施温德模型", "脑网络观",
        ),
        "简述动机的含义": (
            "激活功能", "指向功能", "维持和调整功能", "内部动机", "外部动机", "生理性动机", "社会性动机",
        ),
        "简述耶克斯—道德森定律": (
            "倒U形关系", "最佳水平", "简单任务", "困难任务",
        ),
        "论述马斯洛需要层次理论": (
            "生理需要", "安全需要", "归属与爱的需要", "尊重需要", "自我实现需要", "层次关系",
        ),
        "论述并评价阿特金森成就动机理论": (
            "成就需要", "成功可能性", "成功诱因值", "力求成功者", "避免失败者", "中等难度任务",
        ),
        "什么是归因": (
            "归因", "控制点", "稳定性", "可控性", "习得性无助",
        ),
        "论述主要学习动机理论": (
            "期待—价值理论", "归因理论", "自我决定理论", "自我效能理论", "成就目标理论",
        ),
        "简述情绪的核心功能": (
            "适应功能", "动机功能", "组织功能", "社会沟通功能",
        ),
        "论述情绪的主要维度": (
            "愉快度", "激动度", "强度", "紧张度", "基本情绪", "复合情绪", "心境", "激情", "应激",
        ),
        "论述情绪和动机的关系": (
            "情绪具有动机功能", "动机影响情绪", "需要", "活动效率", "动机—分化",
        ),
        "简述情绪智力的含义": (
            "情绪知觉、评价和表达", "情绪促进思维", "理解和运用情绪知识", "调节情绪",
        ),
        "论述情绪调节的含义": (
            "防御机制理论", "情境理论", "过程理论", "情境选择", "情境修正", "注意转换", "认知重评", "表达抑制",
        ),
        "论述智力发展的一般趋势": (
            "负加速", "18～25岁", "流体智力", "晶体智力", "发展速度", "智力水平", "智力结构", "性别差异", "遗传", "环境和教育", "主观能动性",
        ),
        "论述弗洛伊德关于人格结构": (
            "意识层次结构", "本我", "自我", "超我", "人格动力", "人格发展阶段", "心理防御机制",
        ),
        "比较人本主义人格理论与班杜拉": (
            "自我实现", "自我概念", "无条件积极关注", "交互决定论", "自我效能", "观察学习",
        ),
        "论述人格测评的主要方法": (
            "自陈量表", "投射测验", "主题统觉测验", "罗夏墨迹测验", "行为观察法", "形容词列表法", "Q分类法",
        ),
        "论述遗传、环境和自我因素": (
            "遗传因素", "家庭环境", "学校环境", "社会文化环境", "自我因素",
        ),
        "简述学习进程的特点": (
            "逐步提高", "高原现象", "个体差异", "整体学习", "分解学习", "过度学习", "反馈",
        ),
        "简述学习迁移的含义": (
            "正迁移", "负迁移", "近迁移", "远迁移", "有意迁移", "无意迁移", "自动式迁移", "反省式迁移",
        ),
        "简述认知学习的含义": (
            "初级认知学习", "高级认知学习", "特异性", "非特异性", "阶段性", "连续性", "层次性", "逆层次性",
        ),
        "简述动作技能学习的含义": (
            "连续技能", "非连续技能", "封闭技能", "开放技能", "精细动作", "粗大动作", "自动化", "反馈",
        ),
        "比较个体发展中的关键期与敏感期": (
            "关键期", "敏感期", "不可逆转", "经验作用最容易产生影响",
        ),
        "比较语言发展的学习观": (
            "学习观", "先天观", "普遍语法", "语言获得装置", "相互作用论", "生理成熟、认知发展和语言环境",
        ),
        "比较皮亚杰和科尔伯格": (
            "他律道德", "自律道德", "前习俗水平", "习俗水平", "后习俗水平",
        ),
        "简述桑代克联结主义": (
            "尝试—错误", "刺激—反应联结", "效果律", "练习律", "准备律",
        ),
        "比较学习动机的强化理论与人本主义理论": (
            "强化", "自我实现", "内在学习", "有意义学习", "自由学习", "以学生为中心",
        ),
        "简述科温顿自我价值理论": (
            "高趋低避型", "高趋高避型", "低趋高避型", "低趋低避型",
        ),
        "比较促进聚焦与防御聚焦": (
            "促进聚焦", "防御聚焦", "提高需要", "安全需要", "收益", "损失",
        ),
        "论述遗忘的原因": (
            "衰退说", "干扰说", "压抑说", "提取失败说", "时间因素", "识记材料的性质和数量", "学习的程度", "识记材料的系列位置", "识记者的态度", "清醒状态", "集中注意", "深层次", "形象化", "韵律化", "及时复习", "经常复习", "精细复述", "正确分配复习时间", "阅读与回忆", "过度学习", "编码特异性", "测试效应",
        ),
    },
    "实验心理学": {
        "简述科学方法的主要特点": (
            "系统的经验观察", "自我校正", "可公开", "可反复获得", "可证伪原则", "操作定义", "概率推断",
        ),
        "简述实验设计的含义": (
            "被试间设计", "被试内设计", "混合设计", "单因素实验设计", "多因素实验设计", "真实验设计", "准实验设计", "非实验设计", "小样本设计",
        ),
        "简述反应时的含义": (
            "A反应时", "B反应时", "C反应时",
        ),
        "简述韦伯定律和费希纳定律": (
            "韦伯定律", "K=ΔI/I", "费希纳定律", "P=KlgI",
        ),
    },
    "心理与教育测量": {
        "简述心理特质的含义": (
            "客观存在", "数量属性", "相对稳定", "主要优点", "主要局限",
        ),
        "论述测量误差的含义": (
            "随机误差", "系统误差", "测量工具", "测量对象", "施测过程", "提高工具质量", "标准化施测与评分",
        ),
        "简述经典测验理论的基本概念": (
            "观察分数", "真分数", "误差分数", "X=T+E", "误差均值为零", "真分数与误差独立", "误差之间相互独立",
        ),
        "简述结构效度的含义": (
            "结构效度", "心理特质理论", "理论假设不成立或实验设计不适当", "没有单一的数量指标",
        ),
        "简述效标（准则）关联效度": (
            "同时效度", "预测效度", "相关法", "区分法", "命中率法",
        ),
        "简述常模的相对性": (
            "一般常模", "特殊常模", "依赖特定测验", "依赖常模团体", "常模", "标准",
        ),
    },
}


# Earlier ledgers contain a few superseded expressions. Exact-title overrides replace,
# rather than union with, those old lists.
POINT_OVERRIDES = {
    "普通心理学": {
        "简述心理学的基本任务及其学科性质": (
            "描述、解释、预测与控制心理现象和行为", "自然科学", "社会科学", "交叉学科", "中间学科",
        ),
        "论述遗忘的原因": ADDITIONAL_POINT_LEDGER["普通心理学"]["论述遗忘的原因"],
    },
    "实验心理学": {},
    "心理与教育测量": {},
}

POINT_OVERRIDES["心理与教育测量"]["简述投射测验的含义、主要特点及局限"] = (
    "材料无明确结构", "反应不受限制", "测量目的隐蔽", "重视整体人格", "较少受语言限制", "定量分析",
)
POINT_OVERRIDES["心理与教育测量"]["简述项目反应理论的基础知识、主要性质及应用"] = (
    "潜在特质", "项目特征曲线", "跨群体不变性", "可选择性", "科学性", "信息函数", "题库建设", "常模参照测验", "目标参照测验", "计算机化自适应测验", "认知诊断测量模型",
)


def plain(text: str) -> str:
    return re.sub(r"[*`#]", "", text)


def explicit_terms(subject: str, title: str) -> tuple[str, ...]:
    clean_title = plain(title)
    overrides = [
        terms for fragment, terms in POINT_OVERRIDES[subject].items()
        if plain(fragment) in clean_title
    ]
    if overrides:
        return tuple(dict.fromkeys(term for terms in overrides for term in terms))

    pools = (
        source_base.V7_POINT_LEDGER[subject],
        source_base.EXHAUSTIVE_ADDITIONS[subject],
        ADDITIONAL_POINT_LEDGER[subject],
    )
    found: list[str] = []
    for pool in pools:
        for fragment, terms in pool.items():
            if plain(fragment) in clean_title:
                for term in terms:
                    if term not in found:
                        found.append(term)
    return tuple(found)


def validate_no_singletons(text: str, subject: str) -> None:
    lines = text.splitlines()
    for level in (2, 3, 4):
        singles = [
            (parent, children[0])
            for parent, children in numbered_groups(lines, level).items()
            if parent >= 0 and len(children) == 1
        ]
        assert not singles, (subject, "singleton sublevel", level, singles)


def main() -> None:
    rows: list[dict[str, str]] = []
    totals = Counter()

    for subject, config in SUBJECTS.items():
        expected_text = config["build"]()
        config["manual"].write_text(expected_text.rstrip() + "\n", encoding="utf-8")
        manual = config["manual"].read_text(encoding="utf-8")
        assert manual == expected_text.rstrip() + "\n"
        validate_no_singletons(manual, subject)

        speed_text = config["speed"].read_text(encoding="utf-8")
        ybt_text = config["yibentong"].read_text(encoding="utf-8")
        speed_chapters = split_chapters(speed_text)
        ybt_chapters = split_chapters(ybt_text)
        questions = split_questions(manual)
        assert len(questions) == EXPECTED_QUESTIONS[subject], (subject, len(questions))

        for index, (chapter, title, answer) in enumerate(questions, start=1):
            terms = explicit_terms(subject, title)
            assert terms, (subject, index, title, "no explicit source checklist")
            missing = [term for term in terms if term not in answer]
            assert not missing, (subject, index, title, "missing source points", missing)

            local_source = source_chapter(subject, chapter, speed_chapters)
            local_source += "\n" + source_chapter(subject, chapter, ybt_chapters)
            if subject == "心理与教育测量" and "比较智龄、年级当量和比率智商" in title:
                local_source += "\n" + speed_text + "\n" + ybt_text
            formula_terms = {"K=ΔI/I", "P=KlgI", "X=T+E"}
            untraced = [
                term for term in terms
                if term not in formula_terms and not trace(term, local_source)
            ]
            assert not untraced, (subject, index, title, "untraced checklist points", untraced)

            rows.append(
                {
                    "科目": subject,
                    "序号": str(index),
                    "章节": chapter,
                    "题目": title,
                    "独立来源采分点": "；".join(terms),
                    "点数": str(len(terms)),
                    "结果": "完整覆盖",
                }
            )
            totals["questions"] += 1
            totals["points"] += len(terms)

    assert totals["questions"] == 160, totals

    forgetting = next(
        answer
        for chapter, title, answer in split_questions(GENERAL_OUTPUT.read_text(encoding="utf-8"))
        if "论述遗忘的原因" in title
    )
    for term in (
        "衰退说", "干扰说", "压抑说", "提取失败说",
        "时间因素", "识记材料的性质和数量", "学习的程度", "识记材料的系列位置", "识记者的态度",
    ):
        assert term in forgetting, term

    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题采分点完整性复核报告V14

## 结论

- 普通心理学90题、实验心理学25题、心理与教育测量45题，共160/160题均由显式来源采分点清单反向核对，不再从现稿答案反推清单。
- 共反向核对{totals['points']}个来源采分点；每一点均须同时出现在本题对应的速背手册／一本通知识块和最终答案正文或紧邻扩容中。
- 已全局删除孤立的`（1）`、`①`和`a.`：任何下级序号都必须具有至少两个同父级并列项。
- 遗忘题已完整覆盖四种原因、五个影响因素，以及速背手册“提高记忆效果的策略”中编码、存储和提取三个阶段的方法。

## 本轮纠错原则

1. 合并可以改变呈现形式，不能减少来源采分点。
2. 简答题容量不足时，次要但合法的采分点进入紧邻圆括号扩容，不能静默删除。
3. 总起、总结和比较结论可以依据原有材料归纳，但不得形成新的理论采分点。
4. 序号层级为`1. →（1）→①→a.`；某一级只有一个项目时并回父级，不保留孤立序号。
""",
        encoding="utf-8",
    )
    print(f"PASS questions={totals['questions']} points={totals['points']} no_singletons=true")


if __name__ == "__main__":
    main()
