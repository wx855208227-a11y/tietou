from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile

import fitz
from docx import Document
from docx.shared import Pt

import merge_shenzhen_baoming_manuals_v21 as combined
import render_shenzhen_baoming_v5 as guide
import render_shenzhen_general_baoming as renderer


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"

# These three chapter-tail units left a short final page in the combined book.
# Tightening affects paragraph rhythm only; wording, hierarchy and 12 pt body
# text remain unchanged.
renderer.DENSE_UNIT_PREFIXES += (
    "八、内隐记忆与外显记忆",
    "二、智力的发展、差异及影响因素",
    "三、自我价值理论与调节聚焦理论",
)

SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_V19基线逐题保守精修版V21.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_V19基线逐题保守精修版V21.docx",
        ROOT / "content/shenzhen_general_baoming_v21_page_map.json",
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_V19基线逐题保守精修版V21.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_V19基线逐题保守精修版V21.docx",
        ROOT / "content/shenzhen_experiment_baoming_v21_page_map.json",
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_V19基线逐题保守精修版V21.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_V19基线逐题保守精修版V21.docx",
        ROOT / "content/shenzhen_measurement_baoming_v21_page_map.json",
    ),
)


def convert_pdf(docx: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="shenzhen-v21-lo-") as profile:
        command = (
            "libreoffice",
            f"-env:UserInstallation=file://{profile}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(docx.parent),
            str(docx),
        )
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(result.stdout.strip())
    pdf = docx.with_suffix(".pdf")
    assert pdf.is_file(), pdf
    return pdf


def compact(value: str) -> str:
    return re.sub(r"[\s\-‐‑‒–—―]+", "", value)


def heading_keys(markdown: Path) -> list[str]:
    lines = markdown.read_text(encoding="utf-8").splitlines()
    first = next(index for index, line in enumerate(lines) if line.startswith("# 第一章 "))
    return [
        line.lstrip("# ").strip().split("【", 1)[0]
        for line in lines[first:]
        if line.startswith("# ") or re.match(r"^## [一二三四五六七八九十]+、", line)
    ]


def extract_subject_page_map(markdown: Path, pdf: Path, output: Path) -> None:
    keys = heading_keys(markdown)
    document = fitz.open(pdf)
    pages = [compact(page.get_text()) for page in document]
    first_hits = [index for index, page in enumerate(pages) if compact(keys[0]) in page]
    assert len(first_hits) >= 2, (keys[0], first_hits)
    first_body = first_hits[-1]
    mapping: dict[str, int] = {}
    cursor = first_body
    for key in keys:
        needle = compact(key)
        found = next(index for index in range(cursor, len(pages)) if needle in pages[index])
        mapping[key] = found - first_body + 1
        cursor = found
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_subject(label: str, markdown: Path, docx: Path, page_map: Path | None) -> None:
    renderer.add_student_guide = guide.add_student_guide
    renderer.render(
        markdown,
        docx,
        page_map,
        subject_label=label,
        header_text=f"深圳大学347｜{label}保命手册",
        compact_answers=True,
    )
    if label == "普通心理学":
        tighten_critical_units(docx)


def tighten_critical_units(docx: Path) -> None:
    document = Document(docx)
    active = False
    compact_chapter = False
    prefixes = (
        "八、内隐记忆与外显记忆",
        "三、自我价值理论与调节聚焦理论",
    )
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            compact_chapter = paragraph.text.strip().startswith(("第六章 记忆", "补充章 高频学习理论"))
            active = False
        elif paragraph.style.name == "Heading 2":
            active = paragraph.style.name == "Heading 2" and paragraph.text.strip().startswith(prefixes)
        if not active and not compact_chapter:
            continue
        if paragraph.style.name == "Normal":
            paragraph.paragraph_format.line_spacing = 1.0 if active else 1.12
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0 if active else 0.5)
        elif paragraph.style.name == "Heading 3":
            paragraph.paragraph_format.space_before = Pt(3 if active else 5)
            paragraph.paragraph_format.space_after = Pt(2 if active else 3)
    document.save(docx)


def main() -> None:
    for label, markdown, docx, page_map in SPECS:
        render_subject(label, markdown, docx, None)
        pdf = convert_pdf(docx)
        extract_subject_page_map(markdown, pdf, page_map)
        render_subject(label, markdown, docx, page_map)
        convert_pdf(docx)

    combined.base.build(combined.base.OUTPUT, None)
    combined_pdf = convert_pdf(combined.base.OUTPUT)
    mapping = combined.base.extract_page_map(combined_pdf)
    combined.base.build(combined.base.OUTPUT, mapping)
    convert_pdf(combined.base.OUTPUT)
    print("PASS built subject and combined V21 artifacts")


if __name__ == "__main__":
    main()
