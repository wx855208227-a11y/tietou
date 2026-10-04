from __future__ import annotations

from pathlib import Path

import qa_shenzhen_subject_artifacts_v12 as previous


ROOT = Path(__file__).resolve().parents[1]
previous.SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V15.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V15.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V15.pdf",
        ROOT / "content/shenzhen_general_baoming_v15_page_map.json",
        (15, 75, 90, 236),
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V15.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V15.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V15.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v15_page_map.json",
        (4, 25, 25, 50),
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V15.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V15.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V15.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v15_page_map.json",
        (13, 39, 45, 76),
    ),
)


if __name__ == "__main__":
    previous.main()
