from __future__ import annotations

from pathlib import Path

import build_shenzhen_baoming_v24_artifacts as base


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
CONTENT = ROOT / "content"

SUBJECTS = (
    (
        "普通心理学",
        DELIVERABLES / "深圳大学347普通心理学保命手册_V19完整范围去重容量校正版V25.md",
        DELIVERABLES / "深圳大学347普通心理学保命手册_V19完整范围去重容量校正版V25.docx",
        CONTENT / "shenzhen_general_baoming_v25_page_map.json",
    ),
    (
        "实验心理学",
        DELIVERABLES / "深圳大学347实验心理学保命手册_V19完整范围去重容量校正版V25.md",
        DELIVERABLES / "深圳大学347实验心理学保命手册_V19完整范围去重容量校正版V25.docx",
        CONTENT / "shenzhen_experiment_baoming_v25_page_map.json",
    ),
    (
        "心理与教育测量",
        DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19完整范围去重容量校正版V25.md",
        DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19完整范围去重容量校正版V25.docx",
        CONTENT / "shenzhen_measurement_baoming_v25_page_map.json",
    ),
)

COMBINED_DOCX = DELIVERABLES / "深圳大学347心理学保命手册_普心实验测量合订V19完整范围去重容量校正版V25.docx"
COMBINED_PAGE_MAP = CONTENT / "shenzhen_baoming_combined_v25_page_map.json"


def configure_base() -> None:
    base.SUBJECTS = SUBJECTS
    base.COMBINED_DOCX = COMBINED_DOCX
    base.COMBINED_PAGE_MAP = COMBINED_PAGE_MAP


def configure_combined() -> None:
    configure_base()
    base.configure_combined()


def main() -> None:
    configure_base()
    base.main()


if __name__ == "__main__":
    main()
