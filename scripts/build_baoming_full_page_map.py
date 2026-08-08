from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import fitz


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text).translate(str.maketrans("", "", "—–－-"))


def headings(markdown: Path) -> list[str]:
    result = []
    for line in markdown.read_text(encoding="utf-8").splitlines():
        if line.startswith("# 第") or re.match(r"^## [一二三四五六七八九十]+、", line):
            result.append(line.lstrip("# ").strip().split("【", 1)[0])
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    document = fitz.open(arguments.pdf)
    pages = [compact(page.get_text()) for page in document]
    first_chapter = "第一章心理学研究的对象、方法及其学科发展"
    body_header = "华东师范大学347｜心理学导论保命手册"
    first_body = next(
        index for index, text in enumerate(pages)
        if first_chapter in text and body_header in text
    )

    page_map: dict[str, int] = {}
    missing = []
    for heading in headings(arguments.markdown):
        needle = compact(heading)
        found = next(
            (index for index in range(first_body, len(pages)) if needle in pages[index]),
            None,
        )
        if found is None:
            missing.append(heading)
        else:
            page_map[heading] = found - first_body + 1
    if missing:
        raise AssertionError(f"目录标题未在正文PDF中检出：{missing}")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(page_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"目录页码已反查：{len(page_map)}项，正文{len(pages) - first_body}页，"
        f"正文起始物理页{first_body + 1}。"
    )


if __name__ == "__main__":
    main()
