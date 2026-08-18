#!/usr/bin/env python3
"""Attach textbook OCR evidence and review buckets to the SZU unit ledger."""

from __future__ import annotations

import argparse
import csv
import re
from difflib import SequenceMatcher
from pathlib import Path


CHAPTER_TEXTBOOK_RANGES = {
    "第一章 心理学的研究对象和方法": (1, 36),
    "第二章 心理与行为的脑神经基础": (37, 74),
    "第三章 感觉": (75, 122),
    "第四章 知觉": (123, 164),
    "第五章 意识": (165, 200),
    "第六章 记忆": (201, 244),
    "第七章 思维": (245, 286),
    "第八章 语言": (287, 322),
    "第九章 动机": (323, 352),
    "第十章 情绪": (353, 388),
    "第十一章 智力": (389, 424),
    "第十二章 人格": (425, 456),
    "第十三章 学习": (457, 494),
    "第十四章 人生全程发展": (495, 527),
}


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9Α-ωα-ω+−-]+", text)).lower()


def load_textbook(directory: Path) -> dict[int, tuple[str, str]]:
    pages: dict[int, tuple[str, str]] = {}
    for path in sorted(directory.glob("tb-*.txt")):
        pdf_page = int(path.stem.split("-")[1])
        printed = pdf_page - 12
        if printed < 1:
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        pages[printed] = (raw, normalize(raw))
    return pages


def strip_point_marker(text: str) -> str:
    return re.sub(
        r"^(?:\d+[.．]?|（\d+）|[一二三四五六七八九十]+、?|（[一二三四五六七八九十]+）|"
        r"[①②③④⑤⑥⑦⑧⑨⑩]|[A-Za-z][.．]?)",
        "",
        text,
    )


def page_candidates(row: dict[str, str]) -> range:
    chapter_start, chapter_end = CHAPTER_TEXTBOOK_RANGES[row["章节"]]
    hint = row["最近教材页提示"]
    if hint:
        value = int(hint[1:])
        start = max(chapter_start, value - 2)
        end = min(chapter_end, value + 7)
        # A stale, mistyped, or explicitly external page reference must not
        # produce an empty search range.  Searching the assigned chapter keeps
        # the anomaly visible for later page-reference review.
        if start <= end:
            return range(start, end + 1)
    return range(chapter_start, chapter_end + 1)


def align(source: str, target: str) -> tuple[float, float, int, int, str]:
    """Return coverage, pair ratio, excerpt bounds and an edit summary."""
    matcher = SequenceMatcher(None, source, target, autojunk=False)
    blocks = [block for block in matcher.get_matching_blocks() if block.size]
    if not blocks:
        return 0.0, 0.0, 0, 0, ""
    matched = sum(block.size for block in blocks)
    coverage = matched / max(1, len(source))
    start = min(block.b for block in blocks)
    end = max(block.b + block.size for block in blocks)
    # Do not let scattered one-character matches span a whole page.  Anchor the
    # excerpt on the largest match when the inferred span is implausibly long.
    if end - start > max(80, len(source) * 3):
        anchor = max(blocks, key=lambda block: block.size)
        start = max(0, anchor.b - max(20, len(source) // 2))
        end = min(len(target), start + max(80, int(len(source) * 1.8)))
    excerpt = target[start:end]
    pair_matcher = SequenceMatcher(None, source, excerpt, autojunk=False)
    ratio = pair_matcher.ratio()
    changes: list[str] = []
    for tag, i1, i2, j1, j2 in pair_matcher.get_opcodes():
        if tag == "equal":
            continue
        left = source[i1:i2]
        right = excerpt[j1:j2]
        if max(len(left), len(right)) <= 24:
            changes.append(f"{tag}:{left or '∅'}→{right or '∅'}")
        elif len(changes) < 4:
            changes.append(f"{tag}:{left[:12]}…→{right[:12]}…")
        if len(changes) >= 8:
            break
    return coverage, ratio, start, end, " | ".join(changes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--textbook-ocr", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.ledger.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    textbook = load_textbook(args.textbook_ocr)

    counts: dict[str, int] = {}
    for row in rows:
        text = row["一本通文本"]
        norm = normalize(text)
        row.update(
            {
                "最佳教材页": "",
                "教材OCR证据片段": "",
                "一本通字符覆盖率": "",
                "与教材片段相似度": "",
                "自动差异摘要": "",
                "逐条复核桶": "",
            }
        )

        if not text:
            bucket = "不适用_空段落"
        elif row["一本通实际页码"] == "前置页":
            bucket = "前置页_结构格式核对"
        elif row["来源区"] in {"Tips", "补充内容", "补充章"}:
            bucket = f"{row['来源区']}_来源与专业核对"
        elif row["章节"] not in CHAPTER_TEXTBOOK_RANGES:
            bucket = "来源待确认"
        elif row["单元类型"] == "标题/分点":
            bucket = "标题_结构范围与真题核对"
        elif row["单元类型"] == "表格单元格":
            bucket = "表格_教材与内部一致性核对"
        elif len(norm) < 8:
            bucket = "短句_结合上下文核对"
        else:
            variants = [norm]
            stripped = strip_point_marker(norm)
            if len(stripped) >= 8 and stripped != norm:
                variants.append(stripped)
            best: tuple[float, float, int, int, int, str, str] | None = None
            for printed_page in page_candidates(row):
                raw_page, norm_page = textbook[printed_page]
                for variant in variants:
                    if variant in norm_page:
                        start = norm_page.index(variant)
                        candidate = (1.0, 1.0, printed_page, start, start + len(variant), "", variant)
                    else:
                        coverage, ratio, start, end, changes = align(variant, norm_page)
                        candidate = (coverage, ratio, printed_page, start, end, changes, variant)
                    if best is None or (candidate[0] * 0.72 + candidate[1] * 0.28) > (best[0] * 0.72 + best[1] * 0.28):
                        best = candidate
            assert best is not None
            coverage, ratio, printed_page, start, end, changes, variant = best
            _, norm_page = textbook[printed_page]
            excerpt = norm_page[start:end]
            row["最佳教材页"] = f"P{printed_page}"
            row["教材OCR证据片段"] = excerpt
            row["一本通字符覆盖率"] = f"{coverage:.3f}"
            row["与教材片段相似度"] = f"{ratio:.3f}"
            row["自动差异摘要"] = changes
            if coverage == 1.0 and ratio == 1.0:
                bucket = "文本一致_仍检查结构与上下文"
            elif coverage >= 0.92 and ratio >= 0.82:
                bucket = "近似复述_核对微小删改"
            elif coverage >= 0.78:
                bucket = "应试压缩_逐条语义核对"
            elif coverage >= 0.58:
                bucket = "较大改写_强核对"
            else:
                bucket = "未可靠对齐_强核对"

        row["逐条复核桶"] = bucket
        counts[bucket] = counts.get(bucket, 0) + 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    for bucket, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{bucket}\t{count}")


if __name__ == "__main__":
    main()
