#!/usr/bin/env python3
"""Build a page-accurate, unit-level ledger for the SZU Yibentong review.

This script maps clean DOCX paragraphs/table cells to LibreOffice-rendered pages.
The printed footer page is physical page minus eight.  The resulting ledger is
review infrastructure only: it does not decide whether a wording difference is
an error.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


CHAPTER_RANGES = [
    (1, 22, "第一章 心理学的研究对象和方法"),
    (23, 41, "第二章 心理与行为的脑神经基础"),
    (42, 66, "第三章 感觉"),
    (67, 106, "第四章 知觉"),
    (107, 144, "第五章 意识"),
    (145, 190, "第六章 记忆"),
    (191, 239, "第七章 思维"),
    (240, 255, "第八章 语言"),
    (256, 295, "第九章 动机"),
    (296, 321, "第十章 情绪"),
    (322, 337, "第十一章 智力"),
    (338, 375, "第十二章 人格"),
    (376, 411, "第十三章 学习"),
    (412, 440, "第十四章 人生全程发展"),
    (441, 447, "补充章1 行为学习理论"),
    (448, 467, "补充章2 认知学习理论"),
    (468, 480, "补充章3 建构主义与人本主义学习理论"),
    (481, 492, "补充章4 学习动机"),
]

TITLE_RE = re.compile(
    r"^(?:第[一二三四五六七八九十百0-9]+章|[一二三四五六七八九十]+、|"
    r"（[一二三四五六七八九十]+）|\d+[.．]|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[A-Za-z][.．])"
)
TB_PAGE_RE = re.compile(r"(?<![A-Za-z])P\s*(\d{1,3})", re.IGNORECASE)


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9Α-ωα-ω+−-]+", text)).lower()


def chapter_for(actual_page: int | None) -> str:
    if actual_page is None:
        return "前置页"
    for start, end, chapter in CHAPTER_RANGES:
        if start <= actual_page <= end:
            return chapter
    return "页码范围外"


@dataclass
class Record:
    record_no: int
    kind: str
    locator: str
    style: str
    text: str


def load_structure(path: Path) -> list[Record]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream, delimiter="\t")
        return [
            Record(
                record_no=int(row["record_no"]),
                kind=row["kind"],
                locator=row["locator"],
                style=row["style"],
                text=row["text"].strip(),
            )
            for row in rows
        ]


def load_pages(directory: Path) -> dict[int, str]:
    pages: dict[int, str] = {}
    for path in sorted(directory.glob("page-*.txt")):
        physical = int(path.stem.split("-")[1])
        pages[physical] = normalize(path.read_text(encoding="utf-8", errors="replace"))
    return pages


def find_page(text: str, pages: dict[int, str], current: int) -> tuple[int, str]:
    norm = normalize(text)
    if not norm:
        return current, "blank_inherit"

    # Very short labels recur often.  Prefer the current page and only advance
    # one page when the label is not present locally.
    if len(norm) <= 6:
        for page in (current, current + 1):
            if norm in pages.get(page, ""):
                return page, "short_exact"
        return current, "short_inherit"

    probes = [norm]
    for length in (48, 32, 20, 12):
        if len(norm) > length:
            probes.append(norm[:length])

    start = max(1, current - 1)
    stop = min(max(pages), current + 7)
    for probe in probes:
        for page in range(start, stop + 1):
            if probe in pages.get(page, ""):
                return page, "exact" if probe == norm else f"prefix_{len(probe)}"

    # A paragraph can begin near the end of one page and OCR/rendering may omit
    # its first few punctuation-adjacent characters.  Search an internal anchor.
    if len(norm) >= 28:
        anchor = norm[8:28]
        for page in range(start, stop + 1):
            if anchor in pages.get(page, ""):
                return page, "internal_anchor"

    return current, "unresolved_inherit"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = load_structure(args.structure)
    pages = load_pages(args.pages)
    if sorted(pages) != list(range(1, 501)):
        raise SystemExit("expected rendered physical pages 1..500")

    output: list[dict[str, object]] = []
    current_page = 1
    current_tb_page: int | None = None
    current_heading = ""
    zone = "正文"
    zone_has_content = False

    for record in records:
        page, map_status = find_page(record.text, pages, current_page)
        current_page = max(current_page, page)
        actual_page = page - 8 if page >= 9 else None
        text = record.text

        is_title = bool(record.style in {"1", "2", "3", "4"} or TITLE_RE.match(text))
        if is_title and text:
            current_heading = text

        tb_matches = TB_PAGE_RE.findall(text)
        if tb_matches:
            current_tb_page = int(tb_matches[-1])

        compact = re.sub(r"\s+", "", text).lower()
        if "铁头tips" in compact:
            zone = "Tips"
            zone_has_content = False
        elif compact.startswith("补充内容") or "的补充内容" in compact:
            zone = "补充内容"
            zone_has_content = False
        elif zone in {"Tips", "补充内容"} and zone_has_content and is_title:
            zone = "正文"
            zone_has_content = False

        if actual_page is not None and actual_page >= 441:
            source_zone = "补充章"
        else:
            source_zone = zone

        if text and "铁头tips" not in compact and not compact.startswith("补充内容"):
            zone_has_content = True

        if not text:
            unit_type = "空段落"
        elif record.kind == "table":
            unit_type = "表格单元格"
        elif is_title:
            unit_type = "标题/分点"
        else:
            unit_type = "正文句段"

        output.append(
            {
                "单元编号": record.record_no,
                "DOCX定位": record.locator,
                "结构类型": record.kind,
                "样式": record.style,
                "物理页": page,
                "一本通实际页码": actual_page if actual_page is not None else "前置页",
                "章节": chapter_for(actual_page),
                "单元类型": unit_type,
                "来源区": source_zone,
                "最近教材页提示": f"P{current_tb_page}" if current_tb_page is not None else "",
                "最近标题": current_heading,
                "一本通文本": text,
                "页码映射状态": map_status,
                "审核状态": "待逐条核对" if text else "不适用_空段落",
                "教材/真题证据": "",
                "审核备注": "",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(output)

    nonblank = [row for row in output if row["一本通文本"]]
    body = [row for row in nonblank if row["一本通实际页码"] != "前置页"]
    unresolved = [row for row in nonblank if str(row["页码映射状态"]).startswith("unresolved")]
    covered_pages = {int(row["一本通实际页码"]) for row in body}
    print(f"records={len(output)} nonblank={len(nonblank)} body_units={len(body)}")
    print(f"covered_printed_pages={len(covered_pages)} min={min(covered_pages)} max={max(covered_pages)}")
    print(f"unresolved_page_maps={len(unresolved)}")


if __name__ == "__main__":
    main()
