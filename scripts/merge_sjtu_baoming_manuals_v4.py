from __future__ import annotations

from pathlib import Path

import merge_sjtu_baoming_manuals_v3 as previous


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.OUTPUT = ROOT / "deliverables/上海交通大学347心理学保命手册_普心临床实验合订重编版V4.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/sjtu_baoming_combined_v4_page_map.json"
base.CORE_SUBJECT = "普通心理学、临床心理学、实验心理学合订重编版V4"
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "上海交通大学347｜普通心理学保命手册",
        ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V4.docx",
    ),
    (
        "第二部分 临床心理学",
        "临床心理学",
        "上海交通大学347｜临床心理学保命手册",
        ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V4.docx",
    ),
    (
        "第三部分 实验心理学",
        "实验心理学",
        "上海交通大学347｜实验心理学保命手册",
        ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V4.docx",
    ),
)


if __name__ == "__main__":
    base.main()
