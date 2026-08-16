from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/sjtu_baoming_20260816"
SOURCES = WORK / "sources"
TEXT = WORK / "text"


DOCX_FILES = (
    "27上交普心速背手册.docx",
    "上交普通心理学一本通.docx",
    "上交实验心理学一本通.docx",
    "上交临床心理学一本通.docx",
    "312心理学考研历年真题详解.docx",
    "347应用心理专硕名校真题正解_勤思.docx",
    "347应用心理硕士名校真题真练_学府.docx",
    "347应用心理专研试题册_文都比邻.docx",
    "347应用心理专研解析册_文都比邻.docx",
)


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
    text = re.sub(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", r"**\1\2**", text)
    return text


def heading_level(style_name: str) -> int | None:
    match = re.fullmatch(r"Heading (\d+)", style_name)
    if match:
        return min(int(match.group(1)), 4)
    if style_name == "标题4":
        return 4
    return None


def to_markdown(source: Path, output: Path) -> tuple[int, int, Counter[str]]:
    document = Document(source)
    lines: list[str] = []
    for paragraph in document.paragraphs:
        text = formatted_text(paragraph)
        if not text or paragraph.style.name.startswith("toc "):
            continue
        level = heading_level(paragraph.style.name)
        lines.extend((f"{'#' * level} {text}" if level else text, ""))

    if document.tables:
        lines.extend(("", "# 文档表格", ""))
        for table_index, table in enumerate(document.tables, 1):
            lines.extend((f"## 表格{table_index}", ""))
            for row in table.rows:
                values = [cell.text.strip().replace("\n", " / ") for cell in row.cells]
                lines.extend((" | ".join(values), ""))

    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return len(document.paragraphs), len(document.tables), Counter(
        paragraph.style.name for paragraph in document.paragraphs if paragraph.text.strip()
    )


def main() -> None:
    TEXT.mkdir(parents=True, exist_ok=True)
    for name in DOCX_FILES:
        source = SOURCES / name
        assert source.is_file(), source
        paragraphs, tables, styles = to_markdown(source, TEXT / f"{source.stem}.md")
        print(
            f"{name}: paragraphs={paragraphs} tables={tables} "
            f"top_styles={styles.most_common(5)}"
        )


if __name__ == "__main__":
    main()
