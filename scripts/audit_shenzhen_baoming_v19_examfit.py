from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re

from audit_shenzhen_baoming_v7_sources import normalize_heading, source_chapter, split_chapters, split_questions, trace
from audit_shenzhen_baoming_v1_sources import compact
from rebuild_shenzhen_baoming_v14_point_integrity import numbered_groups
from rebuild_shenzhen_baoming_v19_examfit import INPUTS, OUTPUTS, TITLE_REVISIONS
from validate_shenzhen_baoming_v14_point_integrity import explicit_terms


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题题干题型知识归属审计台账V19.tsv"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题题干题型知识归属审计报告V19.md"

EXPECTED = {"普通心理学": 90, "实验心理学": 25, "心理与教育测量": 45}

SOURCE_PATHS = {
    subject: (
        SOURCE_ROOT / subject / "速背手册.md",
        SOURCE_ROOT / subject / "一本通.md",
    )
    for subject in EXPECTED
}

# 第39题是深大既往原题，题干明确要求“至少六种方法”，答题任务本身按论述题
# 组织；主体字数略低于一般参考带，但采分点数量和真题题型证据均支持保留。
TYPE_EXCEPTIONS = {
    ("普通心理学", 39): "深大既往论述真题；至少六种方法，按题型证据保留",
    ("普通心理学", 60): "深大2020年论述真题，按院校真实题型证据保留",
    ("心理与教育测量", 10): "需展开五种估计方法并比较一致性与误差来源，任务结构支持论述",
}

PROBLEM_SOLVING_POINTS = (
    "问题空间", "算法策略", "启发法策略", "手段—目的分析法", "逆向搜索", "爬山法",
    "类比迁移策略", "知识经验", "问题的表征方式", "无谓的限制", "定势",
    "问题解决策略", "功能固着", "功能变通", "动机和情绪", "人际关系",
    "原型启发", "个性特征", "酝酿效应",
)

QUESTION_POINT_OVERRIDES = {
    ("普通心理学", 40): (
        "外显记忆", "过去经验", "有意识的影响", "内隐记忆", "无意识影响",
        "加工深度", "保持时间", "记忆负荷量", "呈现方式", "干扰因素",
    ),
}


def plain_count(value: str) -> int:
    value = re.sub(r"【名词解释：[^】]+】", "", value)
    value = re.sub(r"^#{1,6}.*$", "", value, flags=re.MULTILINE)
    value = value.replace("**", "")
    return len(re.sub(r"[^\u4e00-\u9fffA-Za-z0-9±Δφ]", "", value))


def remove_expansions(value: str) -> str:
    previous = None
    while previous != value:
        previous = value
        value = re.sub(r"（[^（）\n]*）", "", value)
    return value


def point_present(point: str, answer: str) -> bool:
    wanted = compact(point)
    actual = compact(answer)
    if wanted in actual:
        return True
    # 只容许虚词“的”的书面变体，不用低阈值模糊匹配替代采分点核对。
    return wanted.replace("的", "") in actual.replace("的", "")


def question_style(title: str) -> str:
    if any(token in title for token in ("为什么", "如何", "哪些变化", "是否越", "面对同一", "请结合实例")):
        return "问题／应用型"
    if "比较" in title:
        return "概念比较型"
    if "结合" in title or "举例" in title:
        return "结合材料型"
    return "直接知识型"


def type_judgment(subject: str, index: int, title: str, base: int, total: int) -> tuple[str, str]:
    question_type = re.search(r"【(简答|论述)】", title).group(1)
    exception = TYPE_EXCEPTIONS.get((subject, index))
    if exception:
        return "保留（有题型证据）", exception
    if question_type == "简答":
        if 180 <= base <= 450:
            return "匹配", "主体容量位于简答参考带或合理浮动范围"
        if base < 180 and total >= 200:
            return "匹配（主体精简）", "主体较精简，连同有据扩容后达到简答容量"
        if 150 <= base < 180 and total < 200:
            return "匹配（知识点有限）", "来源采分点数量有限，不为凑字数新增内容"
        if base > 450 and total <= 650:
            return "匹配（上限浮动）", "并列来源点较多，保留完整性优先于机械压缩"
        return "待复核", "简答容量偏离参考带"
    if 400 <= base <= 850:
        return "匹配", "主体容量位于论述参考带或合理浮动范围"
    if 350 <= base < 400 and total >= 450:
        return "匹配（主体临界）", "主体接近论述下限，扩容后任务完整"
    if base > 850 and total <= 1050:
        return "匹配（上限浮动）", "理论点较多，未为压缩容量删除采分点"
    return "待复核", "论述容量偏离参考带"


def validate_no_singleton(answer: str, subject: str, index: int) -> None:
    lines = answer.splitlines()
    for level in (2, 3, 4):
        singles = [
            (parent, children[0])
            for parent, children in numbered_groups(lines, level).items()
            if parent >= 0 and len(children) == 1
        ]
        assert not singles, (subject, index, "singleton sublevel", level, singles)


def validate_problem_solving(answer: str) -> None:
    for point in PROBLEM_SOLVING_POINTS:
        assert point in answer, ("问题解决漏点", point)
    assert "（3）**无谓的限制**" in answer
    assert "**问题的表征方式**" in answer and "无谓限制会" not in answer
    strategy_end = answer.index("2. 影响问题解决的主要因素如下：")
    assert answer.index("类比迁移策略") < strategy_end
    assert "原型启发**和**类比迁移" not in answer
    factor_markers = re.findall(r"^（([1-8])）\*\*", answer[strategy_end:], flags=re.MULTILINE)
    assert factor_markers == list("12345678"), factor_markers


def main() -> None:
    rows: list[dict[str, str]] = []
    totals = Counter()
    changed_title_pairs = {
        subject: {
            normalize_heading(old.removeprefix("### ")): normalize_heading(new.removeprefix("### "))
            for old, new in pairs
        }
        for subject, pairs in TITLE_REVISIONS.items()
    }

    for subject in EXPECTED:
        old_questions = split_questions(INPUTS[subject].read_text(encoding="utf-8"))
        new_questions = split_questions(OUTPUTS[subject].read_text(encoding="utf-8"))
        assert len(old_questions) == len(new_questions) == EXPECTED[subject]
        speed = SOURCE_PATHS[subject][0].read_text(encoding="utf-8")
        yibentong = SOURCE_PATHS[subject][1].read_text(encoding="utf-8")
        speed_chapters = split_chapters(speed)
        yibentong_chapters = split_chapters(yibentong)

        for index, ((old_chapter, old_title, _), (chapter, title, answer)) in enumerate(
            zip(old_questions, new_questions, strict=True), start=1
        ):
            assert chapter == old_chapter, (subject, index, old_chapter, chapter)
            validate_no_singleton(answer, subject, index)
            answer_body = answer.split("\n", 1)[1]
            total = plain_count(answer_body)
            base = plain_count(remove_expansions(answer_body))
            expected_title = changed_title_pairs[subject].get(old_title, old_title)
            if subject == "普通心理学" and index == 46:
                expected_title = title
            assert title == expected_title, (subject, index, old_title, title, expected_title)

            points = list(QUESTION_POINT_OVERRIDES.get((subject, index), explicit_terms(subject, old_title)))
            if (subject, index) == ("普通心理学", 46):
                points = list(PROBLEM_SOLVING_POINTS)
                validate_problem_solving(answer)
            assert points, (subject, index, "empty explicit point list", old_title)
            missing = [point for point in points if not point_present(point, answer)]
            assert not missing, (subject, index, "missing points", missing)

            local_source = source_chapter(subject, chapter, speed_chapters)
            local_source += "\n" + source_chapter(subject, chapter, yibentong_chapters)
            if (subject, index) == ("心理与教育测量", 27):
                # 智龄定义位于智力测验章节，年级当量与比率智商位于常模章节。
                local_source += "\n" + speed + "\n" + yibentong
            formula_terms = {"K=ΔI/I", "P=KlgI", "X=T+E"}
            untraced = [
                point for point in points
                if point not in formula_terms and not trace(point, local_source)
            ]
            assert not untraced, (subject, index, "untraced points", untraced)

            judgment, note = type_judgment(subject, index, title, base, total)
            assert judgment != "待复核", (subject, index, title, base, total, note)
            changed = old_title != title or (subject, index) == ("普通心理学", 46)
            rows.append(
                {
                    "科目": subject,
                    "题号": str(index),
                    "章节": chapter,
                    "原题干": old_title,
                    "复核后题干": title,
                    "题干类型": question_style(title),
                    "主体字数": str(base),
                    "含扩容字数": str(total),
                    "来源采分点数": str(len(points)),
                    "采分点完整性": "完整",
                    "知识归属": "通过",
                    "题型容量": judgment,
                    "处理": "实质修订" if changed else "逐题核对后保留",
                    "说明": note,
                }
            )
            totals["questions"] += 1
            totals["points"] += len(points)
            totals["revised"] += int(changed)
            totals["simple"] += "【简答】" in title
            totals["essay"] += "【论述】" in title

    assert totals["questions"] == 160, totals
    assert totals["simple"] + totals["essay"] == 160
    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题题干、题型与知识归属审计报告V19

## 审计结论

- 已按普通心理学90题、实验心理学25题、心理与教育测量45题逐题复核，共160/160题。
- 共反向核对{totals['points']}个速背手册／一本通来源采分点；正文合并不允许造成遗漏，移出主体的合法点必须在圆括号扩容中保留。
- 本轮对{totals['revised']}题作出题干、题型或知识归属的实质修订，其余题逐题核对后保留；最终简答{totals['simple']}题、论述{totals['essay']}题。
- “问题解决”题已将类比迁移放回启发法策略，将无谓的限制恢复为独立影响因素，并完整保留八项主体影响因素及三个有据扩容因素。
- 题型容量以名解100—200字、简答200—400字、论述400—800字为参考带，不机械卡死；有真题题型证据或来源点数量特殊的题，在台账中单独说明。

## 逐题执行规则

1. 先依据题干任务确定答案模块，再核对每一采分点的上位类别，禁止把策略、影响因素、理论观点等错放。
2. 题干以深大真题中的概念比较、原因分析、结合实例和应用表达为参照；稳定的定义、分类型简答保留直接问法，不强行情境化。
3. 论述题必须具有足够的理论展开、关系分析或应用任务；答案仅够简答容量时调整题型，不用无来源内容凑字数。
4. 序号按`1. →（1）→①→a.`展开；没有同级并列项时不得孤立使用下级序号。
5. 速背手册表述和关键词优先，一本通只作有据扩容；所有扩容仍须能回溯来源。
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} points={totals['points']} "
        f"revised={totals['revised']} simple={totals['simple']} essay={totals['essay']}"
    )


if __name__ == "__main__":
    main()
