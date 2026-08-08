from __future__ import annotations

import hashlib
from pathlib import Path
import re
import zipfile

from lxml import etree


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_逐题直背版V1.md")
SPEED = Path(
    "/home/yileiyang/multi_agent/.work/workspaces/github.com/agiamason/"
    "tietou/agents/tietou_course/inbox/feishu/"
    "om_x100b690fde5974a0b10d419cacda419/27_.docx"
)
YIBENTONG = Path("/tmp/tietou_hf_sources_20260725/ecnu_yibentong.docx")
PUBLIC_347 = Path("/tmp/tietou_hf_sources_20260725/public_347_questions.docx")
PUBLIC_312 = Path("/tmp/tietou_hf_sources_20260725/public_312_questions.docx")
EXPECTED_HASHES = {
    SPEED: "4e27908521316b81d78dd20c88d99e49d46dfded581bc963ffb9ba770b0e80ca",
    YIBENTONG: "1ce2fcdcc29a7d5c81e8ae1f5dab2576e451a26740489ab5f31f634d851d8caf",
    PUBLIC_347: "269942da810827495730185388ee84ac01ae5b7f90682ef3c5e3061381f9efa2",
    PUBLIC_312: "d64f050d5d6fff6752b95d02a407fa713f1ed45ef90c0fb60f76b9d548d39c8f",
}
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


SOURCE_LABEL_ALIASES = {
    "坎农—巴德的情绪理论": "坎农——巴德的情绪理论",
    "大脑半球单侧化": "大脑两半球单侧化",
    "感觉后像": "正后像",
    "流体—晶体智力理论": "液态智力和晶态智力",
    "流体智力": "液态智力",
    "耶克斯—多德森定律": "耶克斯一多德森定律",
    "詹姆斯—朗格理论": "詹姆斯——朗格理论",
    "阿诺德和拉扎勒斯的认知—评价情绪理论": "阿诺德和拉扎勒斯的认知——评价情绪理论",
}
QUESTION_SUPPORTED_LABELS = {
    "偏见": "为什么我们会对他人和他群体会产生偏见",
    "利他行为": "论述利他行为的影响因素和如何提高利他行为",
    "旁观者效应": "旁观者效应",
    "社会抑制": "比较分析社会促进和社会抑制作用",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    return "".join(node.text or "" for node in root.findall(f".//{{{W_NS}}}t"))


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        assert path.is_file(), path
        assert digest(path) == expected, path

    speed_text = docx_text(SPEED)
    yibentong_text = docx_text(YIBENTONG)
    source_text = speed_text + yibentong_text
    public_347_text = docx_text(PUBLIC_347)
    markdown = MARKDOWN.read_text(encoding="utf-8")
    body = markdown[markdown.index("# 第一章 "):]

    labels = set(re.findall(r"【名词解释：([^】]+)】", body))
    missing_exact = {label for label in labels if label not in source_text}
    expected_missing = set(SOURCE_LABEL_ALIASES) | set(QUESTION_SUPPORTED_LABELS)
    assert missing_exact == expected_missing, sorted(missing_exact ^ expected_missing)
    for label, source_alias in SOURCE_LABEL_ALIASES.items():
        assert source_alias in source_text, (label, source_alias)
    for label, question_anchor in QUESTION_SUPPORTED_LABELS.items():
        assert question_anchor in public_347_text, (label, question_anchor)

    # 双源正文不足、但现有主观题原问要求补齐的三个模块。
    assert "试述人格的人本主义理论，并对其进行评价" in public_347_text
    assert "耶鲁态度改变研究法" in public_347_text
    assert "为什么我们会对他人和他群体会产生偏见" in public_347_text
    assert "七、人本主义人格理论【一级】" in body
    assert "耶鲁态度改变模型" in body
    assert "十二、偏见的形成、后果与减少【一级】" in body

    forbidden = (
        "格雷", "强化敏感性理论", "行为趋近系统", "行为抑制系统",
        "信号检测论", "系列位置效应", "单纯接触效应", "长时增强",
    )
    assert not any(token in body for token in forbidden), {
        token for token in forbidden if token in body
    }
    assert "长时程增强" in body and "长时程增强" in source_text
    assert "第十七章" not in body

    print(
        "全本来源核验通过："
        f"速背/一本通/347题库/312题库哈希一致；"
        f"{len(labels)}个名词解释中，{len(labels) - len(missing_exact)}个标签可在双源直接检出，"
        f"{len(SOURCE_LABEL_ALIASES)}个属于同义或规范术语对齐，"
        f"{len(QUESTION_SUPPORTED_LABELS)}个由可复核主观题原问支持。"
    )


if __name__ == "__main__":
    main()
