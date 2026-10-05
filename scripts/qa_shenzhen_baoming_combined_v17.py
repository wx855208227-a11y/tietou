from __future__ import annotations

from pathlib import Path

import merge_shenzhen_baoming_manuals_v17 as merge_v17
import qa_shenzhen_baoming_combined_v14 as previous
from docx import Document
from qa_shenzhen_subject_artifacts_v17 import ignore_renderer_tags, word_body_runs


ROOT = Path(__file__).resolve().parents[1]
qa_base = previous.qa_base

qa_base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订Word关键词逐词校准版V17.docx"
qa_base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订Word关键词逐词校准版V17.pdf"
qa_base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v17_page_map.json"
qa_base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V17.md"
qa_base.REPORT_VERSION = "V17"
qa_base.EXPECTED_DEFINITION_CALLS = 362
qa_base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.pdf",
        ROOT / "content/shenzhen_general_baoming_v17_page_map.json",
        15,
        75,
        90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v17_page_map.json",
        4,
        25,
        25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v17_page_map.json",
        13,
        39,
        45,
    ),
)

previous.previous.previous.previous.merge_v11.base.SOURCES = merge_v17.base.SOURCES


def paragraph_runs(paragraph) -> tuple[str, tuple[bool, ...]]:
    text: list[str] = []
    mask: list[bool] = []
    for run in paragraph.runs:
        for char in run.text:
            if char == "\u2060":
                continue
            text.append(char)
            mask.append(run.bold is True)
    plain = "".join(text)
    return plain, ignore_renderer_tags(plain, tuple(mask))


def validate_combined_word_runs() -> None:
    document = Document(qa_base.DOCX)
    paragraphs = document.paragraphs
    part_indexes = [
        index for index, paragraph in enumerate(paragraphs)
        if paragraph.style.name == "Part Title"
    ]
    assert len(part_indexes) == len(qa_base.SUBJECTS), part_indexes
    for subject_index, (subject, source_docx, *_rest) in enumerate(qa_base.SUBJECTS):
        start = part_indexes[subject_index] + 1
        end = part_indexes[subject_index + 1] if subject_index + 1 < len(part_indexes) else len(paragraphs)
        actual = [
            paragraph_runs(paragraph)
            for paragraph in paragraphs[start:end]
            if paragraph.style.name == "Normal" and paragraph.text
        ]
        expected = word_body_runs(source_docx)
        assert actual == expected, (subject, len(actual), len(expected))
        print(f"PASS 合订{subject}关键词run={len(actual)}")


if __name__ == "__main__":
    validate_combined_word_runs()
    previous.previous.previous.main()
