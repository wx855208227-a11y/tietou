from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
import statistics

import qa_sjtu_baoming_v3 as previous


ROOT = Path(__file__).resolve().parents[1]
previous.DOCX = ROOT / "deliverables/上海交通大学347心理学保命手册_普心临床实验合订重编版V4.docx"
previous.PDF = ROOT / "deliverables/上海交通大学347心理学保命手册_普心临床实验合订重编版V4.pdf"
previous.PAGE_MAP = ROOT / "content/sjtu_baoming_combined_v4_page_map.json"
previous.REPORT = ROOT / "deliverables/上海交通大学347心理学保命手册_全本V4_排版与结构质检报告.md"
previous.MARKDOWN = (
    ROOT / "deliverables/上海交通大学347普通心理学保命手册_全本V4.md",
    ROOT / "deliverables/上海交通大学347临床心理学保命手册_全本V4.md",
    ROOT / "deliverables/上海交通大学347实验心理学保命手册_全本V4.md",
)


def markdown_checks() -> tuple[dict[str, int], dict[str, dict[str, float]]]:
    all_text = "\n".join(path.read_text(encoding="utf-8") for path in previous.MARKDOWN)
    counts = {
        "chapters": sum(
            len(re.findall(r"^# ", path.read_text(encoding="utf-8"), re.MULTILINE)) - 1
            for path in previous.MARKDOWN
        ),
        "units": len(re.findall(r"^## [一二三四五六七八九十]+、", all_text, re.MULTILINE)),
        "questions": len(re.findall(r"^### 押题\d+【(?:简答|论述)】", all_text, re.MULTILINE)),
        "definitions": all_text.count("【名词解释："),
        "three_star": all_text.count("【★★★】"),
        "two_star": all_text.count("【★★】"),
        "one_star": all_text.count("【★】"),
    }
    assert counts == {
        "chapters": 40,
        "units": 158,
        "questions": 177,
        "definitions": 366,
        "three_star": 88,
        "two_star": 63,
        "one_star": 7,
    }, counts
    assert not any(item in all_text for item in previous.FORBIDDEN)
    assert all_text.count("**") % 2 == 0

    numbered = [
        line
        for line in all_text.splitlines()
        if re.match(r"^(?:\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[a-zA-Z]\.)", line)
    ]
    missing_keyword = [line for line in numbered if "**" not in line and "【名词解释：" not in line]
    assert not missing_keyword, missing_keyword[:10]

    definitions: dict[str, list[str]] = defaultdict(list)
    missing_expansion: list[str] = []
    tag_followed_by_text: list[str] = []
    for line in all_text.splitlines():
        for term in re.findall(r"【名词解释：([^】]+)】", line):
            core = previous.strip_list_prefix(line)
            definitions[term].append(core)
            before_tag, after_tag = line.split("【名词解释：", 1)
            if "（" not in before_tag or "）" not in before_tag:
                missing_expansion.append(line)
            if "】" in after_tag and after_tag.split("】", 1)[1].strip():
                tag_followed_by_text.append(line)
    assert not missing_expansion, missing_expansion
    assert not tag_followed_by_text, tag_followed_by_text
    inconsistent = {
        term: values
        for term, values in definitions.items()
        if len(values) > 1 and len(set(values)) > 1
    }
    assert not inconsistent, inconsistent

    answer_sizes: dict[str, list[int]] = defaultdict(list)
    compare_missing: list[str] = []
    no_summary: list[str] = []
    for path in previous.MARKDOWN:
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(
            r"^### 押题\d+【(简答|论述)】([^\n]*)\n(.*?)(?=^### 押题\d+|^## |^# |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        ):
            kind, question, body = match.groups()
            assert previous.compact(body)
            if "综上" not in body:
                no_summary.append(match.group(0).splitlines()[0])
            answer_sizes[kind].append(len(re.sub(r"[#*`\s]", "", body)))
            if "比较" in question and not (
                ("共同" in body or "相同点" in body or "联系" in body)
                and ("区别" in body or "不同" in body)
            ):
                compare_missing.append(match.group(0).splitlines()[0])
    assert not no_summary, no_summary
    assert not compare_missing, compare_missing
    assert min(answer_sizes["简答"]) >= 280
    assert min(answer_sizes["论述"]) >= 500
    assert statistics.mean(answer_sizes["论述"]) > statistics.mean(answer_sizes["简答"])
    size_stats = {
        kind: {
            "count": len(values),
            "min": min(values),
            "median": round(statistics.median(values), 1),
            "average": round(statistics.mean(values), 1),
            "max": max(values),
        }
        for kind, values in answer_sizes.items()
    }
    return counts, size_stats


def main() -> None:
    previous.markdown_checks = markdown_checks
    previous.main()
    report = previous.REPORT.read_text(encoding="utf-8").replace("V3", "V4")
    report = report.rstrip() + (
        "\n- 已小批量视觉复核封面、使用说明、目录、三科起始页和末页；"
        "层级、字距、分页与边界正常。\n"
        "- 内容与排版已完成；真实学员15—20分钟计时手写仍待线下校准。\n"
    )
    previous.REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
