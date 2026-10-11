from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pymupdf
from docx import Document
from docx.oxml.ns import qn

import merge_ecnu_baoming_manuals as merger
from build_shenzhen_baoming_v19_final_artifacts import compact, heading_keys
from build_shenzhen_baoming_v23_artifacts import (
    COMBINED_DOCX,
    COMBINED_PAGE_MAP,
    SUBJECTS,
    configure_combined,
)
from qa_shenzhen_baoming_v19_final_artifacts import paragraph_runs
from qa_shenzhen_subject_artifacts_v17 import markdown_body_runs, word_body_runs
from rebuild_shenzhen_baoming_v23_v19_complete import (
    EXPECTED_COUNTS,
    validate as validate_markdown_scope,
)


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
REPORT = DELIVERABLES / "深圳大学347心理学保命手册_V19完整范围排版优化版V23成品质检报告.md"


def page_break_before(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is None:
        return False
    node = properties.find(qn("w:pageBreakBefore"))
    return node is not None and node.get(qn("w:val"), "1") not in {
        "0",
        "false",
        "off",
    }


def effective_size(run, paragraph) -> float | None:
    if run.font.size is not None:
        return run.font.size.pt
    if paragraph.style.font.size is not None:
        return paragraph.style.font.size.pt
    return None


def question_blocks(text: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r"^### 押题", text, re.MULTILINE)]
    return [
        text[start : starts[index + 1] if index + 1 < len(starts) else len(text)]
        for index, start in enumerate(starts)
    ]


def assert_no_isolated_numbering(markdown_path: Path) -> None:
    text = markdown_path.read_text(encoding="utf-8")
    failures: list[tuple[str, str]] = []
    for block in question_blocks(text):
        title = block.splitlines()[0]
        lines = block.splitlines()[1:]
        primary_positions = [
            index for index, line in enumerate(lines) if re.match(r"^\d+\.\s", line)
        ]
        if len(primary_positions) == 1:
            failures.append((title, "孤立一级序号"))
        primary_bounds = primary_positions + [len(lines)]
        for p_index, start in enumerate(primary_positions):
            stop = primary_bounds[p_index + 1]
            secondary_positions = [
                index
                for index in range(start + 1, stop)
                if re.match(r"^（\d+）", lines[index])
            ]
            if len(secondary_positions) == 1:
                failures.append((title, "孤立（1）"))
            secondary_bounds = secondary_positions + [stop]
            for s_index, secondary_start in enumerate(secondary_positions):
                secondary_stop = secondary_bounds[s_index + 1]
                circled_positions = [
                    index
                    for index in range(secondary_start + 1, secondary_stop)
                    if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", lines[index])
                ]
                if len(circled_positions) == 1:
                    failures.append((title, "孤立①"))
                circled_bounds = circled_positions + [secondary_stop]
                for c_index, circled_start in enumerate(circled_positions):
                    circled_stop = circled_bounds[c_index + 1]
                    alpha = [
                        index
                        for index in range(circled_start + 1, circled_stop)
                        if re.match(r"^[a-z]\.\s", lines[index])
                    ]
                    if len(alpha) == 1:
                        failures.append((title, "孤立a."))
    assert not failures, (markdown_path.name, failures[:20])


def validate_subject_word(
    subject: str,
    markdown_path: Path,
    docx_path: Path,
) -> dict[str, int]:
    text = markdown_path.read_text(encoding="utf-8")
    validate_markdown_scope(subject, text)
    assert_no_isolated_numbering(markdown_path)
    forbidden_design = [
        line
        for line in text.splitlines()
        if line.startswith("### 押题")
        and re.search(r"请设计|设计一项|如何设计.{0,10}实验", line)
    ]
    assert not forbidden_design, forbidden_design

    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml")
    assert b"**" not in xml

    document = Document(docx_path)
    expected_chapters, expected_units, expected_questions = EXPECTED_COUNTS[subject]
    h1 = [p for p in document.paragraphs if p.style.name == "Heading 1"]
    h2 = [p for p in document.paragraphs if p.style.name == "Heading 2"]
    questions = [p for p in document.paragraphs if p.text.startswith("押题")]
    definitions = [p for p in document.paragraphs if "【名词解释：" in p.text]
    assert (len(h1), len(h2), len(questions)) == (
        expected_chapters,
        expected_units,
        expected_questions,
    )
    assert not page_break_before(h1[0])
    assert all(page_break_before(paragraph) for paragraph in h1[1:])

    body_started = False
    min_spacing = 10.0
    min_after = 10.0
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            body_started = True
        if not body_started:
            continue
        if paragraph.style.name == "Normal" and paragraph.text.strip():
            spacing = paragraph.paragraph_format.line_spacing
            if isinstance(spacing, (int, float)):
                min_spacing = min(min_spacing, float(spacing))
            after = paragraph.paragraph_format.space_after
            if after is not None:
                min_after = min(min_after, after.pt)
            for run in paragraph.runs:
                if not run.text:
                    continue
                size = effective_size(run, paragraph)
                assert size is None or abs(size - 12) < 0.01, (
                    subject,
                    paragraph.text,
                    size,
                )
                spacing_node = run._r.get_or_add_rPr().find(qn("w:spacing"))
                assert spacing_node is None, (subject, "异常字距", paragraph.text)
        elif paragraph.style.name == "Heading 3" and paragraph.text.startswith("押题"):
            for run in paragraph.runs:
                if not run.text:
                    continue
                size = effective_size(run, paragraph)
                assert size is None or abs(size - 12) < 0.01, (
                    subject,
                    paragraph.text,
                    size,
                )
    assert min_spacing >= 1.45, (subject, min_spacing)
    assert min_after >= 3.0, (subject, min_after)
    assert markdown_body_runs(markdown_path) == word_body_runs(docx_path)
    return {
        "chapters": len(h1),
        "units": len(h2),
        "questions": len(questions),
        "definitions": len(definitions),
    }


def actual_subject_page_map(markdown_path: Path, pdf_path: Path) -> dict[str, int]:
    keys = heading_keys(markdown_path)
    with pymupdf.open(pdf_path) as pdf:
        pages = [compact(page.get_text()) for page in pdf]
    first_hits = [index for index, page in enumerate(pages) if compact(keys[0]) in page]
    assert len(first_hits) >= 2
    first_body_page = first_hits[-1]
    mapping: dict[str, int] = {}
    cursor = first_body_page
    for key in keys:
        needle = compact(key)
        found = next(index for index in range(cursor, len(pages)) if needle in pages[index])
        mapping[key] = found - first_body_page + 1
        cursor = found
    return mapping


def validate_subject_pdf(
    subject: str,
    markdown_path: Path,
    pdf_path: Path,
    page_map_path: Path,
) -> dict[str, object]:
    inventory = subprocess.run(
        (
            sys.executable,
            str(Path.home() / ".codex/skills/intern-agent-pdf-ocr-batch/scripts/pdf_inventory.py"),
            str(pdf_path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    assert inventory.returncode == 0
    stored = json.loads(page_map_path.read_text(encoding="utf-8"))
    assert stored == actual_subject_page_map(markdown_path, pdf_path)

    keys = heading_keys(markdown_path)
    chapter_needles = {
        compact(key) for key in keys if key.startswith("第") or key.startswith("补充章")
    }
    with pymupdf.open(pdf_path) as pdf:
        texts = ["".join(page.get_text().split()) for page in pdf]
        assert all(len(text) >= 10 for text in texts), (subject, "空白页")
        first_hits = [index for index, text in enumerate(texts) if compact(keys[0]) in compact(text)]
        first_body = first_hits[-1]
        sparse: list[tuple[int, int]] = []
        for index in range(first_body, len(texts)):
            count = len(texts[index])
            if count < 450:
                sparse.append((index + 1, count))
                if index + 1 < len(texts):
                    next_text = compact(texts[index + 1])
                    assert any(needle in next_text for needle in chapter_needles), (
                        subject,
                        index + 1,
                        count,
                        "低密度页后不是强制另起的章节",
                    )
            page = pdf[index]
            blocks = [block for block in page.get_text("blocks") if block[4].strip()]
            assert blocks
            assert max(block[3] for block in blocks) < page.rect.height - 10
    return {
        "pages": len(texts),
        "body_pages": len(texts) - first_body,
        "sparse": sparse,
    }


def validate_combined_word(subject_results: dict[str, dict[str, int]]) -> dict[str, int]:
    configure_combined()
    document = Document(COMBINED_DOCX)
    part_indexes = [
        index
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style.name == "Part Title"
    ]
    assert [document.paragraphs[index].text for index in part_indexes] == [
        "第一部分 普通心理学",
        "第二部分 实验心理学",
        "第三部分 心理与教育测量",
    ]
    assert len(part_indexes) == 3
    for subject_index, (subject, _markdown, source_docx, _page_map) in enumerate(SUBJECTS):
        start = part_indexes[subject_index] + 1
        stop = part_indexes[subject_index + 1] if subject_index < 2 else len(document.paragraphs)
        actual = [
            paragraph_runs(paragraph)
            for paragraph in document.paragraphs[start:stop]
            if paragraph.style.name == "Normal" and paragraph.text
        ]
        assert actual == word_body_runs(source_docx), subject
    result = {
        key: sum(value[key] for value in subject_results.values())
        for key in ("chapters", "units", "questions", "definitions")
    }
    assert sum(p.style.name == "Heading 1" for p in document.paragraphs) == result["chapters"]
    assert sum(p.style.name == "Heading 2" for p in document.paragraphs) == result["units"]
    assert sum(p.text.startswith("押题") for p in document.paragraphs) == result["questions"]
    return result


def validate_combined_pdf() -> dict[str, int]:
    configure_combined()
    pdf_path = COMBINED_DOCX.with_suffix(".pdf")
    inventory = subprocess.run(
        (
            sys.executable,
            str(Path.home() / ".codex/skills/intern-agent-pdf-ocr-batch/scripts/pdf_inventory.py"),
            str(pdf_path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )
    assert inventory.returncode == 0
    stored = json.loads(COMBINED_PAGE_MAP.read_text(encoding="utf-8"))
    actual = merger.extract_page_map(pdf_path)
    assert stored == actual
    with pymupdf.open(pdf_path) as pdf:
        texts = ["".join(page.get_text().split()) for page in pdf]
        assert all(len(text) >= 10 for text in texts)
        assert all(page.get_text().strip() for page in pdf)
        assert all(
            max(block[3] for block in page.get_text("blocks") if block[4].strip())
            < page.rect.height - 10
            for page in pdf
        )
    return {"pages": len(texts)}


def write_report(
    subject_word: dict[str, dict[str, int]],
    subject_pdf: dict[str, dict[str, object]],
    combined_word: dict[str, int],
    combined_pdf: dict[str, int],
) -> None:
    lines = [
        "# 深圳大学347心理学保命手册V23成品质检报告",
        "",
        "## 结论",
        "",
        "- 三科Markdown、Word与合订本内容一致，正文和关键词run未在排版中丢失。",
        "- 章节均另起页；未发现空白页、异常字符间距、越界文字或由分页链造成的异常低密度页。",
        "- 正文及【简答／论述】【名词解释】均为12磅；正文行距不低于1.45倍、段后距不低于3磅，已取消V19少数单元的单倍行距紧缩。",
        "- 所有低密度正文页均位于章节末尾，下一页为按规则另起的新章，不属于可消除的异常空白。",
        "- 未发现孤立的1.、（1）、①或a.层级；未设置要求考生自行设计实验的题目。",
        "",
        "## 数量",
        "",
    ]
    for subject in subject_word:
        word = subject_word[subject]
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
    subject_word: dict[str, dict[str, int]] = {}
    subject_pdf: dict[str, dict[str, object]] = {}
    for subject, markdown_path, docx_path, page_map_path in SUBJECTS:
        subject_word[subject] = validate_subject_word(subject, markdown_path, docx_path)
        subject_pdf[subject] = validate_subject_pdf(
            subject,
            markdown_path,
            docx_path.with_suffix(".pdf"),
            page_map_path,
        )
        print(f"PASS {subject}")
    combined_word = validate_combined_word(subject_word)
    combined_pdf = validate_combined_pdf()
    write_report(subject_word, subject_pdf, combined_word, combined_pdf)
    print(f"PASS combined pages={combined_pdf['pages']}")
    print(REPORT)


if __name__ == "__main__":
    main()
