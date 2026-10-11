from __future__ import annotations

import csv
from pathlib import Path
import re

import build_shenzhen_baoming_v25_artifacts as build
import qa_shenzhen_baoming_v23_artifacts as qa
import rebuild_shenzhen_baoming_v25_dedup_capacity as rebuild


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
REPORT = DELIVERABLES / "深圳大学347心理学保命手册_V19完整范围去重容量校正版V25成品质检报告.md"
WORD_KEYWORDS = DELIVERABLES / "深圳大学347心理学保命手册_三科速背Word关键词基线V17.tsv"


def compact_keyword(value: str) -> str:
    return re.sub(r"[\s—－:：,，。；;、\"“”‘’（）()【】\[\]\.0-9]+", "", value)


def keyword_paragraph_in_scope(number: int) -> bool:
    return (
        574 <= number <= 634
        or 640 <= number <= 700
        or number in {710, 719}
        or 722 <= number <= 749
    )


def validate_source_keywords() -> dict[str, int]:
    texts = [
        rebuild.GENERAL_OUTPUT.read_text(encoding="utf-8"),
        rebuild.EXPERIMENT_OUTPUT.read_text(encoding="utf-8"),
        rebuild.MEASUREMENT_OUTPUT.read_text(encoding="utf-8"),
    ]
    combined = "\n".join(texts)
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", combined)
    marks = re.findall(r"\*\*([^*]+)\*\*", combined)
    with WORD_KEYWORDS.open(encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle, delimiter="\t")
            if row["科目"] == "实验心理学"
            and keyword_paragraph_in_scope(int(row["Word段落序号"]))
        ]
    absent: list[str] = []
    unmarked: list[str] = []
    for row in rows:
        term = row["原关键词"]
        normalized = compact_keyword(term)
        if len(normalized) < 2:
            continue
        if normalized not in compact_keyword(plain):
            absent.append(term)
            continue
        if not any(
            normalized in compact_keyword(mark) or compact_keyword(mark) in normalized
            for mark in marks
            if len(compact_keyword(mark)) >= 2
        ):
            unmarked.append(term)
    assert not absent, sorted(set(absent))
    assert not unmarked, sorted(set(unmarked))

    general = texts[0]
    duplicate_checks = (
        "**布罗德本特**",
        "**双耳分听实验**",
        "**衰减理论**",
        "**后期选择理论**",
        "**认知资源理论**",
        "**多存储模型**",
        "**感觉记忆**",
        "**短时记忆**",
        "**长时记忆**",
        "**假设检验说**",
        "**期望效用理论**",
        "**前景理论**",
    )
    for phrase in duplicate_checks:
        assert phrase in general, phrase
    return {"source_runs": len(rows), "answer_marks": len(marks)}


def clean_answer_length(block: str) -> int:
    return len(re.sub(r"\s+|[*#【】\[\]—]", "", block))


def question_lengths(text: str) -> list[tuple[str, int, str]]:
    starts = list(re.finditer(r"^### 押题\d+【(简答|论述)】([^\n]+)", text, re.MULTILINE))
    result: list[tuple[str, int, str]] = []
    for index, match in enumerate(starts):
        stop = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[match.end() : stop]
        block = re.split(r"\n(?=# |## )", block)[0]
        result.append((match.group(1), clean_answer_length(block), match.group(2)))
    return result


def validate_later_answer_lengths() -> dict[str, int]:
    text = rebuild.EXPERIMENT_OUTPUT.read_text(encoding="utf-8")
    later = text[text.index("# 第六章 注意") :]
    counts = {"简答": 0, "论述": 0}
    for kind, length, title in question_lengths(later):
        counts[kind] += 1
        if kind == "简答":
            assert 200 <= length <= 400, (title, length)
        else:
            assert 400 <= length <= 800, (title, length)
    assert counts == {"简答": 6, "论述": 1}
    return counts


def validate_full_lower_bounds() -> dict[str, object]:
    exceptions: list[tuple[str, int, str]] = []
    for subject, markdown_path, _docx_path, _page_map_path in build.SUBJECTS:
        for kind, length, title in question_lengths(markdown_path.read_text(encoding="utf-8")):
            if kind == "简答" and length < 200:
                exceptions.append((subject, length, title))
            if kind == "论述":
                assert length >= 400, (subject, title, length)
    assert exceptions == [("心理与教育测量", 196, "简述信度的含义及主要作用。")], exceptions
    return {"boundary_exceptions": exceptions}


def validate_ledgers() -> dict[str, int]:
    with rebuild.AUDIT_LEDGER.open(encoding="utf-8") as handle:
        audit_rows = list(csv.DictReader(handle, delimiter="\t"))
    with rebuild.POINT_LEDGER.open(encoding="utf-8") as handle:
        point_rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(audit_rows) == 15
    assert len(point_rows) == len(rebuild.v24.POINTS) == 49
    assert not any(not row["V25具体去向"].strip() for row in point_rows)
    return {"audit_units": len(audit_rows), "source_points": len(point_rows)}


def configure_qa() -> None:
    build.configure_base()
    qa.SUBJECTS = build.SUBJECTS
    qa.COMBINED_DOCX = build.COMBINED_DOCX
    qa.COMBINED_PAGE_MAP = build.COMBINED_PAGE_MAP
    qa.EXPECTED_COUNTS = rebuild.EXPECTED_COUNTS
    qa.validate_markdown_scope = rebuild.validate
    qa.configure_combined = build.configure_combined


def write_report(
    subject_word: dict[str, dict[str, int]],
    subject_pdf: dict[str, dict[str, object]],
    combined_word: dict[str, int],
    combined_pdf: dict[str, int],
    source_keywords: dict[str, int],
    answer_types: dict[str, int],
    ledger_stats: dict[str, int],
) -> None:
    lines = [
        "# 深圳大学347心理学保命手册V25成品质检报告",
        "",
        "## 结论",
        "",
        f"- 已复核实验补编{ledger_stats['audit_units']}个考点、{ledger_stats['source_points']}条速背采分点；每条均有主体、圆括号扩容或跨分册去重去向。",
        f"- 实验后五章最终为{answer_types['简答']}道简答、{answer_types['论述']}道论述，全部通过简答200—400字、论述400—800字的参考容量检查。",
        "- 全书未保留低于400字的论述题；仅测量‘信度的含义及主要作用’为196字的临界简答，具备定义、三项作用和总结，未为凑字数增加内容。",
        f"- 反向核对保留或迁移内容对应的速背Word关键词run {source_keywords['source_runs']}处，结果为0缺失、0漏标。",
        "- 三科Markdown、Word与合订本正文及关键词run一致；章节另起页，正文和题型／名解标签均为12磅。",
        "- 未发现孤立序号、空白页、异常字符间距、越界文字、无意义分页空白或实验设计题。",
        "",
        "## 数量",
        "",
    ]
    for subject, word in subject_word.items():
        pdf = subject_pdf[subject]
        lines.append(
            f"- {subject}：{word['chapters']}章，{word['units']}个考点，{word['questions']}道题，"
            f"{word['definitions']}处名词解释标注；PDF {pdf['pages']}页。"
        )
    lines.extend(
        (
            f"- 合订本：{combined_word['chapters']}章，{combined_word['units']}个考点，"
            f"{combined_word['questions']}道题；PDF {combined_pdf['pages']}页。",
            "",
            "## 低密度页说明",
            "",
        )
    )
    for subject, result in subject_pdf.items():
        value = "、".join(f"第{page}页（{count}字）" for page, count in result["sparse"])
        lines.append(f"- {subject}：{value or '无'}。")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_qa()
    source_keywords = validate_source_keywords()
    answer_types = validate_later_answer_lengths()
    validate_full_lower_bounds()
    ledger_stats = validate_ledgers()
    subject_word: dict[str, dict[str, int]] = {}
    subject_pdf: dict[str, dict[str, object]] = {}
    for subject, markdown_path, docx_path, page_map_path in build.SUBJECTS:
        subject_word[subject] = qa.validate_subject_word(subject, markdown_path, docx_path)
        subject_pdf[subject] = qa.validate_subject_pdf(
            subject,
            markdown_path,
            docx_path.with_suffix(".pdf"),
            page_map_path,
        )
        print(f"PASS {subject}")
    combined_word = qa.validate_combined_word(subject_word)
    combined_pdf = qa.validate_combined_pdf()
    write_report(
        subject_word,
        subject_pdf,
        combined_word,
        combined_pdf,
        source_keywords,
        answer_types,
        ledger_stats,
    )
    print(f"PASS combined pages={combined_pdf['pages']}")
    print(REPORT)


if __name__ == "__main__":
    main()
