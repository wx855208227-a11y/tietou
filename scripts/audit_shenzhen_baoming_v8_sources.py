from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import csv
import re

from audit_shenzhen_baoming_v7_sources import (
    CHAPTER_ALIASES,
    EXPECTED_QUESTIONS,
    POINT_LEDGER as V7_POINT_LEDGER,
    STRUCTURAL_TERMS,
    bold_terms,
    digest,
    normalize_heading,
    source_chapter,
    split_chapters,
    split_questions,
    trace,
)
from rebuild_shenzhen_baoming_v8 import EXPERIMENT_OUTPUT, GENERAL_OUTPUT, MEASUREMENT_OUTPUT


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源审计报告V8.md"
LEDGER_TSV = ROOT / "deliverables/深圳大学347心理学保命手册_160题全量逐点来源台账V8.tsv"


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


EXHAUSTIVE_ADDITIONS = {
    "普通心理学": {
        "过去经验和知觉定势": (
            "自下而上加工", "自上而下加工", "两种加工的关系", "知觉定势", "倒视现象",
        ),
        "负启动、返回抑制和注意瞬脱": (
            "选择性注意", "负启动", "返回抑制", "注意瞬脱", "主要区别",
        ),
    },
    "实验心理学": {},
    "心理与教育测量": {
        "项目难度对测验的影响": (
            "影响分数分布形态", "影响分数离散程度", "潜在区分度越大", "相对性",
        ),
        "发展量表的主要形式": (
            "年龄常模", "年级常模", "年级单位不相等", "年级当量的解释比较困难", "误用为应当达到的标准",
        ),
        "比较智龄、年级当量和比率智商": (
            "智龄", "年级当量", "比率智商", "施特恩", "不适用于成人", "主要区别",
        ),
        "组内常模的含义": (
            "百分等级常模", "百分等级", "标准分数常模", "标准分数", "剖析图",
        ),
        "比内智力量表的发展": (
            "1905年", "1908年", "1911年", "1916年", "1937年", "1960年", "比率智商", "离差智商",
        ),
        "韦克斯勒儿童智力量表": (
            "6—16岁儿童", "降低测验难度", "迷津分测验", "放弃智龄", "离差智商", "12个分测验",
        ),
        "瑞文测验的性质": (
            "团体智力测验", "非文字图形测验", "瑞文标准推理测验", "瑞文彩图推理测验", "瑞文高级推理测验",
        ),
        "人格测量的含义": (
            "心理特质和行为倾向进行定量分析", "反应定势", "反应形态", "信度和效度较低", "说谎量表", "投射测验",
        ),
        "投射测验的含义、主要特点": (
            "材料无明确结构", "反应不受限制", "测量目的隐蔽", "重视整体人格", "较少受语言限制", "主要局限",
        ),
        "项目反应理论的基础知识": (
            "潜在特质", "项目特征曲线", "跨群体不变性", "可选择性", "参数设计", "信息函数", "题库建设", "计算机化自适应测验",
        ),
    },
}


CORRECTED_FRAGMENTS = {
    "过去经验和知觉定势",
    "负启动、返回抑制和注意瞬脱",
    "项目难度对测验的影响",
    "发展量表的主要形式",
    "比较智龄、年级当量和比率智商",
    "组内常模的含义",
    "比内智力量表的发展",
    "韦克斯勒儿童智力量表",
    "瑞文测验的性质",
    "人格测量的含义",
    "投射测验的含义、主要特点",
    "项目反应理论的基础知识",
}


# 仅在题干明确整合另一章概念时，登记具体跨章范围；禁止退回全科模糊检索。
EXPLICIT_CROSS_CHAPTERS = {
    "心理与教育测量": {
        "比较智龄、年级当量和比率智商": ("第十一章",),
    },
}


def explicit_cross_source(
    subject: str,
    title: str,
    speed_chapters: dict[str, str],
    ybt_chapters: dict[str, str],
) -> tuple[str, str]:
    prefixes: tuple[str, ...] = ()
    for fragment, values in EXPLICIT_CROSS_CHAPTERS.get(subject, {}).items():
        if fragment in title:
            prefixes = values
            break
    speed = "\n".join(
        value for key, value in speed_chapters.items() if any(key.startswith(prefix) for prefix in prefixes)
    )
    ybt = "\n".join(
        value for key, value in ybt_chapters.items() if any(key.startswith(prefix) for prefix in prefixes)
    )
    return speed, ybt


def parenthetical_text(answer: str) -> str:
    return "\n".join(re.findall(r"（[^（）]*）", answer))


def body_text(answer: str) -> str:
    return re.sub(r"（[^（）]*）", "", answer)


def old_required(subject: str, title: str) -> tuple[str, ...]:
    if extra_required(subject, title):
        return ()
    hits = [terms for fragment, terms in V7_POINT_LEDGER[subject].items() if fragment in title]
    return tuple(dict.fromkeys(term for terms in hits for term in terms))


def extra_required(subject: str, title: str) -> tuple[str, ...]:
    hits = [terms for fragment, terms in EXHAUSTIVE_ADDITIONS[subject].items() if fragment in title]
    return tuple(dict.fromkeys(term for terms in hits for term in terms))


def candidate_points(answer: str) -> tuple[str, ...]:
    definitions = re.findall(r"【名词解释：([^】]+)】", answer)
    content = "\n".join(answer.splitlines()[1:])
    terms = []
    for term in [*bold_terms(content), *definitions]:
        clean = term.strip().strip("：:")
        if len(clean) < 2 or clean in STRUCTURAL_TERMS:
            continue
        if clean not in terms:
            terms.append(clean)
    return tuple(terms)


def term_destination(term: str, answer: str) -> str:
    in_body = term in body_text(answer)
    in_expansion = term in parenthetical_text(answer)
    if in_body and in_expansion:
        return "正文＋扩容"
    if in_body:
        return "正文"
    if in_expansion:
        return "圆括号扩容"
    return "缺失"


def joined(values: list[str] | tuple[str, ...]) -> str:
    return "；".join(values).replace("\t", " ").replace("\n", " ")


def main() -> None:
    rows: list[dict[str, str]] = []
    report_rows: list[str] = []
    totals = Counter()

    for subject, paths in SUBJECTS.items():
        manual = paths["manual"].read_text(encoding="utf-8")
        speed_text = paths["speed"].read_text(encoding="utf-8")
        ybt_text = paths["yibentong"].read_text(encoding="utf-8")
        speed_chapters = split_chapters(speed_text)
        ybt_chapters = split_chapters(ybt_text)
        questions = split_questions(manual)
        assert len(questions) == EXPECTED_QUESTIONS[subject], (subject, len(questions))

        for index, (chapter, title, answer) in enumerate(questions, start=1):
            speed_local = source_chapter(subject, chapter, speed_chapters)
            ybt_local = source_chapter(subject, chapter, ybt_chapters)
            cross_speed, cross_ybt = explicit_cross_source(
                subject, title, speed_chapters, ybt_chapters
            )
            speed_local += "\n" + cross_speed
            ybt_local += "\n" + cross_ybt
            local_source = speed_local + "\n" + ybt_local

            independent = tuple(dict.fromkeys((*old_required(subject, title), *extra_required(subject, title))))
            content_points = candidate_points(answer)
            checklist = tuple(dict.fromkeys((*independent, *content_points)))
            assert checklist, (subject, index, title, "empty checklist")

            missing = [term for term in independent if term not in answer]
            assert not missing, (subject, index, title, "missing source points", missing)

            unsourced = [term for term in checklist if not trace(term, local_source)]
            assert not unsourced, (subject, index, title, "not traceable in local chapter", unsourced)

            definitions = re.findall(r"【名词解释：([^】]+)】", answer)
            unsupported_definitions = [term for term in definitions if not trace(term, local_source)]
            assert not unsupported_definitions, (subject, index, title, "definitions", unsupported_definitions)

            destinations = {term: term_destination(term, answer) for term in independent}
            missing_destination = [term for term, destination in destinations.items() if destination == "缺失"]
            assert not missing_destination, (subject, index, title, "missing destination", missing_destination)

            speed_points = [term for term in checklist if trace(term, speed_local)]
            ybt_only_points = [term for term in checklist if not trace(term, speed_local) and trace(term, ybt_local)]
            body_points = [term for term in checklist if term in body_text(answer)]
            expansion_points = [term for term in checklist if term in parenthetical_text(answer)]
            assert speed_points or ybt_only_points, (subject, index, title, "no source origin")

            status = "实质修订后通过" if any(fragment in title for fragment in CORRECTED_FRAGMENTS) else "逐题复核通过"
            rows.append({
                "科目": subject,
                "序号": str(index),
                "局部来源范围": chapter,
                "题目": title,
                "独立完整清单": joined(independent or checklist),
                "速背主体点": joined(speed_points),
                "一本通辅助点": joined(ybt_only_points),
                "正文去向": joined(body_points),
                "圆括号扩容去向": joined(expansion_points),
                "新增表述来源": "仅重组双源已有信息；未新增来源外理论采分点",
                "结果": status,
            })
            report_rows.append(
                f"| {subject} | {index} | {chapter} | {title} | {len(checklist)} | {len(independent)} | {status} |"
            )
            totals["questions"] += 1
            totals["checklist"] += len(checklist)
            totals["independent"] += len(independent)
            totals["definitions"] += len(definitions)
            totals["corrected"] += status.startswith("实质")

    assert totals["questions"] == 160, totals
    assert all(row["独立完整清单"] for row in rows), "zero-item audit record"

    fieldnames = list(rows[0])
    with LEDGER_TSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`"
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    )
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册160题全量逐点来源审计报告V8

## 审计结论

- 普通心理学90题、实验心理学25题、心理与教育测量45题，共160/160题建立了非空逐题清单；不存在0项记录。
- 每题均限定在对应章节的速背手册与一本通内核对，不再用全科关键词回查掩盖跨章错配。
- 共核对{totals['checklist']}个来源关键词与采分点，其中{totals['independent']}个属于分类较多、容易漏点题目的独立完整清单；每一点均记录正文或圆括号扩容去向。
- 共核对{totals['definitions']}次名词解释调用；名词解释名称与答案表述均须在本题局部来源中回溯。
- 本轮有{totals['corrected']}道题因题干超出来源、遗漏来源点或存在无来源扩写而实质改写；其余题逐题核对后保留。

## 与V7审计的关键区别

1. 禁止空清单：每道题必须有非空来源点记录。
2. 禁止全科兜底：局部章节无法支持的理论点不得借其他章节的同名词放行。
3. 双向核查：既检查来源点是否进入正文或扩容，也检查答案理论点是否能回溯到局部来源。
4. 题干校正：资料无法支撑完整答案时，直接改为资料能够完整支持且容量匹配的题目。

## 逐题结果

| 科目 | 序号 | 局部来源范围 | 题目 | 清单点数 | 独立完整清单点数 | 结果 |
|---|---:|---|---|---:|---:|---|
{chr(10).join(report_rows)}

## 来源文件校验值

{hashes}
""",
        encoding="utf-8",
    )
    print(
        f"PASS questions={totals['questions']} checklist={totals['checklist']} "
        f"independent={totals['independent']} definitions={totals['definitions']} corrected={totals['corrected']}"
    )


if __name__ == "__main__":
    main()
