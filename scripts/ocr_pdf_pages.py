#!/usr/bin/env python3
"""Run local OCR on selected PDF pages and write durable page-level JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pymupdf
from rapidocr_onnxruntime import RapidOCR


def parse_pages(spec: str, page_count: int) -> list[int]:
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start, end = int(start_text), int(end_text)
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    invalid = sorted(page for page in pages if page < 1 or page > page_count)
    if invalid:
        raise ValueError(f"pages outside 1-{page_count}: {invalid}")
    return sorted(pages)


def crop_pixmap(page: pymupdf.Page, scale: float, crop: tuple[float, ...]):
    rect = page.rect
    left, top, right, bottom = crop
    clip = pymupdf.Rect(
        rect.x0 + rect.width * left,
        rect.y0 + rect.height * top,
        rect.x1 - rect.width * right,
        rect.y1 - rect.height * bottom,
    )
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False
    )
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pages", required=True, help="1-based pages, e.g. 1-20,25")
    parser.add_argument("--scale", type=float, default=1.5)
    parser.add_argument(
        "--crop",
        type=float,
        nargs=4,
        metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"),
        default=(0.0, 0.0, 0.0, 0.0),
        help="fractional margins removed before OCR",
    )
    args = parser.parse_args()

    document = pymupdf.open(args.pdf)
    pages = parse_pages(args.pages, document.page_count)
    engine = RapidOCR()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with args.output.open("w", encoding="utf-8") as handle:
        for page_number in pages:
            image = crop_pixmap(
                document[page_number - 1], args.scale, tuple(args.crop)
            )
            result, elapsed = engine(image)
            elapsed_seconds = (
                sum(float(value) for value in elapsed)
                if isinstance(elapsed, (list, tuple))
                else float(elapsed)
            )
            lines = []
            if result:
                for box, text, confidence in result:
                    lines.append(
                        {
                            "box": [[round(float(x), 1), round(float(y), 1)] for x, y in box],
                            "text": text,
                            "confidence": round(float(confidence), 4),
                        }
                    )
            average_confidence = (
                sum(line["confidence"] for line in lines) / len(lines)
                if lines
                else 0.0
            )
            record = {
                "pdf_page": page_number,
                "elapsed_seconds": round(elapsed_seconds, 4),
                "average_confidence": round(average_confidence, 4),
                "line_count": len(lines),
                "text": "\n".join(line["text"] for line in lines),
                "lines": lines,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
