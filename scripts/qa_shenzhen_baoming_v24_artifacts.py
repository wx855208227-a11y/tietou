from __future__ import annotations

import csv
from pathlib import Path
import re

import build_shenzhen_baoming_v24_artifacts as build
import qa_shenzhen_baoming_v23_artifacts as qa
import rebuild_shenzhen_baoming_v24_source_faithful as rebuild


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
REPORT = DELIVERABLES / "深圳大学347心理学保命手册_V19完整范围来源精校版V24成品质检报告.md"
WORD_KEYWORDS = DELIVERABLES / "深圳大学347心理学保命手册_三科速背Word关键词基线V17.tsv"


def compact_keyword(value: str) -> str:
    return re.sub(r"[\s—－:：,，。；;、\"“”‘’（）()【】\[\]\.0-9]+", "", value)


def validate_source_keywords() -> dict[str, int]:
    text = rebuild.EXPERIMENT_OUTPUT.read_text(encoding="utf-8")
    later = text[text.index("# 第六章 注意") :]
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", later)
    marks = re.findall(r"\*\*([^*]+)\*\*", later)
    with WORD_KEYWORDS.open(encoding="utf-8") as handle:
        rows = [
            row
            for row in csv.DictReader(handle, delimiter="\t")
            if row["科目"] == "实验心理学" and int(row["Word段落序号"]) >= 556
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
    return {"source_runs": len(rows), "answer_marks": len(marks)}


def validate_later_answer_lengths() -> dict[str, int]:
    text = rebuild.EXPERIMENT_OUTPUT.read_text(encoding="utf-8")
    later = text[text.index("# 第六章 注意") :]
    starts = list(re.finditer(r"^### 押题\d+【(简答|论述)】[^\n]+", later, re.MULTILINE))
    counts = {"简答": 0, "论述": 0}
    for index, match in enumerate(starts):
        stop = starts[index + 1].start() if index + 1 < len(starts) else len(later)
        block = later[match.end() : stop]
        block = re.split(r"\n#", block)[0]
        length = len(re.sub(r"\s+|[*#【】\[\]]", "", block))
        kind = match.group(1)
        counts[kind] += 1
        if kind == "简答":
            assert 140 <= length <= 430, (match.group(0), length)
        else:
            assert 340 <= length <= 850, (match.group(0), length)
    assert counts == {"简答": 15, "论述": 1}
    return counts


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
) -> None:
    lines = [
        "# 深圳大学347心理学保命手册V24成品质检报告",
        "",
        "## 结论",
        "",
        "- 普心、测量及实验前五章保持V19成熟正文；实验第六至十章已按速背Word整体重编。",
        f"- 反向核对实验后五章速背Word关键词run {source_keywords['source_runs']}处；进入答案的原关键词均已继承标注，答案共保留{source_keywords['answer_marks']}处关键词标记。",
        f"- 新编后五章共{answer_types['简答']}道简答、{answer_types['论述']}道论述；答案容量通过参考区间检查。",
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
    )
    print(f"PASS combined pages={combined_pdf['pages']}")
    print(REPORT)


if __name__ == "__main__":
    main()
