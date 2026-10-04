from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

from audit_shenzhen_baoming_v7_sources import source_chapter, split_chapters, split_questions
from rebuild_shenzhen_baoming_v3 import replace_question
from rebuild_shenzhen_baoming_v14_point_integrity import (
    build_experiment as build_experiment_v14,
    build_general as build_general_v14,
    build_measurement as build_measurement_v14,
    collapse_singleton_subpoints,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V15.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V15.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V15.md"


SUBJECT_SOURCES = {
    "普通心理学": SOURCE_ROOT / "普通心理学/速背手册.md",
    "实验心理学": SOURCE_ROOT / "实验心理学/速背手册.md",
    "心理与教育测量": SOURCE_ROOT / "心理与教育测量/速背手册.md",
}


IMPLICIT_EXPLICIT_MEMORY = r"""### 押题1【论述】比较内隐记忆和外显记忆的异同。

内隐记忆和外显记忆都反映过去经验对当前行为的作用，但二者受各种实验变量影响的方式不同。

1. 两类记忆的基本含义如下：

（1）外显记忆是过去经验对当前作业产生的有意识影响。（从意识参与角度看，外显记忆要求有意识地回忆或再认；词表回忆是常用任务。）【名词解释：外显记忆】

（2）内隐记忆是个体在无意识情况下，过去经验对当前任务产生的无意识影响。（从意识参与角度看，内隐记忆不要求有意识提取；词干补笔中的启动效应是常用任务。）【名词解释：内隐记忆】

2. 二者的联系：二者都以过去经验为基础，都能影响当前任务表现，并可通过实验任务加以测量。（同一次学习经历可能同时留下外显和内隐效应。）

3. 二者的区别如下：

（1）加工深度对两者的影响不同：加工深度不影响内隐记忆，但对外显记忆有非常明显的影响。（语义加工通常提高有意识回忆，却未必同等提高启动效应。）

（2）两者的保持时间不同：内隐记忆随时间延长而发生的消退比外显记忆慢得多。（经过较长时间，个体可能说不出学过的内容，但作业表现仍受其影响。）

（3）记忆负荷量的变化对两者的影响不同：外显记忆会随记忆项目增多而不容易记住，内隐记忆则不然。（有限意识资源对外显提取的制约更明显。）

（4）呈现方式的改变对两者的影响不同：感觉通道的改变会严重影响内隐记忆的作业成绩，而对外显记忆的效果没有影响。（内隐启动对刺激的知觉形式更敏感。）

（5）干扰因素对两者的影响不同：外显记忆容易受到其他无关信息的干扰，内隐记忆则不易受到干扰。（这说明二者可能依赖不同的加工和表征机制。）

综上，内隐记忆与外显记忆在加工深度、保持时间、记忆负荷量、呈现方式和干扰因素上表现出不同的实验效应。

---
"""


ENUM_PREFIX = re.compile(
    r"^(?:\s*(?:\d+[.、]|[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|[a-z][.、])\s*)+"
)
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
TAG_RE = re.compile(r"【[^】]+】")

# These fragments are too general to function as useful scoring keywords on their own.
KEYWORD_STOPLIST = {
    "主要", "基本", "一般", "不同", "相同", "影响", "特点", "内容", "方法",
    "过程", "作用", "功能", "关系", "因素", "问题", "结果", "进行", "通过",
    "可以", "包括", "分类", "意义", "研究", "理论", "实验", "测验", "被试",
    "行为", "心理", "信息", "材料", "个体", "活动", "发展", "学习", "记忆",
    "如下", "以上", "其他", "重要", "水平", "方面", "阶段", "条件", "系统",
    "事物", "基础", "特征", "规则", "结论", "部分", "结合", "运用", "时间",
    "效果", "同时", "提取", "回忆", "再认", "消退", "干扰", "联系",
}


def compact(value: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9±△Δ=./—-]+", value))


def clean_source_keyword(raw: str) -> str | None:
    value = ENUM_PREFIX.sub("", raw)
    value = re.sub(r"【[^】]+】", "", value)
    value = value.strip(" \t\r\n，。；：、,.!?！？（）()[]【】“”‘’—-|")
    key = compact(value)
    if not key or key in KEYWORD_STOPLIST:
        return None
    if len(key) < 2 or len(key) > 22:
        return None
    if value.startswith(("是指", "指的是", "认为", "包括以下", "主要包括")):
        return None
    return value


def keyword_variants(term: str) -> tuple[str, ...]:
    variants: list[str] = [term]
    if "——" in term:
        right = re.sub(r"[（(][^）)]*[）)]", "", term.split("——", 1)[1])
        variants.extend(
            value.strip() for value in re.split(r"[、和与及]", right) if value.strip()
        )
    for pattern in (
        r"^(.+?)的变化对两者.*$",
        r"^(.+?)的改变对两者.*$",
        r"^(.+?)对两者.*$",
        r"^两者的(.+?)不同$",
    ):
        match = re.match(pattern, term)
        if match:
            variants.append(match.group(1))
            break
    cleaned: list[str] = []
    for value in variants:
        item = clean_source_keyword(value)
        if item and item not in cleaned:
            cleaned.append(item)
    return tuple(cleaned)


def source_keywords(source: str) -> tuple[str, ...]:
    terms: list[str] = []
    # Point headings are scoring keywords even when the source Word did not apply
    # bold/underline to the heading itself.
    for line in source.splitlines():
        plain_line = line.replace("**", "").strip()
        match = re.match(
            r"^(?:\d+[.、]|[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|[a-z][.、])\s*(.+)$",
            plain_line,
        )
        if not match:
            continue
        label = match.group(1).split("：", 1)[0].strip()
        label = re.sub(r"【[^】]+】|[（(](?:一级|二级|三级|\d+年真题)[^）)]*[）)]", "", label)
        if label.endswith("。") or len(compact(label)) > 20:
            continue
        item = clean_source_keyword(label)
        if item and item not in terms:
            terms.append(item)
    for match in BOLD_RE.finditer(source):
        raw = match.group(1)
        raw_without_prefix = ENUM_PREFIX.sub("", raw).strip()
        if "——" in raw_without_prefix:
            right = re.sub(
                r"[（(][^）)]*[）)]", "", raw_without_prefix.split("——", 1)[1]
            )
            for value in re.split(r"[、和与及]", right):
                item = clean_source_keyword(value.strip())
                if item and item not in terms:
                    terms.append(item)
        term = clean_source_keyword(raw)
        if not term:
            continue
        # Reject short fragments created when Word formatting cuts through a Chinese word,
        # such as "高**级形式**" in the extracted source.
        before = source[match.start() - 1 : match.start()]
        after = source[match.end() : match.end() + 1]
        if len(compact(term)) <= 3 and (
            (before and re.match(r"[\u4e00-\u9fff]", before))
            or (after and re.match(r"[\u4e00-\u9fff]", after))
        ):
            continue
        for value in keyword_variants(term):
            if value not in terms:
                terms.append(value)
    return tuple(terms)


def protected_ranges(line: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in TAG_RE.finditer(line)]


def mark_line(line: str, terms: tuple[str, ...]) -> str:
    plain = line.replace("**", "")
    if not plain or plain.startswith("#") or plain == "---":
        return plain

    protected = protected_ranges(plain)
    spans: list[tuple[int, int]] = []
    occupied = [False] * len(plain)
    line_terms = list(terms)
    for definition in re.findall(r"【名词解释：([^】]+)】", plain):
        if definition not in line_terms:
            line_terms.append(definition)
    for term in sorted(line_terms, key=lambda value: (-len(value), value)):
        start = 0
        while True:
            index = plain.find(term, start)
            if index < 0:
                break
            end = index + len(term)
            start = end
            if any(left < end and index < right for left, right in protected):
                continue
            if any(occupied[index:end]):
                continue
            spans.append((index, end))
            occupied[index:end] = [True] * (end - index)

    if not spans:
        return plain
    pieces: list[str] = []
    cursor = 0
    for start, end in sorted(spans):
        pieces.append(plain[cursor:start])
        pieces.append(f"**{plain[start:end]}**")
        cursor = end
    pieces.append(plain[cursor:])
    result = "".join(pieces)
    while "****" in result:
        result = result.replace("****", "")
    return result


def align_question_keywords(answer: str, local_source: str) -> str:
    terms = source_keywords(local_source)
    return "\n".join(mark_line(line, terms) for line in answer.splitlines())


def align_manual_keywords(text: str, subject: str) -> str:
    speed = SUBJECT_SOURCES[subject].read_text(encoding="utf-8")
    chapters = split_chapters(speed)
    questions = split_questions(text)
    replacements: dict[str, str] = {}
    for chapter, title, answer in questions:
        local_source = source_chapter(subject, chapter, chapters)
        replacements[answer] = align_question_keywords(answer, local_source)
    for old, new in replacements.items():
        text = text.replace(old, new, 1)
    # Question titles should use heading style only; inline keyword bolding belongs to answers.
    text = re.sub(r"(?m)^(### .*)$", lambda match: match.group(1).replace("**", ""), text)
    return text


def update_guide(text: str) -> str:
    old = "- 圆括号外是背诵主体，写全可以拿到主要分数。"
    new = "- 圆括号外是背诵主体，写全可以拿到主要分数；正文加粗处为需要优先记忆的关键词。"
    assert old in text
    return text.replace(old, new, 1)


def build_general() -> str:
    text = replace_question(
        build_general_v14(),
        "比较内隐记忆和外显记忆",
        IMPLICIT_EXPLICIT_MEMORY,
    )
    text = collapse_singleton_subpoints(text)
    text = update_guide(text)
    return align_manual_keywords(text, "普通心理学").rstrip() + "\n"


def build_experiment() -> str:
    return align_manual_keywords(update_guide(build_experiment_v14()), "实验心理学").rstrip() + "\n"


def build_measurement() -> str:
    return align_manual_keywords(update_guide(build_measurement_v14()), "心理与教育测量").rstrip() + "\n"


def main() -> None:
    outputs = (
        (GENERAL_OUTPUT, build_general()),
        (EXPERIMENT_OUTPUT, build_experiment()),
        (MEASUREMENT_OUTPUT, build_measurement()),
    )
    for path, content in outputs:
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
