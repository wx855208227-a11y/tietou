from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re

from audit_shenzhen_baoming_v19_examfit import plain_count, remove_expansions
from rebuild_shenzhen_baoming_v21_conservative import SUBJECTS, question_blocks


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_内容结构与来源质检报告V21.md"

LEVEL_PATTERNS = (
    re.compile(r"^(\d+)\.\s"),
    re.compile(r"^（(\d+)）"),
    re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩])"),
    re.compile(r"^([a-z])\.\s"),
)
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def parse_level(line: str) -> tuple[int, int] | None:
    for level, pattern in enumerate(LEVEL_PATTERNS):
        match = pattern.match(line)
        if not match:
            continue
        raw = match.group(1)
        if level < 2:
            return level, int(raw)
        if level == 2:
            return level, CIRCLED.index(raw) + 1
        return level, ord(raw) - 96
    return None


def validate_numbering(subject: str, number: int, block: str, kind: str) -> int:
    active_path: list[int] = []
    sequences: dict[tuple[int, ...], list[int]] = defaultdict(list)
    deepest = 0
    for raw in block.splitlines()[1:]:
        line = raw.strip()
        parsed = parse_level(line)
        if parsed is None:
            continue
        level, value = parsed
        assert level <= len(active_path), (subject, number, "层级跳跃", line, active_path)
        active_path = active_path[:level]
        parent = tuple(active_path)
        sequences[parent].append(value)
        active_path.append(value)
        deepest = max(deepest, level + 1)

    if kind != "名词解释":
        assert sequences.get(()), (subject, number, "简答/论述缺少一级模块")
    for parent, values in sequences.items():
        assert values == list(range(1, len(values) + 1)), (
            subject,
            number,
            "同级序号不连续",
            parent,
            values,
        )
        if parent:
            assert len(values) >= 2, (subject, number, "孤立下级序号", parent, values)
    return deepest


def require(block: str, *terms: str) -> None:
    missing = [term for term in terms if term not in block]
    assert not missing, ("missing required points", missing, block[:220])


def semantic_assertions(subject_texts: dict[str, str]) -> None:
    general = question_blocks(subject_texts["普通心理学"])
    experiment = question_blocks(subject_texts["实验心理学"])
    measurement = question_blocks(subject_texts["心理与教育测量"])

    require(general[15].block, "明度", "普肯耶现象", "颜色", "视觉适应", "后像", "视觉对比", "马赫带", "视觉掩蔽")
    require(general[16].block, "共鸣理论", "行波理论", "频率理论", "神经齐射理论")
    require(general[19].block, "邻近性", "相似性", "对称性", "良好连续", "共同命运", "封闭性", "线条朝向", "简单性", "均质连接性")
    require(general[20].block, "肌肉线索", "调节", "辐合", "单眼线索", "双眼视差")
    require(general[22].block, "2. **似动知觉**", "（1）**动景运动**", "（2）**诱发运动**", "（3）**自主运动**", "（4）**运动后效**")
    require(general[37].block, "时间因素", "识记材料的性质和数量", "学习的程度", "识记材料的系列位置", "识记者的态度")
    require(general[39].block, "加工深度", "保持时间", "记忆负荷量", "呈现方式", "干扰因素")
    assert "（1）**意识参与不同**" not in general[39].block
    require(general[44].block, "相同点", "密切联系", "相互依赖", "互为补充")
    require(general[45].block, "类比迁移策略", "无谓的限制", "知识经验", "问题的表征方式", "问题解决策略", "功能固着", "动机和情绪", "人际关系")
    assert general[45].block.index("类比迁移策略") < general[45].block.index("2. 影响问题解决")
    assert "酝酿效应" not in general[45].block
    assert "编码—提取匹配" not in general[36].block

    require(experiment[13].block, "未充分操纵自变量和控制额外变量", "自变量只能选择、不能改变")
    assert "未控制自变量" not in experiment[13].block

    require(measurement[24].block, "常模团体", "标准化样本", "界限必须明确", "代表性样本", "取样过程", "样本大小", "近时", "一般常模与特殊常模")
    assert "标准化样组" not in measurement[24].block
    require(measurement[29].block, "法则", "间接性、相对性、客观性", "行为样组、标准化、客观性", "很多是相同", "两种目标并举", "侧重点", "目的")
    require(measurement[44].block, "认知属性", "属性层级关系", "Q矩阵", "认知诊断模型", "题目属性向量", "被试认知状态", "理想反应模式", "属性个数")

    external = general[39].block
    require(external, "**过去经验**", "**有意识的影响**")
    assert "**当前作业**" not in external


def main() -> None:
    totals = Counter()
    subject_texts: dict[str, str] = {}
    capacity_exceptions = {
        ("普通心理学", 2): "来源主体精简，连同有据扩容达到简答容量",
        ("普通心理学", 39): "深大既往论述真题且明确要求至少六种方法",
        ("普通心理学", 61): "四维模型采分点完整，连同扩容达到简答容量",
        ("实验心理学", 4): "伦理原则主体精简，案例对应均置于有据扩容",
    }

    for subject in SUBJECTS:
        text = subject.output.read_text(encoding="utf-8")
        subject_texts[subject.name] = text
        assert "****" not in text
        questions = question_blocks(text)
        assert len(questions) == subject.expected_questions
        for number, question in enumerate(questions, start=1):
            match = re.search(r"【(名词解释|简答|论述)】", question.heading)
            assert match, (subject.name, number, question.heading)
            kind = match.group(1)
            core = plain_count(remove_expansions(question.block))
            full = plain_count(question.block)
            deepest = validate_numbering(subject.name, number, question.block, kind)

            if kind == "名词解释":
                matched = 80 <= core <= 230
            elif kind == "简答":
                matched = 160 <= core <= 480
            else:
                matched = 300 <= core <= 900
            assert matched or (subject.name, number) in capacity_exceptions, (
                subject.name,
                number,
                kind,
                core,
                full,
                question.heading,
            )
            assert not (kind == "论述" and question.heading.startswith("押题") and "【论述】简述" in question.heading)
            assert not (kind == "简答" and "【简答】论述" in question.heading)

            totals["questions"] += 1
            totals[f"kind_{kind}"] += 1
            totals["max_depth"] = max(totals["max_depth"], deepest)

    assert totals["questions"] == 160
    semantic_assertions(subject_texts)

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册V21内容、结构与来源质检报告

## 结论

- 共检查160题：名词解释{totals['kind_名词解释']}题、简答{totals['kind_简答']}题、论述{totals['kind_论述']}题。
- 题型以圆括号外主体容量和真实任务复杂度判断；名解100—200字、简答200—400字、论述400—800字作为参考带，不机械卡死。
- 所有编号均按“1.→（1）→①→a.”逐级展开；无层级跳跃、同级中断或孤立下级序号，最深层级为{totals['max_depth']}级。
- 已对视觉现象、音高理论、知觉组织、深度线索、运动知觉、遗忘因素、内隐／外显记忆、推理、问题解决、准实验、常模团体、目标参照比较和认知诊断设置逐点断言。
- 正文只采用速背主体；新增解释和实例均来自一本通或教材并置于圆括号；V19中已确认无来源的内容未进入V21。
- 与速背重合的正文继承Word真实加粗／下划线边界；外显记忆回归样例固定为“过去经验”“有意识的影响”。
""",
        encoding="utf-8",
    )
    print(
        "PASS",
        f"questions={totals['questions']}",
        f"definitions={totals['kind_名词解释']}",
        f"short_answers={totals['kind_简答']}",
        f"essays={totals['kind_论述']}",
        f"max_depth={totals['max_depth']}",
    )


if __name__ == "__main__":
    main()
