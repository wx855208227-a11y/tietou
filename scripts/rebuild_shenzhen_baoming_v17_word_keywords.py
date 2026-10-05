from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from pathlib import Path
import re

from docx import Document

from audit_shenzhen_baoming_v7_sources import source_chapter, split_chapters, split_questions
from rebuild_shenzhen_baoming_v15_source_keywords import (
    build_experiment as build_experiment_v15,
    build_general as build_general_v15,
    build_measurement as build_measurement_v15,
)
from rebuild_shenzhen_baoming_v16_reverse_keywords import (
    BOLD_RE,
    ITEM_PATTERNS,
    META_TERMS,
    SourceScope,
    canonical,
    compact,
    context_similarity,
    item_nodes,
    line_level,
    protected_ranges,
    source_sections,
    strip_source_label,
)
from validate_shenzhen_baoming_v15_source_keywords import explicit_terms


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V17.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V17.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V17.md"

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

SUBJECT_DOCX = {
    subject: SOURCE_ROOT / subject / "速背手册.docx"
    for subject in SUBJECT_OUTPUTS
}

TAG_RE = re.compile(r"【[^】]+】")
ENUM_PREFIX = re.compile(
    r"^(?:\s*(?:\d+[.、]|[（(]\d+[）)]|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z][.、])\s*)+"
)
IMPORTANCE_RE = re.compile(r"[（(](?:一级|二级|三级)考点[^）)]*[）)]")

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
class WordKeyword:
    term: str
    context: str
    anchor: str
    source_line: int
    source_start: int


def run_emphasized(run) -> bool:
    if run.bold is True or bool(run.underline):
        return True
    style = getattr(run, "style", None)
    font = getattr(style, "font", None)
    return bool(font and (font.bold is True or bool(font.underline)))


def formatted_paragraph(paragraph) -> str:
    pieces: list[str] = []
    for run in paragraph.runs:
        if not run.text:
            continue
        pieces.append(f"**{run.text}**" if run_emphasized(run) else run.text)
    value = "".join(pieces).strip()
    value = re.sub(r"\*\*\s*\*\*", "", value)
    while re.search(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", value):
        value = re.sub(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", r"**\1\2**", value)
    return value


def word_source_markdown(path: Path) -> str:
    document = Document(path)
    lines: list[str] = []
    for paragraph in document.paragraphs:
        value = formatted_paragraph(paragraph)
        if not value:
            continue
        style = paragraph.style.name
        if style == "Heading 1":
            lines.extend((f"# {value}", ""))
        elif style == "Heading 2":
            lines.extend((f"## {value}", ""))
        elif style == "Heading 3":
            lines.extend((f"### {value}", ""))
        elif not style.startswith("toc "):
            lines.extend((value, ""))
    return "\n".join(lines).strip() + "\n"


def source_label(value: str) -> str:
    value = strip_source_label(value)
    value = IMPORTANCE_RE.sub("", value)
    return value.strip(" \t\r\n，。；：、,.!?！？（）()[]【】“”‘’—-|")


def clean_word_term(raw: str) -> str | None:
    value = source_label(raw)
    value = re.sub(r"【(?:简答|论述|名词解释)[^】]*】", "", value)
    value = value.strip(" \t\r\n，。；：、,.!?！？（）()[]【】“”‘’—-|")
    key = compact(value)
    if not key or len(key) > 80:
        return None
    if len(key) < 2 and not re.fullmatch(r"[A-Z]", key):
        return None
    if value in META_TERMS or value.startswith(("版权所有", "铁头班寄语")):
        return None
    return value


def label_match(line: str, anchor: str) -> tuple[int, int, int]:
    level = line_level(line)
    if level is None:
        return 0, 0, 0
    candidate = canonical(source_label(line))
    wanted = canonical(anchor)
    if not candidate or not wanted:
        return 0, 0, 0
    exact = candidate == wanted
    prefix = candidate.startswith(wanted) or wanted.startswith(candidate)
    bold_exact = exact and any(
        canonical(source_label(raw)) == wanted for raw in BOLD_RE.findall(line)
    )
    return int(bold_exact), int(exact), int(prefix)


def term_in(value: str, source: str) -> bool:
    wanted = canonical(value)
    return bool(wanted) and wanted in canonical(source)


def choose_section(
    lines: list[str], sections: list[tuple[int, int]], anchor: str, anchors: tuple[str, ...]
) -> tuple[int, int] | None:
    candidates: list[tuple[int, int, int, int, int, int, int]] = []
    for start, end in sections:
        block = "\n".join(lines[start:end])
        if not term_in(anchor, block):
            continue
        qualities = [label_match(lines[index], anchor) for index in range(start, end)]
        bold_label, exact_label, prefix_label = max(qualities, default=(0, 0, 0))
        exact_heading = canonical(source_label(lines[start])) == canonical(anchor)
        coverage = sum(term_in(term, block) for term in anchors)
        candidates.append(
            (
                bold_label,
                exact_label,
                prefix_label,
                int(exact_heading),
                -(end - start),
                coverage,
                -start,
            )
        )
    if not candidates:
        return None
    *_, negative_start = max(candidates)
    start = -negative_start
    end = next(end for candidate_start, end in sections if candidate_start == start)
    return start, end


def choose_hit(lines: list[str], start: int, end: int, anchor: str) -> int | None:
    hits: list[tuple[int, int, int, int, int]] = []
    wanted = canonical(anchor)
    for index in range(start, end):
        candidate = canonical(source_label(lines[index]))
        if not wanted or wanted not in candidate:
            continue
        bold_label, exact_label, prefix_label = label_match(lines[index], anchor)
        extra = max(0, len(candidate) - len(wanted))
        hits.append((-exact_label, -bold_label, -prefix_label, extra, index))
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
            if not ancestors:
                start, end = hit, hit + 1
            else:
                start, end, level = max(ancestors, key=lambda node: (node[2], node[0]))
                direct_children = [
                    node for node in nodes if start < node[0] < end and node[2] == level + 1
                ]
                if direct_children:
                    first_child = min(direct_children, key=lambda node: node[0])
                    child_label = source_label(lines[first_child[0]])
                    if any(word in child_label for word in ("定义", "含义", "基本概念")):
                        end = first_child[1]
                    elif canonical(source_label(lines[hit])) == canonical(anchor):
                        end = hit + 1
                # A leaf item keeps its following definition/explanation until the
                # next sibling. V16 incorrectly truncated every leaf to its label.
        scope = SourceScope(start, end, anchor)
        if scope not in scopes:
            scopes.append(scope)
    return tuple(scopes)


def scoped_word_keywords(local_source: str, anchors: tuple[str, ...]) -> tuple[WordKeyword, ...]:
    lines = local_source.splitlines()
    keywords: list[WordKeyword] = []
    for scope in question_source_scopes(local_source, anchors):
        for line_index in range(scope.start, scope.end):
            line = lines[line_index]
            context = strip_source_label(line)
            for match in BOLD_RE.finditer(line):
                raw = match.group(1)
                term = clean_word_term(raw)
                keyword = (
                    WordKeyword(term, context, scope.anchor, line_index, match.start())
                    if term
                    else None
                )
                if keyword and keyword not in keywords:
                    keywords.append(keyword)
    return tuple(keywords)


def strict_projection(value: str) -> tuple[str, list[int]]:
    projected: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(value):
        if re.match(r"[\u4e00-\u9fffA-Za-z0-9±△Δ=./—～~%-]", char):
            projected.append(char)
            positions.append(index)
    return "".join(projected), positions


def fuzzy_projection(value: str) -> tuple[str, list[int]]:
    projected: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(value):
        if char == "的":
            continue
        if re.match(r"[\u4e00-\u9fffA-Za-z0-9±△Δ=./—～~%-]", char):
            projected.append(char)
            positions.append(index)
    return "".join(projected), positions


def projected_spans(line: str, term: str, *, fuzzy: bool = False) -> list[tuple[int, int]]:
    projection = fuzzy_projection if fuzzy else strict_projection
    projected, positions = projection(line)
    wanted, _ = projection(term)
    if not wanted:
        return []
    spans: list[tuple[int, int]] = []
    cursor = 0
    while True:
        index = projected.find(wanted, cursor)
        if index < 0:
            break
        spans.append((positions[index], positions[index + len(wanted) - 1] + 1))
        cursor = index + len(wanted)
    return spans


def usable_spans(line: str, term: str, *, fuzzy: bool = False) -> list[tuple[int, int]]:
    protected = protected_ranges(line)
    return [
        (start, end)
        for start, end in projected_spans(line, term, fuzzy=fuzzy)
        if not any(left < end and start < right for left, right in protected)
    ]


def chinese_neighbor(value: str, index: int) -> str:
    if 0 <= index < len(value) and re.match(r"[\u4e00-\u9fff]", value[index]):
        return value[index]
    return ""


def keyword_spans(line: str, keyword: WordKeyword, *, fuzzy: bool = False) -> list[tuple[int, int]]:
    spans = usable_spans(line, keyword.term, fuzzy=fuzzy)
    if len(compact(keyword.term)) > 3:
        return spans
    source = keyword.context.replace("**", "")
    # The source itself contains the authoritative spelling. Even during a
    # fuzzy answer match, use the source's exact span so a skipped “的” is
    # included before comparing neighboring Chinese characters.
    source_spans = usable_spans(source, keyword.term)
    if not source_spans:
        source_spans = usable_spans(source, keyword.term, fuzzy=fuzzy)
    if not source_spans:
        return []
    accepted: list[tuple[int, int]] = []
    for start, end in spans:
        left = chinese_neighbor(line, start - 1)
        right = chinese_neighbor(line, end)
        if any(
            (
                not left
                or chinese_neighbor(source, source_start - 1) in (left, "的")
            )
            and (
                not right
                or chinese_neighbor(source, source_end) in (right, "的")
            )
            for source_start, source_end in source_spans
        ):
            accepted.append((start, end))
    return accepted


def line_score(line: str, keyword: WordKeyword, definition_terms: tuple[str, ...]) -> float:
    score = context_similarity(keyword.context, line)
    plain_line = line.replace("**", "")
    if keyword.anchor in definition_terms and f"【名词解释：{keyword.anchor}】" in plain_line:
        score += 3.0
    content = re.sub(
        r"^(?:\d+\.\s*|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z]\.\s*)",
        "",
        plain_line,
    )
    if canonical(content).startswith(canonical(keyword.anchor)):
        score += 1.25
    if plain_line.startswith("综上"):
        score -= 0.5
    return score


def restore_source_wording(
    lines: list[str], keywords: tuple[WordKeyword, ...], definition_terms: tuple[str, ...]
) -> tuple[list[str], list[tuple[str, str, str]]]:
    restored: list[tuple[str, str, str]] = []
    for keyword in keywords:
        candidates: list[tuple[float, int, tuple[int, int], bool]] = []
        for index, line in enumerate(lines):
            if line.startswith("#") or line == "---":
                continue
            for span in keyword_spans(line, keyword):
                candidates.append((line_score(line, keyword, definition_terms) + 0.05, index, span, False))
            if not keyword_spans(line, keyword):
                for span in keyword_spans(line, keyword, fuzzy=True):
                    actual = line[span[0] : span[1]]
                    if actual.replace("的", "") == keyword.term.replace("的", ""):
                        candidates.append((line_score(line, keyword, definition_terms), index, span, True))
        if not candidates:
            continue
        _, index, (start, end), fuzzy = max(candidates, key=lambda item: (item[0], -item[1]))
        if fuzzy:
            before = lines[index]
            lines[index] = before[:start] + keyword.term + before[end:]
            restored.append((before[start:end], keyword.term, keyword.context))
    return lines, restored


def structural_assignment(
    subject: str, title: str, lines: list[str], definition_terms: tuple[str, ...]
) -> dict[int, list[str]]:
    assigned: dict[int, list[str]] = {}
    terms = list(explicit_terms(subject, title)) + list(definition_terms)
    for term in dict.fromkeys(terms):
        visible = term
        candidates = [
            index for index, line in enumerate(lines)
            if not line.startswith("#") and line != "---" and usable_spans(line, visible)
        ]
        if not candidates and term in TERM_ALIASES:
            visible = TERM_ALIASES[term]
            candidates = [
                index for index, line in enumerate(lines)
                if not line.startswith("#") and line != "---" and usable_spans(line, visible)
            ]
        if not candidates:
            continue
        best = max(
            candidates,
            key=lambda index: (
                3 if f"【名词解释：{term}】" in lines[index] else 0,
                1 if canonical(strip_source_label(lines[index])).startswith(canonical(visible)) else 0,
                0 if lines[index].startswith("综上") else 1,
                -index,
            ),
        )
        assigned.setdefault(best, []).append(visible)
    return assigned


def source_assignment(
    lines: list[str], keywords: tuple[WordKeyword, ...], definition_terms: tuple[str, ...]
) -> dict[int, list[str]]:
    assigned: dict[int, list[str]] = {}
    for keyword in keywords:
        candidates = [
            index for index, line in enumerate(lines)
            if not line.startswith("#") and line != "---" and keyword_spans(line, keyword)
        ]
        if not candidates:
            continue
        best = max(
            candidates,
            key=lambda index: (line_score(lines[index], keyword, definition_terms), -index),
        )
        assigned.setdefault(best, []).append(keyword.term)
    return assigned


def merged_terms(structural: list[str], sourced: list[str]) -> tuple[str, ...]:
    counts = Counter(sourced)
    for term in structural:
        counts[term] = max(1, counts[term])
    return tuple(term for term, count in counts.items() for _ in range(count))


def mark_line(line: str, terms: tuple[str, ...]) -> str:
    plain_line = line.replace("**", "")
    if not plain_line or plain_line.startswith("#") or plain_line == "---":
        return plain_line
    protected = protected_ranges(plain_line)
    spans: list[tuple[int, int]] = []
    term_counts = Counter(terms)
    for term in sorted(term_counts, key=lambda value: (-len(value), value)):
        accepted = 0
        for start, end in usable_spans(plain_line, term):
            if any(left < end and start < right for left, right in protected):
                continue
            spans.append((start, end))
            accepted += 1
            if accepted >= term_counts[term]:
                break
    if not spans:
        return plain_line
    # Keep distinct source keyword boundaries distinct when ordinary text lies
    # between them. Adjacent spans must be merged because Markdown cannot
    # represent `**A****B**` safely and the Word display is identical.
    selected: list[tuple[int, int]] = []
    for start, end in sorted(spans, key=lambda item: (item[0], -(item[1] - item[0]))):
        if any(left <= start and end <= right for left, right in selected):
            continue
        selected = [
            (left, right) for left, right in selected
            if not (start <= left and right <= end)
        ]
        if any(left < end and start < right for left, right in selected):
            continue
        selected.append((start, end))
    merged: list[tuple[int, int]] = []
    for start, end in sorted(selected):
        if merged and start == merged[-1][1]:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    pieces: list[str] = []
    cursor = 0
    for start, end in merged:
        pieces.extend((plain_line[cursor:start], f"**{plain_line[start:end]}**"))
        cursor = end
    pieces.append(plain_line[cursor:])
    return "".join(pieces)


def align_question(
    subject: str, title: str, answer: str, local_source: str
) -> tuple[str, tuple[WordKeyword, ...], tuple[tuple[str, str, str], ...]]:
    anchors = explicit_terms(subject, title)
    keywords = scoped_word_keywords(local_source, anchors)
    definition_terms = tuple(re.findall(r"【名词解释：([^】]+)】", answer))
    lines = [line.replace("**", "") for line in answer.splitlines()]
    lines, restored = restore_source_wording(lines, keywords, definition_terms)
    structural = structural_assignment(subject, title, lines, definition_terms)
    sourced = source_assignment(lines, keywords, definition_terms)
    marked: list[str] = []
    for index, line in enumerate(lines):
        terms = merged_terms(structural.get(index, []), sourced.get(index, []))
        marked.append(mark_line(line, terms))
    result = "\n".join(marked)
    if answer.endswith("\n"):
        result += "\n"
    return result, keywords, tuple(restored)


def build_subject(subject: str) -> str:
    text = SUBJECT_BUILDERS[subject]().rstrip() + "\n"
    word_source = word_source_markdown(SUBJECT_DOCX[subject])
    chapters = split_chapters(word_source)
    for chapter, title, answer in split_questions(text):
        local_source = source_chapter(subject, chapter, chapters)
        marked, _, _ = align_question(subject, title, answer, local_source)
        text = text.replace(answer, marked, 1)
    text = re.sub(r"(?m)^(### .*)$", lambda match: match.group(1).replace("**", ""), text)
    return text.rstrip() + "\n"


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
