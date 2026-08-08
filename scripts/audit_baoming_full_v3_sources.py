from __future__ import annotations

from pathlib import Path
import re

from audit_baoming_full_v2_sources import (
    EXPECTED_HASHES,
    SOURCE_LABEL_ALIASES,
    SPEED,
    YIBENTONG,
    digest,
    docx_text,
)


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_现行范围重编版V3.md")


def main() -> None:
    for path in (SPEED, YIBENTONG):
        assert path.is_file(), path
        assert digest(path) == EXPECTED_HASHES[path], path

    speed_text = docx_text(SPEED)
    yibentong_text = docx_text(YIBENTONG)
    source_text = speed_text + yibentong_text
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 "):]

    labels = set(re.findall(r"【名词解释：([^】]+)】", body))
    missing_exact = {label for label in labels if label not in source_text}
    assert missing_exact == set(SOURCE_LABEL_ALIASES), sorted(missing_exact)
    for label, source_alias in SOURCE_LABEL_ALIASES.items():
        assert source_alias in source_text, (label, source_alias)

    removed_units = (
        "人本主义人格理论", "旁观者效应与利他行为", "偏见的形成、后果与减少",
    )
    removed_terms = (
        "耶鲁态度改变模型", "社会抑制", "旁观者效应", "利他行为", "偏见",
    )
    assert not any(unit in body for unit in removed_units)
    assert not any(term in body for term in removed_terms)

    # 社会心理只保留速背手册和一本通现有范围。
    for anchor in (
        "社会促进", "他人在场", "分心冲突", "评价恐惧",
        "态度学习论", "态度分阶段变化论", "认知失调理论", "认知平衡理论",
    ):
        assert anchor in source_text, anchor
        assert anchor in body, anchor

    # 这些内容在双源中均无正文，V3不得再用旧真题恢复。
    for absent in ("偏见", "利他行为", "旁观者效应", "社会抑制", "耶鲁态度改变"):
        assert absent not in source_text, absent

    forbidden = (
        "格雷", "强化敏感性理论", "行为趋近系统", "行为抑制系统",
        "信号检测论", "系列位置效应", "单纯接触效应", "长时增强",
    )
    assert not any(token in body for token in forbidden), {
        token for token in forbidden if token in body
    }

    print(
        "全本V3来源准入审计通过："
        f"速背手册与一本通哈希一致；正文{len(labels)}个名词概念中，"
        f"{len(labels) - len(missing_exact)}个可在双源直接检出，"
        f"{len(missing_exact)}个为规范术语别名；"
        "5类旧真题缺口内容均未越过现行范围准入门槛。"
    )


if __name__ == "__main__":
    main()
