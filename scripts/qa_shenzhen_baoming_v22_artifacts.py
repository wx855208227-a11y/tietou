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

import build_shenzhen_baoming_v22_artifacts as build
import merge_shenzhen_baoming_manuals_v22 as combined
from merge_ecnu_baoming_manuals import compact, source_chapters
from qa_shenzhen_subject_artifacts_v17 import markdown_body_runs, word_body_runs


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_成品质检报告V22.md"

SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全范围复核版V22.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全范围复核版V22.docx",
        ROOT / "content/shenzhen_general_baoming_v22_page_map.json",
        (15, 75, 90, 239),
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全范围补编版V22.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全范围补编版V22.docx",
        ROOT / "content/shenzhen_experiment_baoming_v22_page_map.json",
        (10, 38, 39, 83),
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全范围复核版V22.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全范围复核版V22.docx",
        ROOT / "content/shenzhen_measurement_baoming_v22_page_map.json",
        (16, 42, 48, 72),
    ),
)


def page_break_before(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is None:
        return False
    element = properties.find(qn("w:pageBreakBefore"))
    return element is not None and element.get(qn("w:val"), "1") not in {
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


def subject_page_map(markdown: Path, pdf_path: Path) -> dict[str, int]:
    keys = build.heading_keys(markdown)
    with fitz.open(pdf_path) as pdf:
        pages = [compact(page.get_text()) for page in pdf]
    first_hits = [index for index, text in enumerate(pages) if compact(keys[0]) in text]
    assert len(first_hits) >= 2, (markdown.name, keys[0], first_hits)
    first_body = first_hits[-1]
    output: dict[str, int] = {}
    cursor = first_body
    for key in keys:
        needle = compact(key)
        found = next(index for index in range(cursor, len(pages)) if needle in pages[index])
        output[key] = found - first_body + 1
        cursor = found
    return output


def validate_word(
    subject: str,
    markdown: Path,
    docx_path: Path,
    expected: tuple[int, int, int, int],
) -> dict[str, int]:
    with zipfile.ZipFile(docx_path) as archive:
        xml = archive.read("word/document.xml")
    assert b"**" not in xml, (subject, "残留Markdown标记")

    document = Document(docx_path)
    chapters = [p for p in document.paragraphs if p.style.name == "Heading 1"]
    units = [p for p in document.paragraphs if p.style.name == "Heading 2"]
    questions = [p for p in document.paragraphs if p.text.startswith("押题")]
    definitions = [p for p in document.paragraphs if "【名词解释：" in p.text]
    assert (len(chapters), len(units), len(questions), len(definitions)) == expected
    assert not page_break_before(chapters[0])
    assert all(page_break_before(paragraph) for paragraph in chapters[1:])

    started = False
    question_markers = 0
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            started = True
        if not started:
            continue
        if paragraph.style.name not in {"Normal", "Heading 3"}:
            continue
        if not paragraph.text.strip():
            continue
        for run in paragraph.runs:
            if not run.text:
                continue
            size = effective_size(run, paragraph)
            assert size is None or abs(size - 12) < 0.01, (
                subject,
                "正文／题型标记字号不一致",
                paragraph.text,
                size,
            )
            assert run.font.underline in (None, False), (subject, "正文存在下划线")
            properties = run._r.rPr
            spacing = properties.find(qn("w:spacing")) if properties is not None else None
            assert spacing is None, (subject, "异常字符间距", paragraph.text)
            if paragraph.style.name == "Heading 3" and (
                "【简答】" in run.text or "【论述】" in run.text
            ):
                question_markers += 1
    expected_markers = sum(
        "【简答】" in paragraph.text or "【论述】" in paragraph.text
        for paragraph in questions
    )
    assert question_markers == expected_markers, (
        subject,
        question_markers,
        expected_markers,
    )

    expected_runs = markdown_body_runs(markdown)
    actual_runs = word_body_runs(docx_path)
    assert expected_runs == actual_runs, (subject, "Markdown与Word正文／关键词不一致")
    return {
        "chapters": len(chapters),
        "units": len(units),
        "questions": len(questions),
        "definitions": len(definitions),
    }


def validate_pdf(
    subject: str,
    markdown: Path,
    pdf_path: Path,
    page_map_path: Path,
) -> dict[str, int]:
    stored = json.loads(page_map_path.read_text(encoding="utf-8"))
    assert stored == subject_page_map(markdown, pdf_path), (subject, "目录页码不一致")
    first_key = build.heading_keys(markdown)[0]
    chapter_titles = [
        line[2:].strip()
        for line in markdown.read_text(encoding="utf-8").splitlines()
        if line.startswith("# 第") or line.startswith("# 补充章")
    ]
    with fitz.open(pdf_path) as pdf:
        texts = ["".join(page.get_text().split()) for page in pdf]
        assert all(len(text) >= 10 for text in texts), (subject, "存在空白页")
        first_hits = [index for index, text in enumerate(texts) if compact(first_key) in compact(text)]
        first_body = first_hits[-1]
        body_counts = [len(text) for text in texts[first_body:]]
        assert min(body_counts) >= 300, (subject, min(body_counts), "正文异常稀疏页")
        for number, page in enumerate(pdf, start=1):
            blocks = [block for block in page.get_text("blocks") if block[4].strip()]
            assert blocks, (subject, number, "空白页")
            assert max(block[3] for block in blocks) < page.rect.height - 18, (
                subject,
                number,
                "文字越界",
            )
        pages_compact = [compact(page.get_text()) for page in pdf]
        cursor = first_body
        for title in chapter_titles:
            needle = compact(title)
            found = next(index for index in range(cursor, len(pdf)) if needle in pages_compact[index])
            hits = pdf[found].search_for(title)
            assert hits and min(rect.y0 for rect in hits) < 130, (
                subject,
                title,
                found + 1,
                "章节未从新页页首开始",
            )
            cursor = found
    return {
        "pages": len(texts),
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
    document = Document(combined.base.OUTPUT)
    part_indexes = [
        index
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style.name == "Part Title"
    ]
    expected_titles = ["第一部分 普通心理学", "第二部分 实验心理学", "第三部分 心理与教育测量"]
    assert [document.paragraphs[index].text for index in part_indexes] == expected_titles
    for subject_index, (subject, _markdown, source_docx, _page_map, _expected) in enumerate(SUBJECTS):
        start = part_indexes[subject_index] + 1
        stop = part_indexes[subject_index + 1] if subject_index < 2 else len(document.paragraphs)
        actual = [
            paragraph_runs(paragraph)
            for paragraph in document.paragraphs[start:stop]
            if paragraph.style.name == "Normal" and paragraph.text
        ]
        expected = word_body_runs(source_docx)
        assert actual == expected, (subject, "合订版正文／关键词与分册不一致")

    counts = {
        "chapters": sum(p.style.name == "Heading 1" for p in document.paragraphs),
        "units": sum(p.style.name == "Heading 2" for p in document.paragraphs),
        "questions": sum(p.text.startswith("押题") for p in document.paragraphs),
        "definitions": sum("【名词解释：" in p.text for p in document.paragraphs),
    }
    assert counts == {"chapters": 41, "units": 155, "questions": 177, "definitions": 394}
    return counts


def actual_combined_page_map(pdf_path: Path) -> dict[str, int]:
    with fitz.open(pdf_path) as pdf:
        pages = [compact(page.get_text()) for page in pdf]
    part_pages: dict[str, int] = {}
    for part_title, _label, _header, _source in combined.base.SOURCES:
        hits = [index for index, text in enumerate(pages) if compact(part_title) in text]
        assert hits, part_title
        part_pages[part_title] = hits[-1]
    first_body = part_pages[combined.base.SOURCES[0][0]]
    output: dict[str, int] = {}
    for index, (part_title, _label, _header, source_path) in enumerate(combined.base.SOURCES):
        start = part_pages[part_title]
        stop = part_pages[combined.base.SOURCES[index + 1][0]] if index < 2 else len(pages)
        output[part_title] = start - first_body + 1
        cursor = start
        for chapter in source_chapters(Document(source_path)):
            found = next(i for i in range(cursor, stop) if compact(chapter) in pages[i])
            output[f"{part_title}|{chapter}"] = found - first_body + 1
            cursor = found
    return output


def validate_combined_pdf() -> dict[str, int]:
    pdf_path = combined.base.OUTPUT.with_suffix(".pdf")
    stored = json.loads(combined.base.PAGE_MAP_OUTPUT.read_text(encoding="utf-8"))
    assert stored == actual_combined_page_map(pdf_path), "合订版目录页码不一致"
    with fitz.open(pdf_path) as pdf:
        texts = ["".join(page.get_text().split()) for page in pdf]
        assert all(len(text) >= 10 for text in texts), "合订版存在空白页"
        for number, page in enumerate(pdf, start=1):
            blocks = [block for block in page.get_text("blocks") if block[4].strip()]
            assert blocks, (number, "合订版空白页")
            assert max(block[3] for block in blocks) < page.rect.height - 18, (
                number,
                "合订版文字越界",
            )
    return {"pages": len(texts)}


def main() -> None:
    scope = subprocess.run(
        (sys.executable, "scripts/validate_shenzhen_baoming_v22_scope.py"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    rows: list[str] = []
    for subject, markdown, docx_path, page_map, expected in SUBJECTS:
        word = validate_word(subject, markdown, docx_path, expected)
        pdf = validate_pdf(subject, markdown, docx_path.with_suffix(".pdf"), page_map)
        rows.append(
            f"- {subject}：{word['chapters']}章、{word['units']}节、{word['questions']}题、"
            f"{word['definitions']}处名解；PDF {pdf['pages']}页，正文单页最少"
            f"{pdf['min_body_chars']}个文本字符。"
        )

    combined_word = validate_combined_word()
    combined_pdf = validate_combined_pdf()
    report = f"""# 深圳大学347心理学保命手册成品质检报告V22

## 结论

- 内容结构：{scope.replace(chr(10), '；')}。
- 三科合计：{combined_word['chapters']}章、{combined_word['units']}节、{combined_word['questions']}题、{combined_word['definitions']}处名词解释标注。
- 合订顺序：普通心理学 → 实验心理学 → 心理与教育测量。
- 合订版：PDF {combined_pdf['pages']}页。

## 分科结果

{chr(10).join(rows)}

## 已检查项目

- 普心、实验、测量逐章检查；实验心理学完整覆盖十章，未再出现第六章以后整体缺失。
- 逐题Markdown与Word正文、关键词加粗一致；合订版正文与三科分册一致。
- 各章另起一页；目录页码与最终PDF正文位置一致。
- 正文、【简答／论述】标记和【名词解释】标记采用12磅规格；未发现异常字符间距、下划线或残留Markdown标记。
- PDF逐页检查通过：无空白页、无文字越界、无仅剩少量尾点或总结单独占页的异常稀疏正文页。
- 全文未编“请设计实验”类题目；未发现孤立的（1）层级。
"""
    REPORT.write_text(report, encoding="utf-8")
    print("PASS V22 artifact QA")
    print(*rows, sep="\n")
    print(f"PASS combined pages={combined_pdf['pages']}")


if __name__ == "__main__":
    main()
