#!/usr/bin/env python3
"""Export DOCX paragraphs and table cells without flattening their source order."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


def iter_blocks(document: Document):
    body = document.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield "paragraph", Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield "table", Table(child, document)


def clean(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def export(source: Path, output: Path) -> None:
    document = Document(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["block_index", "block_type", "style", "location", "text"])
        block_index = 0
        for block_type, block in iter_blocks(document):
            block_index += 1
            if block_type == "paragraph":
                text = clean(block.text)
                if text:
                    writer.writerow(
                        [block_index, block_type, block.style.name, "", text]
                    )
                continue

            for row_index, row in enumerate(block.rows, start=1):
                for cell_index, cell in enumerate(row.cells, start=1):
                    text = clean(cell.text)
                    if text:
                        writer.writerow(
                            [
                                block_index,
                                "table_cell",
                                "",
                                f"R{row_index}C{cell_index}",
                                text,
                            ]
                        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.source, args.output)


if __name__ == "__main__":
    main()
