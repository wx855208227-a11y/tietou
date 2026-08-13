from __future__ import annotations

import json
from pathlib import Path
import re

import fitz


ROOT = Path(__file__).resolve().parents[1]
BOOKS = (
    {
        "base": ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_任务适配精校版V10",
        "page_map": ROOT / "content/ecnu_intro_baoming_v10_page_map.json",
        "inventory": ROOT / "analysis/ecnu-combined-v2/intro-pdf-inventory.md",
        "first": "第一章心理学研究的对象、方法及其学科发展",
        "header": "华东师范大学347｜心理学导论保命手册",
        "expected_titles": 134,
    },
    {
        "base": ROOT / "deliverables/华东师范大学347实验心理学保命手册_全本_任务适配精校版V2",
        "page_map": ROOT / "content/ecnu_experiment_baoming_v2_page_map.json",
        "inventory": ROOT / "analysis/ecnu-combined-v2/experiment-pdf-inventory.md",
        "first": "第一章绪论",
        "header": "华东师范大学347｜实验心理学保命手册",
        "expected_titles": 60,
    },
)


def compact(value: str) -> str:
    return re.sub(r"\s+|\u2060", "", value).translate(str.maketrans("", "", "—–－-"))


def markdown_titles(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        line[2:].strip() if line.startswith("# ") else line[3:].strip().split("【", 1)[0]
        for line in lines
        if (line.startswith("# ") and not line.startswith("# 华东师范大学"))
        or re.match(r"^## [一二三四五六七八九十百]+、", line)
    ]


def update(spec: dict[str, object]) -> None:
    base = Path(spec["base"])
    markdown = base.with_suffix(".md")
    pdf = base.with_suffix(".pdf")
    titles = markdown_titles(markdown)
    assert len(titles) == spec["expected_titles"] and len(titles) == len(set(titles))
    document = fitz.open(pdf)
    page_texts = [page.get_text() for page in document]
    first_body = next(
        index
        for index, text in enumerate(page_texts)
        if compact(str(spec["first"])) in compact(text)
        and compact(str(spec["header"])) in compact(text)
    )

    actual: dict[str, int] = {}
    cursor = first_body
    for title in titles:
        needle = compact(title)
        found = next(
            index for index in range(cursor, len(page_texts)) if needle in compact(page_texts[index])
        )
        actual[title] = found - first_body + 1
        cursor = found

    page_map = Path(spec["page_map"])
    page_map.parent.mkdir(parents=True, exist_ok=True)
    page_map.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    inventory = Path(spec["inventory"])
    inventory.parent.mkdir(parents=True, exist_ok=True)
    inventory_lines = [f"file: {pdf.resolve()}", f"pages: {len(document)}"]
    for page_number, page in enumerate(document, start=1):
        text = page.get_text()
        blocks = page.get_text("dict")["blocks"]
        inventory_lines.append(
            f"PAGE {page_number}: text_chars={len(text)} images={len(page.get_images(full=True))} "
            f"image_blocks={sum(block['type'] == 1 for block in blocks)}"
        )
        inventory_lines.append("  text_sample: " + re.sub(r"\s+", " ", text).strip()[:300].rstrip())
    inventory.write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")
    print(
        f"{base.name}: {len(actual)}项目录页码，正文从物理第{first_body + 1}页开始，"
        f"正文{len(page_texts) - first_body}页，总页数{len(document)}。"
    )


def main() -> None:
    for spec in BOOKS:
        update(spec)


if __name__ == "__main__":
    main()
