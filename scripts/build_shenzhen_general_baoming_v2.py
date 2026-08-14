from __future__ import annotations

from pathlib import Path
import re

from shenzhen_baoming_canonical import canonicalize_definitions


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V1.md"
OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V2.md"


COMPARISON_SUMMARIES = {
    "比较**自然观察法和实验法**的含义、优缺点及适用范围": "二者都用于收集心理与行为证据；主要区别在于观察法保留自然情境但控制较弱，实验法主动操纵和控制变量，因果推断较强。",
    "比较研究中的**因果关系和相关关系**": "二者都描述变量之间的联系；主要区别在于相关只说明共同变化，因果还要求时间先后、稳定共变并排除其他解释。",
    "比较脑功能的**定位说、整体说、机能系统说、模块说和神经网络说**": "各学说都解释脑活动与心理功能的关系；主要区别在于分别强调局部定位、整体作用、动态系统、专门模块和分布式网络。",
    "比较**感觉适应、感觉对比和感觉的相互作用**": "三者都表现为刺激条件改变引起感受性变化；主要区别在于适应强调同一刺激持续作用，对比强调不同刺激作用于同一感受器，相互作用强调不同感受器之间的影响。",
    "比较颜色视觉的**三色理论、对立过程理论和两阶段理论**": "三种理论都解释颜色编码；主要区别在于三色理论强调三类感受器，对立过程理论强调拮抗通道，两阶段理论把二者安排在视觉加工的不同阶段。",
    "比较主要的**音高理论**": "各理论都解释声音频率如何形成音高经验；主要区别在于位置理论强调基底膜振动位置，频率理论及其修正强调神经冲动频率和多个神经元协同放电。",
    "比较其联系与区别": "各选择性注意理论都解释有限加工系统如何选择信息；主要区别在于选择发生的阶段及未选择信息能否得到语义加工不同。",
    "比较注意分配的**认知资源理论和双加工理论**": "二者都说明多任务表现受加工资源和任务性质影响；主要区别在于认知资源理论强调资源总量与分配，双加工理论强调自动加工和控制加工的性质差异。",
    "比较感觉记忆、短时记忆和长时记忆的特点": "三者都是记忆系统并通过注意、复述和提取相互联系；主要区别在于保持时间、容量、编码方式和信息功能不同。",
    "比较工作记忆与短时记忆的联系和区别": "二者都涉及信息的短暂保持且容量有限；主要区别在于短时记忆强调临时存储，工作记忆还强调执行控制和对信息的主动加工。",
    "比较内隐记忆和外显记忆的异同": "二者都体现过去经验对当前活动的影响；主要区别在于提取是否需要意识、常用测量任务以及受加工深度和遗忘等变量影响的方式不同。",
    "比较力求成功者与避免失败者的行为特点": "二者都受成就情境中成功期望和结果价值影响；主要区别在于前者趋向成功并选择中等难度任务，后者重在回避失败，常选择极易或极难任务。",
    "比较其核心观点": "各理论都解释情绪如何产生；主要区别在于分别强调外周生理变化、中枢同时激活、生理唤醒与认知标签、认知评价以及认知—生理—行为的综合作用。",
    "比较人本主义人格理论与班杜拉社会学习人格理论": "二者都重视人的主体作用并反对把人视为被动个体；主要区别在于人本主义强调潜能、自我和积极关注，社会学习理论强调交互决定、观察学习和自我效能。",
    "比较自陈量表与投射测验": "二者都用于推断相对稳定的人格特征；主要区别在于自陈量表使用结构化题目和客观计分，投射测验使用模糊刺激和自由反应，解释更依赖专业判断。",
    "比较个体发展中的关键期与敏感期": "二者都指某种能力对经验特别敏感的发展阶段；主要区别在于关键期具有较严格的时限和不可逆性，敏感期强调此时发展最容易，错过后仍可能补偿。",
    "比较语言发展的学习观、先天观和相互作用论": "三种观点都解释儿童语言获得；主要区别在于学习观强调强化和模仿，先天观强调语言获得装置，相互作用论强调先天准备与社会环境共同作用。",
    "比较皮亚杰和科尔伯格的道德认知发展理论": "二者都把道德发展看作认知结构由低到高的阶段变化；主要区别在于皮亚杰侧重儿童规则意识与他律—自律转变，科尔伯格侧重道德判断理由的三水平六阶段。",
    "比较学习动机的强化理论与人本主义理论": "二者都能解释环境和需要对学习行为的推动；主要区别在于强化理论强调行为后果和外部强化，人本主义理论强调基本需要、成长需要与内在自我实现。",
    "比较促进聚焦与防御聚焦": "二者都是个体调节目标追求的方式；主要区别在于促进聚焦追求理想、成长和获得，采用进取策略，防御聚焦重视责任、安全和避免损失，采用警戒策略。",
}


def add_comparison_summary(block: str, heading: str) -> str:
    summary = next((value for key, value in COMPARISON_SUMMARIES.items() if key in heading), None)
    if summary is None:
        return block
    top_numbers = [int(value) for value in re.findall(r"^(\d+)\. ", block, re.MULTILINE)]
    assert top_numbers, heading
    point = f"{max(top_numbers) + 1}. **联系与主要区别**：{summary}\n\n"
    marker = re.search(r"^综上，", block, re.MULTILINE)
    assert marker, heading
    return block[: marker.start()] + point + block[marker.start() :]


def transform(text: str) -> str:
    matches = list(re.finditer(r"^### 押题\d+【(?:简答|论述)】.*$", text, re.MULTILINE))
    parts: list[str] = []
    cursor = 0
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block_end = end
        heading_boundary = re.search(r"^#{1,2} ", text[match.end() : end], re.MULTILINE)
        if heading_boundary:
            block_end = match.end() + heading_boundary.start()
        parts.append(text[cursor : match.end()])
        block = text[match.end() : block_end]
        heading = match.group(0)
        if "比较" in heading or "异同" in heading:
            block = add_comparison_summary(block, heading)
        parts.append(block)
        cursor = block_end
    parts.append(text[cursor:])
    result = "".join(parts)
    assert len(re.findall(r"^### 押题", result, re.MULTILINE)) == 90
    return canonicalize_definitions(result)


def main() -> None:
    OUTPUT.write_text(transform(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
