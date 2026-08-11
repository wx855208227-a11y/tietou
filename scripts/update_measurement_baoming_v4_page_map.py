from __future__ import annotations

import json
from pathlib import Path
import re

import fitz


PDF = Path("deliverables/华东师范大学347心理测量保命手册_全本_答题结构优化版V4.pdf")
PAGE_MAP = Path("content/measurement_baoming_v4_page_map.json")
INVENTORY = Path("analysis/ecnu-measurement-baoming/pdf-inventory-v4.md")
FIRST_CHAPTER = "第一章心理测量和测验的历史回顾"
HEADER = "华东师范大学347｜心理测量保命手册"


def compact(value: str) -> str:
    return re.sub(r"\s+|\u2060", "", value).translate(str.maketrans("", "", "—–－-"))


def main() -> None:
    targets: dict[str, int] = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    document = fitz.open(PDF)
    page_texts = [page.get_text() for page in document]
    first_body = next(
        index
        for index, text in enumerate(page_texts)
        if compact(FIRST_CHAPTER) in compact(text) and compact(HEADER) in compact(text)
    )
    actual: dict[str, int] = {}
    for title in targets:
        needle = compact(title)
        for physical_page in range(first_body, len(page_texts)):
            if needle in compact(page_texts[physical_page]):
                actual[title] = physical_page - first_body + 1
                break
    assert actual.keys() == targets.keys(), set(targets) - set(actual)
    PAGE_MAP.write_text(
        json.dumps(actual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    inventory_lines = [f"file: {PDF.resolve()}", f"pages: {len(document)}"]
    for page_number, page in enumerate(document, start=1):
        text = page.get_text()
        blocks = page.get_text("dict")["blocks"]
        image_blocks = sum(block["type"] == 1 for block in blocks)
        inventory_lines.append(
            f"PAGE {page_number}: text_chars={len(text)} "
            f"images={len(page.get_images(full=True))} image_blocks={image_blocks}"
        )
        inventory_lines.append(
            "  text_sample: " + re.sub(r"\s+", " ", text).strip()[:300].rstrip()
        )
    INVENTORY.write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")
    print(
        f"已更新{len(actual)}项目录页码：正文从物理第{first_body + 1}页开始，"
        f"正文共{len(page_texts) - first_body}页；页面清单共{len(document)}页。"
    )


if __name__ == "__main__":
    main()
