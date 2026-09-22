#!/usr/bin/env python3
"""Audit whether every true-question marker in a Yibentong is effectively 一级.

The DOCX supplies hierarchy and importance labels. A LibreOffice-rendered PDF
supplies the printed footer page number; textbook Pxx annotations are never
used as the Yibentong location.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from zipfile import ZipFile

import pymupdf
from lxml import etree


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
IMPORTANCE_RE = re.compile(r"[（(](一级|二级|三级)[）)]")
TRUE_QUESTION_RE = re.compile(r"【[^】]*真题[^】]*】")
HEADING_LEVEL = {"heading 1": 1, "heading 2": 2, "heading 3": 3, "heading 4": 4}
TEXT_HEADING_PATTERNS = (
    (1, re.compile(r"^第[一二三四五六七八九十百零〇0-9]+章")),
    (2, re.compile(r"^[一二三四五六七八九十百]+、")),
    (3, re.compile(r"^（[一二三四五六七八九十百]+）")),
    (4, re.compile(r"^\d+[.．]")),
    (5, re.compile(r"^（\d+）")),
    (6, re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]")),
    (7, re.compile(r"^[A-Z][.．]")),
    (8, re.compile(r"^[a-z][.．]")),
)
MAX_HEADING_LEVEL = max(level for level, _ in TEXT_HEADING_PATTERNS)


def text_of(paragraph: etree._Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(f".//{W}t")).strip()


def importance(text: str) -> str:
    match = IMPORTANCE_RE.search(text)
    return match.group(1) if match else ""


def normalize(text: str) -> str:
    return "".join(re.findall(r"[\u3400-\u9fffA-Za-z0-9]+", text)).lower()


def footer_page(page: pymupdf.Page) -> str:
    candidates: list[tuple[float, str]] = []
    for block in page.get_text("blocks"):
        _, y0, _, _, text, *_ = block
        compact = "".join(text.split())
        if y0 > page.rect.height * 0.86 and re.fullmatch(r"\d{1,4}", compact):
            candidates.append((y0, compact))
    if not candidates:
        return ""
    return max(candidates)[1]


def rendered_page_for(text: str, normalized_pages: list[str]) -> int | None:
    probes = [normalize(text), normalize(text.split("【", 1)[0])]
    for probe in probes:
        if not probe:
            continue
        matches = [index + 1 for index, page_text in enumerate(normalized_pages) if probe in page_text]
        if len(matches) == 1:
            return matches[0]
    return None


def inferred_heading_level(text: str, style_name: str) -> int | None:
    # Visible numbering is the authoritative hierarchy in the compiled guide.
    # Some older files use Heading 3/4 styles one level deeper than their
    # displayed “三、/（三）” numbering, so style-first inference can erase the
    # actual parent before a numbered child is evaluated.
    for level, pattern in TEXT_HEADING_PATTERNS:
        if pattern.match(text):
            return level
    return HEADING_LEVEL.get(style_name)


def direct_parent(
    current: dict[int, tuple[str, str] | None], structural_level: int | None
) -> str:
    start = (structural_level - 1) if structural_level else MAX_HEADING_LEVEL
    for level in range(start, 0, -1):
        entry = current.get(level)
        if entry:
            return entry[0]
    return ""


def classify(
    own_level: str,
    effective_level: str,
    effective_source: str,
    parent_text: str,
) -> tuple[str, str, str]:
    if effective_level == "一级":
        if own_level == "一级":
            return "是（本条直接一级）", "本条直接标注为一级，符合真题考点必须为一级的规则。", "无需修改"
        return (
            "是（继承一级父标题）",
            f"本条未重复标级，但等级依据“{effective_source}”为一级；按同级子项可省略重复标注规则，实际隶属一级。",
            "无需修改",
        )
    if effective_level in {"二级", "三级"}:
        if own_level:
            suggestion = f"删除本条“（{own_level}）”并使其继承一级父标题，或直接改标“（一级）”。"
            reason = f"本条带真题标注，却明确标为{own_level}，不符合真题考点必须为一级的规则。"
        else:
            suggestion = "在本条或承载该真题点的最近标题上标注“（一级）”；同一父标题下有多个真题点时，可将相应父标题升级为一级。"
            reason = f"本条未单独标级，最近等级依据“{effective_source}”为{effective_level}，因此当前不隶属一级。"
        return f"否（当前为{effective_level}）", reason, suggestion
    return (
        "待确认（无等级依据）",
        f"本条及可识别的上级标题均未发现重要度标注，无法确认是否隶属一级。上级条目：{parent_text or '未识别'}。",
        "在本条或最近的承载标题上补标“（一级）”。",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--file-label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with ZipFile(args.docx) as archive:
        document = etree.fromstring(archive.read("word/document.xml"))
        styles = etree.fromstring(archive.read("word/styles.xml"))
    style_names = {
        style.get(f"{W}styleId"): (
            style.find(f"{W}name").get(f"{W}val") if style.find(f"{W}name") is not None else ""
        )
        for style in styles.findall(f"{W}style")
    }

    pdf = pymupdf.open(args.pdf)
    normalized_pages = [normalize(page.get_text()) for page in pdf]
    current: dict[int, tuple[str, str] | None] = {
        level: None for level in range(1, MAX_HEADING_LEVEL + 1)
    }
    pending_supplement_title = False
    rows: list[dict[str, object]] = []

    for xml_index, paragraph in enumerate(document.findall(f".//{W}p")):
        text = text_of(paragraph)
        style_node = paragraph.find(f"./{W}pPr/{W}pStyle")
        style_id = style_node.get(f"{W}val") if style_node is not None else ""
        style_name = style_names.get(style_id, style_id).lower()
        own_level = importance(text)
        structural_level = inferred_heading_level(text, style_name)

        # Some source documents format a supplement title as an unnumbered,
        # bold paragraph. It is a sibling topic under the current second-level
        # title, not a child of the numbered third-level topic immediately
        # before the supplement box.
        if text and pending_supplement_title:
            if structural_level is None:
                structural_level = 3 if current[2] else 2
            pending_supplement_title = False

        # A few manually compiled titles omit their visible numbering. An
        # explicit importance label still makes them hierarchy-bearing titles.
        if structural_level is None and own_level:
            structural_level = 3 if current[2] else 2

        if structural_level:
            current[structural_level] = (text, own_level)
            for lower in range(structural_level + 1, MAX_HEADING_LEVEL + 1):
                current[lower] = None

        if text.startswith("补充内容"):
            pending_supplement_title = True

        if "真题" not in text:
            continue

        effective_level = own_level
        effective_source = text if own_level else ""
        if not effective_level:
            for level in range(MAX_HEADING_LEVEL, 0, -1):
                entry = current[level]
                if entry and entry[1]:
                    effective_source, effective_level = entry
                    break

        parent_text = direct_parent(current, structural_level)
        conclusion, explanation, suggestion = classify(
            own_level, effective_level, effective_source, parent_text
        )
        physical_page = rendered_page_for(text, normalized_pages)
        printed_page = footer_page(pdf[physical_page - 1]) if physical_page else ""
        chapter = current[1][0] if current[1] else ""
        marker = "；".join(TRUE_QUESTION_RE.findall(text)) or "含‘真题’字样"

        rows.append(
            {
                "文件": args.file_label,
                "一本通实际页码": printed_page or "待定位",
                "PDF物理页": physical_page or "待定位",
                "章节": chapter,
                "真题条目": text,
                "真题标注": marker,
                "本条直接等级": own_level or "未单独标注",
                "最近上级条目": parent_text,
                "有效等级": effective_level or "未标明",
                "等级依据": effective_source or "未找到",
                "是否隶属一级": conclusion,
                "问题说明": explanation,
                "修改建议": suggestion,
                "DOCX_XML定位": f"p{xml_index}",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["是否隶属一级"]).split("（", 1)[0]
        counts[key] = counts.get(key, 0) + 1
    print(f"rows={len(rows)} counts={counts} output={args.output}")


if __name__ == "__main__":
    main()
