#!/usr/bin/env python3
"""Generate independent textbook-alignment candidates for the Huadong Yibentong.

This scanner does not read any prior finding report.  It aligns current Yibentong
sentences directly to the authoritative textbook and exposes small character-level
changes for manual review.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


CHAPTER_NAMES = {
    1: "第一章 心理学研究的对象、方法及其学科发展",
    2: "第二章 心理和行为的生物学基础",
    3: "第三章 条件反射和学习",
    4: "第四章 意识和意识状态",
    5: "第五章 感觉",
    6: "第六章 知觉",
    7: "第七章 记忆",
    8: "第八章 表象和想象",
    9: "第九章 思维",
    10: "第十章 言语",
    11: "第十一章 情绪和情感",
    12: "第十二章 意志",
    13: "第十三章 动机",
    14: "第十四章 技能",
    15: "第十五章 能力",
    16: "第十六章 人格",
    17: "第十七章 心理健康和心理异常",
    18: "第十八章 社会心理",
}

# Physical DOCX-rendered page; the footer-printed body page is physical - 6.
YBT_STARTS = {
    1: 7,
    2: 25,
    3: 42,
    4: 63,
    5: 90,
    6: 118,
    7: 146,
    8: 183,
    9: 192,
    10: 233,
    11: 241,
    12: 256,
    13: 264,
    14: 288,
    15: 301,
    16: 318,
    17: 351,
    18: 357,
}

# Physical textbook PDF pages. Printed textbook page = physical - 12.
TEXTBOOK_RANGES = {
    1: (15, 36),
    2: (37, 59),
    3: (60, 79),
    4: (80, 131),
    5: (132, 176),
    6: (177, 227),
    7: (228, 267),
    8: (268, 287),
    9: (288, 337),
    10: (338, 362),
    11: (363, 394),
    12: (395, 418),
    13: (419, 444),
    14: (445, 466),
    15: (467, 508),
    16: (509, 556),
    17: (557, 588),
    18: (589, 617),
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
    # PDF text extraction inserts blank lines between visual lines. Treating those
    # as paragraph boundaries truncates sentences, so collapse layout whitespace
    # before splitting at real sentence/layer punctuation.
    compact = re.sub(r"\s+", "", text.replace("\f", "\n")).strip()
    return [part for part in re.split(r"(?<=[。！？；;])", compact) if part]


def chapter_for_physical_page(page: int) -> int:
    result = 1
    for chapter, start in YBT_STARTS.items():
        if page >= start:
            result = chapter
    return result


def load_ybt(pages_dir: Path) -> tuple[list[Segment], dict[int, tuple[int, int]]]:
    segments: list[Segment] = []
    coverage: dict[int, list[int]] = defaultdict(list)
    for path in sorted(pages_dir.glob("page-*.txt")):
        physical = int(path.stem.split("-")[1])
        if physical < 7:
            continue
        actual = physical - 6
        chapter = chapter_for_physical_page(physical)
        coverage[chapter].append(actual)
        text = path.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(rf"(?m)^\s*{actual}\s*$", "", text)
        for raw in split_segments(text):
            norm = normalize(raw)
            if 8 <= len(norm) <= 420 and "铁头tips" not in norm:
                segments.append(Segment(chapter, actual, raw, norm))
    ranges = {chapter: (min(pages), max(pages)) for chapter, pages in coverage.items()}
    return segments, ranges


def load_textbook(pages_dir: Path) -> list[Segment]:
    segments: list[Segment] = []
    for chapter, (start, end) in TEXTBOOK_RANGES.items():
        for physical in range(start, end + 1):
            path = pages_dir / f"tb-{physical:03d}.txt"
            text = path.read_text(encoding="utf-8", errors="ignore")
            for raw in split_segments(text):
                norm = normalize(raw)
                if 8 <= len(norm) <= 500:
                    segments.append(Segment(chapter, physical - 12, raw, norm))
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
    by_chapter: dict[int, list[int]] = defaultdict(list)
    index: dict[tuple[int, str], list[int]] = defaultdict(list)
    for number, segment in enumerate(textbook):
        by_chapter[segment.chapter].append(number)
        for gram in ngrams(segment.norm):
            index[(segment.chapter, gram)].append(number)

    rows: list[dict[str, str]] = []
    seen: set[tuple[int, str, str]] = set()
    for source in ybt:
        counts: Counter[int] = Counter()
        for gram in ngrams(source.norm):
            counts.update(index.get((source.chapter, gram), ()))
        if not counts:
            continue
        best: tuple[float, Segment] | None = None
        for number, _ in counts.most_common(16):
            target = textbook[number]
            ratio = SequenceMatcher(None, source.norm, target.norm, autojunk=False).ratio()
            if best is None or ratio > best[0]:
                best = (ratio, target)
        if best is None:
            continue
        ratio, target = best
        cost, changes = edit_summary(source.norm, target.norm)
        if source.norm == target.norm:
            continue
        # Small mutations of otherwise close textbook prose are the highest-risk
        # candidates for added, omitted, or substituted characters.
        if ratio < 0.72 or cost > 28:
            continue
        key = (source.page, source.norm, target.norm)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "章节": CHAPTER_NAMES[source.chapter],
                "一本通实际页码": str(source.page),
                "一本通句段": source.raw,
                "教材页码": f"P{target.page}",
                "教材近似句段": target.raw,
                "相似度": f"{ratio:.4f}",
                "字符差异成本": str(cost),
                "字符差异": changes,
            }
        )
    rows.sort(key=lambda row: (int(row["一本通实际页码"]), -float(row["相似度"])))
    return rows


def write_coverage(path: Path, ranges: dict[int, tuple[int, int]], counts: Counter[int]) -> None:
    lines = [
        "# 华东《心理学导论》一本通从零重审覆盖表",
        "",
        "本表只记录当前附件与主教材的直接核对范围，不记录任何旧版本状态。",
        "",
        "| 章节 | 一本通实际页码 | 主教材页码 | 对齐候选数 | 审核状态 |",
        "|---|---:|---:|---:|---|",
    ]
    for chapter in range(1, 19):
        ybt_start, ybt_end = ranges[chapter]
        tb_start, tb_end = TEXTBOOK_RANGES[chapter]
        lines.append(
            f"| {CHAPTER_NAMES[chapter]} | {ybt_start}—{ybt_end} | "
            f"P{tb_start - 12}—P{tb_end - 12} | {counts[chapter]} | 待人工逐项判定 |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ybt-pages", type=Path, required=True)
    parser.add_argument("--textbook-pages", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    args = parser.parse_args()

    ybt, ranges = load_ybt(args.ybt_pages)
    textbook = load_textbook(args.textbook_pages)
    rows = scan(ybt, textbook)
    args.candidates.parent.mkdir(parents=True, exist_ok=True)
    with args.candidates.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
    counts = Counter(CHAPTER_NAMES.keys())
    counts.clear()
    for row in rows:
        for chapter, name in CHAPTER_NAMES.items():
            if row["章节"] == name:
                counts[chapter] += 1
                break
    write_coverage(args.coverage, ranges, counts)
    print(f"scan_ok ybt_segments={len(ybt)} textbook_segments={len(textbook)} candidates={len(rows)}")


if __name__ == "__main__":
    main()
