from __future__ import annotations

import json
from pathlib import Path
import re

import fitz


BASE = Path("deliverables/华东师范大学347实验心理学保命手册_全本_极简直背版V1")
MARKDOWN = BASE.with_suffix(".md")
PDF = BASE.with_suffix(".pdf")
PAGE_MAP = Path("content/experiment_baoming_v1_page_map.json")
INVENTORY = Path("analysis/ecnu-experiment-baoming/pdf-inventory-v1.md")
FIRST_CHAPTER = "第一章绪论"
HEADER = "华东师范大学347｜实验心理学保命手册"


def compact(value: str) -> str:
    return re.sub(r"\s+|\u2060", "", value).translate(str.maketrans("", "", "—–－-"))


def markdown_titles() -> list[str]:
    text = MARKDOWN.read_text(encoding="utf-8")
    return [
        line.lstrip("# ").strip().split("【", 1)[0]
        for line in text.splitlines()
        if line.startswith("# 第")
        or line.startswith("# 常见的心理学实验")
        or line.startswith("# 心理学研究中的新技术")
        or re.match(r"^## [一二三四五六七八九十]+、", line)
    ]


def main() -> None:
    targets = markdown_titles()
    assert len(targets) == 60 and len(set(targets)) == 60
    PAGE_MAP.parent.mkdir(parents=True, exist_ok=True)
    if not PDF.exists():
        PAGE_MAP.write_text(
            json.dumps(dict.fromkeys(targets, 1), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"已初始化{len(targets)}项目录页码占位表：{PAGE_MAP}")
        return

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
    assert actual.keys() == dict.fromkeys(targets).keys(), set(targets) - set(actual)
    PAGE_MAP.write_text(
        json.dumps(actual, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    INVENTORY.parent.mkdir(parents=True, exist_ok=True)
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
