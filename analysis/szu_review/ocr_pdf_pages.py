#!/usr/bin/env python3
"""OCR selected pages from the scanned Shenzhen University textbook.

Pages are rendered locally and sent to tesseract one at a time. The script is
intended for durable, page-addressable evidence extraction; it never sends page
images to a remote model.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pymupdf


def ocr_one(pdf: str, page_number: int, out_dir: str, dpi: int) -> tuple[int, int]:
    output = Path(out_dir) / f"tb-{page_number:03d}.txt"
    if output.exists() and output.stat().st_size > 20:
        return page_number, output.stat().st_size
    document = pymupdf.open(pdf)
    page = document[page_number - 1]
    pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
    document.close()
    with tempfile.TemporaryDirectory(prefix=f"szu-tb-{page_number:03d}-") as temp_dir:
        image = Path(temp_dir) / "page.png"
        pixmap.save(image)
        result = subprocess.run(
            [
                "tesseract",
                str(image),
                "stdout",
                "-l",
                "chi_sim+eng",
                "--psm",
                "3",
                "-c",
                "preserve_interword_spaces=1",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    text = result.stdout.decode("utf-8", errors="replace")
    output.write_text(text, encoding="utf-8")
    return page_number, len(text)


def page_numbers(spec: str, total: int) -> list[int]:
    if spec == "all":
        return list(range(1, total + 1))
    result: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-", 1))
            result.update(range(start, end + 1))
        elif part:
            result.add(int(part))
    return sorted(number for number in result if 1 <= number <= total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--pages", default="all")
    parser.add_argument("--dpi", type=int, default=260)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 2))
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(args.pdf) as document:
        total = document.page_count
    selected = page_numbers(args.pages, total)
    completed = 0
    total_chars = 0
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(ocr_one, str(args.pdf), number, str(args.out_dir), args.dpi)
            for number in selected
        ]
        for future in as_completed(futures):
            _, chars = future.result()
            completed += 1
            total_chars += chars
            if completed % 50 == 0 or completed == len(selected):
                print(f"ocr_progress={completed}/{len(selected)} chars={total_chars}", flush=True)


if __name__ == "__main__":
    main()
