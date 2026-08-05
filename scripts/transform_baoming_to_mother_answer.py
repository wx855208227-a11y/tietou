from __future__ import annotations

import argparse
import re
from pathlib import Path


TIER_TAGS = ("名解采分点", "答题总起", "共用采分点", "论述新增采分点")
BONUS_TAGS = ("名解加分项", "起笔加分项", "共用加分项", "论述加分项")
QUESTION_REF_RE = re.compile(r"(?:\*\*)?【题[①②③④⑤⑥⑦⑧⑨⑩]+】(?:\*\*)?")
BOLD_QUESTION_TERM_RE = re.compile(
    r"\*\*【题[①②③④⑤⑥⑦⑧⑨⑩]+】([^*]+)\*\*"
)
NUMBERED_RE = re.compile(r"^(\d+)\.\s*(.*)$")


def strip_tag(line: str, tag: str) -> str:
    return re.sub(rf"(?:\*\*)?【{re.escape(tag)}】(?:\*\*)?\s*", "", line, count=1)


def clean_answer_line(line: str) -> str:
    line = BOLD_QUESTION_TERM_RE.sub(r"**\1**", line)
    line = QUESTION_REF_RE.sub("", line)
    line = re.sub(r"\*\*\s+", "** ", line)
    line = re.sub(r"\s+\*\*", " **", line)
    return line.strip()


def transform_answer(lines: list[str]) -> list[str]:
    body: list[str] = []
    bonuses: list[str] = []
    in_definition = False
    definition_number = 0
    main_number = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if body and body[-1] != "":
                body.append("")
            continue
        if "【背诵主线】" in line:
            continue

        bonus_tag = next((tag for tag in BONUS_TAGS if f"【{tag}】" in line), None)
        if bonus_tag:
            content = clean_answer_line(strip_tag(line, bonus_tag))
            if content:
                bonuses.append(content)
            continue

        tier_tag = next((tag for tag in TIER_TAGS if f"【{tag}】" in line), None)
        if tier_tag:
            line = strip_tag(line, tier_tag)
            if tier_tag == "名解采分点":
                in_definition = True
                line = clean_answer_line(line)
                numbered = NUMBERED_RE.match(line)
                if numbered:
                    definition_number += 1
                    _, content = numbered.groups()
                    line = f"（{definition_number}）{content}"
                line = f"**【名词解释】** {line}"
            else:
                in_definition = False

        line = clean_answer_line(line)
        numbered = NUMBERED_RE.match(line)
        if numbered:
            _, content = numbered.groups()
            if in_definition:
                definition_number += 1
                line = f"（{definition_number}）{content}"
            else:
                main_number += 1
                line = f"{main_number}. {content}"

        if line:
            body.append(line)

    while body and body[-1] == "":
        body.pop()
    body.extend(["", "**【灵活扩充】**"])
    body.extend(f"- {content}" for content in bonuses)
    return body


def transform_markdown(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line == "## 前三章·考前冲刺版":
            output.append("## 前三章·综合母答案试行版")
            index += 1
            continue
        if line == "### 综合答案":
            output.append("### 综合母答案")
            index += 1
            answer_lines: list[str] = []
            while index < len(lines):
                candidate = lines[index]
                if candidate == "---" or candidate.startswith("# ") or candidate.startswith("## "):
                    break
                answer_lines.append(candidate)
                index += 1
            output.extend(transform_answer(answer_lines))
            continue
        output.append(line)
        index += 1
    return "\n".join(output).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    source = arguments.input.read_text(encoding="utf-8")
    transformed = transform_markdown(source)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(transformed, encoding="utf-8")


if __name__ == "__main__":
    main()
