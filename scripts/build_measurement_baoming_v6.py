from __future__ import annotations

from pathlib import Path
import re

from build_measurement_baoming_v5 import QUESTION_RE


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_任务驱动精校版V5.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_任务模块编号版V6.md"

TOP_RE = re.compile(r"^(\d+)\.\s+")
SECOND_RE = re.compile(r"^（(\d+)）")
CIRCLE_RE = re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])")
CIRCLES = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"

SPECIAL_COMPARE_HEADING = "押题1【简答】比较**智龄、比率智商和离差智商**的含义及特点。"
SPECIAL_COMPARE_INTRO = (
    "**智龄、比率智商和离差智商**都是智力测验分数的解释方式。"
    "三者的**联系**在于均用于说明个体的智力水平，但参照依据和适用范围不同。"
)
SPECIAL_COMPARE_LEAD = "**智龄、比率智商和离差智商**都是智力测验分数的解释方式。"
SPECIAL_COMPARE_CONTACT = (
    "三者的**联系**在于均用于说明个体的智力水平，但参照依据和适用范围不同。"
)


def is_module_header(paragraph: str) -> bool:
    """Identify task modules without treating continuations as new modules."""
    if TOP_RE.match(paragraph) or SECOND_RE.match(paragraph) or CIRCLE_RE.match(paragraph):
        return False
    if paragraph.startswith("综上"):
        return False
    if paragraph.endswith("："):
        return True
    if paragraph.startswith("测量的**构成**包括"):
        return True
    return bool(
        re.search(
            r"(?:三者|三种量表|两类测验|三类效度|各种信度估计方法|常模与标准)"
            r"的\*\*(?:联系|主要区别)\*\*(?:在于|如下)",
            paragraph,
        )
    )


def prepare_paragraphs(heading: str, body: str) -> list[str]:
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", body.strip())
        if paragraph.strip()
    ]
    if heading != SPECIAL_COMPARE_HEADING:
        return paragraphs

    assert paragraphs[0] == SPECIAL_COMPARE_INTRO
    paragraphs[0] = SPECIAL_COMPARE_LEAD
    difference_index = paragraphs.index("三者的**主要区别**如下：")
    paragraphs.insert(difference_index, SPECIAL_COMPARE_CONTACT)
    return paragraphs


def transform_body(heading: str, body: str) -> str:
    paragraphs = prepare_paragraphs(heading, body)
    module_indices = [
        index for index, paragraph in enumerate(paragraphs) if is_module_header(paragraph)
    ]
    assert module_indices, heading
    assert module_indices[0] > 0, heading

    module_number = 0
    in_modules = False
    child_number = grandchild_number = letter_number = 0
    transformed: list[str] = []
    for index, paragraph in enumerate(paragraphs):
        if index in module_indices:
            module_number += 1
            in_modules = True
            child_number = grandchild_number = letter_number = 0
            transformed.append(f"{module_number}. {paragraph}")
            continue
        if paragraph.startswith("综上"):
            transformed.append(paragraph)
            in_modules = False
            continue
        if not in_modules:
            transformed.append(paragraph)
            continue
        if match := TOP_RE.match(paragraph):
            child_number += 1
            grandchild_number = letter_number = 0
            transformed.append(f"（{child_number}）" + paragraph[match.end() :])
            continue
        if match := SECOND_RE.match(paragraph):
            grandchild_number += 1
            letter_number = 0
            assert grandchild_number <= len(CIRCLES)
            transformed.append(CIRCLES[grandchild_number - 1] + paragraph[match.end() :])
            continue
        if match := CIRCLE_RE.match(paragraph):
            letter_number += 1
            assert letter_number <= 26
            transformed.append(
                f"{chr(ord('a') + letter_number - 1)}. " + paragraph[match.end() :].lstrip()
            )
            continue
        transformed.append(paragraph)

    assert transformed[-1].startswith("综上"), heading
    return "\n\n".join(transformed)


def transform(text: str) -> str:
    # 保留“极简直背版”前缀，以复用已经验收的12磅正文、圆括号扩容、
    # 黑白打印和舒适题间距版式；任务模块编号由文件版本和正文结构体现。
    text = text.replace("## 全本·极简直背版V5", "## 全本·极简直背版V6", 1)

    def replace(match: re.Match[str]) -> str:
        heading = match.group("heading")
        body = transform_body(heading, match.group("body"))
        return f"### {heading}\n\n{body}\n"

    result, count = QUESTION_RE.subn(replace, text)
    assert count == 45
    return result


def main() -> None:
    OUTPUT.write_text(transform(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"已生成{OUTPUT}。")


if __name__ == "__main__":
    main()
