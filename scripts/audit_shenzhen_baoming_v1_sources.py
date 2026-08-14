from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_来源审计报告V1.md"

SUBJECTS = {
    "普通心理学": {
        "manual": ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V2.md",
        "speed": SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "普通心理学/一本通.md",
    },
    "实验心理学": {
        "manual": ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V1.md",
        "speed": SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "实验心理学/一本通.md",
    },
    "心理与教育测量": {
        "manual": ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V1.md",
        "speed": SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": SOURCE_ROOT / "心理与教育测量/一本通.md",
    },
}

TRUE_QUESTIONS = SOURCE_ROOT / "命题证据/深大初试真题册.md"
OUTLINE = SOURCE_ROOT / "命题证据/深圳大学2026年硕士研究生入学考试大纲.md"

ALIASES = {
    "坎农—巴德情绪理论": "坎农—巴德学说",
    "大五人格模型": "人格五因素模型",
    "无条件积极关注": "无条件的积极关注",
    "自上而下加工": "自上而下的加工",
    "自下而上加工": "自下而上的加工",
    "艾宾浩斯遗忘曲线": "艾宾浩斯的记忆遗忘曲线",
    "颜色视觉两阶段理论": "两阶段理论",
    "智力二因素论": "二因素论",
    "智力群因素论": "群因素论",
    "流体智力与晶体智力理论": "流体智力与晶体智力",
    "智力的三因素理论": "三因素理论",
    "语言发展相互作用论": "相互作用论",
    "皮亚杰认知发展理论": "皮亚杰的认知发展理论",
    "埃里克森心理社会性发展理论": "埃里克森的心理社会性发展理论",
    "桑代克联结主义学习理论": "桑代克的联结主义学习理论",
    "多变量实验设计": "多变量设计",
    "内在一致性信度": "同质性信度",
    "效标效度": "效标关联效度",
    "等比量表": "比率量表",
    "等级量表": "顺序量表",
    "项目鉴别力": "区分度",
}

SYNTHESIS_TERMS = {
    "联系",
    "主要区别",
    "共同点",
    "理论关系",
    "阶段关系",
    "比较结论",
    "教育启示",
}


def compact(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text.replace("—", ""))).lower()


def grams(text: str, width: int = 2) -> set[str]:
    value = compact(text)
    return {value[index : index + width] for index in range(max(0, len(value) - width + 1))}


def similarity(term: str, source: str) -> float:
    candidate = compact(term)
    if candidate and candidate in source:
        return 1.0
    pieces = grams(candidate)
    return sum(piece in source for piece in pieces) / len(pieces) if pieces else 0.0


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def bold_terms(line: str) -> list[str]:
    return [term for term in re.findall(r"\*\*([^*]+)\*\*", line) if len(compact(term)) >= 2]


def main() -> None:
    evidence_text = compact(TRUE_QUESTIONS.read_text(encoding="utf-8"))
    outline_text = compact(OUTLINE.read_text(encoding="utf-8"))
    rows: list[str] = []
    unsupported_definitions: list[tuple[str, str]] = []
    low_points: list[tuple[str, int, str]] = []
    totals = Counter()

    for subject, paths in SUBJECTS.items():
        for path in paths.values():
            assert path.is_file(), path
        source_text = compact(
            paths["speed"].read_text(encoding="utf-8")
            + "\n"
            + paths["yibentong"].read_text(encoding="utf-8")
        )
        manual_text = paths["manual"].read_text(encoding="utf-8")

        labels = sorted(set(re.findall(r"【名词解释：([^】]+)】", manual_text)))
        for label in labels:
            candidate = ALIASES.get(label, label)
            if compact(candidate) not in source_text:
                unsupported_definitions.append((subject, label))

        points = exact_points = regrouped_points = 0
        for line_number, line in enumerate(manual_text.splitlines(), 1):
            if not re.match(r"^(?:\d+\. |（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])", line):
                continue
            terms = bold_terms(line)
            if not terms:
                continue
            points += 1
            scores = [similarity(term, source_text) for term in terms]
            if any(score == 1.0 for score in scores):
                exact_points += 1
            else:
                regrouped_points += 1
            is_synthesis = all(term in SYNTHESIS_TERMS for term in terms)
            if max(scores, default=0.0) < 0.20 and not is_synthesis:
                low_points.append((subject, line_number, line))

        units = re.findall(r"^## [一二三四五六七八九十]+、(.+?)【(★★★|★★|★)】$", manual_text, re.MULTILINE)
        stars = Counter(star for _, star in units)
        evidence_hits = Counter()
        for title, star in units:
            title_terms = [term for term in re.split(r"[、与及和的：]", title) if len(compact(term)) >= 2]
            source_score = max((similarity(term, source_text) for term in title_terms), default=0.0)
            assert source_score >= 0.20, (subject, title, source_score)
            if max((similarity(term, evidence_text) for term in title_terms), default=0.0) >= 0.55:
                evidence_hits[f"{star}真题"] += 1
            if max((similarity(term, outline_text) for term in title_terms), default=0.0) >= 0.55:
                evidence_hits[f"{star}考纲"] += 1

        rows.append(
            f"| {subject} | {len(units)} | {stars['★★★']} / {stars['★★']} / {stars['★']} | "
            f"{points} | {exact_points} | {regrouped_points} | {len(labels)} | "
            f"{evidence_hits['★★★真题']} / {evidence_hits['★★★考纲']} |"
        )
        totals.update(
            units=len(units),
            points=points,
            exact=exact_points,
            regrouped=regrouped_points,
            definitions=len(labels),
        )

    assert not unsupported_definitions, unsupported_definitions
    assert not low_points, low_points[:20]

    source_files = [
        path
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    ] + [TRUE_QUESTIONS, OUTLINE]
    hashes = "\n".join(f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`" for path in source_files)
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册来源审计报告V1

## 结论

- 三科答案均以对应**速背手册为表述主源、一本通为补充源**；深大真题和2026考纲用于范围、押题及星级判断。
- 共审计{totals['units']}个知识单元、{totals['points']}个带关键词的编号采分点和{totals['definitions']}个唯一名词解释；未发现脱离速背手册／一本通知识边界的名词解释或低来源覆盖采分点。
- {totals['exact']}个采分点含来源可直接定位词组，{totals['regrouped']}个属于在来源原意基础上完成的比较、合并或应试化重组。
- 312及其他院校真题仅辅助判断可考性，不用于向答案中新增理论模块。

## 分科审计结果

| 科目 | 单元 | 三星 / 二星 / 一星 | 编号采分点 | 可直接定位 | 应试化重组 | 唯一名解 | 三星真题 / 考纲文本命中 |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## 审计口径

1. “来源一致”不等于机械复制；定义、分类、机制和关键判断保持来源主体表述，允许为总—分—总结构和题干任务进行精简、合并与书面化组织。
2. 比较结论、联系与区别、实验任务落地和简短总结，可以依据来源已有知识作应试化归纳，但不能新增来源外理论。
3. 圆括号扩容只补充来源已有的相关概念、角度或简例，不作为新增知识单元和星级依据。
4. 文本命中是可追溯性辅助指标；星级最终综合速背原等级、深大真题、现行考纲、一本通／教材依据和主观题可考性判断。

## 来源文件校验值

{hashes}
""",
        encoding="utf-8",
    )
    print(
        "PASS "
        f"units={totals['units']} points={totals['points']} exact={totals['exact']} "
        f"regrouped={totals['regrouped']} definitions={totals['definitions']} report={REPORT}"
    )


if __name__ == "__main__":
    main()
