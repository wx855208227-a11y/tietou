#!/usr/bin/env python3
"""Extract review-oriented DOCX structure without copying the source into git."""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def paragraph_text(paragraph: ET.Element) -> str:
    chunks: list[str] = []
    for node in paragraph.iter():
        if node.tag == f"{W}t":
            chunks.append(node.text or "")
        elif node.tag == f"{W}tab":
            chunks.append("\t")
        elif node.tag in {f"{W}br", f"{W}cr"}:
            chunks.append("\n")
    return re.sub(r"[ \u3000]+", " ", "".join(chunks)).strip()


def paragraph_style(paragraph: ET.Element) -> str:
    node = paragraph.find(f"./{W}pPr/{W}pStyle")
    return "" if node is None else node.attrib.get(f"{W}val", "")


def rendered_breaks(paragraph: ET.Element) -> int:
    return sum(1 for node in paragraph.iter() if node.tag == f"{W}lastRenderedPageBreak")


def iter_records(root: ET.Element):
    body = root.find(f"./{W}body")
    if body is None:
        return
    body_para = 0
    table_index = 0
    for child in body:
        if child.tag == f"{W}p":
            body_para += 1
            yield "paragraph", f"p{body_para}", child
        elif child.tag == f"{W}tbl":
            table_index += 1
            for row_index, row in enumerate(
                (row for row in child if row.tag == f"{W}tr"), 1
            ):
                cells = [cell for cell in row if cell.tag == f"{W}tc"]
                for cell_index, cell in enumerate(cells, 1):
                    for para_index, para in enumerate(cell.iter(f"{W}p"), 1):
                        locator = f"t{table_index}r{row_index}c{cell_index}p{para_index}"
                        yield "table", locator, para


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with zipfile.ZipFile(args.docx) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    page = 1
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(["record_no", "kind", "locator", "style", "rendered_page", "text"])
        for record_no, (kind, locator, paragraph) in enumerate(iter_records(root), 1):
            text = paragraph_text(paragraph)
            writer.writerow([record_no, kind, locator, paragraph_style(paragraph), page, text])
            page += rendered_breaks(paragraph)


if __name__ == "__main__":
    main()
