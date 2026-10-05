from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from audit_shenzhen_baoming_v7_sources import source_chapter, split_chapters, split_questions
from rebuild_shenzhen_baoming_v15_source_keywords import (
    SUBJECT_SOURCES,
    build_experiment as build_experiment_v15,
    build_general as build_general_v15,
    build_measurement as build_measurement_v15,
)
from validate_shenzhen_baoming_v15_source_keywords import explicit_terms, plain


ROOT = Path(__file__).resolve().parents[1]

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V16.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V16.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V16.md"


SUBJECT_OUTPUTS = {
    "普通心理学": GENERAL_OUTPUT,
    "实验心理学": EXPERIMENT_OUTPUT,
    "心理与教育测量": MEASUREMENT_OUTPUT,
}


SUBJECT_BUILDERS = {
    "普通心理学": build_general_v15,
    "实验心理学": build_experiment_v15,
    "心理与教育测量": build_measurement_v15,
}


BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
TAG_RE = re.compile(r"【[^】]+】")
ENUM_PREFIX = re.compile(
    r"^(?:\s*(?:\d+[.、]|[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z][.、])\s*)+"
)
ITEM_PATTERNS = (
    (3, re.compile(r"^\*{0,2}\s*\d+[.、]")),
    (4, re.compile(r"^\*{0,2}\s*[（(]\d+[）)]")),
    (5, re.compile(r"^\*{0,2}\s*[①②③④⑤⑥⑦⑧⑨⑩]")),
    (6, re.compile(r"^\*{0,2}\s*[a-zA-Z][.、]")),
)


META_TERMS = {
    "补充内容",
    "深大科研热点",
    "简答题考点",
    "论述题考点",
    "简答论述考点",
}


TERM_ALIASES = {
    "颜色视觉两阶段理论": "两阶段理论",
    "艾宾浩斯遗忘曲线": "遗忘曲线",
    "詹姆斯—兰格情绪理论": "詹姆斯—兰格理论",
    "坎农—巴德情绪理论": "坎农—巴德理论",
    "沙赫特—辛格情绪理论": "沙赫特—辛格理论",
    "智力二因素论": "二因素论",
    "智力群因素论": "群因素论",
    "语言发展相互作用论": "相互作用论",
}


@dataclass(frozen=True)
class SourceScope:
    start: int
    end: int
    anchor: str


@dataclass(frozen=True)
class SourceKeyword:
    term: str
    context: str


def compact(value: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9±△Δ=./—～~%-]+", value))


def canonical(value: str) -> str:
    # Function words may be present in the source run but omitted in a compact answer.
    return compact(value).replace("的", "")


def strip_source_label(value: str) -> str:
    value = re.sub(r"[*`#]", "", value).strip()
    value = re.sub(r"^(?:[一二三四五六七八九十百]+[、.]|[（(][一二三四五六七八九十百]+[）)])\s*", "", value)
    return ENUM_PREFIX.sub("", value).strip(" \t\r\n，。；：、,.!?！？（）()[]【】“”‘’—-|")


def clean_source_term(value: str) -> str | None:
    value = strip_source_label(value)
    value = re.sub(r"（(?:一级|二级|三级)考点[^）]*）", "", value)
    value = re.sub(r"【(?:简答|论述|名词解释)[^】]*】", "", value)
    value = value.strip(" \t\r\n，。；：、,.!?！？（）()[]【】“”‘’—-|")
    key = compact(value)
    if not key or len(key) > 28:
        return None
    if len(key) < 2 and not re.fullmatch(r"[A-Z]", key):
        return None
    if value in META_TERMS or value.startswith(("版权所有", "铁头班寄语")):
        return None
    return value


def line_level(line: str) -> int | None:
    stripped = line.strip()
    if stripped.startswith("## "):
        return 1
    if stripped.startswith("### "):
        return 2
    if strip_source_label(stripped) in META_TERMS:
        return 3
    for level, pattern in ITEM_PATTERNS:
        if pattern.match(stripped):
            return level
    return None


def source_sections(lines: list[str]) -> list[tuple[int, int]]:
    """Return question-sized source sections, including ## preambles and ### blocks."""
    boundaries = [
        index
        for index, line in enumerate(lines)
        if line.startswith("## ") or line.startswith("### ")
    ]
    sections: list[tuple[int, int]] = []
    for position, start in enumerate(boundaries):
        level = 1 if lines[start].startswith("## ") else 2
        end = len(lines)
        for candidate in boundaries[position + 1 :]:
            candidate_level = 1 if lines[candidate].startswith("## ") else 2
            if candidate_level <= level:
                end = candidate
                break
        # A ## block that contains ### children is represented only by its preamble.
        if level == 1:
            child = next(
                (candidate for candidate in boundaries[position + 1 :] if candidate < end),
                None,
            )
            if child is not None:
                end = child
        if end > start:
            sections.append((start, end))
    return sections


def term_in(value: str, source: str) -> bool:
    wanted = canonical(value)
    return bool(wanted) and wanted in canonical(source)


def choose_section(
    lines: list[str], sections: list[tuple[int, int]], anchor: str, anchors: tuple[str, ...]
) -> tuple[int, int] | None:
    candidates: list[tuple[int, int, int, int, int]] = []
    for start, end in sections:
        block = "\n".join(lines[start:end])
        if not term_in(anchor, block):
            continue
        coverage = sum(term_in(term, block) for term in anchors)
        heading = strip_source_label(lines[start])
        exact_heading = canonical(heading) == canonical(anchor)
        candidates.append((1 if exact_heading else 0, coverage, -(end - start), -start, end))
    if not candidates:
        return None
    exact_heading, coverage, negative_length, negative_start, end = max(candidates)
    del exact_heading, coverage, negative_length
    return -negative_start, end


def item_nodes(lines: list[str]) -> list[tuple[int, int, int]]:
    levels = [line_level(line) for line in lines]
    nodes: list[tuple[int, int, int]] = []
    for start, level in enumerate(levels):
        if level is None or level <= 2:
            continue
        end = len(lines)
        for candidate in range(start + 1, len(lines)):
            candidate_level = levels[candidate]
            if candidate_level is not None and candidate_level <= level:
                end = candidate
                break
            if lines[candidate].startswith("## ") or lines[candidate].startswith("### "):
                end = candidate
                break
        nodes.append((start, end, level))
    return nodes


def bold_exact_on_line(line: str, anchor: str) -> bool:
    wanted = canonical(anchor)
    return any(canonical(value) == wanted for value in BOLD_RE.findall(line))


def choose_hit(lines: list[str], start: int, end: int, anchor: str) -> int | None:
    hits: list[tuple[int, int, int, int]] = []
    wanted = canonical(anchor)
    for index in range(start, end):
        label = strip_source_label(lines[index])
        candidate = canonical(label)
        if not wanted or wanted not in candidate:
            continue
        exact_bold = bold_exact_on_line(lines[index], anchor)
        exact_line = candidate == wanted
        extra = max(0, len(candidate) - len(wanted))
        hits.append((0 if exact_bold else 1, 0 if exact_line else 1, extra, index))
    return min(hits)[-1] if hits else None


def question_source_scopes(local_source: str, anchors: tuple[str, ...]) -> tuple[SourceScope, ...]:
    lines = local_source.splitlines()
    sections = source_sections(lines)
    nodes = item_nodes(lines)
    scopes: list[SourceScope] = []
    for anchor in anchors:
        section = choose_section(lines, sections, anchor, anchors)
        if section is None:
            continue
        section_start, section_end = section
        hit = choose_hit(lines, section_start, section_end, anchor)
        if hit is None:
            continue
        if hit == section_start:
            start, end = section_start, section_end
        else:
            ancestors = [
                node
                for node in nodes
                if section_start <= node[0] <= hit < node[1] <= section_end
            ]
            if ancestors:
                start, end, level = max(ancestors, key=lambda node: (node[2], node[0]))
                # A category anchor such as “观察法” should not automatically pull all
                # sibling modules (scope, merits, limits) into a narrower question.
                # Keep its immediate definition child by default; more detailed source
                # points are brought in independently by their own checklist anchors.
                if hit == start and canonical(strip_source_label(lines[hit])) == canonical(anchor):
                    direct_children = [
                        node
                        for node in nodes
                        if start < node[0] < end and node[2] == level + 1
                    ]
                    if direct_children:
                        first_child = min(direct_children, key=lambda node: node[0])
                        child_label = strip_source_label(lines[first_child[0]])
                        if any(word in child_label for word in ("定义", "含义", "基本概念")):
                            end = first_child[1]
                        else:
                            end = hit + 1
            else:
                start, end = hit, hit + 1
        scope = SourceScope(start, end, anchor)
        if scope not in scopes:
            scopes.append(scope)
    return tuple(scopes)


def scoped_speed_keywords(
    local_source: str, anchors: tuple[str, ...]
) -> tuple[SourceKeyword, ...]:
    lines = local_source.splitlines()
    keywords: list[SourceKeyword] = []
    for scope in question_source_scopes(local_source, anchors):
        for line in lines[scope.start : scope.end]:
            for raw in BOLD_RE.findall(line):
                term = clean_source_term(raw)
                keyword = SourceKeyword(term, strip_source_label(line)) if term else None
                if keyword and keyword not in keywords:
                    keywords.append(keyword)
    return tuple(keywords)


def scoped_speed_terms(local_source: str, anchors: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item.term for item in scoped_speed_keywords(local_source, anchors)))


def protected_ranges(line: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in TAG_RE.finditer(line)]


def canonical_projection(value: str) -> tuple[str, list[int]]:
    projected: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(value):
        if char == "的":
            continue
        if re.match(r"[\u4e00-\u9fffA-Za-z0-9±△Δ=./—～~%-]", char):
            projected.append(char)
            positions.append(index)
    return "".join(projected), positions


def term_spans(line: str, term: str) -> list[tuple[int, int]]:
    projected, positions = canonical_projection(line)
    wanted = canonical(term)
    if not wanted:
        return []
    spans: list[tuple[int, int]] = []
    cursor = 0
    while True:
        index = projected.find(wanted, cursor)
        if index < 0:
            break
        start = positions[index]
        end = positions[index + len(wanted) - 1] + 1
        spans.append((start, end))
        cursor = index + len(wanted)
    return spans


def mark_line(line: str, terms: tuple[str, ...]) -> str:
    plain_line = line.replace("**", "")
    if not plain_line or plain_line.startswith("#") or plain_line == "---":
        return plain_line
    protected = protected_ranges(plain_line)
    spans: list[tuple[int, int]] = []
    for term in sorted(terms, key=lambda value: (-len(canonical(value)), value)):
        for start, end in term_spans(plain_line, term):
            if any(left < end and start < right for left, right in protected):
                continue
            spans.append((start, end))
            break
    if not spans:
        return plain_line
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    pieces: list[str] = []
    cursor = 0
    for start, end in merged:
        pieces.extend((plain_line[cursor:start], f"**{plain_line[start:end]}**"))
        cursor = end
    pieces.append(plain_line[cursor:])
    return "".join(pieces).replace("****", "")


def question_terms(subject: str, title: str, answer: str, local_source: str) -> tuple[str, ...]:
    points = explicit_terms(subject, title)
    terms: list[str] = list(points)
    for term in scoped_speed_terms(local_source, points):
        if term not in terms:
            terms.append(term)
    for definition in re.findall(r"【名词解释：([^】]+)】", answer):
        if definition not in terms:
            terms.append(definition)
    return tuple(terms)


def grams(value: str) -> set[str]:
    value = canonical(value)
    if len(value) < 2:
        return {value} if value else set()
    return {value[index : index + 2] for index in range(len(value) - 1)}


def context_similarity(left: str, right: str) -> float:
    left_grams = grams(left)
    right_grams = grams(right)
    if not left_grams or not right_grams:
        return 0.0
    return len(left_grams & right_grams) / len(left_grams | right_grams)


def term_line_score(
    line: str, term: str, contexts: tuple[str, ...], definition: bool
) -> float:
    score = max((context_similarity(context, line) for context in contexts), default=0.0)
    plain_line = line.replace("**", "")
    if definition and f"【名词解释：{term}】" in plain_line:
        score += 4.0
    if re.match(r"^(?:\d+\.\s*|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z]\.\s*)", plain_line):
        score += 0.25
    content = re.sub(
        r"^(?:\d+\.\s*|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z]\.\s*)",
        "",
        plain_line,
    )
    if canonical(content).startswith(canonical(term)):
        score += 1.5
    if plain_line.startswith("综上"):
        score -= 0.5
    return score


def line_term_assignment(
    subject: str, title: str, answer: str, local_source: str
) -> dict[int, tuple[str, ...]]:
    points = explicit_terms(subject, title)
    definitions = tuple(re.findall(r"【名词解释：([^】]+)】", answer))
    contexts: dict[str, list[str]] = {term: [] for term in points}
    for keyword in scoped_speed_keywords(local_source, points):
        contexts.setdefault(keyword.term, []).append(keyword.context)
    for term in definitions:
        contexts.setdefault(term, [])

    lines = answer.splitlines()
    assigned: dict[int, list[str]] = {}
    for term, source_contexts in sorted(
        contexts.items(), key=lambda item: (-len(canonical(item[0])), item[0])
    ):
        visible_term = term
        candidates = [
            index
            for index, line in enumerate(lines)
            if not line.startswith("#")
            and line != "---"
            and term_spans(line.replace("**", ""), term)
        ]
        if not candidates and term in definitions and term in TERM_ALIASES:
            visible_term = TERM_ALIASES[term]
            candidates = [
                index
                for index, line in enumerate(lines)
                if not line.startswith("#")
                and line != "---"
                and term_spans(line.replace("**", ""), visible_term)
            ]
        if not candidates:
            continue
        definition = term in definitions
        context_tuple = tuple(source_contexts)
        best = max(
            candidates,
            key=lambda index: (
                term_line_score(lines[index], visible_term, context_tuple, definition),
                -index,
            ),
        )
        assigned.setdefault(best, []).append(visible_term)
    return {index: tuple(terms) for index, terms in assigned.items()}


def align_manual_keywords(text: str, subject: str) -> str:
    speed = SUBJECT_SOURCES[subject].read_text(encoding="utf-8")
    chapters = split_chapters(speed)
    for chapter, title, answer in split_questions(text):
        local_source = source_chapter(subject, chapter, chapters)
        assignment = line_term_assignment(subject, title, answer, local_source)
        marked = "\n".join(
            mark_line(line, assignment.get(index, ()))
            for index, line in enumerate(answer.splitlines())
        )
        if answer.endswith("\n"):
            marked += "\n"
        text = text.replace(answer, marked, 1)
    text = re.sub(r"(?m)^(### .*)$", lambda match: match.group(1).replace("**", ""), text)
    return text.rstrip() + "\n"


def build_subject(subject: str) -> str:
    return align_manual_keywords(SUBJECT_BUILDERS[subject](), subject)


def build_general() -> str:
    return build_subject("普通心理学")


def build_experiment() -> str:
    return build_subject("实验心理学")


def build_measurement() -> str:
    return build_subject("心理与教育测量")


def main() -> None:
    for subject, output in SUBJECT_OUTPUTS.items():
        output.write_text(build_subject(subject), encoding="utf-8")
        print(output)


if __name__ == "__main__":
    main()
