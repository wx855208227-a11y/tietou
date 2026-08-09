from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_名解完整扩容版V6.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_三星分级选背版V7.md"
MATRIX = ROOT / "analysis/华东心理学导论保命手册V7_三星分级矩阵.md"
EVIDENCE = ROOT / "analysis/华东心理学导论保命手册V4_押题证据矩阵.md"


# 只在V6已经确认的一级范围内进一步区分。三星不按数量倒推，而用于
# “华东信号／章节核心度／稳定采分结构／辅助真题支持／答案复用价值”
# 组合更强的单元；原一级的其余单元为两星，原二级全部为一星。
THREE_STAR_UNITS = {
    "第一章 心理学研究的对象、方法及其学科发展｜一、心理学的含义与研究对象",
    "第一章 心理学研究的对象、方法及其学科发展｜四、行为主义",
    "第一章 心理学研究的对象、方法及其学科发展｜六、精神分析学派",
    "第一章 心理学研究的对象、方法及其学科发展｜九、观察法、相关研究法与实验法",
    "第一章 心理学研究的对象、方法及其学科发展｜十二、投射法与投射测验",
    "第二章 心理和行为的生物学基础｜四、大脑皮层的感觉区与运动区",
    "第二章 心理和行为的生物学基础｜五、大脑皮层的言语区与联合区",
    "第二章 心理和行为的生物学基础｜六、大脑两半球的功能分工",
    "第三章 条件反射和学习｜三、经典条件反射",
    "第三章 条件反射和学习｜四、经典条件反射的基本规律",
    "第三章 条件反射和学习｜六、操作条件反射的强化、惩罚与强化程序",
    "第三章 条件反射和学习｜十、观察学习",
    "第四章 意识和意识状态｜四、注意的含义、特点与功能",
    "第四章 意识和意识状态｜六、注意的品质",
    "第四章 意识和意识状态｜七、注意选择的认知理论",
    "第五章 感觉｜三、感受性、感觉阈限与心理物理定律",
    "第六章 知觉｜二、知觉的基本特性",
    "第七章 记忆｜一、记忆的含义与类型",
    "第七章 记忆｜四、短时记忆与工作记忆",
    "第七章 记忆｜五、长时记忆的编码、储存与提取",
    "第七章 记忆｜六、遗忘曲线与遗忘理论",
    "第七章 记忆｜七、影响遗忘的因素与记忆策略",
    "第九章 思维｜二、概念及其形成",
    "第九章 思维｜五、决策理论与启发式偏差",
    "第九章 思维｜六、问题解决的过程与策略",
    "第九章 思维｜七、影响问题解决的因素",
    "第十一章 情绪和情感｜一、情绪和情感的含义、功能与关系",
    "第十一章 情绪和情感｜四、情绪的认知理论",
    "第十二章 意志｜二、意志行动的阶段与动机冲突",
    "第十三章 动机｜一、动机的含义、产生条件与功能",
    "第十三章 动机｜三、需要与马斯洛需要层次理论",
    "第十三章 动机｜四、成就动机理论",
    "第十三章 动机｜六、动机的归因理论",
    "第十三章 动机｜八、自我决定理论与成就目标理论",
    "第十五章 能力｜三、智力的因素与结构理论",
    "第十五章 能力｜四、智力的信息加工理论",
    "第十六章 人格｜一、人格的含义与特征",
    "第十六章 人格｜二、气质类型与高级神经活动类型",
    "第十六章 人格｜四、人格特质理论",
    "第十六章 人格｜五、精神分析人格理论",
    "第十八章 社会心理｜一、态度的结构、功能及其与行为的关系",
    "第十八章 社会心理｜二、态度的形成与改变",
    "第十八章 社会心理｜四、社会归因理论",
    "第十八章 社会心理｜十、从众与服从",
}

PAIR_RE = re.compile(r"【名词解释：([^】]+)】【扩容（选用）：(.*?)】")


def unit_levels(text: str) -> dict[str, str]:
    result = {}
    chapter = ""
    for line in text.splitlines():
        if line.startswith("# 第"):
            chapter = line[2:].strip()
        match = re.match(r"^## (.+)【(一级|二级)】$", line)
        if match:
            result[f"{chapter}｜{match.group(1)}"] = match.group(2)
    return result


def evidence_flags() -> dict[str, dict[str, bool | int]]:
    result: dict[str, dict[str, bool | int]] = defaultdict(
        lambda: {"questions": 0, "target": False, "auxiliary": False, "essay": False}
    )
    for line in EVIDENCE.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| \d+ \|", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        _, chapter, question, target, _, _, auxiliary, _, _ = cells
        unit = question.split("·押题", 1)[0]
        key = f"{chapter}｜{unit}"
        result[key]["questions"] = int(result[key]["questions"]) + 1
        result[key]["target"] = bool(result[key]["target"]) or "检出相关术语" in target
        result[key]["auxiliary"] = bool(result[key]["auxiliary"]) or "题库检出" in auxiliary
        result[key]["essay"] = bool(result[key]["essay"]) or "【论述】" in question
    return result


def star_levels(text: str) -> dict[str, str]:
    original = unit_levels(text)
    assert len(original) == 117
    assert THREE_STAR_UNITS <= {key for key, level in original.items() if level == "一级"}
    result = {}
    for key, level in original.items():
        if level == "二级":
            result[key] = "★"
        elif key in THREE_STAR_UNITS:
            result[key] = "★★★"
        else:
            result[key] = "★★"
    assert list(result.values()).count("★★★") == 44
    assert list(result.values()).count("★★") == 40
    assert list(result.values()).count("★") == 33
    return result


def relevel(text: str, levels: dict[str, str]) -> str:
    chapter = ""
    seen = set()
    output = []
    for line in text.splitlines():
        if line.startswith("# 第"):
            chapter = line[2:].strip()
        match = re.match(r"^(## )(.+)【(?:一级|二级)】$", line)
        if match:
            key = f"{chapter}｜{match.group(2)}"
            line = f"{match.group(1)}{match.group(2)}【{levels[key]}】"
            seen.add(key)
        output.append(line)
    assert seen == set(levels)
    return "\n".join(output) + "\n"


def build_matrix(levels: dict[str, str]) -> str:
    flags = evidence_flags()
    rows = []
    for index, (key, star) in enumerate(levels.items(), start=1):
        chapter, unit = key.split("｜", 1)
        evidence = flags[key]
        signals = []
        if evidence["target"]:
            signals.append("2018—2020华东题册术语信号")
        if evidence["auxiliary"]:
            signals.append("347／312辅助题库支持")
        if evidence["essay"]:
            signals.append("可形成稳定论述采分结构")
        if int(evidence["questions"]) >= 2:
            signals.append("可复用回答多道主观题")
        if star == "★★★":
            conclusion = "原一级中的优先背诵单元；综合章节核心度与上述证据评定"
        elif star == "★★":
            conclusion = "保持原一级；现行核心且可考，但综合优先度低于三星"
        else:
            conclusion = "严格对应原二级；用于完整覆盖"
        rows.append(
            f"| {index} | {chapter} | {unit} | {star} | "
            f"{'；'.join(signals) if signals else '现行速背／一本通范围与稳定采分结构'} | {conclusion} |"
        )
    return """# 华东心理学导论保命手册V7三星分级矩阵

## 使用边界

- ★★★与★★的并集严格等于上一版一级，★严格等于上一版二级，不跨原级别升降。
- ★★★不是机械配额，也不等同于“必考”；它表示原一级中应当更优先背诵的单元。
- 华东题册的术语检出只作直接命题信号之一，不等同于同题、同题型或必然再次命题。
- 其他347／312真题只用于支持知识点可考性和可能题型，不能替代华东现行范围。

## 逐单元分级

| 序号 | 章节 | 单元 | 星级 | 可核验信号 | 分级结论 |
|---:|---|---|:---:|---|---|
""" + "\n".join(rows) + "\n"


def transform(text: str) -> tuple[str, dict[str, str]]:
    levels = star_levels(text)
    result = relevel(text, levels)
    result, pair_count = PAIR_RE.subn(
        lambda match: f"【扩容（选背）：{match.group(2)}】【名词解释：{match.group(1)}】",
        result,
    )
    assert pair_count == 296
    result = result.replace("【扩容（选用）：", "【扩容（选背）：")
    result = result.replace("## 全本·名解完整扩容版V6", "## 全本·三星分级选背版V7", 1)
    old_intro = (
        "> 每道押题均配置一份可直接背写的独立答案，按“总起—分点—总结”组织。括号外是必须优先掌握的基础采分点；"
        "每个`【名词解释：……】`后均紧跟一条标准`【扩容（选背）：……】`，二者共同构成正常名解容量；"
        "其他扩容也紧跟所扩充的采分点，可按题目分值和时间选写。"
    )
    new_intro = (
        "> 每道押题均配置一份可直接背写的独立答案，按“总起—分点—总结”组织。括号外是必须优先掌握的基础采分点；"
        "每个名词解释按“完整核心定义—`【扩容（选背）：……】`—`【名词解释：……】`”呈现，核心定义与其标准扩容共同构成正常名解容量；"
        "其他扩容也紧跟所扩充的采分点，作为可选背内容，作答时按题目分值和时间选写。"
    )
    assert old_intro in result
    result = result.replace(old_intro, new_intro, 1)
    old_level = (
        "> 一级、二级由华东历年命题信号、现行考纲与教材核心度、知识点可考性、其他347与312真题支持、"
        "华东命题风格和答案复用价值综合判断。既往题型不是未来题型上限；最终比例只用于检查分布是否异常，不作为强制配额。"
    )
    new_level = (
        "> ★★★、★★均对应速背手册原一级，★对应速背手册原二级。原一级内部再依据华东命题信号、现行考纲与教材核心度、"
        "主观题采分结构、其他347与312真题支持、华东命题风格和答案复用价值区分优先顺序；星级不是机械配额，也不代表必考。"
    )
    assert old_level in result
    result = result.replace(old_level, new_level, 1)
    return result, levels


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    result, levels = transform(source)
    OUTPUT.write_text(result, encoding="utf-8")
    MATRIX.write_text(build_matrix(levels), encoding="utf-8")
    print(
        f"{OUTPUT}：★★★={list(levels.values()).count('★★★')}，"
        f"★★={list(levels.values()).count('★★')}，★={list(levels.values()).count('★')}。"
    )
    print(MATRIX)


if __name__ == "__main__":
    main()
