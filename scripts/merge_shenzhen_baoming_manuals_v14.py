from __future__ import annotations

from pathlib import Path

import merge_shenzhen_baoming_manuals_v13 as previous
from docx import Document
from docx.shared import Pt


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.OUTPUT = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订采分点完整性复核版V14.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/shenzhen_baoming_combined_v14_page_map.json"
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "深圳大学347｜普通心理学保命手册",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V15.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "深圳大学347｜实验心理学保命手册",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V14.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "深圳大学347｜心理与教育测量保命手册",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V14.docx",
    ),
)


v13_build = base.build


def build_without_sparse_tails(output_path: Path, page_map: dict[str, int] | None = None) -> None:
    """Slightly tighten vertical rhythm while preserving 12 pt body text."""
    v13_build(output_path, page_map)
    document = Document(output_path)
    body_started = False
    break_before_units = {
        "二、语言的神经基础",
        "六、人格的形成",
        "五、信号检测论",
        "五、影响效度的因素",
        "四、多重选择题项目分析",
        "四、自陈量表与投射测验的比较",
    }
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Part Title":
            body_started = True
            continue
        if not body_started:
            continue
        if paragraph.style.name == "Normal":
            spacing = paragraph.paragraph_format.line_spacing
            if isinstance(spacing, (int, float)):
                paragraph.paragraph_format.line_spacing = max(1.0, min(1.12, spacing * 0.94))
            if paragraph.paragraph_format.space_after:
                paragraph.paragraph_format.space_after = Pt(
                    paragraph.paragraph_format.space_after.pt * 0.65
                )
        elif paragraph.style.name in {"Heading 2", "Heading 3"}:
            clean_text = paragraph.text.strip().split("【", 1)[0]
            if paragraph.style.name == "Heading 2" and clean_text in break_before_units:
                paragraph.paragraph_format.page_break_before = True
            if paragraph.paragraph_format.space_before:
                paragraph.paragraph_format.space_before = Pt(
                    paragraph.paragraph_format.space_before.pt * 0.80
                )
            if paragraph.paragraph_format.space_after:
                paragraph.paragraph_format.space_after = Pt(
                    paragraph.paragraph_format.space_after.pt * 0.80
                )
    document.save(output_path)


base.build = build_without_sparse_tails


if __name__ == "__main__":
    base.main()
