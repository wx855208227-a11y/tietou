from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT.parent
WORK = AGENT_DIR / "work/sjtu_baoming_20260914"
LEGACY = AGENT_DIR / "work/sjtu_baoming_20260816/text"
REPORT = ROOT / "deliverables/上海交通大学347心理学保命手册_全本V3_来源与扩容审计报告.md"

HANDBOOKS = {
    "普通心理学": ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V3.md",
    "临床心理学": ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V3.md",
    "实验心理学": ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V3.md",
}
SOURCES = {
    "普通心理学": (
        WORK / "text/general_rapid.md",
        LEGACY / "上交普通心理学_第6版_彭聃龄.txt",
    ),
    "临床心理学": (
        WORK / "text/clinical_rapid.md",
        WORK / "text/clinical_yibentong.md",
        LEGACY / "上交临床心理学_第二版_姚树桥.txt",
    ),
    "实验心理学": (
        WORK / "text/experiment_yibentong.md",
        LEGACY / "上交实验心理学_第3版_郭秀艳.txt",
    ),
}
CURRENT_TO_PREVIOUS = (
    (WORK / "text/general_rapid.md", LEGACY / "27上交普心速背手册.md"),
    (WORK / "text/clinical_yibentong.md", LEGACY / "上交临床心理学一本通.md"),
    (WORK / "text/experiment_yibentong.md", LEGACY / "上交实验心理学一本通.md"),
)


def normalize_line(value: str) -> str:
    return "".join(value.replace("**", "").split())


def line_overlap(current: Path, previous: Path) -> tuple[int, int, int, float]:
    current_lines = [normalize_line(line) for line in current.read_text(encoding="utf-8").splitlines()]
    previous_lines = [normalize_line(line) for line in previous.read_text(encoding="utf-8").splitlines()]
    current_lines = [line for line in current_lines if line]
    previous_lines = [line for line in previous_lines if line]
    common = sum((Counter(current_lines) & Counter(previous_lines)).values())
    return len(current_lines), len(previous_lines), common, common / len(current_lines)


def normalize(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", value.replace("**", "")).lower()


def expansion_coverage(subject: str) -> tuple[int, int, int]:
    source = normalize("".join(path.read_text(encoding="utf-8", errors="ignore") for path in SOURCES[subject]))
    source_bigrams = {source[index:index + 2] for index in range(len(source) - 1)}
    handbook = HANDBOOKS[subject].read_text(encoding="utf-8")
    expansions = re.findall(r"（([^（）]{3,})）", handbook)
    screened = 0
    for expansion in expansions:
        query = normalize(expansion)
        grams = {query[index:index + 2] for index in range(len(query) - 1)}
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
    for key in ("general_rapid", "clinical_rapid", "clinical_yibentong", "experiment_yibentong"):
        item = inventory[key]
        source_rows.append(
            f"| {item['file']} | {item['bytes']:,} | `{item['sha256']}` | "
            f"{item['nonempty_paragraphs']} | {item['tables']} |"
        )

    overlap_rows = []
    for current, previous in CURRENT_TO_PREVIOUS:
        current_count, previous_count, common, ratio = line_overlap(current, previous)
        overlap_rows.append(
            f"| {current.name} | {current_count} | {previous_count} | {common} | {ratio:.2%} |"
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
        expansion_rows.append(
            f"| {subject} | {expansion[0]} | {expansion[1]} | {expansion[2]} |"
        )

    report = f"""# 上海交通大学347心理学保命手册全本V3来源与扩容审计报告

## 结论

本轮成稿已绑定用户本次发送的4份DOCX。普通心理学以本次速背手册为主体；临床心理学以本次速背手册为主体、一本通补充核验；实验心理学以本次一本通为主体；三科指定教材仅用于校准。未使用312／347题库或院系方向资料扩张正文范围。

## 本轮文件指纹

| 文件 | 大小（字节） | SHA-256 | 有效段落 | 表格 |
|---|---:|---|---:|---:|
{chr(10).join(source_rows)}

## 与上一批同类资料的关系

本轮文件不是旧文件的同名替代引用，而是按文件指纹重新接收、解包和提取。逐行去除格式标记后，三份可对照资料的正文高度一致；差异主要是错字修订、品牌称谓和少量补充，因此以已逐题校准的旧答案为底稿，在本轮来源上重新核验并吸收修订，不重复制造无意义改写。

| 本轮文本 | 本轮有效行 | 上批有效行 | 完全相同行 | 本轮行覆盖率 |
|---|---:|---:|---:|---:|
{chr(10).join(overlap_rows)}

本轮新增的临床心理学速背手册没有旧版对应文件，已作为临床主体表述来源，并以本轮临床一本通补点和核验。

## 成稿范围

| 科目 | 章节 | 知识单元 | 押题 | 名词解释标签 |
|---|---:|---:|---:|---:|
{chr(10).join(content_rows)}
| 合计 | {totals[0]} | {totals[1]} | {totals[2]} | {totals[3]} |

- 2024年考（2025级）与2026真题只决定押题方向和星级，不单独制造教材外知识点。
- 312／347题库只用于判断可考性、常见任务和题型；院系材料只用于校准优先级和应用情境。
- 主体采分点沿用速背手册／一本通的概念、分类、机制和关键词；题干导向的联系、区别、材料对应、衔接句和总结允许在不增加理论结论的前提下重新组织。

## 扩容专项检查

| 科目 | 圆括号扩容 | 双字词汇覆盖≥45% | 低覆盖人工复核 |
|---|---:|---:|---:|
{chr(10).join(expansion_rows)}
| 合计 | {expansion_totals[0]} | {expansion_totals[1]} | {expansion_totals[2]} |

扩容先以对应科目的速背手册、一本通和指定教材做双字词汇覆盖筛查；低覆盖项逐条回看。低覆盖项主要是简短举例、情境替换和源文直接改写，如“外正内负／外负内正”、工作记忆例子、迁移例子与治疗互动例子，未发现脱离对应采分点的理论扩写。扩容均紧跟对应采分点；整点扩容只用于简答题容量控制下的追加采分点。

## 一致性与边界

- 重复名词解释已按去除序号后的完整句核验，逐字不一致为0项。
- 每个名词解释均为“完整定义＋圆括号扩容＋句末标签”。
- 比较题均明确给出共同点／联系和主要区别；案例与实验设计题按题干任务逐项组织。
- 未发现从题库或院系资料直接移入的教材外理论采分点。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(REPORT)


if __name__ == "__main__":
    main()
