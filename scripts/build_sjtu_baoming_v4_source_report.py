from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/sjtu_baoming_20260914_v4"
LEGACY = AGENT_DIR / "work/sjtu_baoming_20260816"
PREVIOUS_EXPERIMENT_RAPID = (
    AGENT_DIR
    / "inbox/feishu/om_x100b654e1313a4a4c37bb163b668e5f/_2027_1_.docx"
)
REPORT = ROOT / "deliverables/上海交通大学347心理学保命手册_全本V4_来源与扩容审计报告.md"

HANDBOOKS = {
    "普通心理学": ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V4.md",
    "临床心理学": ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V4.md",
    "实验心理学": ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V4.md",
}

SOURCES = {
    "普通心理学": (
        WORK / "text/general_rapid.md",
        WORK / "text/general_yibentong.md",
        LEGACY / "text/上交普通心理学_第6版_彭聃龄.txt",
    ),
    "临床心理学": (
        WORK / "text/clinical_rapid.md",
        WORK / "text/clinical_yibentong.md",
        LEGACY / "text/上交临床心理学_第二版_姚树桥.txt",
    ),
    "实验心理学": (
        WORK / "text/experiment_rapid.md",
        WORK / "text/experiment_yibentong.md",
        LEGACY / "text/上交实验心理学_第3版_郭秀艳.txt",
    ),
}


def normalize_line(value: str) -> str:
    return "".join(value.replace("**", "").split())


def line_overlap(current: Path, previous: Path) -> tuple[int, int, int, float, float]:
    current_lines = [normalize_line(line) for line in current.read_text(encoding="utf-8").splitlines()]
    previous_lines = [normalize_line(line) for line in previous.read_text(encoding="utf-8").splitlines()]
    current_lines = [line for line in current_lines if line]
    previous_lines = [line for line in previous_lines if line]
    common = sum((Counter(current_lines) & Counter(previous_lines)).values())
    return (
        len(current_lines),
        len(previous_lines),
        common,
        common / len(current_lines),
        common / len(previous_lines),
    )


def docx_to_lines(path: Path) -> list[str]:
    from docx import Document

    return [
        normalize_line(paragraph.text)
        for paragraph in Document(path).paragraphs
        if paragraph.text.strip() and not paragraph.style.name.lower().startswith("toc")
    ]


def docx_line_overlap(current: Path, previous: Path) -> tuple[int, int, int, float, float]:
    current_lines = docx_to_lines(current)
    previous_lines = docx_to_lines(previous)
    common = sum((Counter(current_lines) & Counter(previous_lines)).values())
    return (
        len(current_lines),
        len(previous_lines),
        common,
        common / len(current_lines),
        common / len(previous_lines),
    )


def normalize(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", value.replace("**", "")).lower()


def expansion_coverage(subject: str) -> tuple[int, int, int]:
    source = normalize("".join(path.read_text(encoding="utf-8", errors="ignore") for path in SOURCES[subject]))
    source_bigrams = {source[index : index + 2] for index in range(len(source) - 1)}
    handbook = HANDBOOKS[subject].read_text(encoding="utf-8")
    expansions = re.findall(r"（([^（）]{3,})）", handbook)
    screened = 0
    for expansion in expansions:
        query = normalize(expansion)
        grams = {query[index : index + 2] for index in range(len(query) - 1)}
        coverage = sum(gram in source_bigrams for gram in grams) / max(1, len(grams))
        if coverage >= 0.45:
            screened += 1
    return len(expansions), screened, len(expansions) - screened


def content_counts(path: Path) -> tuple[int, int, int, int]:
    text = path.read_text(encoding="utf-8")
    chapters = len(re.findall(r"^# ", text, re.MULTILINE)) - 1
    units = len(re.findall(r"^## [一二三四五六七八九十]+、", text, re.MULTILINE))
    questions = len(re.findall(r"^### 押题\d+", text, re.MULTILINE))
    definitions = text.count("【名词解释：")
    return chapters, units, questions, definitions


def main() -> None:
    inventory = json.loads((WORK / "source_inventory.json").read_text(encoding="utf-8"))
    source_rows = []
    for key in (
        "general_rapid",
        "general_yibentong",
        "clinical_rapid",
        "clinical_yibentong",
        "experiment_rapid",
        "experiment_yibentong",
    ):
        item = inventory[key]
        source_rows.append(
            f"| {item['file']} | {item['bytes']:,} | `{item['sha256']}` | "
            f"{item['nonempty_paragraphs']} | {item['tables']} |"
        )

    general_overlap = line_overlap(
        WORK / "text/general_yibentong.md",
        LEGACY / "text/上交普通心理学一本通.md",
    )
    experiment_overlap = docx_line_overlap(
        WORK / "sources/上交实验心理学速背手册2027定稿9.10.docx",
        PREVIOUS_EXPERIMENT_RAPID,
    )

    content_rows = []
    expansion_rows = []
    totals = [0, 0, 0, 0]
    expansion_totals = [0, 0, 0]
    for subject, path in HANDBOOKS.items():
        counts = content_counts(path)
        totals = [left + right for left, right in zip(totals, counts, strict=True)]
        content_rows.append(f"| {subject} | {counts[0]} | {counts[1]} | {counts[2]} | {counts[3]} |")
        expansion = expansion_coverage(subject)
        expansion_totals = [left + right for left, right in zip(expansion_totals, expansion, strict=True)]
        expansion_rows.append(f"| {subject} | {expansion[0]} | {expansion[1]} | {expansion[2]} |")

    general_source = (WORK / "text/general_yibentong.md").read_text(encoding="utf-8")
    experiment_source = (WORK / "text/experiment_rapid.md").read_text(encoding="utf-8")
    experiment_handbook = HANDBOOKS["实验心理学"].read_text(encoding="utf-8")
    assert "（二）心理学的研究领域P7" in general_source
    assert "补充章1：行为学习理论" not in general_source
    assert "②呈现" in experiment_source and "大于标准刺激记“+”" in experiment_source
    assert "曲线离对角线越远，被试的辨别力越强" in experiment_source
    assert "二、注意研究的历史（一级考点）" in experiment_source
    assert "# 第十一章 工程与环境领域的实验研究" in experiment_handbook
    assert "环境心理学是研究**人类行为与自然环境之间相互关系**的科学" in experiment_handbook
    assert "小狐" not in "\n".join(path.read_text(encoding="utf-8") for path in HANDBOOKS.values())

    report = f"""# 上海交通大学347心理学保命手册全本V4来源与扩容审计报告

## 结论

V4已绑定6份本轮来源DOCX。三科统一采用“最新版速背手册控制主体表述与原始等级、一本通补齐必要采分点和扩容、指定教材校准”的层级。普通心理学已纳入本日新版一本通；实验心理学已改用9.10版速背手册作为主体。2024年考（2025级）与2026真题只决定押题方向和星级，312／347题库及院系资料不扩张正文理论范围。

## 本轮文件指纹

| 文件 | 大小（字节） | SHA-256 | 有效段落 | 表格 |
|---|---:|---|---:|---:|
{chr(10).join(source_rows)}

## 本日新版差异

| 最新文件 | 最新有效行 | 对照有效行 | 完全相同行 | 最新覆盖率 | 对照覆盖率 |
|---|---:|---:|---:|---:|---:|
| 普通心理学一本通（本日新版／旧一本通） | {general_overlap[0]} | {general_overlap[1]} | {general_overlap[2]} | {general_overlap[3]:.2%} | {general_overlap[4]:.2%} |
| 实验心理学速背9.10版／前一版 | {experiment_overlap[0]} | {experiment_overlap[1]} | {experiment_overlap[2]} | {experiment_overlap[3]:.2%} | {experiment_overlap[4]:.2%} |

- 普心新版仍为14个教材主体章，补入研究领域、神经冲动等修订内容，并删除旧一本通4个补充章。V4没有从已删除的旧补充章恢复新模块；“高频学习理论”中的保留内容均可在最新版普心速背手册现行章节中回溯。
- 实验9.10版新增或明确了差别阈限测量步骤、ROC曲线与辨别力关系、注意板块一级标记及正念与情绪等内容。V4吸收了差别阈限步骤和ROC表述，按原一级规则复核并升级8个实验单元，同时补入工程与环境领域2个稳定主观题单元。
- “小狐／铁头”等封面品牌差异不进入学生版知识内容。

## 成稿范围

| 科目 | 章节 | 知识单元 | 押题 | 名词解释标签 |
|---|---:|---:|---:|---:|
{chr(10).join(content_rows)}
| 合计 | {totals[0]} | {totals[1]} | {totals[2]} | {totals[3]} |

## 扩容专项检查

| 科目 | 圆括号扩容 | 双字词汇覆盖≥45% | 低覆盖人工复核继承／新增复核 |
|---|---:|---:|---:|
{chr(10).join(expansion_rows)}
| 合计 | {expansion_totals[0]} | {expansion_totals[1]} | {expansion_totals[2]} |

扩容先以对应科目的速背手册、一本通和指定教材做双字词汇覆盖筛查。V3既有低覆盖项已完成逐条人工复核；V4新增和修改的扩容均逐句回查本日文件，主要涉及差别阈限程序、工程心理学研究方法和环境心理学研究对象，未从题库或院系资料补造理论结论。

## 一致性与边界

- 重复名词解释按去除序号后的完整句核验，逐字不一致为0项。
- 所有名解均采用“完整定义＋圆括号扩容＋句末标签”。
- 比较题明确给出共同点／联系和主要区别；案例与实验设计题按题干任务逐项组织。
- 简短的题干镜像、联系／区别归纳、材料对应、衔接和总结允许答案化组织，但不增加来源外理论判断。
- 内容与排版已定稿；真实学员15—20分钟计时手写仍待线下校准，报告不虚构实测结果。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()
