from __future__ import annotations

import argparse
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re

from audit_shenzhen_baoming_v7_sources import source_chapter, split_chapters, split_questions
from rebuild_shenzhen_baoming_v17_word_keywords import SUBJECT_DOCX, formatted_paragraph


ROOT = Path(__file__).resolve().parents[1]
MANUALS = {
    "普通心理学": ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.md",
    "实验心理学": ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.md",
    "心理与教育测量": ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.md",
}
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
TAG_RE = re.compile(r"【[^】]+】")
ENUM_RE = re.compile(r"^(?:\d+[.、]|[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z][.、])\s*")


@dataclass(frozen=True)
class SourceLine:
    number: int
    marked: str
    plain: str
    keywords: tuple[str, ...]


def compact(value: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", value.replace("**", ""))


def answer_plain(value: str) -> str:
    value = TAG_RE.sub("", value.replace("**", ""))
    return ENUM_RE.sub("", value).strip()


def inherited_marked(term: str, marked_terms: tuple[str, ...]) -> bool:
    wanted = compact(term)
    return bool(wanted) and any(wanted in compact(item) for item in marked_terms)


def source_markdown_with_tables(path: Path) -> str:
    """Read Word body paragraphs and Word table cells in document order.

    Table rows are inserted at their actual body position so the review packet
    cannot silently omit a source region. This function only prepares evidence;
    it does not alter the answer.
    """
    from docx import Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(path)
    output: list[str] = []
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            paragraph = Paragraph(child, document)
            value = formatted_paragraph(paragraph)
            if not value:
                continue
            style = paragraph.style.name
            if style == "Heading 1":
                output.extend((f"# {value}", ""))
            elif style == "Heading 2":
                output.extend((f"## {value}", ""))
            elif style == "Heading 3":
                output.extend((f"### {value}", ""))
            elif not style.startswith("toc "):
                output.extend((value, ""))
        elif isinstance(child, CT_Tbl):
            table = Table(child, document)
            for row in table.rows:
                cells: list[str] = []
                for cell in row.cells:
                    values = [
                        formatted_paragraph(paragraph)
                        for paragraph in cell.paragraphs
                        if paragraph.text.strip()
                    ]
                    cells.append(" / ".join(values))
                output.extend(("｜".join(cells), ""))
    return "\n".join(output).strip() + "\n"


def source_lines(local_source: str) -> list[SourceLine]:
    output: list[SourceLine] = []
    for number, line in enumerate(local_source.splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue
        keywords = tuple(value.strip() for value in BOLD_RE.findall(line) if value.strip())
        output.append(SourceLine(number, line, line.replace("**", ""), keywords))
    return output


def match_score(answer: str, source: SourceLine) -> tuple[float, int, float]:
    left = compact(answer)
    right = compact(source.plain)
    if not left or not right:
        return 0.0, 0, 0.0
    matcher = SequenceMatcher(None, left, right)
    longest = max((block.size for block in matcher.get_matching_blocks()), default=0)
    containment = longest / min(len(left), len(right))
    return matcher.ratio(), longest, containment


def relevant_matches(answer: str, sources: list[SourceLine]) -> list[SourceLine]:
    candidates: list[tuple[float, int, float, SourceLine]] = []
    for source in sources:
        ratio, longest, containment = match_score(answer, source)
        source_terms_present = sum(
            1 for term in source.keywords if len(compact(term)) >= 2 and compact(term) in compact(answer)
        )
        if longest < 4 and not source_terms_present:
            continue
        score = ratio + min(0.35, containment * 0.25) + min(0.3, source_terms_present * 0.08)
        candidates.append((score, longest, containment, source))
    return [item[-1] for item in sorted(candidates, key=lambda item: item[:3], reverse=True)[:6]]


def question_packet(subject: str, question_index: int) -> str:
    manual = MANUALS[subject].read_text(encoding="utf-8")
    questions = split_questions(manual)
    chapter, title, answer = questions[question_index - 1]
    source = source_markdown_with_tables(SUBJECT_DOCX[subject])
    chapters = split_chapters(source)
    local_source = source_chapter(subject, chapter, chapters)
    sources = source_lines(local_source)

    output = [
        f"# {subject} 第{question_index}题",
        "",
        f"- 章节：{chapter}",
        f"- 题目：{title}",
        "",
        "## 当前答案",
        "",
        answer.rstrip(),
        "",
        "## 逐行来源对照",
        "",
    ]
    for line_number, line in enumerate(answer.splitlines(), start=1):
        if not line.strip() or line.startswith("#") or line.startswith("## "):
            continue
        current_marks = tuple(BOLD_RE.findall(line))
        matches = relevant_matches(answer_plain(line), sources)
        output.extend((f"### A{line_number}", "", line, ""))
        inherited: list[str] = []
        missing: list[str] = []
        plain_line = compact(line)
        for source in matches:
            for term in source.keywords:
                if len(compact(term)) < 2 or compact(term) not in plain_line:
                    continue
                target = inherited if inherited_marked(term, current_marks) else missing
                if term not in target:
                    target.append(term)
        output.append("- 已继承：" + ("；".join(inherited) if inherited else "无"))
        output.append("- 漏标候选：" + ("；".join(missing) if missing else "无"))
        output.append("- 当前其他加粗：" + ("；".join(current_marks) if current_marks else "无"))
        output.append("- 来源候选：")
        for source in matches:
            output.append(f"  - S{source.number}：{source.marked}")
        output.append("")
    return "\n".join(output).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", choices=tuple(MANUALS))
    parser.add_argument("question", type=int)
    arguments = parser.parse_args()
    print(question_packet(arguments.subject, arguments.question), end="")


if __name__ == "__main__":
    main()
