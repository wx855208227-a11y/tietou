from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import fitz


def compact(value: str) -> str:
    return re.sub(r"[\s\-‐‑‒–—―]+", "", value)


def heading_keys(markdown: Path) -> list[str]:
    lines = markdown.read_text(encoding="utf-8").splitlines()
    first_chapter = next(index for index, line in enumerate(lines) if line.startswith("# 第一章 "))
    keys: list[str] = []
    for line in lines[first_chapter:]:
        if line.startswith("# ") or re.match(r"^## [一二三四五六七八九十]+、", line):
            keys.append(line.lstrip("# ").strip().split("【", 1)[0])
    return keys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("markdown", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    keys = heading_keys(arguments.markdown)
    document = fitz.open(arguments.pdf)
    pages = [compact(page.get_text()) for page in document]
    first = compact(keys[0])
    first_hits = [index for index, text in enumerate(pages) if first in text]
    assert len(first_hits) >= 2, (keys[0], first_hits)
    first_body = first_hits[-1]

    mapping: dict[str, int] = {}
    cursor = first_body
    for key in keys:
        needle = compact(key)
        try:
            found = next(index for index in range(cursor, len(pages)) if needle in pages[index])
        except StopIteration as error:
            raise ValueError(f"PDF中未找到标题：{key}；从第{cursor + 1}页开始检索") from error
        mapping[key] = found - first_body + 1
        cursor = found

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS headings={len(keys)} body_pages={len(document) - first_body} output={arguments.output}")


if __name__ == "__main__":
    main()
