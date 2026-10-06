from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import fitz
from docx import Document
from docx.oxml.ns import qn

import merge_ecnu_baoming_manuals as merger
from build_shenzhen_baoming_v19_final_artifacts import (
    COMBINED_DOCX,
    COMBINED_PAGE_MAP,
    SUBJECTS,
    compact,
    configure_combined,
    heading_keys,
)
from merge_ecnu_baoming_manuals import source_chapters
from qa_shenzhen_subject_artifacts_v17 import markdown_body_runs, word_body_runs


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_V19原标准逐题终校成品质检报告.md"

EXPECTED = {
    "普通心理学": (15, 75, 90, 233),
    "实验心理学": (4, 25, 25, 48),
    "心理与教育测量": (13, 41, 46, 84),
}


def page_break_before(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is None:
        return False
    page_break = properties.find(qn("w:pageBreakBefore"))
    return page_break is not None and page_break.get(qn("w:val"), "1") not in {
        "0",
        "false",
        "off",
    }


def run_effective_size(run, paragraph) -> float | None:
    if run.font.size is not None:
        return run.font.size.pt
    if paragraph.style.font.size is not None:
        return paragraph.style.font.size.pt
    return None


def validate_subject_word(
    subject: str,
    markdown_path: Path,
    docx_path: Path,
) -> dict[str, int]:
    assert markdown_path.is_file() and docx_path.is_file()
    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml")
    assert b"**" not in xml

    document = Document(docx_path)
    chapters, units, questions, definitions = EXPECTED[subject]
    h1 = [p for p in document.paragraphs if p.style.name == "Heading 1"]
    h2 = [p for p in document.paragraphs if p.style.name == "Heading 2"]
    q = [p for p in document.paragraphs if p.text.startswith("押题")]
    d = [p for p in document.paragraphs if "【名词解释：" in p.text]
    assert (len(h1), len(h2), len(q), len(d)) == EXPECTED[subject]
    assert not page_break_before(h1[0])
    assert all(page_break_before(paragraph) for paragraph in h1[1:])

    body_started = False
    question_markers = 0
    definition_markers = 0
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            body_started = True
        if not body_started:
            continue
        if paragraph.style.name == "Normal" and paragraph.text.strip():
            assert paragraph.style.font.size is None or abs(paragraph.style.font.size.pt - 12) < 0.01
            for run in paragraph.runs:
                if not run.text:
                    continue
                size = run_effective_size(run, paragraph)
                assert size is None or abs(size - 12) < 0.01, (subject, paragraph.text, size)
                assert run.font.underline in (None, False)
                spacing = run._r.get_or_add_rPr().find(qn("w:spacing"))
                assert spacing is None, (subject, "异常字符间距", paragraph.text)
                if "【名词解释：" in run.text:
                    definition_markers += 1
        elif paragraph.style.name == "Heading 3" and paragraph.text.startswith("押题"):
            for run in paragraph.runs:
                if not run.text:
                    continue
                size = run_effective_size(run, paragraph)
                assert size is None or abs(size - 12) < 0.01, (subject, paragraph.text, size)
                if "【简答】" in run.text or "【论述】" in run.text:
                    question_markers += 1
        if "【名词解释：" in paragraph.text:
            definition_markers += int(not any("【名词解释：" in run.text for run in paragraph.runs))

    assert question_markers == questions
    assert definition_markers <= definitions

    wanted = markdown_body_runs(markdown_path)
    observed = word_body_runs(docx_path)
    assert wanted == observed, (subject, "Markdown与Word正文／关键词run不一致")
    return {
        "chapters": len(h1),
        "units": len(h2),
        "questions": len(q),
        "definitions": len(d),
    }


def actual_subject_page_map(markdown_path: Path, pdf_path: Path) -> dict[str, int]:
    keys = heading_keys(markdown_path)
    with fitz.open(pdf_path) as pdf:
        pages = [compact(page.get_text()) for page in pdf]
    hits = [index for index, value in enumerate(pages) if compact(keys[0]) in value]
    assert len(hits) >= 2
    first_body = hits[-1]
    cursor = first_body
    output: dict[str, int] = {}
    for key in keys:
        found = next(index for index in range(cursor, len(pages)) if compact(key) in pages[index])
        output[key] = found - first_body + 1
        cursor = found
    return output


def validate_pdf(
    subject: str,
    markdown_path: Path,
    pdf_path: Path,
    page_map_path: Path,
) -> dict[str, int]:
    assert pdf_path.is_file() and page_map_path.is_file()
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

    first_key = heading_keys(markdown_path)[0]
    with fitz.open(pdf_path) as pdf:
        page_text = ["".join(page.get_text().split()) for page in pdf]
        assert all(len(value) >= 10 for value in page_text), (subject, "存在空白页")
        body_hits = [index for index, value in enumerate(page_text) if compact(first_key) in compact(value)]
        first_body = body_hits[-1]
        body_counts = [len(value) for value in page_text[first_body:]]
        assert min(body_counts) >= 180, (subject, min(body_counts), "正文异常稀疏页")
        for page_number, page in enumerate(pdf, start=1):
            blocks = [block for block in page.get_text("blocks") if block[4].strip()]
            assert blocks, (subject, page_number, "空白页")
            assert max(block[3] for block in blocks) < page.rect.height - 18
    return {
        "pages": len(page_text),
        "body_pages": len(body_counts),
        "min_body_chars": min(body_counts),
    }


def paragraph_runs(paragraph) -> tuple[str, tuple[bool, ...]]:
    text: list[str] = []
    bold: list[bool] = []
    for run in paragraph.runs:
        for char in run.text:
            if char == "\u2060":
                continue
            text.append(char)
            bold.append(run.bold is True)
    plain = "".join(text)
    for match in re.finditer(r"【名词解释：[^】]+】", plain):
        bold[match.start() : match.end()] = [False] * (match.end() - match.start())
    return plain, tuple(bold)


def validate_combined_word() -> dict[str, int]:
    configure_combined()
    document = Document(COMBINED_DOCX)
    part_indexes = [
        index
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style.name == "Part Title"
    ]
    assert len(part_indexes) == 3
    assert [document.paragraphs[index].text for index in part_indexes] == [
        "第一部分 普通心理学",
        "第二部分 实验心理学",
        "第三部分 心理与教育测量",
    ]
    for subject_index, (subject, _markdown, source_docx, _page_map) in enumerate(SUBJECTS):
        start = part_indexes[subject_index] + 1
        stop = part_indexes[subject_index + 1] if subject_index < 2 else len(document.paragraphs)
        actual = [
            paragraph_runs(paragraph)
            for paragraph in document.paragraphs[start:stop]
            if paragraph.style.name == "Normal" and paragraph.text
        ]
        expected = word_body_runs(source_docx)
        assert actual == expected, (subject, len(actual), len(expected))

    assert sum(p.style.name == "Heading 1" for p in document.paragraphs) == 32
    assert sum(p.style.name == "Heading 2" for p in document.paragraphs) == 141
    assert sum(p.text.startswith("押题") for p in document.paragraphs) == 161
    assert sum("【名词解释：" in p.text for p in document.paragraphs) == 365
    return {"chapters": 32, "units": 141, "questions": 161, "definitions": 365}


def actual_combined_page_map(pdf_path: Path) -> dict[str, int]:
    configure_combined()
    with fitz.open(pdf_path) as pdf:
        pages = [compact(page.get_text()) for page in pdf]
    part_indexes: dict[str, int] = {}
    for part_title, _, _, _ in merger_sources():
        hits = [index for index, text in enumerate(pages) if compact(part_title) in text]
        assert hits, part_title
        part_indexes[part_title] = hits[-1]
    first_body = part_indexes["第一部分 普通心理学"]
    output: dict[str, int] = {}
    for index, (part_title, _, _, source_path) in enumerate(merger_sources()):
        start = part_indexes[part_title]
        stop = part_indexes[merger_sources()[index + 1][0]] if index < 2 else len(pages)
        output[part_title] = start - first_body + 1
        cursor = start
        for chapter in source_chapters(Document(source_path)):
            found = next(i for i in range(cursor, stop) if compact(chapter) in pages[i])
            output[f"{part_title}|{chapter}"] = found - first_body + 1
            cursor = found
    return output


def merger_sources():
    configure_combined()
    return merger.SOURCES


def validate_combined_pdf() -> dict[str, int]:
    pdf_path = COMBINED_DOCX.with_suffix(".pdf")
    assert pdf_path.is_file() and COMBINED_PAGE_MAP.is_file()
    stored = json.loads(COMBINED_PAGE_MAP.read_text(encoding="utf-8"))
    assert stored == actual_combined_page_map(pdf_path)
    with fitz.open(pdf_path) as pdf:
        texts = ["".join(page.get_text().split()) for page in pdf]
        assert all(len(value) >= 10 for value in texts)
        first_part = compact("第一部分 普通心理学")
        first_body = [index for index, value in enumerate(texts) if first_part in compact(value)][-1]
        body_counts = [len(value) for value in texts[first_body:]]
        assert min(body_counts) >= 180, min(body_counts)
        for page_number, page in enumerate(pdf, start=1):
            blocks = [block for block in page.get_text("blocks") if block[4].strip()]
            assert blocks, page_number
            assert max(block[3] for block in blocks) < page.rect.height - 18
    return {
        "pages": len(texts),
        "body_pages": len(body_counts),
        "min_body_chars": min(body_counts),
    }


def main() -> None:
    content_audit = subprocess.run(
        ("python3", "scripts/audit_shenzhen_baoming_v19_rechecked.py"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    subject_rows: list[tuple[str, dict[str, int], dict[str, int]]] = []
    for subject, markdown_path, docx_path, page_map_path in SUBJECTS:
        word = validate_subject_word(subject, markdown_path, docx_path)
        pdf = validate_pdf(subject, markdown_path, docx_path.with_suffix(".pdf"), page_map_path)
        subject_rows.append((subject, word, pdf))

    combined_word = validate_combined_word()
    combined_pdf = validate_combined_pdf()
    rows = "\n".join(
        f"- {subject}：{word['chapters']}章、{word['units']}节、{word['questions']}题、"
        f"{word['definitions']}处名解；PDF {pdf['pages']}页，正文单页最少"
        f"{pdf['min_body_chars']}个文本字符。"
        for subject, word, pdf in subject_rows
    )
    report = f"""# 深圳大学347心理学保命手册V19原标准逐题终校成品质检报告

## 结论

- 内容质检：{content_audit}
- 三科合计：{combined_word['chapters']}章、{combined_word['units']}节、{combined_word['questions']}题、{combined_word['definitions']}处名词解释标注。
- 合订顺序：普通心理学 → 实验心理学 → 心理与教育测量。
- 合订版：PDF {combined_pdf['pages']}页；正文单页最少{combined_pdf['min_body_chars']}个文本字符。

## 分科结果

{rows}

## 已检查项目

- 逐题内容稿与成品Word逐段一致，Markdown关键词加粗完整继承。
- 各章另起一页；目录页码与最终PDF正文位置逐项一致。
- 正文、题型标记和名词解释标记均采用12磅正文规格；未发现异常字符间距、下划线或残留Markdown符号。
- PDF逐页检查通过：无空白页、无越界文字、无仅剩总结或尾点单独占页的异常稀疏正文页。
- 封面仅保留手册名称；未使用V20／V21正文或编制规则。
"""
    REPORT.write_text(report, encoding="utf-8")
    print("PASS V19 final artifacts QA")
    print(rows)
    print(
        f"PASS combined pages={combined_pdf['pages']} "
        f"min_body_chars={combined_pdf['min_body_chars']}"
    )


if __name__ == "__main__":
    main()
