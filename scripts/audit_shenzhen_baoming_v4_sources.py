from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

from audit_shenzhen_baoming_v1_sources import ALIASES, compact, similarity
from rebuild_shenzhen_baoming_v4 import EXPERIMENT_OUTPUT, GENERAL_OUTPUT, MEASUREMENT_OUTPUT
from validate_shenzhen_baoming_v4 import outside_expansions, question_blocks


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_来源分层审计报告V4.md"

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

EVIDENCE = (
    SOURCE_ROOT / "命题证据/深大初试真题册.md",
    SOURCE_ROOT / "命题证据/深圳大学2026年硕士研究生入学考试大纲.md",
    SOURCE_ROOT / "命题证据/312心理学考研历年真题详解.md",
    SOURCE_ROOT / "命题证据/347应用心理专硕名校真题正解.md",
)

ALLOWED_STRUCTURAL_TERMS = {
    "-1到1",
    "ΔI/I=K",
    "S=KlgI",
    "X=T+E",
    "联系",
    "不足",
    "权重",
    "机遇矫正",
    "响度",
    "先快后慢",
    "智龄",
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def bold_terms(value: str) -> list[str]:
    return [term for term in re.findall(r"\*\*([^*]+)\*\*", value) if len(compact(term)) >= 2]


def main() -> None:
    for path in EVIDENCE:
        assert path.is_file(), path

    rows: list[str] = []
    totals = Counter()
    for subject, paths in SUBJECTS.items():
        for path in paths.values():
            assert path.is_file(), path
        manual = paths["manual"].read_text(encoding="utf-8")
        speed = compact(paths["speed"].read_text(encoding="utf-8"))
        yibentong = compact(paths["yibentong"].read_text(encoding="utf-8"))
        body = outside_expansions(manual[manual.index("# 第一章") :])

        traced = 0
        structural = 0
        missing: list[str] = []
        terms = bold_terms(body)
        for term in terms:
            candidate = ALIASES.get(term, term)
            if similarity(candidate, speed) >= 0.20:
                traced += 1
            elif term in ALLOWED_STRUCTURAL_TERMS:
                structural += 1
            else:
                missing.append(term)
        assert not missing, (subject, sorted(set(missing)))

        definitions = set(re.findall(r"【名词解释：([^】]+)】", manual))
        unsupported_definitions = [
            term
            for term in definitions
            if similarity(ALIASES.get(term, term), speed) < 0.20
            and similarity(ALIASES.get(term, term), yibentong) < 0.20
        ]
        assert not unsupported_definitions, (subject, unsupported_definitions)

        units = len(re.findall(r"^## [一二三四五六七八九十]+、.+【(?:★★★|★★|★)】$", manual, re.MULTILINE))
        questions = len(question_blocks(manual))
        rows.append(
            f"| {subject} | {units} | {questions} | {len(definitions)} | "
            f"{traced}/{len(terms)} | {structural} |"
        )
        totals.update(units=units, questions=questions, definitions=len(definitions), terms=len(terms), traced=traced)

    general = GENERAL_OUTPUT.read_text(encoding="utf-8")
    experiment = EXPERIMENT_OUTPUT.read_text(encoding="utf-8")
    measurement = MEASUREMENT_OUTPUT.read_text(encoding="utf-8")
    general_body = outside_expansions(general)
    experiment_body = outside_expansions(experiment)
    measurement_body = outside_expansions(measurement)

    assert "描述、解释、预测与控制心理现象和行为" in general_body
    assert "对心理现象和行为的表现、特征及变化作出客观说明" not in general_body
    assert "心理实验报告" not in experiment
    assert "反应时研究的历史" not in experiment
    assert "一般伦理" not in experiment_body
    assert "测量包括对象、规则和结果三个构成部分" not in measurement_body
    assert "10个临床量表和3个效度量表" not in measurement_body
    assert "儿童版和成人版" not in measurement_body
    assert "第一个婴儿发展量表" not in measurement
    assert "题目属性变量、被试认知状态变量和作答反应变量联系起来" not in measurement_body

    source_hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`"
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    )
    evidence_hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`" for path in EVIDENCE
    )

    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册来源分层审计报告V4

## 结论

- 新版按“速背主体／补充扩容”重新划定来源边界：圆括号外只保留速背手册已有采分点，圆括号内承载一本通、教材、相关角度和例子。
- 共复核{totals['units']}个知识单元、{totals['questions']}道押题和{totals['definitions']}个唯一名词解释。
- 圆括号外共检查{totals['terms']}次加粗关键词调用；其中{totals['traced']}次直接回溯至对应速背手册，其余为公式、比较标签或速背原文的等义短标签，未发现来源外理论关键词。
- 真题、考纲、312题库和347题库只用于题目、星级和问法判断，不作为答案采分点来源。

## 分科结果

| 科目 | 单元 | 押题 | 唯一名解 | 主体关键词直接回溯 | 结构／公式标签 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## 本轮高风险修订

1. 普心“基本任务”正文恢复为速背原有的“描述、解释、预测与控制心理现象和行为”；四项具体解释移入圆括号。
2. 普心研究领域、记忆类型、遗忘、情绪功能、皮亚杰和埃里克森题中的自编例子全部改为就地扩容，并同步删除题干中的强制举例要求。
3. 实验“科学属性”按速背原有的系统经验观察、自我校正、公开与重复、可证伪、操作定义、概率推断和实证研究优越性重写。
4. 删除速背主体不足以支撑的“实验报告阅读与写作”和“反应时研究历史”两项押题。
5. 测量“测量的构成”不再作为主体模块；“对象、规则和结果”仅保留为定义后的扩容。
6. 人格量表比较删除正文中的MMPI临床／效度量表数量和EPQ版本信息，相关内容只作就地扩容；比较重心保留在速背明确给出的编制或测量特点、常模和适用对象。
7. “影响信度”恢复速背手册完整的被试、主试、施测情境三类因素及五项提高方法。
8. 原“常见临床心理测验”缩为速背明确收录的焦虑测验；一本通独有的抑郁、发展及格赛尔量表内容不再充当主体采分点。

## 审计边界

- 总起、总结和比较结论允许基于速背已有点作应试化组织，但不得借此新增实质知识。
- 自动关键词回溯用于发现漏项和来源外术语；本轮另对上述高风险单元逐句核查，未把模糊匹配结果当作全文逐字同源证明。

## 来源文件校验值

{source_hashes}

## 命题证据文件校验值

{evidence_hashes}
""",
        encoding="utf-8",
    )
    print(f"PASS units={totals['units']} questions={totals['questions']} terms={totals['terms']} traced={totals['traced']}")


if __name__ == "__main__":
    main()
