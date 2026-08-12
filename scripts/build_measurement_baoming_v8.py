from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_紧凑排版版V7.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_名解准入精校版V8.md"


REPLACEMENTS = {
    (
        "（1）**16PF**：由卡特尔依据**人格特质理论**编制，把特质作为分析人格的基本测量单元；"
        "它从自然语言中搜集描述人格的词汇，采用**因素分析法**形成16种人格因素。"
        "（不同因素的组合构成个体独特的人格。）"
    ): (
        "（1）**16PF**：16种人格因素测验（16PF）是卡特尔依据**人格特质理论**、采用"
        "**因素分析法**编制的人格自陈量表，包括16种人格因素。（不同因素的组合构成个体独特的人格。）"
        "【名词解释：16PF】\n\n"
        "它把特质作为分析人格的基本测量单元，并从自然语言中搜集描述人格的词汇。"
    ),
    (
        "（2）**MMPI**：由哈慈威和麦金利以**精神病诊断症状群**为实际依据，最初用于诊断精神障碍；"
        "它采用**经验效标法**，根据题目能否区分效标组选择项目，而不以题目表面内容为主要标准。"
    ): (
        "（2）**MMPI**：明尼苏达多相人格问卷（MMPI）是哈慈威和麦金利采用**经验效标法**编制、"
        "最初用于诊断精神障碍的人格自陈量表。（它主要由**效度量表和临床量表**组成。）"
        "【名词解释：MMPI】\n\n"
        "它以**精神病诊断症状群**为实际依据，根据题目能否区分效标组选择项目，而不以题目表面内容为主要标准。"
    ),
    (
        "（3）**EPQ**：由艾森克夫妇编制，以**E、N、P人格维度**为核心；其测题经过**因素分析**测定，"
        "每个测题只负荷一个维度因素；量表包括**E、N、P、L四个分量表**。"
    ): (
        "（3）**EPQ**：艾森克人格问卷（EPQ）是由艾森克夫妇编制、以**E、N、P人格维度**为核心的"
        "人格自陈量表。（其测题经过**因素分析**测定，每个测题只负荷一个维度因素，量表包括"
        "**E、N、P、L四个分量表**。）【名词解释：EPQ】"
    ),
}


def transform(text: str) -> str:
    result = text.replace("## 全本·极简直背版V7", "## 全本·极简直背版V8", 1)
    assert result != text
    for source, replacement in REPLACEMENTS.items():
        assert result.count(source) == 1, source
        result = result.replace(source, replacement, 1)
    assert result.count("【名词解释：16PF】") == 1
    assert result.count("【名词解释：MMPI】") == 1
    assert result.count("【名词解释：EPQ】") == 1
    return result


def main() -> None:
    OUTPUT.write_text(transform(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"已生成{OUTPUT}。")


if __name__ == "__main__":
    main()
