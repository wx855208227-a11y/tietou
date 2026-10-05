from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import re

from docx import Document

from audit_shenzhen_baoming_v7_sources import EXPECTED_QUESTIONS, source_chapter, split_chapters, split_questions
from rebuild_shenzhen_baoming_v17_word_keywords import (
    EXPERIMENT_OUTPUT,
    GENERAL_OUTPUT,
    MEASUREMENT_OUTPUT,
    SUBJECT_BUILDERS,
    SUBJECT_DOCX,
    TERM_ALIASES,
    align_question,
    build_experiment,
    build_general,
    build_measurement,
    clean_word_term,
    explicit_terms,
    formatted_paragraph,
    keyword_spans,
    mark_line,
    merged_terms,
    restore_source_wording,
    run_emphasized,
    scoped_word_keywords,
    source_assignment,
    strict_projection,
    structural_assignment,
    usable_spans,
    word_source_markdown,
)
from validate_shenzhen_baoming_v15_source_keywords import answer_body, plain


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题Word原关键词逐词校准报告V17.md"
LEDGER = ROOT / "deliverables/深圳大学347心理学保命手册_160题Word原关键词去向台账V17.tsv"
BASELINE = ROOT / "deliverables/深圳大学347心理学保命手册_三科速背Word关键词基线V17.tsv"

SUBJECTS = {
    "普通心理学": (GENERAL_OUTPUT, build_general),
    "实验心理学": (EXPERIMENT_OUTPUT, build_experiment),
    "心理与教育测量": (MEASUREMENT_OUTPUT, build_measurement),
}


def marked_terms(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\*\*([^*]+)\*\*", value))


def marked(term: str, values: tuple[str, ...]) -> bool:
    wanted, _ = strict_projection(term)
    return bool(wanted) and any(wanted in strict_projection(value)[0] for value in values)


def structurally_represented(term: str, values: tuple[str, ...]) -> bool:
    wanted = strict_projection(term)[0].replace("的", "")
    if not wanted:
        return False
    for value in values:
        candidate = strict_projection(value)[0].replace("的", "")
        if candidate and (candidate in wanted or wanted in candidate):
            return True
    return False


def direct_word_baseline() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for subject, path in SUBJECT_DOCX.items():
        for paragraph_index, paragraph in enumerate(Document(path).paragraphs, start=1):
            if not paragraph.text.strip():
                continue
            for run_index, run in enumerate(paragraph.runs, start=1):
                if not run.text.strip() or not run_emphasized(run):
                    continue
                term = clean_word_term(run.text)
                if not term:
                    continue
                rows.append(
                    {
                        "科目": subject,
                        "Word段落序号": str(paragraph_index),
                        "Run序号": str(run_index),
                        "段落样式": paragraph.style.name,
                        "原关键词": term,
                        "加粗": "是" if run.bold is True else "否",
                        "下划线": "是" if bool(run.underline) else "否",
                        "所在原句": paragraph.text.strip(),
                    }
                )
    return rows


def main() -> None:
    totals = Counter()
    rows: list[dict[str, str]] = []

    for subject, (manual_path, builder) in SUBJECTS.items():
        actual = manual_path.read_text(encoding="utf-8")
        assert actual == builder(), (subject, "stale generated artifact")
        assert "****" not in actual, (subject, "invalid adjacent bold markers")
        assert not re.search(r"(?m)^### .*\*\*", actual), (subject, "bold in question")

        direct_source = word_source_markdown(SUBJECT_DOCX[subject])
        saved_source = SUBJECT_DOCX[subject].with_suffix(".md").read_text(encoding="utf-8")
        assert direct_source == saved_source, (subject, "Word formatting snapshot drift")
        chapters = split_chapters(direct_source)

        prior = SUBJECT_BUILDERS[subject]().rstrip() + "\n"
        # V17 may restore a missing “的” only when the exact Word keyword contains it.
        assert actual.replace("**", "").replace("的", "") == prior.replace("**", "").replace("的", ""), (
            subject,
            "content changed beyond source-wording restoration",
        )

        actual_questions = split_questions(actual)
        prior_questions = split_questions(prior)
        assert len(actual_questions) == EXPECTED_QUESTIONS[subject]
        assert len(actual_questions) == len(prior_questions)

        for question_index, ((chapter, title, answer), (_, prior_title, prior_answer)) in enumerate(
            zip(actual_questions, prior_questions), start=1
        ):
            assert plain(title) == plain(prior_title)
            local_source = source_chapter(subject, chapter, chapters)
            expected, keywords, restorations = align_question(subject, title, prior_answer, local_source)
            assert answer == expected, (subject, question_index, "answer alignment drift")

            idempotent, _, second_restorations = align_question(subject, title, answer, local_source)
            assert idempotent == answer, (subject, question_index, "not idempotent")
            assert not second_restorations, (subject, question_index, second_restorations)

            body = answer_body(answer)
            body_marks = marked_terms(body)
            definition_terms = tuple(re.findall(r"【名词解释：([^】]+)】", body))
            for term in explicit_terms(subject, title):
                assert structurally_represented(term, body_marks), (
                    subject,
                    question_index,
                    "unmarked scoring label",
                    term,
                )
            for term in definition_terms:
                assert structurally_represented(TERM_ALIASES.get(term, term), body_marks), (
                    subject,
                    question_index,
                    "unmarked definition",
                    term,
                )

            plain_lines = [line.replace("**", "") for line in answer.splitlines()]
            restored_lines, replayed = restore_source_wording(
                plain_lines.copy(), keywords, definition_terms
            )
            assert not replayed, (subject, question_index, replayed)
            structural = structural_assignment(subject, title, restored_lines, definition_terms)
            sourced = source_assignment(restored_lines, keywords, definition_terms)
            for line_index, line in enumerate(restored_lines):
                expected_line = mark_line(
                    line,
                    merged_terms(
                        structural.get(line_index, []),
                        sourced.get(line_index, []),
                    ),
                )
                assert expected_line == answer.splitlines()[line_index], (
                    subject,
                    question_index,
                    line_index,
                    "line-level boundary mismatch",
                )

            for keyword in keywords:
                candidates = [
                    index for index, line in enumerate(restored_lines)
                    if not line.startswith("#") and line != "---" and keyword_spans(line, keyword)
                ]
                destinations = [
                    index for index, terms in sourced.items() if keyword.term in terms
                ]
                status = "答案未调用"
                destination = ""
                if candidates:
                    assert destinations, (subject, question_index, "unassigned Word keyword", keyword)
                    destination = "｜".join(restored_lines[index] for index in destinations)
                    status = "按原词原边界加粗"
                    totals["word_keywords_called"] += 1
                else:
                    totals["word_keywords_not_called"] += 1
                rows.append(
                    {
                        "科目": subject,
                        "题号": str(question_index),
                        "题目": plain(title),
                        "锚点": keyword.anchor,
                        "Word原关键词": keyword.term,
                        "Word所在原句": plain(keyword.context),
                        "答案去向": destination,
                        "结果": status,
                    }
                )

            totals["questions"] += 1
            totals["marks"] += len(body_marks)
            totals["definitions"] += len(definition_terms)
            totals["restorations"] += len(restorations)

    assert totals["questions"] == 160, totals

    general = GENERAL_OUTPUT.read_text(encoding="utf-8")
    expected_definition = "（1）**外显记忆**：**过去经验**对当前作业产生的**有意识的影响**。"
    assert expected_definition in general, "external-memory keyword boundary regression"
    assert "**当前作业**" not in general
    assert "**过去经验对当前作业" not in general

    with LEDGER.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    baseline_rows = direct_word_baseline()
    with BASELINE.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(baseline_rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(baseline_rows)

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题Word原关键词逐词校准报告V17

## 结论

- 三科速背手册均直接读取原始Word；Word解析结果与留存Markdown快照逐字一致。
- 共复核160题、{len(baseline_rows)}个Word原始加粗／下划线run；本题来源范围内有{totals['word_keywords_called']}次原关键词被答案调用，全部按原词和原边界标注。
- 另有{totals['word_keywords_not_called']}次本题来源范围内的Word关键词未被答案调用，台账明确记录为“答案未调用”，没有借关键词校准擅自增加采分点。
- 共保留{totals['definitions']}次名词解释标注、{totals['marks']}处最终加粗；仅有{totals['restorations']}处为恢复Word关键词而补回“的”，其余正文、题目、采分点、扩容和层级与V15内容底稿一致。
- 回归样例已固定：外显记忆只突出“过去经验”和“有意识的影响”，不突出“当前作业”，也不把整句合并加粗。

## 校准规则

1. 关键词来源是速背手册Word正文的加粗和下划线字符区间，不从保命手册反向猜词。
2. 同一概念重复出现时，优先采用专门定义段及其完整定义正文，不采用覆盖面更宽的概括段替代。
3. 原关键词只有在对应答案实际调用时才进入答案；未调用的内容不为凑覆盖率强行补入。
4. 分点名称和名词解释名称属于结构性提示，可独立加粗；正文关键词仍严格服从Word原边界。
5. 普通连接语位于两个关键词之间时保持常规字重，不把相邻采分词机械扩展为整句加粗。
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} called={totals['word_keywords_called']} "
        f"not_called={totals['word_keywords_not_called']} definitions={totals['definitions']} "
        f"marks={totals['marks']} restorations={totals['restorations']} baseline_runs={len(baseline_rows)}"
    )


if __name__ == "__main__":
    main()
