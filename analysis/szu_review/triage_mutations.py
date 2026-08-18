#!/usr/bin/env python3
"""Triage close alignments into small internal mutation candidates."""

from __future__ import annotations

import argparse
import csv
import re
from difflib import SequenceMatcher
from pathlib import Path


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]+", text)).lower()


def useful(piece: str) -> bool:
    if not piece:
        return True
    if len(piece) > 12:
        return False
    return bool(re.fullmatch(r"[\u3400-\u9fff0-9]+", piece))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    results: list[dict[str, str]] = []
    with args.input.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if float(row["相似度"]) < 0.76:
                continue
            left = normalize(row["一本通句段"])
            right = normalize(row["教材OCR近似句段"])
            matcher = SequenceMatcher(None, left, right, autojunk=False)
            opcodes = matcher.get_opcodes()
            for index, (tag, i1, i2, j1, j2) in enumerate(opcodes):
                if tag == "equal":
                    continue
                source_piece = left[i1:i2]
                target_piece = right[j1:j2]
                if not useful(source_piece) or not useful(target_piece):
                    continue
                left_equal = opcodes[index - 1][0] == "equal" and opcodes[index - 1][2] - opcodes[index - 1][1] >= 4 if index else False
                right_equal = opcodes[index + 1][0] == "equal" and opcodes[index + 1][2] - opcodes[index + 1][1] >= 4 if index + 1 < len(opcodes) else False
                if not (left_equal and right_equal):
                    continue
                # Page references, numbering and known OCR-only Latin fragments are
                # handled elsewhere and are not useful internal prose mutations.
                if source_piece.startswith("p") or target_piece.startswith("p"):
                    continue
                results.append(
                    {
                        "章节": row["章节"],
                        "一本通实际页码": row["一本通实际页码"],
                        "一本通句段": row["一本通句段"],
                        "教材页码": row["教材页码"],
                        "教材OCR句段": row["教材OCR近似句段"],
                        "相似度": row["相似度"],
                        "差异类型": tag,
                        "一本通差异": source_piece or "∅",
                        "教材差异": target_piece or "∅",
                        "一本通上下文": left[max(0, i1 - 14) : min(len(left), i2 + 14)],
                        "教材上下文": right[max(0, j1 - 14) : min(len(right), j2 + 14)],
                    }
                )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        headers = list(results[0]) if results else ["章节"]
        writer = csv.DictWriter(stream, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(results)
    print(f"mutation_candidates={len(results)}")


if __name__ == "__main__":
    main()
