from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import zipfile

import fitz
from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订版V2.docx"
PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订版V2.pdf"
PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v2_page_map.json"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版质检报告V2.md"
TITLE = "深圳大学347心理学保命手册"
PARTS = ("第一部分 普通心理学", "第二部分 实验心理学", "第三部分 心理与教育测量")
SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V3.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V3.pdf",
        ROOT / "content/shenzhen_general_baoming_v3_page_map.json",
        15,
        75,
        90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V2.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V2.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v2_page_map.json",
        5,
        27,
        27,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V2.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V2.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v2_page_map.json",
        13,
        39,
        45,
    ),
)


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def page_break_before(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is None:
        return False
    element = properties.find(qn("w:pageBreakBefore"))
    return element is not None and element.get(qn("w:val"), "1") not in {"0", "false", "off"}


def validate_subject_artifacts() -> list[tuple[str, int]]:
    results: list[tuple[str, int]] = []
    for subject, docx_path, pdf_path, page_map_path, chapters, units, questions in SUBJECTS:
        assert docx_path.is_file() and pdf_path.is_file() and page_map_path.is_file()
        with zipfile.ZipFile(docx_path) as archive:
            assert archive.testzip() is None
        document = Document(docx_path)
        assert len([p for p in document.paragraphs if p.style.name == "Heading 1"]) == chapters
        assert len([p for p in document.paragraphs if p.style.name == "Heading 2"]) == units
        assert len([p for p in document.paragraphs if p.text.startswith("押题")]) == questions
        assert not document.tables
        subject_text = "\n".join(p.text for p in document.paragraphs)
        assert "\t000" not in subject_text
        assert "综合实验设计" not in subject_text
        pdf = fitz.open(pdf_path)
        assert all(page.get_text().strip() for page in pdf)
        assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)
        mapping = json.loads(page_map_path.read_text(encoding="utf-8"))
        assert mapping and all(value > 0 for value in mapping.values())
        results.append((subject, len(pdf)))
    return results


def main() -> None:
    subject_results = validate_subject_artifacts()
    assert DOCX.is_file() and PDF.is_file() and PAGE_MAP.is_file()
    with zipfile.ZipFile(DOCX) as archive:
        assert archive.testzip() is None

    document = Document(DOCX)
    assert len(document.sections) == 4, len(document.sections)
    assert not document.tables
    cover = next(
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.style.name == "Title" and paragraph.text.strip()
    )
    assert cover == TITLE, cover

    h1 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 1"]
    h2 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 2"]
    questions = [paragraph for paragraph in document.paragraphs if paragraph.text.startswith("押题")]
    parts = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Part Title"]
    assert [paragraph.text for paragraph in parts] == list(PARTS)
    assert len(h1) == 33 and len(h2) == 141 and len(questions) == 162
    assert len([paragraph for paragraph in h1 if page_break_before(paragraph)]) == 30

    all_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert all_text.count("【名词解释：") == 347
    for forbidden in ("答题思路", "到此停笔", "扩容（选背）", "扩容（选用）", "综合实验设计"):
        assert forbidden not in all_text
    assert not re.search(r"押题.*(?:请(?:完成|设计).{0,18}(?:实验|研究)|设计一项(?:实验|研究))", all_text)

    first_body = next(index for index, paragraph in enumerate(document.paragraphs) if paragraph.style.name == "Part Title")
    body_sizes: list[float] = []
    type_sizes: list[float] = []
    definition_sizes: list[float] = []
    non_black: list[tuple[str, str, str]] = []
    forbidden_styles: list[tuple[str, str]] = []
    abnormal_spacing: list[tuple[str, str]] = []
    for paragraph in document.paragraphs[first_body:]:
        for run in paragraph.runs:
            if not run.text:
                continue
            color = run.font.color.rgb
            if color is not None and str(color) != "000000":
                non_black.append((paragraph.text, run.text, str(color)))
            if run.font.italic or run.font.underline or run.font.highlight_color is not None:
                forbidden_styles.append((paragraph.text, run.text))
            size = run.font.size.pt if run.font.size else None
            if paragraph.style.name == "Normal":
                assert size is not None, (paragraph.text, run.text)
                body_sizes.append(size)
            if "【简答】" in run.text or "【论述】" in run.text:
                type_sizes.append(size)
            if "【名词解释：" in run.text:
                definition_sizes.append(size)
                properties = run._r.rPr
                if properties is not None and (
                    properties.find(qn("w:spacing")) is not None or properties.find(qn("w:w")) is not None
                ):
                    abnormal_spacing.append((paragraph.text, run.text))

    assert body_sizes and set(body_sizes) == {12.0}
    assert type_sizes and set(type_sizes) == {12.0}
    assert definition_sizes and set(definition_sizes) == {12.0}
    assert not non_black and not forbidden_styles and not abnormal_spacing

    pdf = fitz.open(PDF)
    assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)
    page_texts = [page.get_text().strip() for page in pdf]
    assert all(page_texts), [index + 1 for index, text in enumerate(page_texts) if not text]
    assert compact(page_texts[0]) == compact(TITLE)
    assert "使用说明" in page_texts[1]
    assert all(not page.get_images(full=True) for page in pdf)
    assert all(
        span["color"] == 0
        for page in pdf
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
    )
    for page in pdf:
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            assert x0 >= -1 and y0 >= -1 and x1 <= page.rect.width + 1 and y1 <= page.rect.height + 1

    page_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert all(value > 0 for value in page_map.values())
    assert "000" not in "\n".join(page_texts[:8])
    for part in PARTS:
        chapter_pages = [value for key, value in page_map.items() if key.startswith(f"{part}|")]
        assert chapter_pages == sorted(chapter_pages)
        assert len(chapter_pages) == len(set(chapter_pages)), (part, chapter_pages)
        assert page_map[part] == chapter_pages[0]

    body_start = next(index for index, text in enumerate(page_texts) if compact(PARTS[0]) in compact(text) and index > 2)
    char_counts = [len(compact(text)) for text in page_texts[body_start:]]
    sparse_pages = [body_start + index + 1 for index, count in enumerate(char_counts) if count < 120]
    assert not sparse_pages, sparse_pages

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册排版质检报告V2

## 结论

合订本通过结构、分页、字号、字距、颜色、目录、空白页和PDF边界检查，可用于黑白打印与直接背诵。

## 检查结果

- 成品：`{DOCX.name}`、`{PDF.name}`
- PDF页数：{len(pdf)}页
- 科目顺序：普通心理学 → 实验心理学 → 心理与教育测量
- 章节：33章；知识单元：141个；押题：162道
- 名词解释标签调用：347次
- 正文、题型标记、名词解释标签字号：统一12磅
- 颜色：纯黑；无斜体、下划线、高亮或图片
- 分页：三科均另起一页，各章另起一页；未发现空白页、稀疏页或页面越界
- 目录：分科与章节页码均已回填，无占位页码
- 内容禁项：未发现要求考生完成实验设计的押题

## 分科成品

{chr(10).join(f'- {subject}：{pages}页，DOCX／PDF／目录页码检查通过' for subject, pages in subject_results)}

## 字号统计

- 正文运行：{dict(Counter(body_sizes))}
- 简答／论述题型标记：{dict(Counter(type_sizes))}
- 名词解释标签：{dict(Counter(definition_sizes))}
""",
        encoding="utf-8",
    )
    print(
        "PASS "
        f"pages={len(pdf)} chapters={len(h1)} units={len(h2)} questions={len(questions)} "
        f"definitions={all_text.count('【名词解释：')} body_sizes={Counter(body_sizes)}"
    )


if __name__ == "__main__":
    main()
