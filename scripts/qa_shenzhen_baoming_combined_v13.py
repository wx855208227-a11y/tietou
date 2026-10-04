from __future__ import annotations

from pathlib import Path

import merge_shenzhen_baoming_manuals_v13 as merge_v13
import qa_shenzhen_baoming_combined_v12 as previous


ROOT = Path(__file__).resolve().parents[1]
qa_base = previous.qa_base

qa_base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订全局复核版V13.docx"
qa_base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订全局复核版V13.pdf"
qa_base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v13_page_map.json"
qa_base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V13.md"
qa_base.REPORT_VERSION = "V13"
qa_base.EXPECTED_DEFINITION_CALLS = 362
qa_base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V14.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V14.pdf",
        ROOT / "content/shenzhen_general_baoming_v14_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V13.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V13.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v13_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V13.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V13.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v13_page_map.json",
        13, 39, 45,
    ),
)

# V12校验函数通过V11模块中的合订来源定位正文；统一切换至本版来源。
previous.previous.merge_v11.base.SOURCES = merge_v13.base.SOURCES


if __name__ == "__main__":
    previous.main()
