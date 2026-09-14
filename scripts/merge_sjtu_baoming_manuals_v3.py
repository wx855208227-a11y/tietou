from __future__ import annotations

from pathlib import Path

import merge_ecnu_baoming_manuals as base


ROOT = Path(__file__).resolve().parents[1]

base.OUTPUT = ROOT / "deliverables/上海交通大学347心理学保命手册_普心临床实验合订重编版V3.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/sjtu_baoming_combined_v3_page_map.json"
base.COVER_TITLE = "上海交通大学347心理学保命手册"
base.CORE_TITLE = "上海交通大学347心理学保命手册"
base.CORE_SUBJECT = "普通心理学、临床心理学、实验心理学合订重编版"
base.GUIDE_LEVEL_LINES = (
    "★★★  核心优先｜上交近年真题直接考查，或同时得到本轮主体资料、指定教材与312／347高频命题等多重强证据支持，最应优先背诵。",
    "★★  重点掌握｜本轮主体资料依据明确，能够形成稳定的名词解释、简答、论述、案例分析或实验设计题。",
    "★  基础覆盖｜本轮主体资料确有收录，但上交直接命题信号和主观题综合可考性相对较弱。",
)
base.STRIP_NON_CHAPTER_PAGE_BREAKS = False
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "上海交通大学347｜普通心理学保命手册",
        ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V3.docx",
    ),
    (
        "第二部分 临床心理学",
        "临床心理学",
        "上海交通大学347｜临床心理学保命手册",
        ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V3.docx",
    ),
    (
        "第三部分 实验心理学",
        "实验心理学",
        "上海交通大学347｜实验心理学保命手册",
        ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V3.docx",
    ),
)


def compact_for_page_map(text: str) -> str:
    return "".join(text.split()).replace("—", "").replace("–", "").replace("-", "")


base.compact = compact_for_page_map


if __name__ == "__main__":
    base.main()
