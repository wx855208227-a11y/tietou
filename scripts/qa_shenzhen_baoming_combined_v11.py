from __future__ import annotations

import json
from pathlib import Path
import re

import fitz
from docx import Document

import merge_shenzhen_baoming_manuals_v11 as merge_v11
import qa_shenzhen_baoming_combined_v10 as previous
from merge_ecnu_baoming_manuals import compact, source_chapters


ROOT = Path(__file__).resolve().parents[1]

previous.previous.base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V11.docx"
previous.previous.base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V11.pdf"
previous.previous.base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v11_page_map.json"
previous.previous.base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V11.md"
previous.previous.base.REPORT_VERSION = "V11"
previous.previous.base.EXPECTED_DEFINITION_CALLS = 360
previous.previous.base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V12.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V12.pdf",
        ROOT / "content/shenzhen_general_baoming_v12_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V11.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V11.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v11_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V11.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V11.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v11_page_map.json",
        13, 39, 45,
    ),
)


def validate_exact_page_map() -> None:
    pdf = fitz.open(previous.previous.base.PDF)
    pages = [compact(page.get_text()) for page in pdf]
    actual: dict[str, int] = {}
    part_indexes: dict[str, int] = {}
    for part_title, _, _, _ in merge_v11.base.SOURCES:
        hits = [index for index, text in enumerate(pages) if compact(part_title) in text]
        assert hits, part_title
        part_indexes[part_title] = hits[-1]
    first_body = part_indexes[merge_v11.base.SOURCES[0][0]]

    for subject_index, source_spec in enumerate(merge_v11.base.SOURCES):
        part_title, _, _, source_path = source_spec
        start = part_indexes[part_title]
        stop = (
            part_indexes[merge_v11.base.SOURCES[subject_index + 1][0]]
            if subject_index + 1 < len(merge_v11.base.SOURCES)
            else len(pages)
        )
        actual[part_title] = start - first_body + 1
        cursor = start
        for chapter in source_chapters(Document(source_path)):
            found = next(index for index in range(cursor, stop) if compact(chapter) in pages[index])
            actual[f"{part_title}|{chapter}"] = found - first_body + 1
            cursor = found

    stored = json.loads(previous.previous.base.PAGE_MAP.read_text(encoding="utf-8"))
    assert actual == stored, "合订目录页码与最终PDF正文页码不一致"


def body_blocks(page: fitz.Page) -> list[tuple]:
    return sorted(
        [
            block
            for block in page.get_text("blocks")
            if block[4].strip() and block[1] > 70 and block[3] < 750
        ],
        key=lambda block: (block[1], block[0]),
    )


def validate_pagination() -> tuple[float, int]:
    document = Document(previous.previous.base.DOCX)
    paragraphs = document.paragraphs
    for index, paragraph in enumerate(paragraphs):
        text = paragraph.text.strip()
        if text.startswith("综上") and index:
            assert not paragraphs[index - 1].paragraph_format.keep_with_next, (
                "总结前文形成分页长链",
                paragraphs[index - 1].text,
                text,
            )
        if re.match(r"^（(?!\d+）)", text) and index:
            assert not paragraphs[index - 1].paragraph_format.keep_with_next, (
                "独立扩容段反向绑定前文",
                paragraphs[index - 1].text,
                text,
            )

    pdf = fitz.open(previous.previous.base.PDF)
    continuation_blanks: list[float] = []
    continuation_pages = 0
    for index in range(1, len(pdf)):
        current = body_blocks(pdf[index])
        preceding = body_blocks(pdf[index - 1])
        if not current or not preceding:
            continue
        first = "".join(current[0][4].split())
        if not re.match(r"^(?:[（(][1-9]|[①②③④⑤⑥⑦⑧⑨⑩]|[1-9]\.|[a-z]\.)", first):
            continue
        continuation_pages += 1
        blank = 750 - max(block[3] for block in preceding)
        continuation_blanks.append(blank)
        assert blank <= 90, (index + 1, blank, first[:80])

    return max(continuation_blanks, default=0), continuation_pages


def validate_sparse_chapter_tails() -> int:
    pdf = fitz.open(previous.previous.base.PDF)
    pages = [page.get_text().strip() for page in pdf]
    first_part = compact(merge_v11.base.SOURCES[0][0])
    first_body = [index for index, text in enumerate(pages) if first_part in compact(text)][-1]
    sparse = [
        (index + 1, len(text), "".join(text.split())[:80])
        for index, text in enumerate(pages[first_body:-1], start=first_body)
        if len(text) < 300
    ]
    assert not sparse, ("章末或题末存在非必要稀疏页", sparse)
    return min((len(text) for text in pages[first_body:-1]), default=0)


if __name__ == "__main__":
    previous.previous.base.main()
    validate_exact_page_map()
    max_blank, continuation_pages = validate_pagination()
    minimum_nonfinal_chars = validate_sparse_chapter_tails()
    report = previous.previous.base.REPORT.read_text(encoding="utf-8")
    report = report.replace(
        "- 章节：分章另起页；三科分册及合订版目录页码已校准",
        "- 章节：分章另起页；三科分册及合订版目录页码已校准\n"
        "- 题内分页：总起和总结不编号；各任务模块按1.→（1）→①→a.展开；"
        f"共检查{continuation_pages}个自然续页，续页前一页最大非必要底部空白为{max_blank:.1f}磅\n"
        f"- 稀疏页：除全书末页外，正文单页最少{minimum_nonfinal_chars}个文本字符；"
        "未发现仅有少量总结或尾点单独占页的章末稀疏页",
    )
    previous.previous.base.REPORT.write_text(report, encoding="utf-8")
    print(
        f"PASS exact_page_map pagination continuation_pages={continuation_pages} "
        f"max_blank={max_blank:.1f}"
    )
