from __future__ import annotations

from pathlib import Path

import qa_shenzhen_subject_artifacts_v18 as previous


ROOT = Path(__file__).resolve().parents[1]
previous.previous.previous.SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全局题型题干复核版V19.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全局题型题干复核版V19.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全局题型题干复核版V19.pdf",
        ROOT / "content/shenzhen_general_baoming_v19_page_map.json",
        (15, 75, 90, 236),
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全局题型题干复核版V19.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全局题型题干复核版V19.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全局题型题干复核版V19.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v19_page_map.json",
        (4, 25, 25, 50),
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全局题型题干复核版V19.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全局题型题干复核版V19.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全局题型题干复核版V19.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v19_page_map.json",
        (13, 39, 45, 76),
    ),
)


if __name__ == "__main__":
    previous.previous.validate_word_keyword_runs()
    previous.previous.previous.main()
