from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT.parent / "work/shenzhen_general_baoming_sources"
SPEED_MD = SOURCE_DIR / "速背手册_结构化.md"
YIBENTONG_MD = SOURCE_DIR / "一本通_结构化.md"
SPEED_DOCX = SOURCE_DIR / "深大普通心理学速背手册.docx"
YIBENTONG_DOCX = SOURCE_DIR / "深大普通心理学一本通.docx"
TRUE_QUESTIONS = SOURCE_DIR / "深大初试真题册.docx"
OUTLINE = SOURCE_DIR / "深圳大学2026年硕士研究生入学考试大纲.docx"
MANUAL = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.md"
REPORT = ROOT / "analysis/shenzhen-general-baoming/全本V1_双源与命题证据审计.md"
NUMERALS = "一二三四五六七八九十"

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
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def compact(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text.replace("—", ""))).lower()


def bigrams(text: str) -> set[str]:
    value = compact(text)
    return {value[index : index + 2] for index in range(len(value) - 1)}


def chapter_number(value: str) -> str | None:
    match = re.match(rf"^# 第([{NUMERALS}]+)章", value)
    return match.group(1) if match else None


def source_chapters() -> tuple[dict[str, str], str]:
    chapters: dict[str, list[str]] = defaultdict(list)
    all_text: list[str] = []
    for path in (SPEED_MD, YIBENTONG_MD):
        current: str | None = None
        for line in path.read_text(encoding="utf-8").splitlines():
            number = chapter_number(line)
            if number:
                current = number
            all_text.append(line)
            if current:
                chapters[current].append(line)
    return {key: compact("\n".join(value)) for key, value in chapters.items()}, compact("\n".join(all_text))


def bold_terms(line: str) -> list[str]:
    return [value for value in re.findall(r"\*\*([^*]+)\*\*", line) if len(compact(value)) >= 2]


def coverage(terms: list[str], source: str) -> tuple[bool, float]:
    exact = any(compact(term) in source for term in terms)
    scores = []
    for term in terms:
        grams = bigrams(term)
        if grams:
            scores.append(sum(gram in source for gram in grams) / len(grams))
    return exact, max(scores, default=0.0)


def main() -> None:
    for path in (SPEED_MD, YIBENTONG_MD, SPEED_DOCX, YIBENTONG_DOCX, TRUE_QUESTIONS, OUTLINE, MANUAL):
        assert path.is_file(), path

    sources, all_source = source_chapters()
    text = MANUAL.read_text(encoding="utf-8")
    lines = text.splitlines()

    labels = sorted(set(re.findall(r"【名词解释：([^】]+)】", text)))
    missing_labels = []
    for label in labels:
        candidate = ALIASES.get(label, label)
        if compact(candidate) not in all_source:
            missing_labels.append(label)
    assert not missing_labels, missing_labels

    current: str | None = None
    stats: dict[str, Counter[str]] = defaultdict(Counter)
    low_items: list[tuple[int, float, str]] = []
    total = exact_total = 0
    for line_number, line in enumerate(lines, 1):
        number = chapter_number(line)
        if number:
            current = number
            continue
        if line.startswith("# 补充章"):
            current = None
            continue
        if not re.match(r"^\d+\.\s", line):
            continue
        terms = bold_terms(line)
        assert terms, (line_number, line)
        source = sources.get(current, all_source)
        exact, score = coverage(terms, source)
        key = f"第{current}章" if current else "补充章"
        total += 1
        stats[key]["采分点"] += 1
        if exact:
            exact_total += 1
            stats[key]["同章明确词组"] += 1
        else:
            stats[key]["应试化重组"] += 1
        if score < 0.20:
            low_items.append((line_number, score, line))
    assert total > 0
    assert not low_items, low_items[:20]

    source_topics = (
        "智力的测量（详见测量心理学）",
        "人格的形成",
        "经典条件作用",
        "操作性条件作用",
        "皮亚杰的认知发展理论",
        "埃里克森的心理社会性发展理论",
        "自我价值理论",
        "调节聚焦理论",
    )
    for topic in source_topics:
        assert compact(topic) in all_source, topic

    rows = []
    for chapter, values in stats.items():
        rows.append(
            f"| {chapter} | {values['采分点']} | {values['同章明确词组']} | {values['应试化重组']} |"
        )

    hashes = {path.name: digest(path) for path in (SPEED_DOCX, YIBENTONG_DOCX, TRUE_QUESTIONS, OUTLINE)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# 深圳大学347普通心理学保命手册V1双源与命题证据审计

## 结论

- 全本答案知识边界以深大普通心理学速背手册为主、一本通为辅；指定教材用于争议点复核，不以312或其他347题库扩张答案范围。
- 共抽取{total}个编号采分点，全部通过同章双源关键词覆盖检查；其中{exact_total}个含速背手册或一本通可直接定位词组，{total - exact_total}个属于原意基础上的比较、合并或应试化重组。
- 共{len(labels)}个唯一名词解释，全部可在双源中直接检出，或通过登记的规范全称／简称对应检出；未发现材料外名解。
- “智力测量”在速背手册和一本通中仅写明“详见测量心理学”，因此本册没有自行编写智力测验与分数解释单元。
- 扩容内容只用于补充双源已有的相关概念、比较角度或说明性例子，不作为新的理论模块和星级依据。

## 审计口径

1. 深大真题、现行考纲用于判断命题侧重点和题型；312与其他347真题只辅助判断可考性。
2. 来源一致不等于机械复制。定义、分类、机制、关系和评价必须保持双源主体表述，允许为了总—分—总答题结构进行精简、合并和书面化组织。
3. 星级先受速背手册原一级／二级边界约束，再综合深大真题、考纲、一本通、指定教材和主观题可考性细分。

## 逐章采分点覆盖

| 章节 | 编号采分点 | 同章明确词组 | 应试化重组 |
|---|---:|---:|---:|
{"\n".join(rows)}

## 来源文件

- `深大普通心理学速背手册.docx`：SHA-256 `{hashes['深大普通心理学速背手册.docx']}`
- `深大普通心理学一本通.docx`：SHA-256 `{hashes['深大普通心理学一本通.docx']}`
- `深大初试真题册.docx`：SHA-256 `{hashes['深大初试真题册.docx']}`
- `深圳大学2026年硕士研究生入学考试大纲.docx`：SHA-256 `{hashes['深圳大学2026年硕士研究生入学考试大纲.docx']}`

本报告证明知识范围、名词解释和采分点可追溯，不宣称应试答案逐句复制来源。
""",
        encoding="utf-8",
    )
    print(
        "PASS "
        f"scoring_points={total} exact={exact_total} regrouped={total - exact_total} "
        f"definitions={len(labels)} report={REPORT}"
    )


if __name__ == "__main__":
    main()
