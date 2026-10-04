from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import re

from audit_shenzhen_baoming_v13_sources import base as source_base
from audit_shenzhen_baoming_v7_sources import (
    EXPECTED_QUESTIONS,
    source_chapter,
    split_chapters,
    split_questions,
    trace,
)
from rebuild_shenzhen_baoming_v15_source_keywords import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    SUBJECT_SOURCES,
    align_question_keywords,
    build_experiment,
    build_general,
    build_measurement,
    compact,
    source_keywords,
)
from validate_shenzhen_baoming_v14_point_integrity import (
    explicit_terms as explicit_terms_v14,
    validate_no_singletons,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题来源边界与关键词复核报告V15.md"
POINT_LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题采分点完整性台账V15.tsv"
KEYWORD_LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题关键词覆盖台账V15.tsv"


SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": SUBJECT_SOURCES["普通心理学"],
        "yibentong": source_base.SOURCE_ROOT / "普通心理学/一本通.md",
        "build": build_general,
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": SUBJECT_SOURCES["实验心理学"],
        "yibentong": source_base.SOURCE_ROOT / "实验心理学/一本通.md",
        "build": build_experiment,
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": SUBJECT_SOURCES["心理与教育测量"],
        "yibentong": source_base.SOURCE_ROOT / "心理与教育测量/一本通.md",
        "build": build_measurement,
    },
}


POINT_OVERRIDES_V15 = {
    ("普通心理学", "比较内隐记忆和外显记忆"): (
        "外显记忆", "内隐记忆", "加工深度", "保持时间", "记忆负荷量", "呈现方式", "干扰因素",
    ),
}


def plain(value: str) -> str:
    return re.sub(r"[*`#]", "", value)


def explicit_terms(subject: str, title: str) -> tuple[str, ...]:
    clean_title = plain(title)
    for (wanted_subject, fragment), terms in POINT_OVERRIDES_V15.items():
        if subject == wanted_subject and fragment in clean_title:
            return terms
    return explicit_terms_v14(subject, title)


def outside_expansions(value: str) -> str:
    pattern = re.compile(r"（(?!\d+）)[^（）]*）")
    previous = None
    while previous != value:
        previous = value
        value = pattern.sub("", value)
    return value


def marked_terms(answer: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\*\*([^*]+)\*\*", answer))


def covered(term: str, marked: tuple[str, ...]) -> bool:
    wanted = compact(term)
    for value in marked:
        candidate = compact(value)
        if wanted in candidate or candidate in wanted:
            return True
        wanted_grams = {wanted[index : index + 2] for index in range(max(0, len(wanted) - 1))}
        candidate_grams = {
            candidate[index : index + 2] for index in range(max(0, len(candidate) - 1))
        }
        if wanted_grams and len(wanted_grams & candidate_grams) / len(wanted_grams) >= 0.66:
            return True
    return False


def answer_body(block: str) -> str:
    lines = block.splitlines()[1:]
    kept: list[str] = []
    for line in lines:
        if line == "---" or line.startswith("# ") or line.startswith("## "):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def main() -> None:
    point_rows: list[dict[str, str]] = []
    keyword_rows: list[dict[str, str]] = []
    totals = Counter()

    for subject, config in SUBJECTS.items():
        expected = config["build"]()
        actual = config["manual"].read_text(encoding="utf-8")
        assert actual == expected.rstrip() + "\n", (subject, "generated artifact is stale")
        validate_no_singletons(actual, subject)
        assert not re.search(r"(?m)^### .*\*\*", actual), (subject, "bold marker in question title")
        assert "正文加粗处为需要优先记忆的关键词" in actual

        speed_text = config["speed"].read_text(encoding="utf-8")
        ybt_text = config["yibentong"].read_text(encoding="utf-8")
        speed_chapters = split_chapters(speed_text)
        ybt_chapters = split_chapters(ybt_text)
        questions = split_questions(actual)
        assert len(questions) == EXPECTED_QUESTIONS[subject], (subject, len(questions))

        for index, (chapter, title, answer) in enumerate(questions, start=1):
            answer = answer_body(answer)
            local_speed = source_chapter(subject, chapter, speed_chapters)
            local_ybt = source_chapter(subject, chapter, ybt_chapters)
            source_terms = source_keywords(local_speed)
            marked = marked_terms(answer)
            assert len(marked) >= 3, (subject, index, title, "too few keyword marks")
            assert align_question_keywords(answer, local_speed) == answer, (
                subject, index, title, "keyword normalization is not idempotent"
            )

            answer_without_tags = re.sub(r"【[^】]+】", "", plain(answer))
            present_source_terms = tuple(term for term in source_terms if term in answer_without_tags)
            resolved_source_terms = tuple(term for term in present_source_terms if covered(term, marked))

            definition_terms = set(re.findall(r"【名词解释：([^】]+)】", answer))
            unsupported_marks = [
                term
                for term in marked
                if compact(term) not in compact(local_speed)
                and compact(term) not in compact(local_ybt)
                and not covered(term, source_terms)
                and term not in definition_terms
            ]
            assert not unsupported_marks, (subject, index, title, "unsupported keyword marks", unsupported_marks)

            points = explicit_terms(subject, title)
            assert points, (subject, index, title, "empty point checklist")
            missing_points = [term for term in points if term not in plain(answer)]
            assert not missing_points, (subject, index, title, "missing source points", missing_points)
            local_source = local_speed + "\n" + local_ybt
            if subject == "心理与教育测量" and "比较智龄、年级当量和比率智商" in plain(title):
                local_source += "\n" + speed_text + "\n" + ybt_text
            formula_terms = {"K=ΔI/I", "P=KlgI", "X=T+E"}
            untraced = [
                term for term in points
                if term not in formula_terms and not trace(term, local_source)
            ]
            assert not untraced, (subject, index, title, "untraced source points", untraced)

            point_rows.append(
                {
                    "科目": subject,
                    "序号": str(index),
                    "章节": chapter,
                    "题目": plain(title),
                    "来源采分点": "；".join(points),
                    "点数": str(len(points)),
                    "结果": "完整覆盖",
                }
            )
            keyword_rows.append(
                {
                    "科目": subject,
                    "序号": str(index),
                    "章节": chapter,
                    "题目": plain(title),
                    "答案中可定位的速背关键词": str(len(present_source_terms)),
                    "消歧后已标注": str(len(resolved_source_terms)),
                    "实际加粗词组": str(len(marked)),
                    "结果": "规则标注完成",
                }
            )
            totals.update(
                questions=1,
                points=len(points),
                source_keywords=len(resolved_source_terms),
                marked=len(marked),
            )

    assert totals["questions"] == 160, totals

    memory_answer = next(
        answer_body(answer)
        for _, title, answer in split_questions(GENERAL_OUTPUT.read_text(encoding="utf-8"))
        if "比较内隐记忆和外显记忆" in plain(title)
    )
    body = outside_expansions(memory_answer)
    assert "意识参与不同" not in body
    assert "从意识参与角度看" in memory_answer
    for term in ("加工深度", "保持时间", "记忆负荷量", "呈现方式", "干扰因素"):
        assert term in body

    for path, rows in ((POINT_LEDGER, point_rows), (KEYWORD_LEDGER, keyword_rows)):
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册来源边界与关键词复核报告V15

## 结论

- 共160题、{totals['points']}个显式来源采分点，均能在答案与对应速背手册／一本通知识块中定位。
- 共有{totals['source_keywords']}次“答案已出现、速背原文将其作为标题／加粗／下划线内容，且通过重叠消歧”的关键词命中，均已在对应答案中加粗标注。
- 题干只使用标题样式，不再混入正文关键词加粗；正文共保留{totals['marked']}次关键词标注。
- “意识参与不同”不是速背手册在“内隐记忆与外显记忆的差异”中并列的五个采分点，已移入两个定义后的圆括号扩容；正文区别仅保留加工深度、保持时间、记忆负荷量、呈现方式和干扰因素五项。

## 硬规则

1. 速背手册直接列出的采分点才能作为同级正文理论点；根据定义归纳的额外角度放入紧邻扩容。
2. 关键词以速背手册的分点标题、加粗和下划线为基线；一般连接语、大段整句和题干不作关键词标注。
3. 关键词复核与采分点完整性复核分开：前者防止标注漏失或混乱，后者防止合并、压缩时静默删点。
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} points={totals['points']} "
        f"source_keywords={totals['source_keywords']} marked={totals['marked']}"
    )


if __name__ == "__main__":
    main()
