from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

from audit_shenzhen_baoming_v1_sources import ALIASES, compact, similarity
from audit_shenzhen_baoming_v4_sources import ALLOWED_STRUCTURAL_TERMS, bold_terms
from rebuild_shenzhen_baoming_v5 import EXPERIMENT_OUTPUT, GENERAL_OUTPUT, MEASUREMENT_OUTPUT
from validate_shenzhen_baoming_v4 import outside_expansions
from validate_shenzhen_baoming_v5 import block_with


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_来源与扩容分层审计报告V5.md"

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

HIGH_RISK_COVERAGE = {
    "普通心理学": {
        "简述心理学的主要研究领域": (
            "普通心理学", "生理心理学", "发展心理学", "教育心理学", "医学心理学",
            "健康心理学", "工业心理学", "军事心理学", "社会心理学",
        ),
        "简述深度知觉的主要线索": ("调节", "辐合", "遮挡", "运动视差", "明暗", "双眼视差"),
        "简述运动知觉的含义和主要类型": ("真动知觉", "似动知觉", "动景运动", "诱发运动", "自主运动", "运动后效"),
        "简述错觉的含义、特点及主要理论解释": ("眼动说", "移情说", "完形倾向说", "透视说", "常性误用说", "神经抑制作用说"),
        "简述记忆的主要生理机制和脑机制观点": ("突触", "长时程增强", "反响回路", "整合论", "定位说", "SPI理论"),
        "简述加德纳多元智力理论的主要内容": ("言语", "逻辑—数学", "空间", "音乐", "运动", "人际", "自知", "自然智力"),
    },
    "实验心理学": {
        "简述反应时的主要影响因素": (
            "刺激强度", "刺激复杂度", "时空特征", "通道效应", "线索提示", "相容性",
            "适应水平", "动机", "个体差异", "年龄与教育训练",
        ),
    },
    "心理与教育测量": {
        "简述结构效度的含义、用途及特点": ("心理特质理论", "理论假设不成立", "实验设计", "单一的数量指标"),
        "简述标准化样组": ("成员定义明确", "总体代表性", "取样过程", "样本规模", "时空限制", "常模类型"),
        "简述测验等值的含义及基本条件": ("同质性", "等信度", "公平性", "可递推性", "对称性", "样本不变性"),
    },
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows: list[str] = []
    totals = Counter()
    for subject, paths in SUBJECTS.items():
        for path in paths.values():
            assert path.is_file(), path
        manual = paths["manual"].read_text(encoding="utf-8")
        speed_text = paths["speed"].read_text(encoding="utf-8")
        speed = compact(speed_text)
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

        coverage_count = 0
        for heading, required_terms in HIGH_RISK_COVERAGE[subject].items():
            answer = block_with(manual, heading)
            for term in required_terms:
                assert term in answer, (subject, heading, term, "manual")
                assert similarity(ALIASES.get(term, term), speed) >= 0.20, (
                    subject, heading, term, "speed"
                )
                coverage_count += 1

        definitions = set(re.findall(r"【名词解释：([^】]+)】", manual))
        unsupported_definitions = [
            term
            for term in definitions
            if similarity(ALIASES.get(term, term), speed) < 0.20
            and similarity(ALIASES.get(term, term), yibentong) < 0.20
        ]
        assert not unsupported_definitions, (subject, unsupported_definitions)

        whole_expansions = len(re.findall(r"^（\*\*", manual, re.MULTILINE))
        rows.append(
            f"| {subject} | {len(terms)} | {traced} | {structural} | "
            f"{coverage_count} | {whole_expansions} |"
        )
        totals.update(
            terms=len(terms), traced=traced, structural=structural,
            coverage=coverage_count, whole_expansions=whole_expansions,
        )

    hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`"
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    )
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册来源与扩容分层审计报告V5

## 结论

- 新版将答案分为主体采分点和扩容项：正文能够独立支撑主要分数；圆括号既可承载新增采分点，也可承载点内解释、相关概念和例子。
- 主体内容继续以速背手册为来源边界；一本通或教材补充不得进入主体。
- 本轮对并列点较多的高风险题建立反向覆盖清单，共核对{totals['coverage']}个来源采分关键词，均在答案中保留，未因控制简答容量而删除或合并。
- 共识别{totals['whole_expansions']}处整点扩容；扩容是否设置取决于来源与提分价值，未要求每个采分点机械扩容。

## 分科结果

| 科目 | 主体加粗词调用 | 直接回溯速背 | 结构／公式标签 | 高风险来源点覆盖 | 整点扩容 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## 本轮重点修订

1. “心理学的主要研究领域”正文保留五个核心领域；医学、健康、工业和军事心理学分别作为独立采分点扩容，九个来源点实现9/9覆盖。
2. 深度知觉线索、运动知觉类型、错觉理论、记忆机制和多元智力等并列点较多的简答题，按相同规则区分主体与整点扩容。
3. 反应时影响因素、结构效度证据、标准化样组条件和测验等值条件中的补充角度改作整点扩容。
4. 原有的相关概念、解释和例子继续就地放在对应采分点之后，未改变扩容位置规则。

## 来源文件校验值

{hashes}
""",
        encoding="utf-8",
    )
    print(
        f"PASS terms={totals['terms']} traced={totals['traced']} "
        f"coverage={totals['coverage']} whole_expansions={totals['whole_expansions']}"
    )


if __name__ == "__main__":
    main()
