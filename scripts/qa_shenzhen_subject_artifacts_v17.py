from __future__ import annotations

from pathlib import Path
import re

import qa_shenzhen_subject_artifacts_v12 as previous
from docx import Document


ROOT = Path(__file__).resolve().parents[1]
previous.SPECS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.md",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.pdf",
        ROOT / "content/shenzhen_general_baoming_v17_page_map.json",
        (15, 75, 90, 236),
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.md",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v17_page_map.json",
        (4, 25, 25, 50),
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.md",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v17_page_map.json",
        (13, 39, 45, 76),
    ),
)


def ignore_renderer_tags(text: str, mask: tuple[bool, ...]) -> tuple[bool, ...]:
    output = list(mask)
    for match in re.finditer(r"【名词解释：[^】]+】", text):
        output[match.start() : match.end()] = [False] * (match.end() - match.start())
    return tuple(output)


def markdown_body_runs(path: Path) -> list[tuple[str, tuple[bool, ...]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    first = next(index for index, line in enumerate(lines) if line.startswith("# 第一章 "))
    output: list[tuple[str, tuple[bool, ...]]] = []
    for line in lines[first:]:
        value = line.strip()
        if not value or value == "---" or value.startswith("#"):
            continue
        text: list[str] = []
        mask: list[bool] = []
        bold = False
        index = 0
        while index < len(value):
            if value.startswith("**", index):
                bold = not bold
                index += 2
                continue
            if value[index] != "\u2060":
                text.append(value[index])
                mask.append(bold)
            index += 1
        assert not bold, (path, value, "unclosed bold marker")
        plain = "".join(text)
        output.append((plain, ignore_renderer_tags(plain, tuple(mask))))
    return output


def word_body_runs(path: Path) -> list[tuple[str, tuple[bool, ...]]]:
    document = Document(path)
    started = False
    output: list[tuple[str, tuple[bool, ...]]] = []
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Heading 1":
            started = True
            continue
        if not started or paragraph.style.name != "Normal":
            continue
        text: list[str] = []
        mask: list[bool] = []
        for run in paragraph.runs:
            for char in run.text:
                if char == "\u2060":
                    continue
                text.append(char)
                mask.append(run.bold is True)
        plain = "".join(text)
        output.append((plain, ignore_renderer_tags(plain, tuple(mask))))
    return output


def validate_word_keyword_runs() -> None:
    for subject, markdown, docx, *_ in previous.SPECS:
        expected = markdown_body_runs(markdown)
        actual = word_body_runs(docx)
        assert len(expected) == len(actual), (subject, len(expected), len(actual))
        for index, (wanted, observed) in enumerate(zip(expected, actual), start=1):
            assert wanted == observed, (subject, index, wanted[0], observed[0])
        print(f"PASS {subject} Word关键词run={len(actual)}")


if __name__ == "__main__":
    validate_word_keyword_runs()
    previous.main()
