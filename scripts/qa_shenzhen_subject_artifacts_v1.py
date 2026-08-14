from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

import fitz
from docx import Document

from build_shenzhen_subject_page_map import compact, heading_keys


ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V2.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V2.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V2.pdf",
        ROOT / "content/shenzhen_general_baoming_v2_page_map.json",
        (15, 75, 90, 231),
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V1.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V1.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V1.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v1_page_map.json",
        (5, 28, 28, 48),
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V1.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V1.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V1.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v1_page_map.json",
        (13, 39, 45, 65),
    ),
)


def main() -> None:
    for subject, markdown, docx, pdf_path, map_path, expected in SPECS:
        assert all(path.is_file() for path in (markdown, docx, pdf_path, map_path))
        with zipfile.ZipFile(docx) as archive:
            assert archive.testzip() is None
        document = Document(docx)
        h1 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 1"]
        h2 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 2"]
        questions = [paragraph for paragraph in document.paragraphs if paragraph.text.startswith("押题")]
        all_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        assert (len(h1), len(h2), len(questions), all_text.count("【名词解释：")) == expected

        pdf = fitz.open(pdf_path)
        pages = [compact(page.get_text()) for page in pdf]
        assert all(pages)
        assert all(not page.get_images(full=True) for page in pdf)
        keys = heading_keys(markdown)
        first_hits = [index for index, text in enumerate(pages) if compact(keys[0]) in text]
        assert len(first_hits) >= 2
        first_body = first_hits[-1]
        cursor = first_body
        actual: dict[str, int] = {}
        for key in keys:
            found = next(index for index in range(cursor, len(pages)) if compact(key) in pages[index])
            actual[key] = found - first_body + 1
            cursor = found
        stored = json.loads(map_path.read_text(encoding="utf-8"))
        assert actual == stored
        catalog_text = "\n".join(page.get_text() for page in pdf[:first_body])
        assert not re.search(r"\.{3,}\s*0\s*$", catalog_text, re.MULTILINE)
        print(
            f"PASS {subject} pages={len(pdf)} chapters={len(h1)} units={len(h2)} "
            f"questions={len(questions)} definitions={all_text.count('【名词解释：')}"
        )


if __name__ == "__main__":
    main()
