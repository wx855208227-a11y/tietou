#!/usr/bin/env python3
"""Split pdftotext output into stable page-addressable UTF-8 files."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--prefix", default="page")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    text = args.source.read_text(encoding="utf-8", errors="replace")
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    for number, page in enumerate(pages, 1):
        (args.out_dir / f"{args.prefix}-{number:03d}.txt").write_text(
            page.strip() + "\n", encoding="utf-8"
        )
    print(f"split_pages={len(pages)}")


if __name__ == "__main__":
    main()
