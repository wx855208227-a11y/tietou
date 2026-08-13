from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
INTRO_SOURCE = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_极简直背版V9.md"
EXPERIMENT_SOURCE = ROOT / "deliverables/华东师范大学347实验心理学保命手册_全本_极简直背版V1.md"
INTRO_OUTPUT = ROOT / "deliverables/华东师范大学347心理学导论保命手册_全本_任务适配精校版V10.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/华东师范大学347实验心理学保命手册_全本_任务适配精校版V2.md"


def plain(value: str) -> str:
    return value.replace("**", "").strip()


# 比较题不改写来源主体，只把既有分述收束为明确的“联系—区别”结论。
# 下列句子均由对应答案已经呈现的共同属性与差异维度归纳而来。
COMPARE_CONCLUSIONS = {
    "押题1【简答】比较构造主义与机能主义的研究对象与基本观点、研究重心和研究方法。":
        "综上，二者的**联系**在于都是科学心理学早期研究意识的重要流派；**区别**在于构造主义重在分析意识结构并主要采用内省法，机能主义重在解释心理功能且方法范围更广。",
    "押题1【简答】比较观察法、相关研究法和实验法的含义与优缺点。":
        "综上，三者的**联系**在于都是心理学研究心理与行为的基本方法；**区别**在于观察法重视自然描述，相关研究法重视关系与预测，实验法重视条件控制和因果解释。",
    "押题2【简答】比较信度与效度的含义，并说明信效度关系。":
        "综上，二者的**联系**在于都是评价心理测量质量的核心指标；**区别**在于信度强调结果的稳定性和一致性，效度强调测量的准确性和有效性，信度是效度的必要而非充分条件。",
    "押题2【简答】比较交感神经系统与副交感神经系统。":
        "综上，二者的**联系**在于都属于自主神经系统并共同维持机体平衡；**区别**在于交感神经提高机体唤醒并动员能量，副交感神经促进恢复并维持安静，二者作用方向通常相反。",
    "押题1【简答】比较丘脑与下丘脑的主要功能。":
        "综上，二者的**联系**在于都位于前脑并参与机体活动调节；**区别**在于丘脑主要承担感觉中转和初步加工，下丘脑主要调节动机、情绪、内分泌和内稳态。",
    "押题2【简答】比较海马与杏仁核在记忆和情绪中的作用。":
        "综上，二者的**联系**在于都是边缘系统的重要结构并共同参与经验形成；**区别**在于海马侧重事件内容和外显长时记忆，杏仁核侧重事件的情绪意义，尤其是恐惧信息。",
    "押题1【简答】比较脑功能定位说与整体说的主要观点和评价。":
        "综上，二者的**联系**在于都是解释脑如何承担心理功能的理论；**区别**在于定位说强调脑区的局部分工，整体说强调大脑整体协调作用，现代观点需要综合二者的合理成分。",
    "押题2【简答】比较无条件反射与条件反射的形成方式和功能特点。":
        "综上，二者的**联系**在于都是有机体对刺激作出的规律性反应并共同调节行为；**区别**在于无条件反射先天固定，条件反射后天习得且更加灵活。",
    "押题1【简答】比较第一信号系统与第二信号系统。":
        "综上，二者的**联系**在于都是条件反射系统，第二信号系统以第一信号系统为基础；**区别**在于第一信号系统以具体事物为信号，第二信号系统以言语文字为信号。",
    "押题1【简答】比较正强化、负强化、正惩罚和负惩罚。":
        "综上，四者的**联系**在于都通过行为后果调节行为频率；**区别**在于强化提高行为频率、惩罚降低行为频率，正负分别表示刺激的呈现与消除。",
    "押题1【论述】比较经典条件反射与操作条件反射的共同点与区别。":
        "综上，二者的**联系**在于都属于后天学习形成的条件反射并遵循强化、消退等一般规律；**区别**在于二者的反应性质、学习者角色、后果时序和联结性质不同。",
    "押题2【论述】结合实例说明经典条件反射与操作条件反射的区别。":
        "综上，二者的**联系**在于都通过经验建立新的刺激与行为联系；**区别**在于经典条件反射建立刺激—刺激联结，操作条件反射建立反应—结果联结。",
    "押题2【简答】比较认知地图与潜伏学习的含义及关系。":
        "综上，二者的**联系**在于都体现托尔曼对学习内部认知过程的重视；**区别**在于认知地图是学习形成的内部表征，潜伏学习强调学习可以在没有强化和外显行为的情况下发生。",
    "押题1【论述】比较注意选择的主要认知理论。":
        "综上，各理论的**联系**在于都试图解释有限加工能力下的信息选择；**区别**在于其对注意选择发生阶段以及未被注意信息加工深度的判断不同。",
    "押题1【简答】比较颜色视觉的三色说与对立过程说。":
        "综上，二者的**联系**在于都用于解释颜色视觉并可相互补充；**区别**在于三色说强调三类感受器活动，对立过程说强调红—绿、黄—蓝、黑—白系统的对立加工。",
    "押题1【简答】比较知觉中的自下而上加工与自上而下加工。":
        "综上，二者的**联系**在于共同参与完整知觉；**区别**在于自下而上加工由感觉刺激驱动并提供知觉材料，自上而下加工由知识经验和期待驱动并赋予材料意义。",
    "押题1【论述】比较模式识别的主要理论。":
        "综上，各理论的**联系**在于都用输入刺激与头脑表征的匹配解释模式识别；**区别**在于模板匹配强调整体模板，原型匹配强调类别原型，特征匹配强调基本特征。",
    "押题2【简答】比较感觉记忆、短时记忆和长时记忆。":
        "综上，三者的**联系**在于构成相互衔接的信息加工系统；**区别**在于保持时间、容量和主要编码方式不同，并通过注意、复述和提取发生联系。",
    "押题1【简答】比较概念组织的层次网络模型与激活扩散模型。":
        "综上，二者的**联系**在于都以网络解释语义记忆中的概念组织；**区别**在于层次网络模型突出类属层级，激活扩散模型突出语义联系和激活传播。",
    "押题1【简答】比较演绎推理和归纳推理，并说明演绎推理的主要形式。":
        "综上，二者的**联系**在于都是由已有判断推出新结论的推理形式；**区别**在于演绎推理由一般前提推出特殊结论且强调必然性，归纳推理由特殊事例概括一般规律且结论具有或然性。",
    "押题1【简答】比较语言与言语，并说明言语的主要功能和特征。":
        "综上，二者的**联系**在于言语是个体运用语言进行思考和交往的过程；**区别**在于语言是社会共享且相对稳定的符号系统，言语是个人的、具体的动态运用。",
    "押题1【论述】比较言语发展的条件作用理论、先天言语生成说和关键期理论。":
        "综上，三种理论的**联系**在于都解释儿童语言获得；**区别**在于分别强调后天强化与模仿、先天语言机制以及语言发展的成熟时机。",
    "押题1【简答】比较詹姆斯—朗格理论与坎农—巴德理论。":
        "综上，二者的**联系**在于都从生理变化与情绪体验的关系解释情绪；**区别**在于詹姆斯—朗格理论强调外周生理反馈先于情绪体验，坎农—巴德理论强调中枢加工使生理变化与情绪体验同时产生。",
    "押题1【论述】比较情绪的认知评价理论与情绪三因素理论。":
        "综上，二者的**联系**在于都强调认知解释是情绪形成的重要条件；**区别**在于认知评价理论突出对事件意义的评价，情绪三因素理论强调认知、生理状态和环境因素的共同作用。",
    "押题1【简答】比较驱力理论、唤醒理论和诱因理论。":
        "综上，三种理论的**联系**在于都解释行为动力；**区别**在于驱力理论强调内部紧张的降低，唤醒理论强调维持最佳唤醒水平，诱因理论强调外部目标的吸引作用。",
    "押题1【论述】论述自我决定理论，并比较掌握目标与成绩目标。":
        "综上，两类理论的**联系**在于都解释个体行为的动机取向；**区别**在于自我决定理论强调动机由外控走向内化的连续变化，成就目标理论区分掌握知识能力与追求名次成绩两种目标。",
    "押题1【简答】简述技能的含义，并比较技能与知识、习惯的关系。":
        "综上，三者的**联系**在于知识为技能形成提供认知基础，练习使技能趋于自动化并可能形成熟练；**区别**在于知识是经验的概括，技能是合乎法则的操作活动方式，习惯则具有需要被打破的倾向。",
    "押题1【论述】比较智力的主要因素理论和结构理论。":
        "综上，各理论的**联系**在于都试图说明智力的组成及组织方式；**区别**在于因素理论强调一般因素与特殊能力，结构理论进一步强调能力的层次、群组或多维组合。",
    "押题1【简答】简述性格的含义与结构，并比较性格与气质。":
        "综上，二者的**联系**在于都属于稳定的人格特征并相互影响；**区别**在于气质更多体现先天的动力特点，性格更多体现后天形成且具有社会道德评价意义的行为风格。",
    "押题1【论述】比较奥尔波特、卡特尔、艾森克及大五人格特质理论。":
        "综上，各理论的**联系**在于都以相对稳定的特质解释行为一致性；**区别**在于其对特质层次、来源及基本维度数量的划分不同。",
    "押题1【论述】比较阿德勒、荣格和埃里克森的人格理论。":
        "综上，三种理论的**联系**在于都在精神分析传统上更重视社会关系、个体成长和人格发展；**区别**在于阿德勒强调自卑与追求优越，荣格强调集体无意识与人格整合，埃里克森强调毕生发展的心理社会危机。",
    "押题1【简答】比较人格评鉴中的自陈量表与投射测验。":
        "综上，二者的**联系**在于都是人格评鉴的重要工具；**区别**在于自陈量表采用结构化题目和相对客观的计分，投射测验采用模糊刺激和自由反应且解释更依赖专业判断。",
    "押题1【论述】比较社会归因的主要理论。":
        "综上，各理论的**联系**在于都解释人们如何推断行为原因；**区别**在于分别侧重内外因素、行为信息、协变线索以及成败原因维度。",
    "押题1【论述】比较从众与服从，并说明二者的主要影响因素。":
        "综上，二者的**联系**在于都属于社会影响下的行为改变；**区别**在于从众主要源于多数群体压力，服从主要源于权威命令，二者的具体影响因素也不同。",
    "押题1【论述】比较观察法、相关研究法和实验法的含义、优点及局限。":
        "综上，三者的**联系**在于都是收集心理与行为证据的研究方法；**区别**在于观察法侧重描述，相关研究法侧重共变关系，实验法侧重控制条件下的因果检验。",
    "押题1【论述】比较被试间设计、被试内设计和混合设计。":
        "综上，三者的**联系**在于都是安排被试接受实验处理的设计方式；**区别**在于被试间设计使每名被试只接受一个水平，被试内设计使同一被试接受全部水平，混合设计则对不同自变量分别采用两种安排。",
    "押题1【简答】比较准实验设计与真实验设计。":
        "综上，二者的**联系**在于都通过比较条件考察变量关系；**区别**在于真实验依靠严格控制和随机化获得较强因果推论，准实验以较弱控制换取现实可行性。",
    "押题1【简答】比较反应时研究中的减数法与加因素法。":
        "综上，二者的**联系**在于都利用反应时推断信息加工阶段；**区别**在于减数法通过任务反应时相减分离加工时间，加因素法通过因素效应的相加或交互关系识别加工阶段。",
    "押题1【简答】比较费希纳定律和史蒂文斯定律。":
        "综上，二者的**联系**在于都描述心理量与物理量的函数关系并推动感觉量化；**区别**在于费希纳定律以间接阈限测量建立对数关系，史蒂文斯定律以直接数量估计建立幂函数关系。",
    "押题1【简答】比较直接知觉论与间接知觉论，并说明相应实验证据。":
        "综上，二者的**联系**在于都解释外界刺激如何形成知觉；**区别**在于直接知觉论强调刺激信息的充分性，间接知觉论强调过去经验和推断，二者分别得到相应实验现象支持。",
    "押题1【论述】简述推理的主要形式，并比较期望效用理论与前景理论。":
        "综上，二者的**联系**在于都解释方案选择和结果评价；**区别**在于期望效用理论提供完全理性的规范性标准，前景理论解释现实决策中的参照依赖、损失厌恶和风险偏好变化。",
    "押题1【简答】比较情绪研究中的刺激—反应法与情绪诱导法。":
        "综上，二者的**联系**在于都通过可观察刺激、行为和生理指标研究内部情绪；**区别**在于刺激—反应法由刺激与反应联系间接推断情绪，情绪诱导法直接操纵情绪状态并考察其后续影响。",
    "押题1【简答】比较脑电图技术（EEG）与事件相关电位（ERP）。":
        "综上，二者的**联系**在于都以头皮脑电位记录为基础，具有高时间分辨率和低空间分辨率；**区别**在于EEG侧重直接记录脑电位，ERP通过多次叠加平均提取与特定事件相关的认知信号。",
    "押题1【论述】比较MRI/fMRI、fNIRS、MEG和PET的基本原理及优缺点。":
        "综上，各技术的**联系**在于都用于反映神经活动；**区别**在于其信号来源、时间与空间分辨率、是否无创、可重复性、被试限制和造价不同，应依据研究问题选择。",
}


# 只对“同一题中存在两个以上任务、原答案却把叶子采分点平铺”为同级的
# 代表性答案重新分层。键为题目纯文本，值为“任务模块标题—旧一级序号”。
EXPERIMENT_GROUPS = {
    "押题1【简答】简述自变量的主要类型及其操纵方法。": [
        ("自变量的**主要类型**包括：", (1, 2, 3)),
        ("自变量的**操纵方法**主要包括：", (4, 5)),
    ],
    "押题1【论述】论述控制变量的主要来源及其控制方法。": [
        ("控制变量的**主要来源**包括：", (1, 2, 3, 4, 5)),
        ("控制变量的**控制方法**主要包括：", (6, 7, 8, 9, 10, 11)),
    ],
    "押题1【论述】论述多变量实验设计的含义、优缺点及结果解释。": [
        ("多变量实验设计的**主要类型**包括：", (1, 2)),
        ("多变量实验设计的**优缺点**如下：", (3, 4)),
        ("多变量实验结果的**解释要点**包括：", (5, 6)),
    ],
    "押题1【简答】简述反应时的主要影响因素，并说明速度—准确性权衡。": [
        ("反应时的**主要影响因素**包括：", (1, 2, 3, 4, 5, 6)),
        ("研究反应时时应处理好**速度—准确性权衡**：", (7,)),
    ],
    "押题1【论述】论述感觉阈限的含义、传统测量方法及主要误差。": [
        ("感觉阈限的**传统测量方法**包括：", (1, 2, 3)),
        ("传统心理物理法的**主要误差**包括：", (4, 5)),
        ("三种传统测量方法的**比较**如下：", (6, 7)),
    ],
    "押题1【论述】论述信号检测论的基本思想、核心指标及实验方法。": [
        ("信号检测论的**基本思想**包括：", (1, 2, 3)),
        ("信号检测论的**核心指标及其关系**如下：", (4,)),
        ("信号检测论的**实验方法**包括：", (5, 6, 7)),
        ("信号检测论的**主要价值**在于：", (8,)),
    ],
    "押题1【简答】简述韦伯定律和费希纳定律的主要内容及关系。": [
        ("**韦伯定律**的主要内容包括：", (1, 2)),
        ("韦伯定律与费希纳定律的**关系及成立条件**如下：", (3, 4, 5)),
    ],
    "押题1【简答】简述警戒的含义、测量指标及应用。": [
        ("警戒的**测量指标及影响表现**包括：", (1, 2, 3)),
        ("警戒研究的**应用**包括：", (4, 5)),
    ],
    "押题1【简答】简述无觉察知觉的含义、证据及实验逻辑。": [
        ("无觉察知觉的**主要证据**包括：", (1, 2)),
        ("无觉察知觉的**实验逻辑与控制要求**包括：", (3, 4, 5, 6, 7)),
    ],
    "押题1【论述】论述记忆与学习的早期研究及传统测量方法。": [
        ("记忆与学习的**早期研究**包括：", (1, 2, 3, 4)),
        ("记忆与学习的**传统测量方法**包括：", (5, 6, 7, 8)),
    ],
    "押题1【论述】论述内隐记忆的主要研究证据及理论解释。": [
        ("内隐记忆的**主要研究证据**包括：", (1, 2, 3)),
        ("内隐记忆的**理论解释**包括：", (4, 5, 6, 7)),
    ],
    "押题1【简答】简述内隐学习的含义、特征及研究范式。": [
        ("内隐学习的**主要特征**包括：", (1, 2, 3, 4, 5)),
        ("内隐学习的**研究范式**包括：", (6, 7, 8, 9)),
    ],
    "押题1【简答】简述概念形成的假设检验说及功能固着研究。": [
        ("概念形成的**假设检验说及其实验支持**如下：", (1, 2, 3)),
        ("**功能固着研究**的设计要点包括：", (4, 5)),
    ],
    "押题1【论述】简述推理的主要形式，并比较期望效用理论与前景理论。": [
        ("推理的**主要形式及常见偏差**包括：", (1, 2, 3, 4)),
        ("期望效用理论与前景理论的**核心观点**如下：", (5, 6, 7, 8, 9)),
    ],
}


def split_questions(text: str) -> list[str]:
    return re.split(r"(?=^### 押题)", text, flags=re.M)


def replace_compare_conclusion(block: str) -> str:
    key = plain(block.splitlines()[0]).removeprefix("### ")
    synthesis = COMPARE_CONCLUSIONS.get(key)
    if synthesis is None:
        return block

    conclusion_match = re.search(r"^综上，.*$", block, flags=re.M)
    if conclusion_match is None:
        raise ValueError(f"比较题缺少唯一总结句：{key}")
    contact_marker = "**联系**在于"
    difference_marker = "；**区别**在于"
    if contact_marker not in synthesis or difference_marker not in synthesis:
        raise ValueError(f"比较题综合结论格式错误：{key}")
    contact = synthesis.split(contact_marker, 1)[1].split(difference_marker, 1)[0]
    difference = synthesis.split(difference_marker, 1)[1].removesuffix("。")

    numbered_lines = [
        line for line in block.splitlines() if re.match(r"^\d+\.\s", line)
    ]
    next_number = max(int(re.match(r"^(\d+)", line).group(1)) for line in numbered_lines) + 1
    has_contact = any(
        re.match(r"^\d+\.\s", line)
        and any(marker in plain(line) for marker in ("共同点", "基本联系", "三者关系", "二者关系"))
        for line in block.splitlines()
    )
    has_difference = any(
        re.match(r"^\d+\.\s", line)
        and any(marker in plain(line) for marker in ("主要区别", "不同点", "二者区别", "三者区别"))
        for line in block.splitlines()
    )
    modules: list[str] = []
    if not has_contact:
        modules.append(f"{next_number}. **联系**：{contact}。")
        next_number += 1
    if not has_difference:
        modules.append(f"{next_number}. **主要区别**：{difference}。")

    if not modules:
        return block
    insertion = "\n\n".join(modules) + "\n\n"
    return block[: conclusion_match.start()] + insertion + block[conclusion_match.start() :]


def group_numbered_points(block: str) -> str:
    key = plain(block.splitlines()[0]).removeprefix("### ")
    groups = EXPERIMENT_GROUPS.get(key)
    if not groups:
        return block

    lines = block.splitlines()
    number_to_group: dict[int, tuple[int, int]] = {}
    for group_index, (_, old_numbers) in enumerate(groups, start=1):
        for local_index, old_number in enumerate(old_numbers, start=1):
            number_to_group[old_number] = (group_index, local_index)

    seen_groups: set[int] = set()
    result: list[str] = []
    active_group = 0
    for line in lines:
        match = re.match(r"^(\d+)\.\s+(.*)$", line)
        if match and int(match.group(1)) in number_to_group:
            old_number = int(match.group(1))
            group_index, local_index = number_to_group[old_number]
            if group_index not in seen_groups:
                if result and result[-1] != "":
                    result.append("")
                result.append(f"{group_index}. {groups[group_index - 1][0]}")
                result.append("")
                seen_groups.add(group_index)
            active_group = group_index
            result.append(f"（{local_index}）{match.group(2)}")
            continue

        # 原二级、三级随新的任务模块整体下沉一级。
        if active_group:
            secondary = re.match(r"^（(\d+)）(.*)$", line)
            if secondary:
                circled = "①②③④⑤⑥⑦⑧⑨⑩"[int(secondary.group(1)) - 1]
                result.append(f"{circled}{secondary.group(2)}")
                continue
            deep = re.match(r"^([①②③④⑤⑥⑦⑧⑨⑩])(.*)$", line)
            if deep:
                letter = "abcdefghij"["①②③④⑤⑥⑦⑧⑨⑩".index(deep.group(1))]
                result.append(f"{letter}. {deep.group(2)}")
                continue
        result.append(line)

    if seen_groups != set(range(1, len(groups) + 1)):
        raise ValueError(f"任务模块分组不完整：{key}")
    return "\n".join(result) + ("\n" if block.endswith("\n") else "")


def numbered_payload(lines: list[str], number: int) -> str:
    prefix = f"{number}. "
    matches = [line[len(prefix) :] for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"无法定位旧一级采分点{number}：{lines[0]}")
    return matches[0]


def restructure_dependent_variable(block: str) -> str:
    key = plain(block.splitlines()[0]).removeprefix("### ")
    if key != "押题1【简答】简述因变量的类型、指标选择标准及控制要求。":
        return block
    lines = block.splitlines()
    title = lines[0]
    definition = next(line for line in lines if line.startswith("因变量是"))
    range_definition = next(line for line in lines if line.startswith("量程限制是"))
    conclusion = next(line for line in lines if line.startswith("综上，"))
    suffix = lines[lines.index(conclusion) + 1 :]
    payloads = {number: numbered_payload(lines, number) for number in range(1, 7)}
    rebuilt = [
        title, "", definition, "",
        "1. 因变量的**指标类型**包括：", "", f"（1）{payloads[1]}", "",
        "2. 因变量的**指标选择标准**包括：", "",
        f"（1）{payloads[3]}", "", f"（2）{payloads[4]}", "", f"（3）{payloads[5]}", "",
        "3. 因变量的**控制要求**主要包括：", "",
        f"（1）{payloads[2]}", "", range_definition, "", f"（2）{payloads[6]}", "",
        conclusion,
    ] + suffix
    return "\n".join(rebuilt) + ("\n" if block.endswith("\n") else "")


def restructure_experiment_validity(block: str) -> str:
    key = plain(block.splitlines()[0]).removeprefix("### ")
    if key != "押题1【论述】论述实验的内部效度、外部效度及二者关系。":
        return block
    lines = block.splitlines()
    title = lines[0]
    total = next(line for line in lines if line.startswith("实验效度是"))
    internal = next(line for line in lines if line.startswith("内部效度是"))
    external = next(line for line in lines if line.startswith("外部效度是"))
    conclusion = next(line for line in lines if line.startswith("综上，"))
    suffix = lines[lines.index(conclusion) + 1 :]
    payloads = {number: numbered_payload(lines, number) for number in range(1, 8)}
    construct_optional = (
        "（构思效度是**变量关系构想的准确程度**，以及实验变量的**操作定义与推论时定义的一致程度**；"
        "它关注实验操作是否真正代表理论构念。）"
    )
    rebuilt = [
        title, "", total, "",
        "1. **内部效度及其影响因素**如下：", "", internal, "",
        f"（1）{payloads[1]}", "", f"（2）{payloads[2]}", "", f"（3）{payloads[3]}", "", f"（4）{payloads[4]}", "",
        "2. **外部效度及其影响因素**如下：", "", external, "", f"（1）{payloads[5]}", "",
        "3. 内部效度与外部效度的**关系及平衡原则**如下：", "",
        f"（1）{payloads[6]}", "", f"（2）{payloads[7]}{construct_optional}", "",
        conclusion,
    ] + suffix
    return "\n".join(rebuilt) + ("\n" if block.endswith("\n") else "")


def simplify_single_leaf_modules(block: str) -> str:
    return block.replace(
        "4. 信号检测论的**主要价值**在于：\n\n（1）**主要优势**：",
        "4. 信号检测论的**主要价值**在于：",
    )


def transform(text: str, *, version: str, experiment: bool) -> str:
    result = text
    result = re.sub(r"^## 全本·极简直背版V\d+$", f"## 全本·极简直背版{version}", result, count=1, flags=re.M)
    result = result.replace("（固定实验可灵活选用）", "")
    result = result.replace("，**具体方法可灵活替换**", "")
    result = result.replace("，具体方法可灵活替换", "")

    parts = split_questions(result)
    transformed = [parts[0]]
    for block in parts[1:]:
        if experiment:
            block = restructure_dependent_variable(block)
            block = restructure_experiment_validity(block)
            block = group_numbered_points(block)
            block = simplify_single_leaf_modules(block)
        block = replace_compare_conclusion(block)
        transformed.append(block)
    result = "".join(transformed)

    # 新答案仍完整沿用既有名解模块和扩容，不允许结构重组破坏标签段末规则。
    for line in result.splitlines():
        if "【名词解释：" in line and not line.endswith("】"):
            raise ValueError(f"名解标签后仍有正文：{line}")
    assert "固定实验可灵活选用" not in result
    assert "具体方法可灵活替换" not in result
    assert "答题思路" not in result
    assert "扩容（选" not in result
    return result


def main() -> None:
    intro = transform(INTRO_SOURCE.read_text(encoding="utf-8"), version="V10", experiment=False)
    experiment = transform(EXPERIMENT_SOURCE.read_text(encoding="utf-8"), version="V2", experiment=True)
    INTRO_OUTPUT.write_text(intro, encoding="utf-8")
    EXPERIMENT_OUTPUT.write_text(experiment, encoding="utf-8")
    print(f"已生成：{INTRO_OUTPUT}")
    print(f"已生成：{EXPERIMENT_OUTPUT}")


if __name__ == "__main__":
    main()
