#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a PDF page/text/image inventory without rendering pages into model context.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--sample-chars", type=int, default=220)
    args = parser.parse_args()
    path = args.pdf.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"not a file: {path}")
    try:
        import fitz  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise SystemExit("PyMuPDF is required: install/use an environment with `fitz` available") from exc

    doc = fitz.open(path)
    print(f"file: {path}")
    print(f"pages: {doc.page_count}")
    for index, page in enumerate(doc, 1):
        text = page.get_text("text") or ""
        blocks = page.get_text("dict").get("blocks", [])
        image_blocks = sum(1 for block in blocks if block.get("type") == 1)
        images = page.get_images(full=True)
        sample = " ".join(text.split())[: max(args.sample_chars, 0)]
        print(f"PAGE {index}: text_chars={len(text)} images={len(images)} image_blocks={image_blocks}")
        if sample:
            print(f"  text_sample: {sample}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
