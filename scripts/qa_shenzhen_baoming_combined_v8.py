from __future__ import annotations

from pathlib import Path

import qa_shenzhen_baoming_combined_v5 as base


ROOT = Path(__file__).resolve().parents[1]

base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V8.docx"
base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V8.pdf"
base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v8_page_map.json"
base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V8.md"
base.REPORT_VERSION = "V8"
base.EXPECTED_DEFINITION_CALLS = 360
base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V9.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V9.pdf",
        ROOT / "content/shenzhen_general_baoming_v9_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V8.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V8.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v8_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V8.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V8.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v8_page_map.json",
        13, 39, 45,
    ),
)


if __name__ == "__main__":
    base.main()
