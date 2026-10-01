from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.shared import Pt

import merge_shenzhen_baoming_manuals_v5 as previous


ROOT = Path(__file__).resolve().parents[1]
base = previous.base

base.OUTPUT = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V11.docx"
base.PAGE_MAP_OUTPUT = ROOT / "content/shenzhen_baoming_combined_v11_page_map.json"
base.SOURCES = (
    (
        "第一部分 普通心理学",
        "普通心理学",
        "深圳大学347｜普通心理学保命手册",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V12.docx",
    ),
    (
        "第二部分 实验心理学",
        "实验心理学",
        "深圳大学347｜实验心理学保命手册",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V11.docx",
    ),
    (
        "第三部分 心理与教育测量",
        "心理与教育测量",
        "深圳大学347｜心理与教育测量保命手册",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V11.docx",
    ),
)


original_build = base.build


def build_compact_combined(output_path: Path, page_map: dict[str, int] | None = None) -> None:
    """Keep the combined book readable while preventing short chapter-tail pages.

    The part title makes the combined edition reflow differently from the three
    subject booklets. A very small body-only rhythm adjustment avoids leaving a
    conclusion by itself before a mandatory chapter break. Font size, content,
    hierarchy and chapter starts are unchanged.
    """
    original_build(output_path, page_map)
    document = Document(output_path)
    body_started = False
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Part Title":
            body_started = True
            continue
        if not body_started:
            continue
        if paragraph.style.name == "Normal":
            spacing = paragraph.paragraph_format.line_spacing
            if isinstance(spacing, (int, float)):
                paragraph.paragraph_format.line_spacing = max(1.05, spacing * 0.95)
            if paragraph.paragraph_format.space_after:
                paragraph.paragraph_format.space_after = Pt(
                    paragraph.paragraph_format.space_after.pt * 0.8
                )
        elif paragraph.style.name == "Heading 3":
            if paragraph.paragraph_format.space_before:
                paragraph.paragraph_format.space_before = Pt(
                    paragraph.paragraph_format.space_before.pt * 0.85
                )
            if paragraph.paragraph_format.space_after:
                paragraph.paragraph_format.space_after = Pt(
                    paragraph.paragraph_format.space_after.pt * 0.85
                )
    document.save(output_path)


base.build = build_compact_combined


if __name__ == "__main__":
    base.main()
