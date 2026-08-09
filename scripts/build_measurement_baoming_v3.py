from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_名解完整扩容版V2.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_极简直背版V3.md"
PAIR_RE = re.compile(r"【名词解释：([^】]+)】【扩容（选用）：(.*?)】")
EXPANSION_RE = re.compile(r"【扩容（选用）：(.*?)】")


GUIDE = """### 星级

- **★★★ 核心优先**：对应速背手册原一级；一本通与考纲中的核心内容，华东或相关真题信号强，主观题可考性和答案复用价值最高。优先完整背诵。
- **★★ 重点掌握**：同属速背手册原一级；一本通与考纲依据明确，具有稳定可考性，但真题信号或综合优先度略低于三星。完成三星后继续掌握。
- **★ 基础覆盖**：对应速背手册原二级；速背手册或一本通有收录且属于考纲范围，但真题信号和主观题可考性相对较弱。用于补足范围。

### 怎么用

- 方括号外是背诵主体，写全可以拿到主要分数。
- `【】`内是扩容项，选背；用于丰富答题角度、锦上添花，追求更高分数。如果其中是例子，可以根据题目灵活替换。

"""


THREE_STAR_UNITS = {
    "一、测量的含义与基本要素",
    "三、心理测验的含义与基本条件",
    "二、斯坦福—比奈智力量表",
    "二、人格自陈量表",
    "三、投射测验",
    "四、自陈量表与投射测验的比较",
    "一、信度、误差与真分数理论",
    "二、测量误差的来源",
    "三、信度的估计方法",
    "一、效度的含义、种类及其与信度的关系",
    "三、结构效度",
    "四、效标效度",
    "二、常模与标准化样组",
    "三、发展性常模与发展量表",
    "四、组内常模与标准分数",
    "一、测验编制的一般程序",
}


def transform(text: str) -> str:
    body = text[text.index("# 第一章 ") :]
    assert body.count("（例子可灵活替换）") == 4
    source_units = re.findall(r"^## (.+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(source_units) == 39
    source_first_level = {title for title, level in source_units if level == "一级"}
    assert THREE_STAR_UNITS <= source_first_level

    def replace_level(match: re.Match[str]) -> str:
        title, level = match.groups()
        star = "★" if level == "二级" else "★★★" if title in THREE_STAR_UNITS else "★★"
        return f"## {title}【{star}】"

    body = re.sub(r"^## (.+)【(一级|二级)】$", replace_level, body, flags=re.MULTILINE)

    pair_count = 0

    def replace_pair(match: re.Match[str]) -> str:
        nonlocal pair_count
        pair_count += 1
        name, expansion = match.groups()
        expansion = expansion.replace("（例子可灵活替换）", "")
        return f"【{expansion}】【名词解释：{name}】"

    body = PAIR_RE.sub(replace_pair, body)
    assert pair_count == 81
    body = EXPANSION_RE.sub(lambda match: f"【{match.group(1)}】", body)
    body = body.replace("（例子可灵活替换）", "")
    assert "扩容（选用）" not in body and "例子可灵活替换" not in body
    assert all(line.count("【名词解释：") <= 1 for line in body.splitlines())

    return (
        "# 华东师范大学347心理测量保命手册\n\n"
        "## 全本·极简直背版V3\n\n"
        + GUIDE
        + "---\n\n"
        + body
    )


def main() -> None:
    result = transform(SOURCE.read_text(encoding="utf-8"))
    OUTPUT.write_text(result, encoding="utf-8")
    print(f"已生成{OUTPUT}。")


if __name__ == "__main__":
    main()
