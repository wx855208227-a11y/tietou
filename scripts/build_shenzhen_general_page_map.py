from __future__ import annotations

import json
from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.md"
PDF = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.pdf"
OUTPUT = ROOT / "content/shenzhen_general_baoming_v1_page_map.json"


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def headings() -> list[str]:
    result = []
    for line in MARKDOWN.read_text(encoding="utf-8").splitlines():
        if line.startswith("# 第") or line.startswith("# 补充章"):
            result.append(line[2:].strip())
        elif re.match(r"^## [一二三四五六七八九十]+、", line):
            result.append(line[3:].strip().split("【", 1)[0])
    return result


def main() -> None:
    document = fitz.open(PDF)
    pages = [compact(page.get_text()) for page in document]
    first_body = next(
        index
        for index, text in enumerate(pages)
        if compact("深圳大学347｜普通心理学保命手册") in text
        and compact("第一章 心理学的研究对象和方法") in text
    )
    mapping: dict[str, int] = {}
    cursor = first_body
    for heading in headings():
        needle = compact(heading)
        found = next((index for index in range(cursor, len(pages)) if needle in pages[index]), None)
        assert found is not None, heading
        mapping[heading] = found - first_body + 1
        cursor = found
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS headings={len(mapping)} first_body_pdf_page={first_body + 1} body_pages={len(pages) - first_body}")


if __name__ == "__main__":
    main()
