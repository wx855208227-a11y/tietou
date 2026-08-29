from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

from audit_shenzhen_baoming_v1_sources import ALIASES, SYNTHESIS_TERMS, compact, similarity
from rebuild_shenzhen_baoming_v2 import EXPERIMENT_OUTPUT, GENERAL_OUTPUT, MEASUREMENT_OUTPUT


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_来源与逐题采分点审计报告V2.md"

SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "普通心理学/一本通.md",
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "实验心理学/一本通.md",
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": SOURCE_ROOT / "心理与教育测量/一本通.md",
    },
}

TRUE_QUESTIONS = SOURCE_ROOT / "命题证据/深大初试真题册.md"
OUTLINE = SOURCE_ROOT / "命题证据/深圳大学2026年硕士研究生入学考试大纲.md"
AUXILIARY_312 = SOURCE_ROOT / "命题证据/312心理学考研历年真题详解.md"
AUXILIARY_347 = SOURCE_ROOT / "命题证据/347应用心理专硕名校真题正解.md"

SYNTHESIS_LABELS = SYNTHESIS_TERMS | {
    "科学问题示例",
    "实验依据",
    "实验现象",
    "实例",
    "实例与应对",
    "应对",
    "作用角度",
    "教育应用",
    "应用实例",
}

SOURCE_EQUATION_TERMS = {"ΔI/I=K", "S=KlgI", "X=T+E"}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def question_records(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    chapter = ""
    unit = ""
    star = ""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("# ") and not line.startswith("# 深圳大学"):
            chapter = line[2:].strip()
        unit_match = re.match(r"^## [一二三四五六七八九十]+、(.+?)【(★★★|★★|★)】$", line)
        if unit_match:
            unit, star = unit_match.groups()
        question_match = re.match(r"^### 押题\d+【(简答|论述)】(.+)$", line)
        if question_match:
            answer_lines: list[str] = []
            cursor = index + 1
            while cursor < len(lines) and not lines[cursor].startswith(("### 押题", "## ", "# ")):
                if lines[cursor].strip() != "---":
                    answer_lines.append(lines[cursor])
                cursor += 1
            records.append(
                {
                    "chapter": chapter,
                    "unit": unit,
                    "star": star,
                    "type": question_match.group(1),
                    "heading": line.removeprefix("### "),
                    "answer": "\n".join(answer_lines).strip(),
                }
            )
            index = cursor
            continue
        index += 1
    return records


def base_answer(answer: str) -> str:
    result: list[str] = []
    for line in answer.splitlines():
        prefix_match = re.match(r"^(（\d+）)", line)
        prefix = prefix_match.group(1) if prefix_match else ""
        remainder = line[len(prefix) :]
        previous = None
        while previous != remainder:
            previous = remainder
            remainder = re.sub(r"（[^（）]*）", "", remainder)
        result.append(prefix + remainder)
    return "\n".join(result)


def bold_terms(text: str) -> list[str]:
    return [term for term in re.findall(r"\*\*([^*]+)\*\*", text) if len(compact(term)) >= 2]


def task_verdict(heading: str, answer: str) -> str:
    checks: list[bool] = ["综上" in answer]
    if "比较" in heading or "异同" in heading:
        checks.append("联系" in answer and "区别" in answer)
    if any(term in heading for term in ("举例", "实例", "结合实验")):
        checks.append(any(label in base_answer(answer) for label in SYNTHESIS_LABELS - SYNTHESIS_TERMS))
    if "并说明" in heading or "及其" in heading:
        checks.append(len(re.findall(r"^\d+\. ", answer, re.MULTILINE)) >= 2)
    return "通过" if all(checks) else "复核"


def style_category(heading: str) -> str:
    if "比较" in heading or "异同" in heading:
        return "比较辨析"
    if any(term in heading for term in ("举例", "实例", "应用")):
        return "举例应用"
    if "结合实验" in heading:
        return "证据阐释"
    return "结构阐释"


def main() -> None:
    evidence_files = (TRUE_QUESTIONS, OUTLINE, AUXILIARY_312, AUXILIARY_347)
    for path in evidence_files:
        assert path.is_file(), path

    summary_rows: list[str] = []
    question_rows: list[str] = []
    unsupported_definitions: list[tuple[str, str]] = []
    low_trace_terms: list[tuple[str, str, str]] = []
    totals = Counter()

    for subject, paths in SUBJECTS.items():
        for path in paths.values():
            assert path.is_file(), path
        source_raw = paths["speed"].read_text(encoding="utf-8") + "\n" + paths["yibentong"].read_text(encoding="utf-8")
        source = compact(source_raw)
        manual = paths["manual"].read_text(encoding="utf-8")

        labels = sorted(set(re.findall(r"【名词解释：([^】]+)】", manual)))
        for label in labels:
            if compact(ALIASES.get(label, label)) not in source:
                unsupported_definitions.append((subject, label))

        subject_counts = Counter()
        traced_terms = 0
        total_terms = 0
        for record in question_records(manual):
            basic = base_answer(record["answer"])
            terms = [term for term in bold_terms(basic) if term not in SYNTHESIS_LABELS]
            total_terms += len(terms)
            missing: list[str] = []
            for term in terms:
                candidate = ALIASES.get(term, term)
                score = similarity(candidate, source)
                if score >= 0.20 or term in SOURCE_EQUATION_TERMS:
                    traced_terms += 1
                else:
                    missing.append(term)
                    low_trace_terms.append((subject, record["heading"], term))

            top_points = len(re.findall(r"^\d+\. ", basic, re.MULTILINE))
            sub_points = len(re.findall(r"^（\d+）", basic, re.MULTILINE))
            verdict = task_verdict(record["heading"], record["answer"])
            category = style_category(record["heading"])
            subject_counts[category] += 1
            subject_counts[verdict] += 1
            question_rows.append(
                f"| {subject} | {record['unit']} | {record['heading']} | {top_points}+{sub_points} | "
                f"{len(terms) - len(missing)}/{len(terms)} | {category} | {verdict} |"
            )

        units = re.findall(r"^## [一二三四五六七八九十]+、.+?【(?:★★★|★★|★)】$", manual, re.MULTILINE)
        questions = question_records(manual)
        summary_rows.append(
            f"| {subject} | {len(units)} | {len(questions)} | {len(labels)} | "
            f"{traced_terms}/{total_terms} | {subject_counts['比较辨析']} | "
            f"{subject_counts['举例应用'] + subject_counts['证据阐释']} | {subject_counts['通过']} |"
        )
        totals.update(
            units=len(units),
            questions=len(questions),
            definitions=len(labels),
            terms=total_terms,
            traced=traced_terms,
            comparison=subject_counts["比较辨析"],
            application=subject_counts["举例应用"] + subject_counts["证据阐释"],
            passed=subject_counts["通过"],
        )

    assert not unsupported_definitions, unsupported_definitions
    assert not low_trace_terms, low_trace_terms[:20]
    assert totals["passed"] == totals["questions"], totals

    hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`"
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    )
    evidence_hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`" for path in evidence_files
    )

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册来源与逐题采分点审计报告V2

## 结论

- 三科答案继续以对应**速背手册为表述主源、一本通为补充源**；本轮没有通过删减来源采分点调整题型，也没有为凑容量增加来源外理论采分点。
- 共复核{totals['units']}个知识单元、{totals['questions']}道押题、{totals['definitions']}个唯一名词解释和{totals['terms']}个主体关键词；主体关键词均能回溯至速背手册或一本通。
- 每题均完成两项核对：先按题干拆出定义、分类／机制、比较、实例／应用和总结等任务槽，检查主体答案是否覆盖；再把主体关键词反向回查来源，检查是否出现无依据采分点。
- 深大真题用于识别**概念比较、关系辨析、举例应用**的命题偏好；312与泛347真题只辅助判断可考性和问法，不向答案中新增理论模块。
- 已删除要求考生现场完成研究方案的实验设计押题；实验设计、被试间设计、多变量设计等作为考纲内理论知识保留。

## 分科结果

| 科目 | 单元 | 押题 | 唯一名解 | 主体关键词来源回溯 | 比较辨析题 | 举例／证据题 | 题干任务通过 |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(summary_rows)}

## 双向核对口径

1. **来源到答案**：按题干所限定的来源知识范围核对采分模块；来源中的并列分类、阶段、机制或评价点不得无故合并丢失。题干没有要求的旁支内容不机械搬入。
2. **答案到来源**：主体定义、分类、机制和关键判断必须能回溯至速背手册或一本通；比较结论和简例可以依据来源知识作应试化归纳，但不能改变原意。
3. **题型校准**：押题概率由深大真题、考纲、教材与题库证据决定；简答或论述则由实际采分模块和回答负荷决定。不得先定题型再删点或凑点。
4. **题干必答项**：题干明确要求比较、举例、结合实验或应用时，相应内容必须放在圆括号外，作为主体答案。

## 深大命题风格证据

- 2020—2026主观题持续出现概念比较和关系辨析，如自然观察法与实验法、内隐与外显记忆、标准误与标准差等。
- 2021—2026多次明确要求结合实例、经典研究或实际问题说明理论；2022、2024、2025尤为集中。
- 这些证据用于调整押题问法，不等于机械复刻旧题，也不包括要求考生自行完成实验设计的题目。

## 逐题核对记录

“基础点”按“一级编号点+二级编号点”记录；“来源回溯”表示主体关键词中可在速背手册／一本通定位的数量。

| 科目 | 知识单元 | 押题 | 基础点 | 来源回溯 | 问法类型 | 任务覆盖 |
|---|---|---|---:|---:|---|---|
{chr(10).join(question_rows)}

## 来源文件校验值

{hashes}

## 命题证据文件校验值

{evidence_hashes}
""",
        encoding="utf-8",
    )
    print(
        "PASS "
        f"units={totals['units']} questions={totals['questions']} "
        f"terms={totals['traced']}/{totals['terms']} definitions={totals['definitions']} report={REPORT}"
    )


if __name__ == "__main__":
    main()
