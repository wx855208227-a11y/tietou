from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/sjtu_baoming_20260914"
LEGACY_WORK = AGENT_DIR / "work/sjtu_baoming_20260816"

DEFAULT_ANSWERS = {
    "general": ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V1.md",
    "clinical": ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V1.md",
    "experiment": ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V1.md",
}

SOURCES = {
    "general": (
        WORK / "text/general_rapid.md",
        LEGACY_WORK / "text/上交普通心理学_第6版_彭聃龄.txt",
    ),
    "clinical": (
        WORK / "text/clinical_rapid.md",
        WORK / "text/clinical_yibentong.md",
        LEGACY_WORK / "text/上交临床心理学_第二版_姚树桥.txt",
    ),
    "experiment": (
        WORK / "text/experiment_yibentong.md",
        LEGACY_WORK / "text/上交实验心理学_第3版_郭秀艳.txt",
    ),
}

PUNCTUATION = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff]+")
EXPANSION = re.compile(r"（([^（）]{3,})）")
EXAMPLE_PREFIXES = ("例如", "如", "以", "假如", "假设", "可将", "可以把")


def normalize(text: str) -> str:
    text = re.sub(r"【名词解释：[^】]+】", "", text)
    text = text.replace("**", "")
    return PUNCTUATION.sub("", text).lower()


def grams(text: str, size: int = 3) -> set[str]:
    if len(text) < size:
        return {text} if text else set()
    return {text[index : index + size] for index in range(len(text) - size + 1)}


@dataclass(frozen=True)
class SourceChunk:
    source: str
    text: str
    normalized: str
    grams: frozenset[str]


class Matcher:
    def __init__(self, paths: tuple[Path, ...]):
        self.chunks: list[SourceChunk] = []
        self.index: dict[str, set[int]] = defaultdict(set)
        for path in paths:
            assert path.is_file(), path
            raw_lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
            paragraphs = [line for line in raw_lines if line and not line.startswith("#")]
            candidates: list[str] = []
            for index, paragraph in enumerate(paragraphs):
                candidates.append(paragraph)
                if index + 1 < len(paragraphs):
                    candidates.append(paragraph + paragraphs[index + 1])
                candidates.extend(
                    part for part in re.split(r"(?<=[。；！？])", paragraph) if len(normalize(part)) >= 4
                )
            seen: set[str] = set()
            for candidate in candidates:
                value = normalize(candidate)
                if len(value) < 4 or value in seen:
                    continue
                seen.add(value)
                chunk = SourceChunk(path.name, candidate, value, frozenset(grams(value)))
                chunk_id = len(self.chunks)
                self.chunks.append(chunk)
                for gram in chunk.grams:
                    self.index[gram].add(chunk_id)

    def best(self, query: str) -> dict[str, object]:
        value = normalize(query)
        query_grams = grams(value)
        candidate_counts: Counter[int] = Counter()
        for gram in query_grams:
            candidate_counts.update(self.index.get(gram, ()))
        top_ids = [item[0] for item in candidate_counts.most_common(80)]
        if not top_ids:
            return {"coverage": 0.0, "ratio": 0.0, "source": "", "source_text": ""}
        scored: list[tuple[float, float, SourceChunk]] = []
        for chunk_id in top_ids:
            chunk = self.chunks[chunk_id]
            coverage = len(query_grams & chunk.grams) / max(1, len(query_grams))
            ratio = SequenceMatcher(None, value, chunk.normalized, autojunk=False).ratio()
            scored.append((coverage, ratio, chunk))
        coverage, ratio, chunk = max(scored, key=lambda item: (0.72 * item[0] + 0.28 * item[1], item[0]))
        return {
            "coverage": round(coverage, 4),
            "ratio": round(ratio, 4),
            "source": chunk.source,
            "source_text": chunk.text,
        }


def extract_expansions(text: str) -> list[tuple[int, str, str]]:
    results: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for match in EXPANSION.finditer(line):
            results.append((line_number, match.group(1), line))
    return results


def audit(subject: str, answer_path: Path) -> dict[str, object]:
    matcher = Matcher(SOURCES[subject])
    answer = answer_path.read_text(encoding="utf-8")
    expansions: list[dict[str, object]] = []
    for line_number, expansion, context in extract_expansions(answer):
        match = matcher.best(expansion)
        example = normalize(expansion).startswith(EXAMPLE_PREFIXES)
        supported = example or match["coverage"] >= 0.52 or match["ratio"] >= 0.62
        expansions.append(
            {
                "line": line_number,
                "text": expansion,
                "context": context,
                "example": example,
                "supported": supported,
                **match,
            }
        )
    unsupported = [item for item in expansions if not item["supported"]]
    return {
        "subject": subject,
        "answer": str(answer_path),
        "sources": [str(path) for path in SOURCES[subject]],
        "expansion_count": len(expansions),
        "supported_or_example": len(expansions) - len(unsupported),
        "unsupported": len(unsupported),
        "unsupported_items": unsupported,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer-dir", type=Path)
    parser.add_argument("--output", type=Path, default=WORK / "expansion_audit.json")
    arguments = parser.parse_args()
    answers = dict(DEFAULT_ANSWERS)
    if arguments.answer_dir:
        answers = {
            "general": arguments.answer_dir / "上海交通大学347普通心理学保命手册_全本V3.md",
            "clinical": arguments.answer_dir / "上海交通大学347临床心理学保命手册_全本V3.md",
            "experiment": arguments.answer_dir / "上海交通大学347实验心理学保命手册_全本V3.md",
        }
    report = {subject: audit(subject, path) for subject, path in answers.items()}
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                subject: {
                    "expansion_count": values["expansion_count"],
                    "supported_or_example": values["supported_or_example"],
                    "unsupported": values["unsupported"],
                }
                for subject, values in report.items()
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
