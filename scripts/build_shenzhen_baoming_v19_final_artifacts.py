from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile

import fitz
from docx import Document
from docx.shared import Cm, Pt

import merge_ecnu_baoming_manuals as merger
import render_shenzhen_baoming_v5 as guide
import render_shenzhen_general_baoming as renderer


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
CONTENT = ROOT / "content"

SUBJECTS = (
    (
        "普通心理学",
        DELIVERABLES / "深圳大学347普通心理学保命手册_V19原标准重新逐题校正版.md",
        DELIVERABLES / "深圳大学347普通心理学保命手册_V19原标准逐题终校版.docx",
        CONTENT / "shenzhen_general_baoming_v19_final_page_map.json",
    ),
    (
        "实验心理学",
        DELIVERABLES / "深圳大学347实验心理学保命手册_V19原标准逐题校正版.md",
        DELIVERABLES / "深圳大学347实验心理学保命手册_V19原标准逐题终校版.docx",
        CONTENT / "shenzhen_experiment_baoming_v19_final_page_map.json",
    ),
    (
        "心理与教育测量",
        DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19原标准逐题校正版.md",
        DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19原标准逐题终校版.docx",
        CONTENT / "shenzhen_measurement_baoming_v19_final_page_map.json",
    ),
)

TIGHT_UNITS = {
    "普通心理学": (
        "六、催眠",
        "八、内隐记忆与外显记忆",
        "六、决策理论与启发式偏差",
        "七、认知学习与动作技能学习",
    ),
    "实验心理学": (
        "四、序列反应时与内隐联想测验",
        "五、信号检测论",
    ),
    "心理与教育测量": (
        "四、效标效度",
        "五、影响测量效度的因素及提高方法",
    ),
}

COMBINED_DOCX = DELIVERABLES / "深圳大学347心理学保命手册_普心实验测量合订V19原标准逐题终校版.docx"
COMBINED_PAGE_MAP = CONTENT / "shenzhen_baoming_combined_v19_final_page_map.json"


def convert_pdf(docx_path: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="shenzhen-v19-final-lo-") as profile:
        result = subprocess.run(
            (
                "libreoffice",
                f"-env:UserInstallation=file://{profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(docx_path.parent),
                str(docx_path),
            ),
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print(result.stdout.strip())
    pdf_path = docx_path.with_suffix(".pdf")
    assert pdf_path.is_file(), pdf_path
    return pdf_path


def compact(value: str) -> str:
    return re.sub(r"[\s\-‐‑‒–—―]+", "", value)


def heading_keys(markdown_path: Path) -> list[str]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    first_chapter = next(
        index for index, line in enumerate(lines) if line.startswith("# 第一章 ")
    )
    return [
        line.lstrip("# ").strip().split("【", 1)[0]
        for line in lines[first_chapter:]
        if line.startswith("# ")
        or re.match(r"^## [一二三四五六七八九十百]+、", line)
    ]


def extract_subject_page_map(
    markdown_path: Path,
    pdf_path: Path,
    output_path: Path,
) -> None:
    keys = heading_keys(markdown_path)
    with fitz.open(pdf_path) as pdf:
        pages = [compact(page.get_text()) for page in pdf]
    first_hits = [index for index, page in enumerate(pages) if compact(keys[0]) in page]
    assert len(first_hits) >= 2, (keys[0], first_hits)
    first_body_page = first_hits[-1]
    mapping: dict[str, int] = {}
    cursor = first_body_page
    for key in keys:
        needle = compact(key)
        found = next(index for index in range(cursor, len(pages)) if needle in pages[index])
        mapping[key] = found - first_body_page + 1
        cursor = found
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def render_subject(
    subject: str,
    markdown_path: Path,
    docx_path: Path,
    page_map_path: Path | None,
) -> None:
    renderer.add_student_guide = guide.add_student_guide
    renderer.render(
        markdown_path,
        docx_path,
        page_map_path,
        subject_label=subject,
        header_text=f"深圳大学347｜{subject}保命手册",
        compact_answers=True,
    )
    tighten_selected_units(docx_path, TIGHT_UNITS[subject])


def tighten_selected_units(docx_path: Path, prefixes: tuple[str, ...]) -> None:
    """Remove chapter-tail orphan pages without changing content or body size."""
    document = Document(docx_path)
    active = False
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            active = False
        elif paragraph.style.name == "Heading 2":
            active = paragraph.text.strip().startswith(prefixes)
        if not active:
            continue
        if paragraph.style.name == "Normal":
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
        elif paragraph.style.name == "Heading 3":
            paragraph.paragraph_format.space_before = Pt(3)
            paragraph.paragraph_format.space_after = Pt(2)
    document.save(docx_path)


def add_combined_guide(document: Document) -> None:
    merger.add_front_heading(document, "使用说明", 18)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(6)
    merger.set_run_font(heading.add_run("星级"), size=14, bold=True)
    for value in (
        "★★★  核心优先｜对应速背手册原一级；同时得到深大真题、现行考纲、指定教材或一本通中的强证据支持，主观题可考性和答案复用价值最高。",
        "★★  重点掌握｜同属速背手册原一级；教材、一本通和考纲／真题依据明确，能够形成稳定主观题，但综合优先度略低于三星。",
        "★  基础覆盖｜对应速背手册原二级；速背手册或一本通确有收录，属于指定教材范围，但主观题信号和综合可考性相对较弱。",
    ):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.35
        paragraph.paragraph_format.space_after = Pt(5)
        merger.set_run_font(paragraph.add_run(value), size=12)

    heading = document.add_paragraph()
    heading.paragraph_format.first_line_indent = Cm(0)
    heading.paragraph_format.space_before = Pt(10)
    heading.paragraph_format.space_after = Pt(6)
    merger.set_run_font(heading.add_run("怎么用"), size=14, bold=True)
    for value in (
        "1. 圆括号外是背诵主体，写全可以拿到主要分数；正文加粗处为需要优先记忆的关键词。",
        "2. （）内是扩容项，选背；既可补充其他采分点，也可补充相关概念、解释或例子。例子可以根据题目灵活替换。",
    ):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.first_line_indent = Cm(0)
        paragraph.paragraph_format.line_spacing = 1.35
        paragraph.paragraph_format.space_after = Pt(6)
        merger.set_run_font(paragraph.add_run(value), size=12)
    document.add_page_break()


def configure_combined() -> None:
    merger.OUTPUT = COMBINED_DOCX
    merger.PAGE_MAP_OUTPUT = COMBINED_PAGE_MAP
    merger.COVER_TITLE = "深圳大学347心理学保命手册"
    merger.CORE_TITLE = "深圳大学347心理学保命手册"
    merger.CORE_SUBJECT = "普通心理学、实验心理学、心理与教育测量合订版"
    merger.STRIP_NON_CHAPTER_PAGE_BREAKS = False
    merger.COMBINED_NON_CHAPTER_PAGE_BREAK_TEXTS = set()
    merger.SOURCES = (
        (
            "第一部分 普通心理学",
            "普通心理学",
            "深圳大学347｜普通心理学保命手册",
            SUBJECTS[0][2],
        ),
        (
            "第二部分 实验心理学",
            "实验心理学",
            "深圳大学347｜实验心理学保命手册",
            SUBJECTS[1][2],
        ),
        (
            "第三部分 心理与教育测量",
            "心理与教育测量",
            "深圳大学347｜心理与教育测量保命手册",
            SUBJECTS[2][2],
        ),
    )
    merger.add_guide = add_combined_guide


def build_combined() -> None:
    configure_combined()
    merger.build(COMBINED_DOCX, None)
    draft_pdf = convert_pdf(COMBINED_DOCX)
    page_map = merger.extract_page_map(draft_pdf)
    merger.build(COMBINED_DOCX, page_map)
    convert_pdf(COMBINED_DOCX)


def main() -> None:
    for subject, markdown_path, docx_path, page_map_path in SUBJECTS:
        render_subject(subject, markdown_path, docx_path, None)
        pdf_path = convert_pdf(docx_path)
        extract_subject_page_map(markdown_path, pdf_path, page_map_path)
        render_subject(subject, markdown_path, docx_path, page_map_path)
        convert_pdf(docx_path)
        print(f"PASS built {subject}")
    build_combined()
    print("PASS built V19 final subject and combined artifacts")


if __name__ == "__main__":
    main()
