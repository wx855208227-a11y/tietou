from __future__ import annotations

from pathlib import Path

import merge_shenzhen_baoming_manuals_v11 as merge_v11
import merge_shenzhen_baoming_manuals_v21 as merge_v21
import qa_shenzhen_baoming_combined_v20 as previous


ROOT = Path(__file__).resolve().parents[1]
qa_base = previous.qa_base

qa_base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订V19基线逐题保守精修版V21.docx"
qa_base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订V19基线逐题保守精修版V21.pdf"
qa_base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v21_page_map.json"
qa_base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V21.md"
qa_base.REPORT_VERSION = "V21"
qa_base.EXPECTED_DEFINITION_CALLS = 366
qa_base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_V19基线逐题保守精修版V21.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_V19基线逐题保守精修版V21.pdf",
        ROOT / "content/shenzhen_general_baoming_v21_page_map.json",
        15,
        75,
        90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_V19基线逐题保守精修版V21.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_V19基线逐题保守精修版V21.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v21_page_map.json",
        4,
        25,
        25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_V19基线逐题保守精修版V21.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_V19基线逐题保守精修版V21.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v21_page_map.json",
        13,
        39,
        45,
    ),
)

merge_v11.base.SOURCES = merge_v21.base.SOURCES


if __name__ == "__main__":
    previous.previous.previous.previous.validate_combined_word_runs()
    previous.previous.previous.previous.previous.previous.previous.main()
