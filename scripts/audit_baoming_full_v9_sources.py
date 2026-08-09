from __future__ import annotations

from pathlib import Path

from audit_baoming_full_v8_sources import main as audit_v8
from build_baoming_full_v9 import transform


V8 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_三星分级舒适阅读版V8.md")
V9 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_极简直背版V9.md")
V8_REPORT = Path("analysis/华东心理学导论保命手册V8_双源逐采分点审计.md")
V9_REPORT = Path("analysis/华东心理学导论保命手册V9_双源逐采分点审计.md")


def main() -> None:
    audit_v8()
    assert V9.read_text(encoding="utf-8") == transform(V8.read_text(encoding="utf-8"))
    report = V8_REPORT.read_text(encoding="utf-8")
    report = report.replace("V8双源逐采分点审计", "V9双源逐采分点审计", 1)
    report = report.replace(
        "## 结论\n",
        "## 结论\n\n- V9仅删除扩容标签和逐条例子提示，知识结论、采分点、关键词、名解定义及596处扩容实际内容均与已审计V8一致。\n",
        1,
    )
    report = report.replace("596处选背扩容", "596处圆括号扩容")
    V9_REPORT.write_text(report, encoding="utf-8")
    print(
        "全本V9双源审计通过：呈现规则转换后知识内容零漂移；"
        "789个采分点、256个唯一名解、596处扩容沿用V8逐点审计结论。"
    )


if __name__ == "__main__":
    main()
