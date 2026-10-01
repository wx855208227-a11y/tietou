from __future__ import annotations

import json
from pathlib import Path
import re

import fitz
from docx import Document

import merge_shenzhen_baoming_manuals_v10 as merge_v10
import qa_shenzhen_baoming_combined_v9 as previous
from merge_ecnu_baoming_manuals import compact, source_chapters


ROOT = Path(__file__).resolve().parents[1]

previous.base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V10.docx"
previous.base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V10.pdf"
previous.base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v10_page_map.json"
previous.base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V10.md"
previous.base.REPORT_VERSION = "V10"
previous.base.EXPECTED_DEFINITION_CALLS = 360
previous.base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V11.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V11.pdf",
        ROOT / "content/shenzhen_general_baoming_v11_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V10.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V10.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v10_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V10.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V10.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v10_page_map.json",
        13, 39, 45,
    ),
)


def validate_exact_page_map() -> None:
    pdf = fitz.open(previous.base.PDF)
    pages = [compact(page.get_text()) for page in pdf]
    actual: dict[str, int] = {}
    part_indexes: dict[str, int] = {}
    for part_title, _, _, _ in merge_v10.base.SOURCES:
        hits = [index for index, text in enumerate(pages) if compact(part_title) in text]
        assert hits, part_title
        part_indexes[part_title] = hits[-1]
    first_body = part_indexes[merge_v10.base.SOURCES[0][0]]

    for subject_index, source_spec in enumerate(merge_v10.base.SOURCES):
        part_title, _, _, source_path = source_spec
        start = part_indexes[part_title]
        stop = (
            part_indexes[merge_v10.base.SOURCES[subject_index + 1][0]]
            if subject_index + 1 < len(merge_v10.base.SOURCES)
            else len(pages)
        )
        actual[part_title] = start - first_body + 1
        cursor = start
        for chapter in source_chapters(Document(source_path)):
            found = next(
                index for index in range(cursor, stop)
                if compact(chapter) in pages[index]
            )
            actual[f"{part_title}|{chapter}"] = found - first_body + 1
            cursor = found

    stored = json.loads(previous.base.PAGE_MAP.read_text(encoding="utf-8"))
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
    document = Document(previous.base.DOCX)
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

    pdf = fitz.open(previous.base.PDF)
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

    depth_pages = [
        page
        for page in pdf
        if "简述深度知觉的主要线索" in compact(page.get_text())
    ]
    assert len(depth_pages) == 1
    depth_text = compact(depth_pages[0].get_text())
    for value in (
        "肌肉线索（生理线索）主要包括",
        "（1）调节",
        "（2）辐合",
        "单眼线索是只用一只眼睛就能感受的深度线索",
        "双眼线索主要是双眼视差",
        "综上，深度知觉不是由单一线索决定",
    ):
        assert compact(value) in depth_text, value

    return max(continuation_blanks, default=0), continuation_pages


if __name__ == "__main__":
    previous.base.main()
    validate_exact_page_map()
    max_blank, continuation_pages = validate_pagination()
    report = previous.base.REPORT.read_text(encoding="utf-8")
    report = report.replace(
        "- 章节：分章另起页；三科分册及合订版目录页码已校准",
        "- 章节：分章另起页；三科分册及合订版目录页码已校准\n"
        "- 题内分页：父模块仅与首个子项同页，独立扩容段和总结不再反向绑定前文；"
        f"共检查{continuation_pages}个自然续页，续页前一页最大非必要底部空白为{max_blank:.1f}磅",
    )
    previous.base.REPORT.write_text(report, encoding="utf-8")
    print(
        f"PASS exact_page_map pagination continuation_pages={continuation_pages} "
        f"max_blank={max_blank:.1f}"
    )
