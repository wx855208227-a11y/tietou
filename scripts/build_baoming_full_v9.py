from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_三星分级舒适阅读版V8.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_极简直背版V9.md"


GUIDE = """### 星级

- **★★★ 核心优先**：对应速背手册原一级；一本通与考纲中的核心内容，华东或相关真题信号强，主观题可考性和答案复用价值最高。优先完整背诵。
- **★★ 重点掌握**：同属速背手册原一级；一本通与考纲依据明确，具有稳定可考性，但真题信号或综合优先度略低于三星。完成三星后继续掌握。
- **★ 基础覆盖**：对应速背手册原二级；速背手册或一本通有收录且属于考纲范围，但真题信号和主观题可考性相对较弱。用于补足范围。

> 星级只表示背诵顺序，不代表必考概率。

### 怎么用

- 方括号外是背诵主体，写全可以拿到主要分数。
- `【】`内是扩容项，选背；用于丰富答题角度、锦上添花，追求更高分数。如果其中是例子，可以根据题目灵活替换。
- 名词解释背`【名词解释：……】`前的定义及紧邻扩容；简答、论述按题目写相应分点。

"""


def transform(text: str) -> str:
    body_start = text.index("# 第一章 ")
    body = text[body_start:]
    assert body.count("【扩容（选背）：") == 596
    assert body.count("（例子可灵活替换）") == 114
    assert body.count("（固定例子可选用）") == 2
    body = body.replace("【扩容（选背）：", "【")
    body = body.replace("（例子可灵活替换）", "")
    body = body.replace("（固定例子可选用）", "")
    assert "扩容（选背）" not in body
    assert "扩容（选用）" not in body
    assert "例子可灵活替换" not in body
    assert "固定例子可选用" not in body
    return (
        "# 华东师范大学347心理学导论保命手册\n\n"
        "## 全本·极简直背版V9\n\n"
        + GUIDE
        + "---\n\n"
        + body
    )


def main() -> None:
    result = transform(SOURCE.read_text(encoding="utf-8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(result, encoding="utf-8")
    print(
        f"已生成 {OUTPUT}：596处扩容改为纯方括号，"
        "删除114处例子灵活替换提示和2处固定例子提示。"
    )


if __name__ == "__main__":
    main()
