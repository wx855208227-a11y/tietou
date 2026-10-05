from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re

from audit_shenzhen_baoming_v7_sources import EXPECTED_QUESTIONS, source_chapter, split_chapters, split_questions
from rebuild_shenzhen_baoming_v16_reverse_keywords import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    SUBJECT_BUILDERS,
    SUBJECT_SOURCES,
    TERM_ALIASES,
    build_experiment,
    build_general,
    build_measurement,
    canonical,
    scoped_speed_terms,
)
from validate_shenzhen_baoming_v15_source_keywords import answer_body, explicit_terms, plain


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题关键词反向守恒复核报告V16.md"
LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题关键词去向台账V16.tsv"


SUBJECTS = {
    "普通心理学": (GENERAL_OUTPUT, build_general),
    "实验心理学": (EXPERIMENT_OUTPUT, build_experiment),
    "心理与教育测量": (MEASUREMENT_OUTPUT, build_measurement),
}


def marked_terms(answer: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\*\*([^*]+)\*\*", answer_body(answer)))


def term_is_marked(term: str, marked: tuple[str, ...]) -> bool:
    candidates = (term, TERM_ALIASES.get(term, term))
    return any(
        canonical(candidate)
        and any(
            canonical(candidate) in canonical(value) or canonical(value) in canonical(candidate)
            for value in marked
            if canonical(value)
        )
        for candidate in candidates
    )


def term_is_present(term: str, answer: str) -> bool:
    return canonical(term) in canonical(plain(answer_body(answer)))


def main() -> None:
    rows: list[dict[str, str]] = []
    totals = Counter()

    for subject, (manual_path, builder) in SUBJECTS.items():
        actual = manual_path.read_text(encoding="utf-8")
        expected = builder()
        assert actual == expected, (subject, "stale generated artifact")
        speed = SUBJECT_SOURCES[subject].read_text(encoding="utf-8")
        chapters = split_chapters(speed)
        questions = split_questions(actual)
        assert len(questions) == EXPECTED_QUESTIONS[subject], (subject, len(questions))

        prior = SUBJECT_BUILDERS[subject]().replace("**", "")
        assert actual.replace("**", "") == prior, (subject, "content changed outside keyword formatting")

        for index, (chapter, title, answer) in enumerate(questions, start=1):
            assert not re.search(r"^### .*\*\*", answer), (subject, index, "bold in question")
            marked = marked_terms(answer)
            assert len(marked) >= 4, (subject, index, "too few keyword marks")
            local_source = source_chapter(subject, chapter, chapters)
            points = explicit_terms(subject, title)
            assert points, (subject, index, "empty independent scoring-point checklist")

            for term in points:
                assert term_is_present(term, answer), (subject, index, "missing scoring point", term)
                assert term_is_marked(term, marked), (subject, index, "unmarked scoring point", term)
                rows.append(
                    {
                        "科目": subject,
                        "序号": str(index),
                        "题目": plain(title),
                        "来源关键词": term,
                        "来源类型": "独立采分点清单",
                        "去向": "正文或紧邻扩容",
                        "标注结果": "已加粗",
                    }
                )
                totals["points"] += 1

            for term in scoped_speed_terms(local_source, points):
                totals["source_terms"] += 1
                if not term_is_present(term, answer):
                    totals["source_not_called"] += 1
                    continue
                assert term_is_marked(term, marked), (
                    subject,
                    index,
                    "speed-manual keyword appears in answer but is unmarked",
                    term,
                )
                rows.append(
                    {
                        "科目": subject,
                        "序号": str(index),
                        "题目": plain(title),
                        "来源关键词": term,
                        "来源类型": "本题知识块原加粗／下划线",
                        "去向": "正文或紧邻扩容",
                        "标注结果": "已加粗",
                    }
                )
                totals["source_present"] += 1

            definitions = tuple(re.findall(r"【名词解释：([^】]+)】", answer_body(answer)))
            for term in definitions:
                assert term_is_marked(term, marked), (subject, index, "unmarked definition term", term)
            totals["definitions"] += len(definitions)
            totals["marked"] += len(marked)
            totals["questions"] += 1

    assert totals["questions"] == 160, totals

    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题关键词反向守恒复核报告V16

## 复核结论

- 逐题先读取本题对应的速背手册知识块，再核对答案；不再从答案中已经出现的词反推来源关键词。
- 160题共{totals['points']}个独立来源采分点，全部在对应答案中保留并加粗。
- 另有{totals['source_present']}次本题知识块原加粗／下划线词在答案中出现，全部完成对应标注；短词和嵌入句中的关键词不再因“相邻中文字符”被误删。
- 共核对{totals['definitions']}次名词解释调用；正文共保留{totals['marked']}处关键词标注。
- 与V15相比，本轮只重建关键词边界和位置，去除加粗后正文内容完全一致，题目、采分点、扩容和答案层级未被改动。

## 标注规则

1. 独立采分点清单中的词必须在答案中出现并加粗。
2. 速背手册本题知识块中原加粗／下划线的词，只要答案调用了该表述，就必须在最对应的答案位置加粗。
3. 同一关键词原则上定位到最对应的一处，避免在总起、分点和总结中机械重复加粗。
4. 名词解释名称优先标在定义所在行；题干不混入正文关键词加粗。
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} points={totals['points']} "
        f"source_present={totals['source_present']} definitions={totals['definitions']} "
        f"marked={totals['marked']}"
    )


if __name__ == "__main__":
    main()
