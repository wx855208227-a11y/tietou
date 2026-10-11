from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile

import fitz

import merge_shenzhen_baoming_manuals_v22 as combined
import render_shenzhen_baoming_v5 as guide
import render_shenzhen_general_baoming as renderer


ROOT = Path(__file__).resolve().parents[1]

SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全范围复核版V22.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全范围复核版V22.docx",
        ROOT / "content/shenzhen_general_baoming_v22_page_map.json",
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全范围补编版V22.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全范围补编版V22.docx",
        ROOT / "content/shenzhen_experiment_baoming_v22_page_map.json",
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全范围复核版V22.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全范围复核版V22.docx",
        ROOT / "content/shenzhen_measurement_baoming_v22_page_map.json",
    ),
)


def convert_pdf(docx: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="shenzhen-v22-lo-") as profile:
        result = subprocess.run(
            (
                "libreoffice",
                f"-env:UserInstallation=file://{profile}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(docx.parent),
                str(docx),
            ),
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print(result.stdout.strip())
    output = docx.with_suffix(".pdf")
    assert output.is_file(), output
    return output


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


def extract_page_map(markdown: Path, pdf: Path, output: Path) -> None:
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


def main() -> None:
    for label, markdown, docx, page_map in SPECS:
        render_subject(label, markdown, docx, None)
        pdf = convert_pdf(docx)
        extract_page_map(markdown, pdf, page_map)
        render_subject(label, markdown, docx, page_map)
        convert_pdf(docx)

    combined.base.build(combined.base.OUTPUT, None)
    combined_pdf = convert_pdf(combined.base.OUTPUT)
    page_map = combined.base.extract_page_map(combined_pdf)
    combined.base.build(combined.base.OUTPUT, page_map)
    convert_pdf(combined.base.OUTPUT)
    print("PASS built subject and combined V22 artifacts")


if __name__ == "__main__":
    main()
