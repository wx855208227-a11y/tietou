from __future__ import annotations

from pathlib import Path

from docx import Document

import merge_shenzhen_baoming_manuals_v19 as previous


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.OUTPUT = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订逐题人工重审版V20.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/shenzhen_baoming_combined_v20_page_map.json"
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "深圳大学347｜普通心理学保命手册",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_逐题人工重审版V20.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "深圳大学347｜实验心理学保命手册",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_逐题人工重审版V20.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "深圳大学347｜心理与教育测量保命手册",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_逐题人工重审版V20.docx",
    ),
)


original_build = base.build


def build_with_targeted_pagination(
    output_path: Path,
    page_map: dict[str, int] | None = None,
) -> None:
    """Balance three individually verified chapter tails without changing text.

    These links move one complete answer module to the following page.  They
    avoid leaving only a conclusion or the last one/two scoring points on an
    otherwise empty chapter-tail page, while preserving every reviewed run,
    paragraph and mandatory chapter break.
    """
    original_build(output_path, page_map)
    document = Document(output_path)
    link_starts = (
        # 内隐记忆／外显记忆：让“联系”与后续“区别”模块同页。
        "2. 二者的联系：二者都以过去经验为基础",
        # 决策：让三种启发式策略作为完整模块进入下一页。
        "（1）代表性启发法：人们倾向于根据事物或人代表某范畴的程度",
        "（2）易得性启发法：人们根据事件或现象在记忆中获得的难易程度",
        # 智力：让“影响智力的因素”作为完整模块进入下一页。
        "（1）遗传的作用：遗传因素会影响个体的生理发展",
        "①产前环境：胎儿在母体中的环境对其生长发育",
        "②早期经验：从出生到青少年时期是生长发育和智力发展的重要时期",
        "③学校教育：学校教育通过有目的地、系统地培养学生",
    )
    for start in link_starts:
        matches = [paragraph for paragraph in document.paragraphs if paragraph.text.startswith(start)]
        assert len(matches) == 1, (start, len(matches))
        matches[0].paragraph_format.keep_with_next = True
    document.save(output_path)


base.build = build_with_targeted_pagination


if __name__ == "__main__":
    base.main()
