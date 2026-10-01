from __future__ import annotations

from pathlib import Path

import merge_shenzhen_baoming_manuals_v5 as previous


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.OUTPUT = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V9.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/shenzhen_baoming_combined_v9_page_map.json"
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "深圳大学347｜普通心理学保命手册",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V10.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "深圳大学347｜实验心理学保命手册",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V9.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "深圳大学347｜心理与教育测量保命手册",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V9.docx",
    ),
)


if __name__ == "__main__":
    base.main()
