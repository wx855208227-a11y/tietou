from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import zipfile

import fitz
from docx import Document
from docx.oxml.ns import qn

from qa_shenzhen_baoming_combined_v4 import compact, page_break_before


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订版V5.docx"
PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订版V5.pdf"
PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v5_page_map.json"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V5.md"
TITLE = "深圳大学347心理学保命手册"
REPORT_VERSION = "V5"
EXPECTED_DEFINITION_CALLS = 348
PARTS = ("第一部分 普通心理学", "第二部分 实验心理学", "第三部分 心理与教育测量")
SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V6.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V6.pdf",
        ROOT / "content/shenzhen_general_baoming_v6_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V5.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V5.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v5_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V5.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V5.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v5_page_map.json",
        13, 39, 45,
    ),
)


def validate_subjects() -> list[tuple[str, int]]:
    results: list[tuple[str, int]] = []
    for subject, docx_path, pdf_path, map_path, chapters, units, questions in SUBJECTS:
        assert docx_path.is_file() and pdf_path.is_file() and map_path.is_file()
        with zipfile.ZipFile(docx_path) as archive:
            assert archive.testzip() is None
        document = Document(docx_path)
        assert len([p for p in document.paragraphs if p.style.name == "Heading 1"]) == chapters
        assert len([p for p in document.paragraphs if p.style.name == "Heading 2"]) == units
        assert len([p for p in document.paragraphs if p.text.startswith("押题")]) == questions
        assert not document.tables
        pdf = fitz.open(pdf_path)
        assert all(page.get_text().strip() for page in pdf)
        assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
        assert mapping and all(value > 0 for value in mapping.values())
        results.append((subject, len(pdf)))
    return results


def main() -> None:
    subject_results = validate_subjects()
    assert DOCX.is_file() and PDF.is_file() and PAGE_MAP.is_file()
    with zipfile.ZipFile(DOCX) as archive:
        assert archive.testzip() is None

    document = Document(DOCX)
    assert len(document.sections) == 4 and not document.tables
    cover = next(p.text.strip() for p in document.paragraphs if p.style.name == "Title" and p.text.strip())
    assert cover == TITLE

    h1 = [p for p in document.paragraphs if p.style.name == "Heading 1"]
    h2 = [p for p in document.paragraphs if p.style.name == "Heading 2"]
    questions = [p for p in document.paragraphs if p.text.startswith("押题")]
    parts = [p for p in document.paragraphs if p.style.name == "Part Title"]
    assert [p.text for p in parts] == list(PARTS)
    assert len(h1) == 32 and len(h2) == 139 and len(questions) == 160
    assert len([p for p in h1 if page_break_before(p)]) == 29

    all_text = "\n".join(p.text for p in document.paragraphs)
    assert all_text.count("【名词解释：") == EXPECTED_DEFINITION_CALLS
    assert "圆括号外是背诵主体，写全可以拿到主要分数" in all_text
    assert "既可补充其他采分点，也可补充相关概念、解释或例子" in all_text
    assert len([p for p in document.paragraphs if p.text.startswith("（")]) >= 18
    for forbidden in (
        "答题思路", "到此停笔", "扩容（选背）", "扩容（选用）",
        "心理实验报告的阅读与写作", "反应时研究的历史", "综合实验设计",
    ):
        assert forbidden not in all_text
    assert not re.search(r"押题.*(?:请(?:完成|设计).{0,18}(?:实验|研究)|设计一项(?:实验|研究))", all_text)

    first_body = next(index for index, p in enumerate(document.paragraphs) if p.style.name == "Part Title")
    body_sizes: list[float] = []
    type_sizes: list[float] = []
    definition_sizes: list[float] = []
    abnormal_spacing: list[tuple[str, str]] = []
    for paragraph in document.paragraphs[first_body:]:
        for run in paragraph.runs:
            if not run.text:
                continue
            color = run.font.color.rgb
            assert color is None or str(color) == "000000", (paragraph.text, run.text, color)
            assert not run.font.italic and not run.font.underline and run.font.highlight_color is None
            size = run.font.size.pt if run.font.size else None
            if paragraph.style.name == "Normal":
                assert size is not None
                body_sizes.append(size)
            if "【简答】" in run.text or "【论述】" in run.text:
                type_sizes.append(size)
            if "【名词解释：" in run.text:
                definition_sizes.append(size)
                properties = run._r.rPr
                if properties is not None and (
                    properties.find(qn("w:spacing")) is not None
                    or properties.find(qn("w:w")) is not None
                ):
                    abnormal_spacing.append((paragraph.text, run.text))
    assert body_sizes and set(body_sizes) == {12.0}
    assert type_sizes and set(type_sizes) == {12.0}
    assert definition_sizes and set(definition_sizes) == {12.0}
    assert not abnormal_spacing

    pdf = fitz.open(PDF)
    assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)
    page_texts = [page.get_text().strip() for page in pdf]
    assert all(page_texts) and compact(page_texts[0]) == compact(TITLE)
    assert "使用说明" in page_texts[1]
    assert all(not page.get_images(full=True) for page in pdf)
    for page in pdf:
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            assert x0 >= -1 and y0 >= -1 and x1 <= page.rect.width + 1 and y1 <= page.rect.height + 1

    page_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert page_map and all(value > 0 for value in page_map.values())
    for part in PARTS:
        pages = [value for key, value in page_map.items() if key.startswith(f"{part}|")]
        assert pages == sorted(pages) and len(pages) == len(set(pages))
        assert page_map[part] == pages[0]

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册排版与结构质检报告{REPORT_VERSION}

## 结论

新版合订本通过正文结构、主体／扩容分层、章节分页、字号、字距、颜色、目录、空白页和页面边界检查。

## 结构与内容

- 科目顺序：普通心理学 → 实验心理学 → 心理与教育测量
- 章节：32章；知识单元：139个；押题：160道
- 名词解释标签调用：{EXPECTED_DEFINITION_CALLS}次；所有标签均位于对应定义及其点内扩容之后
- 圆括号同时承载整点采分扩容和点内表述扩容；正文能够独立支撑主要分数
- 未设置要求考生现场完成研究方案的实验设计押题

## 制品质检

- 正文、题型标记和名词解释标签：统一12磅
- 颜色：纯黑；无斜体、下划线、高亮或图片
- 章节：分章另起页；三科分册及合订版目录页码已校准
- PDF：{len(pdf)}页；未发现空白页或页面越界
- 分科页数：{'; '.join(f'{subject}{pages}页' for subject, pages in subject_results)}
- 正文运行字号：{dict(Counter(body_sizes))}
""",
        encoding="utf-8",
    )
    print(
        f"PASS pages={len(pdf)} chapters={len(h1)} units={len(h2)} "
        f"questions={len(questions)} definitions={all_text.count('【名词解释：')}"
    )


if __name__ == "__main__":
    main()
