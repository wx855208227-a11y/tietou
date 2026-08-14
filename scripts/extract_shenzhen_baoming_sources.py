from __future__ import annotations

from pathlib import Path
import re
import shutil

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/shenzhen_baoming_sources"
GENERAL_WORK = AGENT_DIR / "work/shenzhen_general_baoming_sources"
INBOX = AGENT_DIR / "inbox/feishu"

SOURCE_FILES = {
    "普通心理学/速背手册.docx": INBOX
    / "om_x100b68a94d54d0a0b29b7ffb1cbf4a0/27_.docx",
    "普通心理学/一本通.docx": INBOX
    / "om_x100b68a94c80fca0b4c6d3b785fdc85/27_.docx",
    "实验心理学/速背手册.docx": INBOX
    / "om_x100b68a94d5464acb1ff1113e56ea4a/27_527_ 2.docx",
    "实验心理学/一本通.docx": INBOX
    / "om_x100b68a94c34a4a4b1a2bba0ef0b3b6/27_8.3_.docx",
    "心理与教育测量/速背手册.docx": INBOX
    / "om_x100b68a94d55486cb4cd0fc89e4243d/27_.docx",
    "心理与教育测量/一本通.docx": INBOX
    / "om_x100b68a94c3444a8b1de056d8fd8a58/27_.docx",
    "命题证据/深大初试真题册.docx": GENERAL_WORK / "深大初试真题册.docx",
    "命题证据/深圳大学2026年硕士研究生入学考试大纲.docx": GENERAL_WORK
    / "深圳大学2026年硕士研究生入学考试大纲.docx",
    "命题证据/312心理学考研历年真题详解.docx": GENERAL_WORK
    / "312心理学考研历年真题详解.docx",
    "命题证据/347应用心理专硕名校真题正解.docx": GENERAL_WORK
    / "347应用心理专硕名校真题正解.docx",
}


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


def to_markdown(source: Path, output: Path) -> None:
    document = Document(source)
    lines: list[str] = []
    for paragraph in document.paragraphs:
        text = formatted_text(paragraph)
        if not text:
            continue
        style = paragraph.style.name
        if style == "Heading 1":
            lines.extend((f"# {text}", ""))
        elif style == "Heading 2":
            lines.extend((f"## {text}", ""))
        elif style == "Heading 3":
            lines.extend((f"### {text}", ""))
        elif style.startswith("toc "):
            continue
        else:
            lines.extend((text, ""))
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    for relative, source in SOURCE_FILES.items():
        assert source.is_file(), source
        target = WORK / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        to_markdown(target, target.with_suffix(".md"))
    print(f"已整理{len(SOURCE_FILES)}份深大资料到{WORK}。")


if __name__ == "__main__":
    main()
