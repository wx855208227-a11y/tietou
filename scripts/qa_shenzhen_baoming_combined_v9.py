from __future__ import annotations

import json
from pathlib import Path

import fitz
from docx import Document

import qa_shenzhen_baoming_combined_v5 as base
import merge_shenzhen_baoming_manuals_v9 as merge_v9
from merge_ecnu_baoming_manuals import compact, source_chapters


ROOT = Path(__file__).resolve().parents[1]

base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V9.docx"
base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V9.pdf"
base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v9_page_map.json"
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V9.md"
base.REPORT_VERSION = "V9"
base.EXPECTED_DEFINITION_CALLS = 360
base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V10.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V10.pdf",
        ROOT / "content/shenzhen_general_baoming_v10_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V9.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V9.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v9_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V9.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V9.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v9_page_map.json",
        13, 39, 45,
    ),
)


def validate_exact_page_map() -> None:
    pdf = fitz.open(base.PDF)
    pages = [compact(page.get_text()) for page in pdf]
    actual: dict[str, int] = {}
    part_indexes: dict[str, int] = {}
    for part_title, _, _, _ in merge_v9.base.SOURCES:
        hits = [index for index, text in enumerate(pages) if compact(part_title) in text]
        assert hits, part_title
        part_indexes[part_title] = hits[-1]
    first_body = part_indexes[merge_v9.base.SOURCES[0][0]]

    for subject_index, source_spec in enumerate(merge_v9.base.SOURCES):
        part_title, _, _, source_path = source_spec
        start = part_indexes[part_title]
        stop = (
            part_indexes[merge_v9.base.SOURCES[subject_index + 1][0]]
            if subject_index + 1 < len(merge_v9.base.SOURCES)
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

    stored = json.loads(base.PAGE_MAP.read_text(encoding="utf-8"))
    assert actual == stored, "合订目录页码与最终PDF正文页码不一致"
    print(f"PASS exact_page_map entries={len(actual)}")


if __name__ == "__main__":
    base.main()
    validate_exact_page_map()
