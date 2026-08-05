from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFINITION_PREFIX_RE = re.compile(r"^(?:\*\*)?【名词解释】(?:\*\*)?\s*")
DEFINITION_NAME_RE = re.compile(r"^(?:（\d+）)?\*\*([^*]+)\*\*")

OPTIONAL_OVERRIDES: dict[str, tuple[str, ...]] = {
    "一、心理学的含义与研究对象": (
        "心理学兼有**自然科学**和**社会科学**的性质，因而被称为中间科学",
        "例如：同一学生的认知、情绪和意志活动，会同时受到成就动机与性格特点的影响",
    ),
    "四、行为主义": (
        "例如：对学生按时完成作业的行为给予奖励，可以提高该行为以后出现的频率",
    ),
    "五、格式塔心理学": (
        "例如：同一线段置于不同背景中，可能被知觉为不同长度，说明部分的性质受到整体结构影响",
    ),
    "六、精神分析学派": (
        "例如：个体用合理化解释失败，以减轻内部冲突引起的焦虑；也可联系其他心理防御机制",
    ),
    "七、人本主义心理学": (
        "人本主义因区别于行为主义和精神分析而被称为心理学的“**第三势力**”；咨询中还强调真诚、无条件积极关注和共情",
    ),
    "八、认知心理学": (
        "例如：比较不同任务的反应时，可以推断内部信息加工阶段及其耗时",
    ),
    "九、观察法、相关研究法与实验法": (
        "例如：自然观察幼儿分享行为、考察睡眠与成绩的相关、操纵学习时间并测量记忆成绩，可分别说明三种方法",
    ),
    "十、实验变量": (
        "例如：研究学习时间对记忆成绩的影响时，学习时间是自变量，记忆成绩是因变量，材料难度和测试环境属于需要控制的变量",
    ),
    "十一、测验法与信效度": (
        "例如：体重秤每次都稳定地多显示2千克，测量结果可能具有较高信度，但效度较低",
    ),
    "十二、投射法与投射测验": (
        "投射测验主要提供人格假设和深层线索，结果应与访谈、观察和自陈量表等资料结合，不能仅凭一次反应作出确定诊断",
    ),
    "十三、心理学的主要分支": (
        "例如：发展心理学可研究儿童言语的年龄特征，教育心理学可研究如何提高学习效果，社会心理学可研究个体何时发生从众",
    ),
    "一、神经元": (
        "例如：刺激信息经感觉神经元传入，由联络神经元加工，再经运动神经元传给肌肉",
    ),
    "三、神经系统的构成与功能": (
        "例如：考试前交感神经活动可使心跳加快，考试后副交感神经活动促进机体逐渐恢复",
    ),
    "七、丘脑与下丘脑": (
        "例如：机体缺水时，下丘脑参与把内部失衡转化为口渴动机并推动饮水",
    ),
    "八、边缘系统、海马与杏仁核": (
        "例如：带有强烈恐惧的事件既包含情境内容，也包含情绪意义，可分别联系海马与杏仁核的作用",
    ),
    "九、脑功能的主要学说": (
        "失语症等局部损伤证据支持功能定位，但复杂语言活动依赖多个脑区协作，又说明脑功能具有整体性",
    ),
    "一、学习的含义与特征": (
        "例如：持续练习后打字速度稳定提高属于学习；因疲劳导致速度暂时下降不属于学习",
    ),
    "二、反射、反射弧与反射类型": (
        "例如：强光引起瞳孔收缩属于无条件反射；铃声与食物配对后引起唾液属于条件反射",
    ),
    "三、经典条件反射": (
        "例如：食物自然引起唾液；铃声原本不引起唾液；二者反复配对后，铃声单独出现也能引起唾液",
    ),
    "四、经典条件反射的基本规律": (
        "例如：见到草绳也害怕说明泛化，只对特定铃声反应说明分化，铃声不再伴随食物后唾液减少说明消退",
    ),
    "五、信号系统与高级神经活动": (
        "例如：看到红灯停车主要体现第一信号系统；听到“红灯”二字便理解其含义体现第二信号系统",
    ),
    "六、操作条件反射与行为调控": (
        "例如：完成作业后获得表扬、免做家务、违规后增加值日、取消娱乐时间，可依次说明正强化、负强化、正惩罚和负惩罚",
        "计件工资、定期测验、随机抽奖和不定期检查，可分别用于说明四种间断强化程序",
    ),
    "七、经典条件反射与操作条件反射的比较": (
        "例如：铃声预示食物属于经典条件反射；按键得到食物并使按键行为增加属于操作条件反射",
    ),
    "八、顿悟学习": (
        "例如：学习者观察问题情境后，突然想到把两个工具组合起来取得远处物品",
    ),
    "九、目的行为学习理论": (
        "例如：熟悉校园后能够选择一条从未走过的新路线到达食堂，说明个体已经形成认知地图",
    ),
    "十、观察学习": (
        "例如：学习者先观察示范、记住操作步骤、尝试复现，再因获得积极反馈而继续练习",
    ),
    "十一、格雷的强化敏感性理论": (
        "例如：BAS较敏感者面对即时奖励更容易趋近，BIS较敏感者面对可能失败更容易暂停并评估风险",
    ),
}


def definition_name(line: str) -> str:
    match = DEFINITION_NAME_RE.match(line.strip())
    if not match:
        raise ValueError(f"无法识别名词解释概念：{line}")
    return match.group(1).strip()


def add_inline_definition_tags(lines: list[str]) -> list[str]:
    output: list[str] = []
    definition_mode = False
    for raw_line in lines:
        line = raw_line
        if DEFINITION_PREFIX_RE.match(line.strip()):
            line = DEFINITION_PREFIX_RE.sub("", line.strip(), count=1)
            definition_mode = True
        elif definition_mode and not line.strip():
            definition_mode = False

        if definition_mode and line.strip():
            name = definition_name(line)
            line = f"{line.rstrip()} **【名词解释：{name}】**"
        output.append(line)
    return output


def optional_paragraph(content: str) -> str:
    content = content.strip()
    if content.startswith("（") and content.endswith("）"):
        content = content[1:-1].strip()
    content = content.rstrip("。； ")
    if "例如" in content:
        suffix = "；例子可按题干灵活替换。"
    else:
        suffix = "；可按题干和时间灵活选写。"
    return f"（加分项：{content}{suffix}）"


def transform_answer(lines: list[str], unit_name: str) -> list[str]:
    body: list[str] = []
    in_optional_block = False

    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped == "**【灵活扩充】**":
            in_optional_block = True
            continue
        if in_optional_block:
            continue
        body.append(raw_line)

    while body and not body[-1].strip():
        body.pop()
    body = add_inline_definition_tags(body)
    optional_items = OPTIONAL_OVERRIDES.get(unit_name, ())
    if optional_items:
        body.append("")
        body.extend(optional_paragraph(item) for item in optional_items)
    return body


def transform_markdown(source: str) -> str:
    lines = source.splitlines()
    output: list[str] = []
    index = 0
    unit_name = ""
    while index < len(lines):
        line = lines[index]
        if line == "## 前三章·综合母答案试行版":
            output.append("## 前三章·直背综合答案版")
            index += 1
            continue
        if line.startswith("## "):
            unit_name = line[3:].split("【", 1)[0].strip()
        if line == "### 综合母答案":
            output.append("### 综合答案")
            index += 1
            answer_lines: list[str] = []
            while index < len(lines):
                candidate = lines[index]
                if candidate == "---" or candidate.startswith("# ") or candidate.startswith("## "):
                    break
                answer_lines.append(candidate)
                index += 1
            output.extend(transform_answer(answer_lines, unit_name))
            continue
        output.append(line)
        index += 1
    return "\n".join(output).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    source = arguments.input.read_text(encoding="utf-8")
    transformed = transform_markdown(source)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(transformed, encoding="utf-8")


if __name__ == "__main__":
    main()
