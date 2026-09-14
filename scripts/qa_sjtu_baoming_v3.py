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
DOCX = ROOT / "deliverables/上海交通大学347心理学保命手册_普心临床实验合订重编版V3.docx"
PDF = ROOT / "deliverables/上海交通大学347心理学保命手册_普心临床实验合订重编版V3.pdf"
PAGE_MAP = ROOT / "content/sjtu_baoming_combined_v3_page_map.json"
REPORT = ROOT / "deliverables/上海交通大学347心理学保命手册_全本V3_排版与结构质检报告.md"
TITLE = "上海交通大学347心理学保命手册"

MARKDOWN = (
    ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V3.md",
    ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V3.md",
    ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V3.md",
)
PARTS = ("第一部分 普通心理学", "第二部分 临床心理学", "第三部分 实验心理学")
FORBIDDEN = (
    "答题思路", "到此停笔", "综合答案", "共用", "本题补充",
    "扩容（选用）", "扩容（选背）", "可灵活替换",
)


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def strip_list_prefix(value: str) -> str:
    return re.sub(r"^(?:\d+\.\s*|（\d+）\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*|[a-zA-Z]\.\s*)", "", value)


def paragraph_page_break_before(paragraph) -> bool:
    properties = paragraph._p.pPr
    if properties is None:
        return False
    element = properties.find(qn("w:pageBreakBefore"))
    return element is not None and element.get(qn("w:val"), "1") not in {"0", "false", "off"}


def markdown_checks() -> tuple[dict[str, int], dict[str, dict[str, float]]]:
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in MARKDOWN)
    counts = {
        "chapters": sum(
            len(re.findall(r"^# ", path.read_text(encoding="utf-8"), re.MULTILINE)) - 1
            for path in MARKDOWN
        ),
        "units": len(re.findall(r"^## [一二三四五六七八九十]+、", all_text, re.MULTILINE)),
        "questions": len(re.findall(r"^### 押题\d+【(?:简答|论述)】", all_text, re.MULTILINE)),
        "definitions": all_text.count("【名词解释："),
        "three_star": all_text.count("【★★★】"),
        "two_star": all_text.count("【★★】"),
        "one_star": all_text.count("【★】"),
    }
    assert counts == {
        "chapters": 39, "units": 156, "questions": 175, "definitions": 365,
        "three_star": 88, "two_star": 53, "one_star": 15,
    }, counts
    assert not any(item in all_text for item in FORBIDDEN)
    assert all_text.count("**") % 2 == 0

    numbered = [
        line for line in all_text.splitlines()
        if re.match(r"^(?:\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z]\.)", line)
    ]
    missing_keyword = [line for line in numbered if "**" not in line and "【名词解释：" not in line]
    assert not missing_keyword, missing_keyword[:10]

    definitions: dict[str, list[str]] = defaultdict(list)
    missing_expansion: list[str] = []
    for line in all_text.splitlines():
        for term in re.findall(r"【名词解释：([^】]+)】", line):
            core = strip_list_prefix(line)
            definitions[term].append(core)
            before_tag = line.split("【名词解释：", 1)[0]
            if "（" not in before_tag or "）" not in before_tag:
                missing_expansion.append(line)
    assert not missing_expansion, missing_expansion
    inconsistent = {
        term: values for term, values in definitions.items()
        if len(values) > 1 and len(set(values)) > 1
    }
    assert not inconsistent, inconsistent

    answer_sizes: dict[str, list[int]] = defaultdict(list)
    compare_missing: list[str] = []
    for path in MARKDOWN:
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(
            r"^### 押题\d+【(简答|论述)】([^\n]*)\n(.*?)(?=^### 押题\d+|^## |^# |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        ):
            kind, question, body = match.groups()
            assert compact(body)
            assert "综上" in body, match.group(0).splitlines()[0]
            answer_sizes[kind].append(len(re.sub(r"[#*`\s]", "", body)))
            if "比较" in question and not (
                ("共同" in body or "相同点" in body or "联系" in body)
                and ("区别" in body or "不同" in body)
            ):
                compare_missing.append(match.group(0).splitlines()[0])
    assert not compare_missing, compare_missing
    assert min(answer_sizes["简答"]) >= 280
    assert min(answer_sizes["论述"]) >= 500
    assert sum(answer_sizes["论述"]) / len(answer_sizes["论述"]) > sum(answer_sizes["简答"]) / len(answer_sizes["简答"])
    size_stats = {
        kind: {
            "count": len(values),
            "min": min(values),
            "average": round(sum(values) / len(values), 1),
            "max": max(values),
        }
        for kind, values in answer_sizes.items()
    }
    return counts, size_stats


def main() -> None:
    counts, size_stats = markdown_checks()
    assert DOCX.is_file() and PDF.is_file() and PAGE_MAP.is_file()
    with zipfile.ZipFile(DOCX) as archive:
        assert archive.testzip() is None

    document = Document(DOCX)
    assert len(document.sections) == 4
    assert not document.tables
    cover = next(
        paragraph.text.strip() for paragraph in document.paragraphs
        if paragraph.style.name == "Title" and paragraph.text.strip()
    )
    assert cover == TITLE
    h1 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 1"]
    h2 = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Heading 2"]
    questions = [paragraph for paragraph in document.paragraphs if paragraph.text.startswith("押题")]
    parts = [paragraph for paragraph in document.paragraphs if paragraph.style.name == "Part Title"]
    assert [paragraph.text for paragraph in parts] == list(PARTS)
    assert len(h1) == counts["chapters"] and len(h2) == counts["units"]
    assert len(questions) == counts["questions"]
    assert len([paragraph for paragraph in h1 if paragraph_page_break_before(paragraph)]) == counts["chapters"] - 3

    all_docx_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert all_docx_text.count("【名词解释：") == counts["definitions"]
    first_body = next(index for index, paragraph in enumerate(document.paragraphs) if paragraph.style.name == "Part Title")
    body_sizes: list[float] = []
    tag_sizes: list[float] = []
    non_black: list[str] = []
    forbidden_style: list[str] = []
    abnormal_spacing: list[str] = []
    for paragraph in document.paragraphs[first_body:]:
        for run in paragraph.runs:
            if not run.text:
                continue
            color = run.font.color.rgb
            if color is not None and str(color) != "000000":
                non_black.append(run.text)
            if run.font.italic or run.font.underline or run.font.highlight_color is not None:
                forbidden_style.append(run.text)
            size = run.font.size.pt if run.font.size else None
            if paragraph.style.name == "Normal":
                assert size is not None
                body_sizes.append(size)
            if any(tag in run.text for tag in ("【简答】", "【论述】", "【名词解释：")):
                tag_sizes.append(size)
            if "【名词解释：" in run.text:
                properties = run._r.rPr
                if properties is not None and (
                    properties.find(qn("w:spacing")) is not None or properties.find(qn("w:w")) is not None
                ):
                    abnormal_spacing.append(run.text)
    assert body_sizes and set(body_sizes) == {12.0}
    assert tag_sizes and set(tag_sizes) == {12.0}
    assert not non_black and not forbidden_style and not abnormal_spacing

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

    part_pages = [
        next(index for index, text in enumerate(page_texts) if compact(part) in compact(text) and index > 2)
        for part in PARTS
    ]
    assert part_pages == sorted(part_pages)
    sparse = [index + 1 for index, text in enumerate(page_texts[part_pages[0]:], part_pages[0]) if len(compact(text)) < 200]
    assert not sparse, sparse
    page_map = json.loads(PAGE_MAP.read_text(encoding="utf-8"))
    assert page_map and all(value > 0 for value in page_map.values())
    assert "000" not in "\n".join(page_texts[:5])

    REPORT.write_text(
        f"""# 上海交通大学347心理学保命手册全本V3排版与结构质检报告

## 结论

V3合订本通过结构、题型任务、名词解释一致性、关键词、分页、字号、字距、颜色和PDF边界检查，可用于黑白打印和直接背诵。

## 内容与结构

- 科目顺序：普通心理学 → 临床心理学 → 实验心理学
- 章节：{counts['chapters']}章；知识单元：{counts['units']}个；押题：{counts['questions']}道
- 星级：三星{counts['three_star']}个；二星{counts['two_star']}个；一星{counts['one_star']}个
- 名词解释标签：{counts['definitions']}次；重复名解逐字不一致：0项
- 所有名解均采用“完整定义＋圆括号扩容＋句末标签”结构
- 比较题均明确呈现共同点／联系与主要区别；每道答案均有总起、题干对应分块和总结
- 简答：{size_stats['简答']}；论述：{size_stats['论述']}（按去除Markdown和空白后的字符数统计）
- 未发现禁用提示语；各级采分点均有关键词加粗

## 排版

- PDF页数：{len(pdf)}页；A4；文本页{len(page_texts)}页；图片0；空白页0
- 正文、题型标记、名词解释标签：统一12磅
- 全文纯黑；无斜体、下划线或高亮
- 名词解释标签未设置异常字符间距或字符缩放
- 三科及各章另页开始；未发现正文稀疏页或文字越界
- 目录页码已回填，无“000”占位页码
""",
        encoding="utf-8",
    )
    print(f"PASS pages={len(pdf)} chapters={counts['chapters']} questions={counts['questions']}")


if __name__ == "__main__":
    main()
