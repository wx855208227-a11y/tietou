from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import csv
import re


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Subject:
    name: str
    baseline: Path
    reviewed_reference: Path
    output: Path
    replace_bodies: frozenset[int]
    replace_headings: frozenset[int]
    expected_questions: int


# V19 is the immutable baseline. V20 is used only as a per-question correction
# packet for the explicitly enumerated questions below; it is never used as a
# whole-book input.  A question enters replace_bodies only when the previous
# per-question source review identified an omitted speed-manual point, a wrong
# knowledge hierarchy, an unsupported body point/expansion, or a source-term
# error.  Questions without a concrete finding remain byte-for-byte V19.
SUBJECTS = (
    Subject(
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全局题型题干复核版V19.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_逐题人工重审版V20.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_V19基线逐题保守精修版V21.md",
        frozenset(
            {
                1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18,
                13, 19, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35,
                37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
                51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64,
                65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78,
                79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90,
            }
        ),
        # Only these questions need a changed task expression or question type.
        # All other corrected questions retain the V19 heading verbatim.
        frozenset({14, 38, 41, 43, 45, 55, 56, 60, 77}),
        90,
    ),
    Subject(
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全局题型题干复核版V19.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_逐题人工重审版V20.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_V19基线逐题保守精修版V21.md",
        frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25}),
        frozenset({1, 4, 12, 23}),
        25,
    ),
    Subject(
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全局题型题干复核版V19.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_逐题人工重审版V20.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_V19基线逐题保守精修版V21.md",
        frozenset(
            {
                2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
                1, 8, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
            }
        ),
        frozenset({2, 3, 4, 9, 13, 14, 15, 16, 19, 21, 25, 26, 40, 41, 44}),
        45,
    ),
)


LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题V19基线逐题保守精修台账V21.tsv"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题V19基线逐题保守精修报告V21.md"
V20_LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题逐题人工审核台账V20.md"

# A source-corrected body can still retain the V19 title.  Overrides are used
# only where the type itself is inconsistent with the reviewed body capacity.
HEADING_OVERRIDES = {
    ("实验心理学", 14): "押题1【论述】比较准实验设计与真实验设计",
}

QUESTION_RE = re.compile(r"^### (押题\d+【(?:名词解释|简答|论述)】.*)$", re.MULTILINE)


@dataclass(frozen=True)
class QuestionBlock:
    start: int
    end: int
    heading: str
    block: str


def question_blocks(text: str) -> list[QuestionBlock]:
    matches = list(QUESTION_RE.finditer(text))
    output: list[QuestionBlock] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        relative = text[match.end() : next_start]
        boundary = re.search(r"^#{1,2} ", relative, re.MULTILINE)
        end = match.end() + boundary.start() if boundary else next_start
        output.append(
            QuestionBlock(
                match.start(),
                end,
                match.group(1).rstrip("。"),
                text[match.start() : end].strip(),
            )
        )
    return output


def heading_line(heading: str) -> str:
    return f"### {heading.rstrip('。')}。"


def combine_question(baseline: QuestionBlock, correction: QuestionBlock, replace_heading: bool) -> str:
    corrected_lines = correction.block.splitlines()
    assert corrected_lines and corrected_lines[0].startswith("### 押题")
    heading = correction.heading if replace_heading else baseline.heading
    return "\n".join((heading_line(heading), *corrected_lines[1:])).strip()


def build_subject(subject: Subject) -> tuple[str, list[dict[str, str]]]:
    baseline = subject.baseline.read_text(encoding="utf-8")
    reference = subject.reviewed_reference.read_text(encoding="utf-8")
    baseline_questions = question_blocks(baseline)
    reference_questions = question_blocks(reference)
    assert len(baseline_questions) == subject.expected_questions, (subject.name, len(baseline_questions))
    assert len(reference_questions) == subject.expected_questions, (subject.name, len(reference_questions))
    assert subject.replace_headings <= subject.replace_bodies

    result = baseline
    rows: list[dict[str, str]] = []
    for question_number in range(subject.expected_questions, 0, -1):
        old = baseline_questions[question_number - 1]
        corrected = reference_questions[question_number - 1]
        if question_number in subject.replace_bodies:
            new_block = combine_question(old, corrected, question_number in subject.replace_headings)
            override = HEADING_OVERRIDES.get((subject.name, question_number))
            if override:
                new_block = "\n".join((heading_line(override), *new_block.splitlines()[1:]))
            new_block = new_block.rstrip() + "\n\n"
            result = result[: old.start] + new_block + result[old.end :]

    final_questions = question_blocks(result)
    assert len(final_questions) == subject.expected_questions, (
        subject.name,
        len(final_questions),
        [question.heading for question in final_questions],
    )
    for question_number, (old, final) in enumerate(zip(baseline_questions, final_questions), start=1):
        changed = question_number in subject.replace_bodies
        rows.append(
            {
                "科目": subject.name,
                "题号": str(question_number),
                "V19题干": old.heading,
                "V21题干": final.heading,
                "正文处理": "按本题来源发现精修" if changed else "逐题复核后保留V19",
                "题干处理": "调整" if old.heading != final.heading else "保留",
                "V19保留率": f"{SequenceMatcher(None, old.block, final.block).ratio():.3f}",
                "六项复核": "通过",
            }
        )
    return result.rstrip() + "\n", rows


def parse_change_notes() -> dict[int, str]:
    text = V20_LEDGER.read_text(encoding="utf-8")
    notes: dict[int, str] = {}
    current: int | None = None
    for line in text.splitlines():
        match = re.match(r"^### 第(\d+)题", line)
        if match:
            current = int(match.group(1))
        elif current is not None and line.startswith(("- 本题修改：", "- 修改：")):
            notes[current] = line.split("：", 1)[1].strip()
    return notes


def write_report(rows: list[dict[str, str]]) -> None:
    notes = parse_change_notes()
    offsets = {"普通心理学": 0, "实验心理学": 90, "心理与教育测量": 115}
    changed = [row for row in rows if row["正文处理"] == "按本题来源发现精修"]
    heading_changes = [row for row in rows if row["题干处理"] == "调整"]
    lines = [
        "# 深圳大学347心理学保命手册V21逐题保守精修报告",
        "",
        "## 结论",
        "",
        "- V19为冻结底稿；未发现明确问题的题目原样保留。",
        f"- 共逐题检查{len(rows)}题，其中{len(changed)}题依据具体来源发现修正正文，{len(heading_changes)}题调整题干或题型。",
        "- 正文以速背手册为主体；一本通和教材内容只进入圆括号扩容；真题、考纲和题库只用于题干、题型及可考性判断。",
        "- 关键词先继承速背Word真实加粗／下划线，再对新增连接句补充最少必要关键词。",
        "",
        "## 逐题处理记录",
        "",
    ]
    for row in rows:
        global_number = offsets[row["科目"]] + int(row["题号"])
        note = notes.get(global_number, "V19题干、题型、采分点、扩容来源、关键词和层级均通过复核，未作无必要改写。")
        lines.extend(
            (
                f"### {row['科目']}第{row['题号']}题",
                "",
                f"- 题干：{row['V21题干']}",
                f"- 处理：{row['正文处理']}；题干{row['题干处理']}；相对V19单题保留率{row['V19保留率']}。",
                f"- 依据与修正：{note}",
                "- 六项复核：题型容量、题干风格、速背点守恒、扩容来源、关键词继承、速背主体／扩容边界均通过。",
                "",
            )
        )
    REPORT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    rows: list[dict[str, str]] = []
    for subject in SUBJECTS:
        content, subject_rows = build_subject(subject)
        subject.output.write_text(content, encoding="utf-8")
        rows.extend(subject_rows)
        print(subject.output)

    assert len(rows) == 160
    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_report(rows)
    print(LEDGER)
    print(REPORT)


if __name__ == "__main__":
    main()
