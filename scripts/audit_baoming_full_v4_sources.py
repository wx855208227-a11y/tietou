from __future__ import annotations

from pathlib import Path
import re

from audit_baoming_full_v2_sources import (
    EXPECTED_HASHES,
    SOURCE_LABEL_ALIASES,
    SPEED,
    YIBENTONG,
    PUBLIC_347,
    PUBLIC_312,
    digest,
    docx_text,
)
from validate_baoming_full_v1 import plain, question_blocks


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_综合证据重编版V4.md")
V3 = Path("deliverables/华东师范大学347心理学导论保命手册_全本_现行范围重编版V3.md")


def semantic_answer(block: str) -> str:
    return "\n".join(plain(line) for line in block.splitlines()).strip()


def main() -> None:
    for path in (SPEED, YIBENTONG, PUBLIC_347, PUBLIC_312):
        assert path.is_file(), path
        assert digest(path) == EXPECTED_HASHES[path], path

    speed_text = docx_text(SPEED)
    yibentong_text = docx_text(YIBENTONG)
    source_text = speed_text + yibentong_text
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 "):]
    old_body = V3.read_text(encoding="utf-8")
    old_body = old_body[old_body.index("# 第一章 "):]

    # V4只重审层级、命题证据和关键词标记，不借本轮改版暗改已经完成
    # 现行范围／双源审校的答案正文。
    current_blocks = question_blocks(body)
    old_blocks = question_blocks(old_body)
    assert len(current_blocks) == len(old_blocks) == 145
    for (heading, block), (old_heading, old_block) in zip(current_blocks, old_blocks):
        assert plain(heading) == plain(old_heading), (heading, old_heading)
        assert semantic_answer(block) == semantic_answer(old_block), heading

    labels = set(re.findall(r"【名词解释：([^】]+)】", body))
    missing_exact = {label for label in labels if label not in source_text}
    assert missing_exact == set(SOURCE_LABEL_ALIASES), sorted(missing_exact)
    for label, source_alias in SOURCE_LABEL_ALIASES.items():
        assert source_alias in source_text, (label, source_alias)

    removed_terms = (
        "人本主义人格理论", "耶鲁态度改变模型", "社会抑制", "旁观者效应",
        "利他行为", "偏见", "格雷", "强化敏感性理论", "行为趋近系统",
        "行为抑制系统", "BAS", "BIS",
    )
    assert not any(term in body for term in removed_terms), {
        term for term in removed_terms if term in body
    }

    print(
        "全本V4来源审计通过：四份输入哈希一致；145道答案的非格式正文与V3现行范围版逐题一致；"
        f"{len(labels)}个名词概念中，{len(labels) - len(missing_exact)}个可在速背／一本通直接检出，"
        f"{len(missing_exact)}个为已登记规范术语别名；范围外旧真题模块未恢复。"
    )


if __name__ == "__main__":
    main()
