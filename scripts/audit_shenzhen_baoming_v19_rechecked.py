from __future__ import annotations

import csv
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_shenzhen_baoming_v7_sources import split_questions  # noqa: E402
from rebuild_shenzhen_baoming_v14_point_integrity import numbered_groups  # noqa: E402


MANUALS = {
    "普通心理学": ROOT / "deliverables/深圳大学347普通心理学保命手册_V19原标准重新逐题校正版.md",
    "实验心理学": ROOT / "deliverables/深圳大学347实验心理学保命手册_V19原标准逐题校正版.md",
    "心理与教育测量": ROOT / "deliverables/深圳大学347心理与教育测量保命手册_V19原标准逐题校正版.md",
}
EXPECTED = {"普通心理学": 90, "实验心理学": 25, "心理与教育测量": 46}
KEYWORD_BASELINE = ROOT / "deliverables/深圳大学347心理学保命手册_三科速背Word关键词基线V17.tsv"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_V19原标准逐题终校质检报告.md"
KEYWORD_CANDIDATES = ROOT / "deliverables/深圳大学347心理学保命手册_V19原标准关键词漏标复核候选.tsv"

META_TERMS = {
    "定义", "特点", "原因", "方法", "作用", "应用", "意义", "含义", "关系",
    "类型", "过程", "理论", "模型", "研究", "分类", "功能", "优点", "缺点",
    "步骤", "条件", "内容", "目的", "考点",
}

# 逐条对照速背Word上下文后确认：这些命中并非关键词漏标。
# 原因仅限于核心词已被同一题中的更长加粗短语覆盖、重复出现无需再次加粗，
# 或速背来源语境与当前答案语境并不对应。
MANUAL_KEYWORD_EXCLUSIONS = {
    ("普通心理学", 17, "神经齐射理论都"): "核心词已包含在‘位置理论和神经齐射理论’的加粗短语中，仅虚词‘都’在外",
    ("普通心理学", 37, "长时记忆"): "来源上下文分别属于知觉匹配和工作记忆，当前题中的同名词为另一语境且已在本题关键位置标注",
    ("普通心理学", 47, "对行动目标与手段的探索"): "核心内容已由‘行动目标与手段的探索、判断、评价’整体加粗，仅介词‘对’在外",
    ("普通心理学", 49, "布洛卡区"): "本题定义位置已经加粗，候选只是后文模型中的重复出现",
    ("普通心理学", 58, "厌恶恐惧"): "普拉切克基本情绪列表已经整体加粗，候选来自后文艾克曼列表的重复列举",
    ("普通心理学", 76, "操作性条件作用"): "本题概念定义已经加粗，候选只是后文模块提示语中的重复出现",
    ("实验心理学", 7, "操作定义"): "答案采用并已加粗规范术语‘操作性定义’，覆盖速背中的简称‘操作定义’",
}

# 这些题的主体略低于通常参考带，但来源点有限或题内并列任务足以支持题型。
CAPACITY_EXCEPTIONS = {
    ("普通心理学", 2): "主体精简，含有据扩容后达到简答容量",
    ("实验心理学", 4): "伦理原则来源点有限，含有据扩容后达到简答容量",
    ("心理与教育测量", 9): "信度含义与作用来源点有限，不为凑字数新增内容",
    ("心理与教育测量", 18): "需同时展开两类计算方法和六类用途选择，任务结构支持论述",
    ("心理与教育测量", 24): "需展开六项解释原则和四项报告原则，采分点密度支持论述",
    ("心理与教育测量", 25): "含三项定义、四项测验特点和六项常模团体条件，任务结构支持论述",
}


@dataclass(frozen=True)
class Keyword:
    term: str
    source_line: str
    context: str


def compact(value: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", value.replace("**", ""))


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


def source_match(answer: str, context: str) -> bool:
    left = compact(answer)
    right = compact(context)
    if not left or not right:
        return False
    matcher = SequenceMatcher(None, left, right)
    longest = max((block.size for block in matcher.get_matching_blocks()), default=0)
    containment = longest / min(len(left), len(right))
    return longest >= 8 and (matcher.ratio() >= 0.25 or containment >= 0.45)


def keyword_baseline() -> dict[str, list[Keyword]]:
    output: dict[str, list[Keyword]] = {subject: [] for subject in MANUALS}
    seen: set[tuple[str, str, str]] = set()
    with KEYWORD_BASELINE.open(encoding="utf-8") as file:
        for row in csv.reader(file, delimiter="\t"):
            if len(row) < 8 or row[0] not in output:
                continue
            term = row[4].strip()
            normalized = compact(term)
            key = (row[0], normalized, row[7])
            if len(normalized) < 4 or normalized in META_TERMS or key in seen:
                continue
            seen.add(key)
            output[row[0]].append(Keyword(term, row[1], row[7]))
    return output


def keyword_candidates(
    subject: str,
    questions: list[tuple[str, str, str]],
    baseline: list[Keyword],
) -> list[dict[str, str]]:
    by_first: dict[str, list[Keyword]] = {}
    for item in baseline:
        normalized = compact(item.term)
        by_first.setdefault(normalized[0], []).append(item)

    rows: list[dict[str, str]] = []
    seen: set[tuple[int, int, str, str]] = set()
    for question_index, (_, title, answer) in enumerate(questions, start=1):
        for line_index, line in enumerate(answer.splitlines(), start=1):
            if not line.strip() or line.startswith("#") or line.lstrip().startswith("综上"):
                continue
            plain = compact(line)
            bold = [compact(value) for value in re.findall(r"\*\*([^*]+)\*\*", line)]
            first_characters = set(plain)
            for character in first_characters:
                for item in by_first.get(character, ()):
                    term = compact(item.term)
                    if (subject, question_index, term) in MANUAL_KEYWORD_EXCLUSIONS:
                        continue
                    if term not in plain or not source_match(line, item.context):
                        continue
                    if any(term in value or (len(value) >= 4 and value in term) for value in bold):
                        continue
                    key = (question_index, line_index, term, item.context)
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "科目": subject,
                            "题号": str(question_index),
                            "题干": title,
                            "答案行": str(line_index),
                            "速背Word关键词": item.term,
                            "速背Word行": item.source_line,
                            "答案原文": line.strip(),
                            "来源原文": item.context,
                            "处理状态": "待人工复核",
                        }
                    )
    return rows


def capacity_judgment(subject: str, index: int, title: str, answer: str) -> tuple[str, str, int, int]:
    total = plain_count(answer)
    base = plain_count(remove_expansions(answer))
    if (subject, index) in CAPACITY_EXCEPTIONS:
        return "通过（有说明）", CAPACITY_EXCEPTIONS[(subject, index)], base, total
    if "【简答】" in title:
        passed = 150 <= base <= 480 or 200 <= total <= 520
    else:
        passed = 330 <= base <= 950 or 400 <= total <= 1050
    return (
        "通过" if passed else "待复核",
        "主体与含扩容容量匹配题型" if passed else "容量超出参考浮动范围",
        base,
        total,
    )


def main() -> None:
    baseline = keyword_baseline()
    totals = {"questions": 0, "simple": 0, "essay": 0, "name_tags": 0}
    name_entry_lengths: list[int] = []
    capacities: list[tuple[str, int, str, int, int, str]] = []
    candidate_rows: list[dict[str, str]] = []
    subject_summary: list[tuple[str, int, int, int]] = []

    for subject, path in MANUALS.items():
        text = path.read_text(encoding="utf-8")
        questions = split_questions(text)
        assert len(questions) == EXPECTED[subject], (subject, len(questions), EXPECTED[subject])
        assert "【扩容" not in text and "扩容（选用）" not in text
        assert not re.search(r"【\s+名词解释|名\s+词\s+解\s+释", text)
        assert text.count("**") % 2 == 0
        for line_number, line in enumerate(text.splitlines(), start=1):
            tags = re.findall(r"【名词解释：([^】]+)】", line)
            if not tags:
                continue
            assert re.search(r"(?:【名词解释：[^】]+】)+$", line), (
                subject, line_number, "名解标签不在条目末尾", line,
            )
            assert line.rfind("【名词解释：") > line.rfind("）"), (
                subject, line_number, "名解标签未置于扩容之后", line,
            )
            length = plain_count(line)
            assert length >= 40, (subject, line_number, "名解条目容量过低", length, line)
            name_entry_lengths.extend([length] * len(tags))
        for heading in re.findall(r"^## (.+)$", text, flags=re.MULTILINE):
            if re.match(r"^[一二三四五六七八九十]+、", heading):
                assert re.search(r"【★{1,3}】$", heading), (subject, "星级格式", heading)

        simple = essay = 0
        for index, (_, title, answer) in enumerate(questions, start=1):
            assert re.match(r"^押题\d+【(?:简答|论述)】", title), (subject, index, title)
            assert answer.count("**") % 2 == 0, (subject, index, "加粗标记不成对")
            for level in (2, 3, 4):
                singles = [
                    (parent, children[0])
                    for parent, children in numbered_groups(answer.splitlines(), level).items()
                    if parent >= 0 and len(children) == 1
                ]
                assert not singles, (subject, index, "孤立下级序号", level, singles)
            status, note, base, total = capacity_judgment(subject, index, title, answer)
            capacities.append((subject, index, status, base, total, note))
            assert status != "待复核", (subject, index, title, base, total)
            simple += int("【简答】" in title)
            essay += int("【论述】" in title)

        candidate_rows.extend(keyword_candidates(subject, questions, baseline[subject]))
        subject_summary.append((subject, len(questions), simple, essay))
        totals["questions"] += len(questions)
        totals["simple"] += simple
        totals["essay"] += essay
        totals["name_tags"] += text.count("【名词解释：")

    assert totals["questions"] == 161, totals
    fields = [
        "科目", "题号", "题干", "答案行", "速背Word关键词", "速背Word行",
        "答案原文", "来源原文", "处理状态",
    ]
    with KEYWORD_CANDIDATES.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(candidate_rows)

    summary_lines = [
        "# 深圳大学347心理学保命手册V19原标准逐题终校质检报告",
        "",
        "## 自动质检结论",
        "",
        f"- 三科共{totals['questions']}题：简答{totals['simple']}题、论述{totals['essay']}题。",
        f"- 名词解释标注共{totals['name_tags']}处。",
        f"- 名解标签均位于对应定义／扩容之后且处于条目末尾；条目有效字符中位数为{statistics.median(name_entry_lengths):g}，最短为{min(name_entry_lengths)}。",
        "- 星级格式、题型标记、Markdown加粗、序号层级和旧扩容标记检查均通过。",
        "- 所有题目的主体／含扩容容量均处于参考带或已在例外说明中给出题型依据。",
        f"- 速背Word关键词精确重合自动复核剩余{len(candidate_rows)}条未决候选；已逐条人工排除{len(MANUAL_KEYWORD_EXCLUSIONS)}类假阳性。",
        "",
        "## 分科题数",
        "",
    ]
    for subject, count, simple, essay in subject_summary:
        summary_lines.append(f"- {subject}：{count}题（简答{simple}，论述{essay}）。")
    summary_lines.extend(("", "## 关键词人工判定", ""))
    for (subject, index, term), reason in MANUAL_KEYWORD_EXCLUSIONS.items():
        summary_lines.append(f"- {subject}第{index}题“{term}”：无需重复标注；{reason}。")
    summary_lines.extend(("", "## 容量例外说明", ""))
    for subject, index, status, base, total, note in capacities:
        if status != "通过":
            summary_lines.append(f"- {subject}第{index}题：主体{base}字、含扩容{total}字；{note}。")
    summary_lines.extend(
        (
            "",
            "## 人工终校范围",
            "",
            "- 逐题核对题干、题型、速背采分点、一本通／教材扩容、关键词、序号和名解准入。",
            "- 第160题因完整答案容量过大，拆为第160—161题；两题分别承载核心概念与流程／模型。",
            "- 最终排版另行检查正文12磅一致性、章节另起页、空白页和页面尾部留白。",
            "",
        )
    )
    REPORT.write_text("\n".join(summary_lines), encoding="utf-8")
    print(
        f"PASS questions={totals['questions']} simple={totals['simple']} "
        f"essay={totals['essay']} keyword_candidates={len(candidate_rows)}"
    )


if __name__ == "__main__":
    main()
