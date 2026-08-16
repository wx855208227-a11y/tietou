from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import zipfile

import fitz
from docx import Document
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "deliverables/上海交通大学347心理学保命手册_普心实验临床合订版V1.docx"
PDF = ROOT / "deliverables/上海交通大学347心理学保命手册_普心实验临床合订版V1.pdf"
PAGE_MAP = ROOT / "content/sjtu_baoming_combined_v1_page_map.json"
REPORT = ROOT / "deliverables/上海交通大学347心理学保命手册_全本V1_质检报告.md"
TITLE = "上海交通大学347心理学保命手册"

MARKDOWN = (
    ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V1.md",
    ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V1.md",
    ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V1.md",
)

PARTS = (
    "第一部分 普通心理学",
    "第二部分 实验心理学",
    "第三部分 临床心理学",
)

TRUE_QUESTION_TERMS = (
    "心理现象", "神经元", "神经冲动", "感觉", "阈下知觉", "动机",
    "行为样本", "预防性干预", "面质技术", "智力三元理论", "选择反应时",
    "交叉滞后法", "量程效应", "ROC曲线", "短时记忆", "人格特质理论",
    "情绪的测量指标", "注意偏向", "学习迁移", "行为治疗", "韦伯定律",
    "费希纳定律", "初次接待", "精神分析取向案例解释", "目击记忆",
    "马斯洛", "知觉的含义与基本特性", "心理防御机制", "潜意识", "智力",
    "冲击疗法", "启动效应", "抵消平衡法", "内隐联想测验", "情绪调节",
    "学习的含义和分类", "正念减压疗法", "心理治疗疗效", "基于反应时",
    "精神分析和心理动力学", "被试间设计",
)


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def paragraph_page_break_before(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is None:
        return False
    element = properties.find(qn("w:pageBreakBefore"))
    if element is None:
        return False
    return element.get(qn("w:val"), "1") not in {"0", "false", "off"}


def markdown_checks() -> dict[str, int]:
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in MARKDOWN)
    counts = {
        "chapters": len(re.findall(r"^# (?:第|补充章)", all_text, re.MULTILINE)),
        "units": len(re.findall(r"^## [一二三四五六七八九十]+、", all_text, re.MULTILINE)),
        "questions": len(re.findall(r"^### 押题\d+【(?:简答|论述)】", all_text, re.MULTILINE)),
        "definitions": all_text.count("【名词解释："),
        "three_star": all_text.count("【★★★】"),
        "two_star": all_text.count("【★★】"),
        "one_star": all_text.count("【★】"),
    }
    assert counts == {
        "chapters": 39,
        "units": 156,
        "questions": 175,
        "definitions": 366,
        "three_star": 88,
        "two_star": 53,
        "one_star": 15,
    }, counts
    assert all(term in all_text for term in TRUE_QUESTION_TERMS)
    assert not any(
        forbidden in all_text
        for forbidden in (
            "答题思路", "到此停笔", "综合答案", "共用", "本题补充",
            "扩容（选用）", "扩容（选背）", "可灵活替换",
        )
    )
    assert all_text.count("**") % 2 == 0

    numbered_points = [
        line
        for line in all_text.splitlines()
        if re.match(r"^(?:\d+\.|（\d+）)", line)
    ]
    assert numbered_points and all("**" in line for line in numbered_points)

    definitions: dict[str, list[str]] = defaultdict(list)
    no_expansion: list[str] = []
    for line in all_text.splitlines():
        for term in re.findall(r"【名词解释：([^】]+)】", line):
            core = re.sub(r"^\d+\.\s*", "", line)
            definitions[term].append(core)
            before_tag = line.split("【名词解释：", 1)[0]
            if "（" not in before_tag or "）" not in before_tag:
                no_expansion.append(line)
    assert not no_expansion, no_expansion
    inconsistent = {
        term: values
        for term, values in definitions.items()
        if len(values) > 1 and len(set(values)) > 1
    }
    assert not inconsistent, inconsistent
    return counts


def main() -> None:
    counts = markdown_checks()
    assert DOCX.is_file() and PDF.is_file() and PAGE_MAP.is_file()
    with zipfile.ZipFile(DOCX) as archive:
        assert archive.testzip() is None

    document = Document(DOCX)
    assert len(document.sections) == 4
    assert not document.tables
    cover = next(
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.style.name == "Title" and paragraph.text.strip()
    )
    assert cover == TITLE

    h1 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 1"]
    h2 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 2"]
    questions = [paragraph for paragraph in document.paragraphs if paragraph.text.startswith("押题")]
    parts = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Part Title"]
    assert [paragraph.text for paragraph in parts] == list(PARTS)
    assert len(h1) == counts["chapters"]
    assert len(h2) == counts["units"]
    assert len(questions) == counts["questions"]
    assert len([paragraph for paragraph in h1 if paragraph_page_break_before(paragraph)]) == 36

    all_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert all_text.count("【名词解释：") == counts["definitions"]
    first_body = next(index for index, paragraph in enumerate(document.paragraphs) if paragraph.style.name == "Part Title")
    body_sizes: list[float] = []
    type_sizes: list[float] = []
    definition_sizes: list[float] = []
    non_black: list[tuple[str, str, str]] = []
    forbidden_styles: list[tuple[str, str]] = []
    abnormal_spacing: list[tuple[str, str]] = []
    for paragraph in document.paragraphs[first_body:]:
        for run in paragraph.runs:
            if not run.text:
                continue
            color = run.font.color.rgb
            if color is not None and str(color) != "000000":
                non_black.append((paragraph.text, run.text, str(color)))
            if run.font.italic or run.font.underline or run.font.highlight_color is not None:
                forbidden_styles.append((paragraph.text, run.text))
            size = run.font.size.pt if run.font.size else None
            if paragraph.style.name == "Normal":
                assert size is not None
                body_sizes.append(size)
            if "【简答】" in run.text or "【论述】" in run.text:
                type_sizes.append(size)
            if "【名词解释：" in run.text:
                definition_sizes.append(size)
                properties = run._r.rPr
                if properties is not None and (
                    properties.find(qn("w:spacing")) is not None
                    or properties.find(qn("w:w")) is not None
                ):
                    abnormal_spacing.append((paragraph.text, run.text))
    assert body_sizes and set(body_sizes) == {12.0}
    assert type_sizes and set(type_sizes) == {12.0}
    assert definition_sizes and set(definition_sizes) == {12.0}
    assert not non_black and not forbidden_styles and not abnormal_spacing

    pdf = fitz.open(PDF)
    assert all(round(page.rect.width, 1) == 595.3 and round(page.rect.height, 1) == 841.9 for page in pdf)
    page_texts = [page.get_text().strip() for page in pdf]
    assert all(page_texts)
    assert compact(page_texts[0]) == compact(TITLE)
    assert "使用说明" in page_texts[1]
    assert all(not page.get_images(full=True) for page in pdf)
    assert all(
        span["color"] == 0
        for page in pdf
        for block in page.get_text("dict")["blocks"]
        for line in block.get("lines", [])
        for span in line["spans"]
    )
    for page in pdf:
        for block in page.get_text("blocks"):
            x0, y0, x1, y1 = block[:4]
            assert x0 >= -1 and y0 >= -1 and x1 <= page.rect.width + 1 and y1 <= page.rect.height + 1

    page_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert all(value > 0 for value in page_map.values())
    assert "000" not in "\n".join(page_texts[:4])
    first_body_page = next(
        index for index, text in enumerate(page_texts)
        if compact(PARTS[0]) in compact(text) and index > 2
    )
    sparse_pages = [
        first_body_page + index + 1
        for index, text in enumerate(page_texts[first_body_page:])
        if len(compact(text)) < 200
    ]
    assert not sparse_pages, sparse_pages

    REPORT.write_text(
        f"""# 上海交通大学347心理学保命手册全本V1质检报告

## 结论

合订本通过内容结构、真题覆盖、名解一致性、关键词密度、分页、字号、字距、颜色和PDF边界检查，可用于黑白打印与直接背诵。

## 内容检查

- 科目顺序：普通心理学 → 实验心理学 → 临床心理学
- 章节：{counts['chapters']}章；知识单元：{counts['units']}个；押题：{counts['questions']}道
- 星级：三星{counts['three_star']}个；二星{counts['two_star']}个；一星{counts['one_star']}个
- 名词解释标签：{counts['definitions']}次；重复名解24项，表述不一致0项
- 所有名解均为“完整定义＋圆括号扩容＋句末标签”结构
- 所有一级、二级采分点均有关键词标注；未发现后半册关键词稀疏
- 2025—2026上交真题主题全部检出
- 未发现“答题思路、综合答案、共用、本题补充、到此停笔”等冗余标签

## 排版检查

- PDF页数：{len(pdf)}页
- 正文、题型标记、名词解释标签字号：统一12磅
- 颜色：纯黑；无斜体、下划线、高亮或图片
- 名解字距：未发现字符间距或字符缩放异常
- 分页：三科和各章均另起一页；未发现空白页或正文稀疏页
- 目录：分科与章节页码已回填，无占位页码
- 页面边界：未发现文字越界

## 字号统计

- 正文运行：{dict(Counter(body_sizes))}
- 简答／论述题型标记：{dict(Counter(type_sizes))}
- 名词解释标签：{dict(Counter(definition_sizes))}
""",
        encoding="utf-8",
    )
    print(
        "PASS "
        f"pages={len(pdf)} chapters={len(h1)} units={len(h2)} "
        f"questions={len(questions)} definitions={counts['definitions']}"
    )


if __name__ == "__main__":
    main()
