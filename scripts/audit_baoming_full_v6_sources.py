from __future__ import annotations

import hashlib
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

from build_baoming_full_v6 import NEW_EXPANSIONS, SOURCE, transform
from validate_baoming_full_v6 import V6, without_name_expansions


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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    return "".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))


def compact(text: str) -> str:
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", text))


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        assert path.is_file(), path
        assert digest(path) == expected, path

    speed_text = docx_text(SPEED)
    yibentong_text = docx_text(YIBENTONG)
    source_text = speed_text + yibentong_text
    source_compact = compact(source_text)
    v5 = SOURCE.read_text(encoding="utf-8")
    v6 = V6.read_text(encoding="utf-8")
    body5 = v5[v5.index("# 第一章 "):]
    body6 = v6[v6.index("# 第一章 "):]

    # 新版没有借名解扩容重开知识边界。
    assert without_name_expansions(body6) == without_name_expansions(body5)
    labels = set(re.findall(r"【名词解释：([^】]+)】", body6))
    missing_exact = {label for label in labels if label not in source_text}
    assert missing_exact == set(SOURCE_LABEL_ALIASES), sorted(missing_exact)
    for label, alias in SOURCE_LABEL_ALIASES.items():
        assert alias in source_text, (label, alias)

    _, standard = transform(v5)
    assert set(standard) == labels
    assert set(NEW_EXPANSIONS) <= labels

    # 对容易被外部常识带偏的扩容，使用速背／一本通中的原词锚点复核。
    # 例句允许在概念边界内灵活组织，不要求与来源逐字相同。
    source_anchors = (
        "PASS是指计划注意同时性加工继时性加工",
        "人格评鉴的方法有",
        "访谈法",
        "观察法",
        "自陈量表",
        "投射法",
        "忽视了它们他们发生的基础概率",
        "212岁言语能力逐渐大脑左侧化",
        "动作成分包括反射动作和基本动作",
        "知觉能力是指在动作技能领域",
        "体能是人体各种器官的运动能力",
        "选择发生的阶段依赖于当前的任务要求",
        "共同特征存储在上层概念中",
        "语音环路视觉空间模板情景缓冲器",
        "警觉阻抗衰竭三个阶段",
        "完全归纳推理是指",
        "不完全归纳推理是指",
        "态度由认知成分情感成分和行为意向成分三个部分构成",
        "1采取决定阶段",
        "2执行决定阶段",
        "绝对感觉阈限和差别感觉阈限",
        "罗夏墨渍测验和主题统觉测验",
        "过度焦虑冷漠攻击退行固着",
        "比纳西蒙智力测验",
        "斯坦福比纳智力测验",
        "大小恒常性形状恒常性方向恒常性明度恒常性颜色恒常性",
        "维系群体的存在",
        "统一群体成员的认识",
        "指引群体成员的行为",
        "自我决定行为和非自我决定行为",
        "成败经验替代性经验言语劝说生理和情绪状态",
        "片面强调自主神经系统的作用忽视中枢神经系统",
        "SKlogR",
    )
    for anchor in source_anchors:
        assert compact(anchor) in source_compact, anchor

    forbidden = (
        "格雷", "强化敏感性理论", "行为趋近系统", "行为抑制系统", "BAS", "BIS",
        "偏见", "利他行为", "旁观者效应", "社会抑制", "耶鲁态度改变模型",
    )
    assert not any(token in body6 for token in forbidden), {
        token for token in forbidden if token in body6
    }

    print(
        "全本V6来源审计通过：四份输入哈希一致；"
        "删除名解即时扩容后与V5现行范围正文逐字一致；"
        f"{len(labels)}个名词概念中，{len(labels) - len(missing_exact)}个可在速背／一本通直接检出，"
        f"{len(missing_exact)}个按登记别名核验；"
        f"{len(NEW_EXPANSIONS)}个新增标准扩容完成高风险原词锚点复核，范围外旧模块未恢复。"
    )


if __name__ == "__main__":
    main()
