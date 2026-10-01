from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from rebuild_shenzhen_baoming_v10_semantic import (
    build_experiment as build_experiment_v10,
    build_general as build_general_v10,
    build_measurement as build_measurement_v10,
)


ROOT = Path(__file__).resolve().parents[1]

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V12.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V11.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V11.md"


def update_question(text: str, fragment: str, updater: Callable[[str], str]) -> str:
    matches = [
        match
        for match in re.finditer(r"(?m)^### 押题\d+【(?:简答|论述)】[^\n]+\n", text)
        if fragment in match.group(0)
    ]
    assert len(matches) == 1, (fragment, len(matches))
    match = matches[0]
    boundary = re.search(r"(?m)^(?:### 押题\d+【|## |# )", text[match.end() :])
    end = match.end() + boundary.start() if boundary else len(text)
    block = text[match.start() : end]
    revised = updater(block)
    assert revised != block, fragment
    return text[: match.start()] + revised + text[end:]


def retitle(new_title: str) -> Callable[[str], str]:
    def updater(block: str) -> str:
        return re.sub(r"^### .*?$", f"### {new_title}", block, count=1, flags=re.MULTILINE)

    return updater


def replace_required(block: str, old: str, new: str) -> str:
    assert old in block, old
    return block.replace(old, new, 1)


def replace_last_module(block: str, number: int, replacement: str) -> str:
    pattern = rf"\n{number}\. .*?(?=\n\n综上)"
    revised, count = re.subn(pattern, "\n" + replacement.rstrip(), block, count=1, flags=re.DOTALL)
    assert count == 1, (number, block.splitlines()[0])
    return revised


def retitle_then(new_title: str, transform: Callable[[str], str]) -> Callable[[str], str]:
    def updater(block: str) -> str:
        revised = retitle(new_title)(block)
        return transform(revised)

    return updater


def build_general() -> str:
    text = build_general_v10()

    # 题型先由答案主体容量反向校准；不靠删采分点或添加无关内容硬凑字数。
    type_only = {
        "因果关系和相关关系": "押题1【论述】比较研究中的**因果关系和相关关系**，并说明解释相关结果时应注意的问题。",
        "大脑皮层的主要机能分区": "押题1【论述】论述大脑皮层的主要机能分区，并说明大脑两半球的**功能单侧化**。",
        "感觉的基本现象，并比较": "押题2【论述】论述感觉的基本现象，并比较**感觉适应、感觉对比和感觉的相互作用**。",
        "工作记忆与短时记忆": "押题2【论述】比较工作记忆与短时记忆的联系和区别。",
        "语言的含义、基本特征": "押题1【论述】论述语言的含义、基本特征及转换生成语法理论。",
        "情绪的主要维度": "押题1【论述】论述情绪的主要维度、种类及典型情绪状态。",
        "促进聚焦与防御聚焦": "押题2【论述】比较促进聚焦与防御聚焦的目标追求特点。",
    }
    for fragment, title in type_only.items():
        text = update_question(text, fragment, retitle(title))

    # 以上位、稳定考点命题，避免机械地把所有下位概念塞进题干。
    title_only = {
        "过去经验和知觉定势": "押题2【简答】简述过去经验和知觉定势对知觉的影响。",
        "视觉适应、后像、视觉对比": "押题2【简答】简述视觉的主要现象。",
        "动机的本能论、驱力理论": "押题1【论述】论述动机的主要理论。",
        "智力的含义及主要理论": "押题1【论述】论述智力的主要理论。",
        "苛勒、托尔曼和建构主义": "押题1【论述】论述认知学习理论的主要观点。",
    }
    for fragment, title in title_only.items():
        text = update_question(text, fragment, retitle(title))

    def natural_observation(block: str) -> str:
        replacement = """3. **二者的联系与区别**：二者都用于收集心理与行为证据，可以相互补充；观察法保留自然情境、真实性较高，但控制较弱，实验法主动操纵和控制变量、因果推断较强。（研究中可先用观察法发现问题、形成假设，再用实验法检验；也可采用自然实验兼顾真实性与控制。）"""
        pattern = r"\n3\. \*\*二者关系\*\*：.*?\n\n4\. \*\*联系与主要区别\*\*：.*?(?=\n\n综上)"
        revised, count = re.subn(pattern, "\n" + replacement, block, count=1, flags=re.DOTALL)
        assert count == 1
        return revised

    text = update_question(text, "自然观察法和实验法", natural_observation)

    def schools(block: str) -> str:
        return replace_last_module(
            block,
            9,
            "（从研究重点看，构造主义重在意识“由什么构成”，机能主义重在意识“有什么功能”，行为主义重在外显行为，格式塔强调整体结构，精神分析强调无意识冲突，人本主义强调人的潜能和价值。）",
        )

    text = update_question(text, "心理学主要流派", schools)

    def brain_theories(block: str) -> str:
        block = retitle("押题1【论述】比较脑功能的主要学说。")(block)
        replacement = """6. **联系与主要区别**：各学说都解释脑活动与心理功能的关系；定位说突出局部功能专门化，整体说突出总体活动，机能系统说强调多个系统动态协同，模块说强调专门模块，神经网络说强调分布式连接。（现代研究通常同时关注局部脑区和大范围网络。）"""
        pattern = r"\n6\. \*\*理论关系\*\*：.*?\n\n7\. \*\*联系与主要区别\*\*：.*?(?=\n\n综上)"
        revised, count = re.subn(pattern, "\n" + replacement, block, count=1, flags=re.DOTALL)
        assert count == 1
        return revised

    text = update_question(text, "比较脑功能的", brain_theories)

    def psychophysical_laws(block: str) -> str:
        block = retitle("押题1【论述】论述心理物理学的主要定律及其关系。")(block)
        return replace_last_module(
            block,
            5,
            "（适用边界：韦伯定律和费希纳定律并非适用于所有刺激强度和感觉通道；幂定律扩大了阈上感觉测量范围，但其参数仍随感觉类型和测量条件变化。）",
        )

    text = update_question(text, "韦伯定律、费希纳定律和斯蒂文斯", psychophysical_laws)

    def color_theories(block: str) -> str:
        block = retitle("押题1【简答】比较颜色视觉的主要理论。")(block)
        replacement = """4. **联系与主要区别**：三种理论都解释颜色编码；三色理论强调感受器水平的三类视锥细胞，对立过程理论强调后续神经编码中的拮抗通道，两阶段理论则把二者安排在颜色加工的不同阶段。（因此，三色理论与对立过程理论并非互相排斥，两阶段理论把二者统一起来。）"""
        pattern = r"\n4\. \*\*理论关系\*\*：.*?\n\n5\. \*\*联系与主要区别\*\*：.*?(?=\n\n综上)"
        revised, count = re.subn(pattern, "\n" + replacement, block, count=1, flags=re.DOTALL)
        assert count == 1
        return revised

    text = update_question(text, "颜色视觉的", color_theories)

    text = update_question(
        text,
        "声音的心理维度和声音掩蔽",
        retitle("押题1【论述】论述听觉的基本现象，并比较主要音高理论。"),
    )
    text = update_question(
        text,
        "注意分配的",
        retitle("押题2【论述】比较注意分配的主要理论。"),
    )

    def attention_phenomena(block: str) -> str:
        block = retitle("押题1【简答】简述选择性注意的经典现象。")(block)
        block = re.sub(
            r"\n4\. 三种现象的\*\*主要区别\*\*在于：.*?(?=\n\n综上)",
            "",
            block,
            count=1,
            flags=re.DOTALL,
        )
        old = "综上，负启动、返回抑制和注意瞬脱分别从被忽略信息、原先注意位置和时间序列说明选择性注意的加工特点。"
        new = "综上，选择性注意可表现为负启动、返回抑制和注意瞬脱，这些现象说明被忽略信息、先前注意和时间序列都会影响当前加工。"
        return replace_required(block, old, new)

    text = update_question(text, "负启动、返回抑制和注意瞬脱", attention_phenomena)

    def hypnosis(block: str) -> str:
        return replace_last_module(
            block,
            3,
            "（理论侧重点：特殊状态理论强调意识状态发生质变，非特殊状态理论强调注意、期待、动机和社会情境等正常心理机制。）",
        )

    text = update_question(text, "催眠的含义及其主要理论", hypnosis)

    def working_memory_compare(block: str) -> str:
        block = replace_last_module(block, 6, "")
        block = replace_required(block, "1. **共同点**：", "1. **联系（共同点）**：")
        return replace_required(block, "2. **成分不同**：", "2. **区别一——成分不同**：")

    text = update_question(text, "工作记忆与短时记忆", working_memory_compare)

    def concept_strategies(block: str) -> str:
        block = replace_last_module(
            block,
            5,
            "（四种策略主要在初始假设范围、每次改变的属性数以及假设检验是同时还是依次进行等方面有所不同。）",
        )
        old = "综上，四种策略的核心差异在于初始假设范围、每次改变的属性数以及假设检验是同时还是依次进行。"
        new = "综上，布鲁纳的概念形成策略包括保守性聚焦、冒险性聚焦、同时性扫描和继时性扫描，均通过提出并检验假设来发现概念规则。"
        return replace_required(block, old, new)

    text = update_question(text, "布鲁纳提出的概念形成策略", concept_strategies)

    text = update_question(
        text,
        "决策的主要理论",
        lambda block: replace_last_module(
            block,
            3,
            "（理论关系：古典理论和期望效用理论提供规范性标准，行为决策、前景理论和启发式研究则揭示真实决策中的有限理性、参照依赖和系统偏差。）",
        ),
    )

    text = update_question(
        text,
        "动机的主要理论",
        lambda block: replace_last_module(
            block,
            6,
            "（综合来看，复杂行为通常是内部需要、外部诱因、唤醒水平和认知评价共同作用的结果。）",
        ),
    )

    text = update_question(text, "情绪的核心功能", lambda block: replace_last_module(block, 5, ""))

    text = update_question(
        text,
        "智力的主要理论",
        lambda block: replace_last_module(
            block,
            8,
            "（从理论发展看，智力理论由一般因素和多因素结构逐渐拓展到多元能力、现实适应和认知加工过程。）",
        ),
    )

    text = update_question(
        text,
        "弗洛伊德关于人格结构",
        lambda block: replace_last_module(
            block,
            5,
            "（理论评价：精神分析拓展了对潜意识、动机、人格发展和心理防御的研究，但过分强调本能和早期经验，部分观点较难以客观检验。）",
        ),
    )

    text = update_question(
        text,
        "主要人格特质理论",
        lambda block: replace_last_module(
            block,
            3,
            "（理论脉络：奥尔波特重视特质的共同性和个别性，卡特尔用因素分析寻找根源特质，艾森克提炼高级人格维度，大五模型则形成较有共识的五维结构。）",
        ),
    )

    def cognitive_learning(block: str) -> str:
        old = """（3）**教育应用**：教学应创设需要探索的整体情境，帮助学生关注关键关系、形成认知地图并主动建构知识，同时提供适当榜样和社会互动。（教师的作用是组织经验、提供支架和促进理解。）"""
        new = """（教育应用：教学可创设需要探索的整体情境，帮助学生关注关键关系、形成认知地图并主动建构知识，同时提供适当的社会互动和学习支架。）"""
        return replace_required(block, old, new)

    text = update_question(text, "认知学习理论的主要观点", cognitive_learning)

    text = update_question(
        text,
        "皮亚杰的认知发展理论",
        lambda block: replace_last_module(
            block,
            4,
            "（理论评价：该理论强调主客体相互作用、活动作用和阶段间质的差异，但可能低估儿童能力，年龄划分也有绝对化倾向；新皮亚杰理论进一步重视任务、训练、社会互动和文化经验。）",
        ),
    )

    def moral_theories(block: str) -> str:
        pattern = r"\n3\. \*\*两种理论的联系与区别如下：\*\*.*?\n\n4\. \*\*教育启示\*\*：.*?(?=\n\n综上)"
        replacement = """
3. **两种理论的联系与区别**：二者都把道德发展看作认知结构由低到高的阶段变化，并强调认知发展和观点采择；皮亚杰侧重儿童规则意识及他律—自律转变，科尔伯格侧重道德判断理由的三水平六阶段。（二者都较少直接说明道德情感、具体行为和文化情境；教育中可通过平等交往、规则讨论、观点采择和道德两难问题促进道德推理。）"""
        revised, count = re.subn(pattern, replacement.rstrip(), block, count=1, flags=re.DOTALL)
        assert count == 1
        return revised

    text = update_question(text, "皮亚杰和科尔伯格", moral_theories)

    text = update_question(
        text,
        "桑代克联结主义",
        lambda block: replace_last_module(
            block,
            3,
            "（教育应用：教学可提供适量练习和及时反馈，并使学习结果具有满意性；复杂技能可分步练习，但还需帮助学生理解知识关系。）",
        ),
    )

    text = update_question(
        text,
        "科温顿自我价值理论",
        lambda block: replace_last_module(
            block,
            2,
            "（教育应用：应减少以能力高低标签化学生，强调可控努力、策略改进和掌握目标，并提供适度挑战与成功经验。）",
        ),
    )

    def regulatory_focus(block: str) -> str:
        replacement = """3. **二者的联系与区别**：二者都是个体调节目标追求的方式；促进聚焦追求理想、成长和收益，采用进取策略，防御聚焦重视责任、安全和避免损失，采用警戒策略。（两种聚焦没有简单的好坏之分，表现取决于调节方式与任务要求是否匹配。）"""
        return replace_last_module(block, 3, replacement)

    text = update_question(text, "促进聚焦与防御聚焦", regulatory_focus)
    return text


def build_experiment() -> str:
    text = build_experiment_v10()

    text = update_question(
        text,
        "费希纳、冯特和艾宾浩斯",
        retitle("押题1【简答】简述实验心理学创立与早期发展的主要代表人物及其贡献。"),
    )
    text = update_question(
        text,
        "减数法与加因素法",
        retitle("押题1【论述】比较反应时研究中的**减数法与加因素法**。"),
    )
    text = update_question(
        text,
        "费希纳定律和史蒂文斯定律",
        retitle("押题1【论述】比较**费希纳定律和史蒂文斯定律**。"),
    )

    text = update_question(
        text,
        "实验设计的含义及主要分类",
        lambda block: replace_last_module(
            block,
            5,
            "（设计选择应综合考虑处理延续性、个体差异、顺序效应、变量数量、控制条件和被试数量。）",
        ),
    )

    def quasi_experiment(block: str) -> str:
        block = replace_last_module(block, 5, "")
        block = replace_required(block, "1. **控制程度**：", "1. **区别一——控制程度**：")
        return replace_required(block, "4. **共同要求**：", "4. **联系（共同要求）**：")

    text = update_question(text, "准实验设计与真实验设计", quasi_experiment)

    text = update_question(
        text,
        "A、B、C三类反应时",
        lambda block: replace_last_module(
            block,
            4,
            "（三类反应时的关系：C减A可估计刺激辨别时间，B减C可估计反应选择时间，这构成唐德斯减数法的基础。）",
        ),
    )

    def implicit_paradigms(block: str) -> str:
        block = retitle("押题1【论述】论述两种经典内隐研究范式的基本原理。")(block)
        block = replace_last_module(block, 3, "")
        old = "综上，两种范式都利用条件间反应时差异揭示内隐加工，但前者测量内隐学习，后者测量内隐态度。"
        new = "综上，序列反应时任务通过规则序列与随机序列的反应时差异测量内隐学习，内隐联想测验通过相容与不相容任务的反应时差异测量自动化联系。"
        return replace_required(block, old, new)

    text = update_question(text, "序列反应时任务和内隐联想测验", implicit_paradigms)

    text = update_question(
        text,
        "感觉阈限的含义、传统测量方法",
        lambda block: replace_last_module(
            block,
            3,
            "（三种方法都通过多次刺激判断估计感觉阈限，但刺激呈现顺序、被试任务和主要误差不同。）",
        ),
    )

    text = update_question(
        text,
        "信号检测论的基本思想",
        lambda block: replace_last_module(
            block,
            4,
            "（信号检测论的主要价值在于把主观判断标准与客观辨别力分离，明确虚报概念，并把噪音信息纳入分析。）",
        ),
    )
    return text


def build_measurement() -> str:
    text = build_measurement_v10()

    type_changes = {
        "心理测验的**主要分类": "押题1【论述】论述心理测验的主要分类及应用。",
        "内容效度的**含义": "押题1【论述】论述内容效度的含义、验证方法及提高方法。",
        "多重选择题项目分析": "押题1【论述】论述多重选择题项目分析，并说明猜测校正的作用与局限。",
        "智龄、年级当量和比率智商": "押题1【论述】比较智龄、年级当量和比率智商的含义及局限。",
        "组内常模的含义": "押题1【论述】论述组内常模的含义、主要形式及分数解释。",
        "目标参照测验的项目分析": "押题1【论述】论述目标参照测验的项目分析、信效度评价及分数分界点确定方法。",
        "自陈量表和投射测验": "押题1【论述】比较人格测验中自陈量表和投射测验的优缺点。",
        "认知诊断的含义": "押题1【论述】论述认知诊断的含义、核心概念及基本流程。",
    }
    for fragment, title in type_changes.items():
        text = update_question(text, fragment, retitle(title))

    text = update_question(
        text,
        "心理测验结果",
        retitle("押题1【简答】简述心理测验分数解释和结果报告的基本要求。"),
    )
    text = update_question(
        text,
        "罗夏克墨迹测验、主题统觉测验",
        retitle("押题2【简答】简述人格测量中的常见投射测验和内隐测验。"),
    )

    text = update_question(
        text,
        "内容效度的含义、验证方法",
        lambda block: replace_last_module(
            block,
            3,
            "（相关概念：表面效度是测验使用者主观认为测验有效的程度，不属于真正的效度证据；它有助于取得被试合作，职业兴趣和成就测验宜重视，人格测验则不宜过高。）",
        ),
    )

    text = update_question(
        text,
        "项目难度对测验的影响",
        lambda block: replace_last_module(
            block,
            3,
            "（区分度具有相对性，其数值会受到计算方法、样本容量、分组标准和被试样本同质性程度的影响。）",
        ),
    )

    text = update_question(
        text,
        "人格测量的**含义",
        lambda block: replace_last_module(
            block,
            4,
            "（应对上述问题，可插入说谎量表检查防卫性反应，也可用投射测验补充自陈资料，但投射结果较难量化且解释较主观。）",
        ),
    )

    def self_report_bias(block: str) -> str:
        pattern = r"\n2\. 反应偏差产生的原因包括：.*?(?=\n\n3\. 主要应对方法包括：)"
        replacement = "\n（这些偏差可能来自人格特质的社会评价色彩、被试自我认识不清、无意识防卫以及问卷备选项过少。）"
        revised, count = re.subn(pattern, replacement, block, count=1, flags=re.DOTALL)
        assert count == 1
        revised = revised.replace("\n\n3. 主要应对方法包括：", "\n\n2. 主要应对方法包括：", 1)
        return revised

    text = update_question(text, "人格自陈量表常见的", self_report_bias)
    return text


def main() -> None:
    outputs = (
        (GENERAL_OUTPUT, build_general()),
        (EXPERIMENT_OUTPUT, build_experiment()),
        (MEASUREMENT_OUTPUT, build_measurement()),
    )
    for path, content in outputs:
        path.write_text(content, encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
