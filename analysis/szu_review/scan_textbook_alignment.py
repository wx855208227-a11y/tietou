#!/usr/bin/env python3
"""Generate direct Yibentong-to-textbook alignment candidates for review.

The current uploaded document is compared only with the assigned authoritative
textbook.  Historical Yibentong versions and prior findings are not inputs.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


CHAPTERS = {
    1: "第一章 心理学的研究对象和方法",
    2: "第二章 心理与行为的脑神经基础",
    3: "第三章 感觉",
    4: "第四章 知觉",
    5: "第五章 意识",
    6: "第六章 记忆",
    7: "第七章 思维",
    8: "第八章 语言",
    9: "第九章 动机",
    10: "第十章 情绪",
    11: "第十一章 智力",
    12: "第十二章 人格",
    13: "第十三章 学习",
    14: "第十四章 人生全程发展",
}

# LibreOffice-rendered physical page; footer-printed body page = physical - 8.
YBT_STARTS = {
    1: 9,
    2: 31,
    3: 50,
    4: 75,
    5: 115,
    6: 153,
    7: 199,
    8: 248,
    9: 264,
    10: 304,
    11: 330,
    12: 346,
    13: 384,
    14: 420,
}

# Scanned textbook PDF pages. Printed textbook page = PDF page - 12.
TEXTBOOK_RANGES = {
    1: (13, 48),
    2: (49, 86),
    3: (87, 134),
    4: (135, 176),
    5: (177, 212),
    6: (213, 256),
    7: (257, 298),
    8: (299, 334),
    9: (335, 364),
    10: (365, 400),
    11: (401, 436),
    12: (437, 468),
    13: (469, 506),
    14: (507, 539),
}


@dataclass(frozen=True)
class Segment:
    chapter: int
    page: int
    raw: str
    norm: str


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]+", text)).lower()


def split_segments(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text.replace("\f", "\n")).strip()
    return [part for part in re.split(r"(?<=[。！？；;])", compact) if part]


def chapter_for_ybt_page(physical: int) -> int:
    result = 1
    for chapter, start in YBT_STARTS.items():
        if physical >= start:
            result = chapter
    return result


def load_ybt(pages_dir: Path) -> list[Segment]:
    segments: list[Segment] = []
    for path in sorted(pages_dir.glob("page-*.txt")):
        physical = int(path.stem.split("-")[1])
        if physical < 9:
            continue
        actual = physical - 8
        chapter = chapter_for_ybt_page(physical)
        text = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(rf"(?m)^\s*{actual}\s*$", "", text)
        for raw in split_segments(text):
            norm = normalize(raw)
            if 8 <= len(norm) <= 520 and "铁头tips" not in norm:
                segments.append(Segment(chapter, actual, raw, norm))
    return segments


def load_textbook(pages_dir: Path) -> list[Segment]:
    segments: list[Segment] = []
    for chapter, (start, end) in TEXTBOOK_RANGES.items():
        for pdf_page in range(start, end + 1):
            path = pages_dir / f"tb-{pdf_page:03d}.txt"
            if not path.exists():
                continue
            for raw in split_segments(path.read_text(encoding="utf-8", errors="replace")):
                norm = normalize(raw)
                if 8 <= len(norm) <= 620:
                    segments.append(Segment(chapter, pdf_page - 12, raw, norm))
    return segments


def ngrams(text: str, size: int = 3) -> set[str]:
    return {text[index : index + size] for index in range(max(0, len(text) - size + 1))}


def edit_summary(left: str, right: str) -> tuple[int, str]:
    matcher = SequenceMatcher(None, left, right, autojunk=False)
    cost = 0
    changes: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        cost += max(i2 - i1, j2 - j1)
        changes.append(f"{tag}:{left[i1:i2]}→{right[j1:j2]}")
    return cost, " | ".join(changes)


def scan(ybt: list[Segment], textbook: list[Segment]) -> list[dict[str, str]]:
    index: dict[tuple[int, str], list[int]] = defaultdict(list)
    for number, segment in enumerate(textbook):
        for gram in ngrams(segment.norm):
            index[(segment.chapter, gram)].append(number)

    rows: list[dict[str, str]] = []
    seen: set[tuple[int, str, str]] = set()
    for source in ybt:
        counts: Counter[int] = Counter()
        for gram in ngrams(source.norm):
            counts.update(index.get((source.chapter, gram), ()))
        best: tuple[float, Segment] | None = None
        for number, _ in counts.most_common(24):
            target = textbook[number]
            ratio = SequenceMatcher(None, source.norm, target.norm, autojunk=False).ratio()
            if best is None or ratio > best[0]:
                best = (ratio, target)
        if best is None:
            continue
        ratio, target = best
        if source.norm == target.norm:
            continue
        cost, changes = edit_summary(source.norm, target.norm)
        max_len = max(len(source.norm), len(target.norm))
        # Retain close prose mutations and moderately close definition/classification
        # candidates. OCR creates noise, so these remain candidates until image check.
        if ratio < 0.57 or cost > max(42, int(max_len * 0.38)):
            continue
        key = (source.page, source.norm, target.norm)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "章节": CHAPTERS[source.chapter],
                "一本通实际页码": str(source.page),
                "一本通句段": source.raw,
                "教材页码": f"P{target.page}",
                "教材OCR近似句段": target.raw,
                "相似度": f"{ratio:.4f}",
                "字符差异成本": str(cost),
                "字符差异": changes,
            }
        )
    rows.sort(key=lambda row: (int(row["一本通实际页码"]), -float(row["相似度"])))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ybt-pages", type=Path, required=True)
    parser.add_argument("--textbook-pages", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ybt = load_ybt(args.ybt_pages)
    textbook = load_textbook(args.textbook_pages)
    rows = scan(ybt, textbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        headers = list(rows[0]) if rows else ["章节"]
        writer = csv.DictWriter(stream, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"scan_ok ybt_segments={len(ybt)} textbook_segments={len(textbook)} candidates={len(rows)}")


if __name__ == "__main__":
    main()
