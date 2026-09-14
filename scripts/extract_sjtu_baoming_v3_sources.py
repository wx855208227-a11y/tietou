from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import zipfile

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/sjtu_baoming_20260914"
SOURCES = WORK / "sources"
TEXT = WORK / "text"
INVENTORY = WORK / "source_inventory.json"

FILES = (
    ("general_rapid", "上交普通心理学速背手册.docx"),
    ("clinical_rapid", "上交临床心理学速背手册2025定稿.docx"),
    ("clinical_yibentong", "上交临床心理学一本通2025定稿.docx"),
    ("experiment_yibentong", "上交实验心理学一本通.docx"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def formatted_text(paragraph) -> str:
    pieces: list[str] = []
    for run in paragraph.runs:
        value = run.text
        if not value:
            continue
        emphasized = bool(run.bold or run.underline)
        pieces.append(f"**{value}**" if emphasized else value)
    text = "".join(pieces).strip()
    text = re.sub(r"\*\*\s*\*\*", "", text)
    while re.search(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", text):
        text = re.sub(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", r"**\1\2**", text)
    return text


def heading_level(style_name: str) -> int | None:
    match = re.fullmatch(r"Heading (\d+)", style_name)
    if match:
        return min(int(match.group(1)), 4)
    match = re.fullmatch(r"标题\s*([一二三四1234])", style_name)
    if match:
        value = match.group(1)
        if value in {"一", "二", "三", "四"}:
            return {"一": 1, "二": 2, "三": 3, "四": 4}[value]
        return int(value)
    return None


def extract(source: Path, output: Path) -> dict[str, object]:
    document = Document(source)
    lines: list[str] = []
    nonempty = 0
    styles: Counter[str] = Counter()
    for paragraph in document.paragraphs:
        text = formatted_text(paragraph)
        if not text or paragraph.style.name.lower().startswith("toc "):
            continue
        nonempty += 1
        styles[paragraph.style.name] += 1
        level = heading_level(paragraph.style.name)
        lines.extend((f"{'#' * level} {text}" if level else text, ""))

    table_rows = 0
    if document.tables:
        lines.extend(("", "# 文档表格", ""))
        for table_index, table in enumerate(document.tables, 1):
            lines.extend((f"## 表格{table_index}", ""))
            for row in table.rows:
                table_rows += 1
                values = [re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells]
                lines.extend((" | ".join(values), ""))

    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    with zipfile.ZipFile(source) as archive:
        assert archive.testzip() is None
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    return {
        "file": source.name,
        "bytes": source.stat().st_size,
        "sha256": sha256(source),
        "paragraphs": len(document.paragraphs),
        "nonempty_paragraphs": nonempty,
        "tables": len(document.tables),
        "table_rows": table_rows,
        "embedded_media": len(media),
        "top_styles": styles.most_common(12),
        "markdown": str(output),
    }


def main() -> None:
    TEXT.mkdir(parents=True, exist_ok=True)
    inventory: dict[str, dict[str, object]] = {}
    for key, name in FILES:
        source = SOURCES / name
        assert source.is_file(), source
        inventory[key] = extract(source, TEXT / f"{key}.md")
    INVENTORY.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(inventory, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
