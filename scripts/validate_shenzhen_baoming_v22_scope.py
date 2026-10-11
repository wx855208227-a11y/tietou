from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"

FILES = {
    "普通心理学": (
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全范围复核版V22.md",
        90,
    ),
    "实验心理学": (
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全范围补编版V22.md",
        39,
    ),
    "心理与教育测量": (
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全范围复核版V22.md",
        48,
    ),
}

QUESTION_RE = re.compile(r"^### 押题\d+【(名词解释|简答|论述)】(.+)$", re.MULTILINE)
SUBPOINT_RE = re.compile(r"^（(\d+)）", re.MULTILINE)


def question_blocks(text: str) -> list[tuple[re.Match[str], str]]:
    matches = list(QUESTION_RE.finditer(text))
    blocks: list[tuple[re.Match[str], str]] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        relative = text[match.end() : next_start]
        boundary = re.search(r"^#{1,2} ", relative, re.MULTILINE)
        end = match.end() + boundary.start() if boundary else next_start
        blocks.append((match, text[match.end() : end]))
    return blocks


def validate_singleton_subpoints(text: str) -> None:
    for heading, block in question_blocks(text):
        lines = block.splitlines()
        for index, line in enumerate(lines):
            if not re.match(r"^\d+\. ", line):
                continue
            end = next(
                (candidate for candidate in range(index + 1, len(lines)) if re.match(r"^\d+\. ", lines[candidate])),
                len(lines),
            )
            children = [
                int(match.group(1))
                for child in lines[index + 1 : end]
                if (match := re.match(r"^（(\d+)）", child))
            ]
            assert children != [1], (heading.group(0), line)


def main() -> None:
    total = 0
    for subject, (path, expected) in FILES.items():
        text = path.read_text(encoding="utf-8")
        blocks = question_blocks(text)
        assert len(blocks) == expected, (subject, len(blocks), expected)
        assert "请设计实验" not in text and "完成实验设计" not in text
        assert not re.search(r"^### .*\*\*", text, re.MULTILINE)
        validate_singleton_subpoints(text)
        total += len(blocks)
        print(f"PASS {subject} questions={len(blocks)}")

    experiment = FILES["实验心理学"][0].read_text(encoding="utf-8")
    for number, name in zip(
        "一二三四五六七八九十",
        ("绪论", "实验研究的基本问题", "如何读和写心理学实验报告", "反应时", "心理物理学", "注意", "知觉", "记忆与学习", "思维", "情绪"),
    ):
        assert f"# 第{number}章 {name}" in experiment
    measurement = FILES["心理与教育测量"][0].read_text(encoding="utf-8")
    for title in (
        "# 第二章 心理与教育测量简史",
        "# 第十二章 能力测验（下）",
        "# 第十五章 测量应用实务",
    ):
        assert title in measurement
    measurement_source = (
        SOURCE_ROOT / "心理与教育测量/一本通.md"
    ).read_text(encoding="utf-8")
    for term in (
        "高尔顿",
        "首次提出“心理测验",
        "比内—西蒙智力量表",
        "预测目的",
        "能力剖面图",
        "流畅性、变通性、独特性",
        "无领导小组讨论",
        "文件筐测试",
        "职业决策自我效能量表",
        "品德测量",
    ):
        assert term in measurement_source, ("测量一本通缺少新增依据", term)
        assert term.replace("首次提出“心理测验", "首次提出“心理测验**") in measurement or term in measurement, (
            "测量新增内容未保留来源点",
            term,
        )
    assert total == 177
    print("PASS total questions=177, experiment chapters=10, measurement restored chapters=3")


if __name__ == "__main__":
    main()
