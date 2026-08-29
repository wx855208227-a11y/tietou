from __future__ import annotations

from pathlib import Path
import re

from shenzhen_baoming_canonical import canonicalize_definitions


ROOT = Path(__file__).resolve().parents[1]

GENERAL_SOURCE = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V3.md"
EXPERIMENT_SOURCE = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V2.md"
MEASUREMENT_SOURCE = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V2.md"

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V4.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V3.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V3.md"


FIRST_QUESTION = r"""### 押题1【简答】简述心理学的**研究对象**，并说明**心理与行为的关系**。

1. 心理学是主要研究**人的心理和行为**的科学。（心理学既研究人的心理，也研究行为；人的心理主要包括**认知、动机和情绪、心理特征**等方面。）【名词解释：心理学】

（1）**认知**：是指**获得或应用知识**的过程，或**信息加工**的过程。（主要包括**感觉、知觉、记忆、思维和语言**等。）【名词解释：认知】

（2）**动机和情绪**：

①动机是由目标或对象**引导、激发和维持个体活动**，使活动朝向某一目标的内部动力。（动机以需要为基础，并受环境诱因影响。）【名词解释：动机】

②情绪是个体对外界刺激的一种**生理和心理反应**，由主观体验、外部表现和生理唤醒三种成分组成。（情绪反映客观事物与个体需要之间的关系。）【名词解释：情绪】

（3）**心理特征**：是个体**稳固且经常出现**的心理特点，主要包括**智力和人格**。（心理特征使不同个体在相同情境中可能表现出不同的心理和行为。）

2. 行为是由一系列**反应动作和活动**构成的反应系统，总是在**一定的刺激情境**下产生。（行为是心理活动可以观察和测量的外部表现。）【名词解释：行为】

3. **心理与行为的关系**：行为不同于心理，但二者有密切联系；**心理支配行为，又通过行为表现出来**。（研究者可以根据可观察的行为推测内部心理活动，但不能把心理简单等同于行为。）

综上，心理学通过研究人的心理和行为，揭示二者在具体情境中的联系及其活动规律。
"""


# Each tuple is (new task-module sentence, original top-level point numbers).
# A None sentence keeps every listed point at the top level.  A sentence demotes
# the listed points to genuine children of that task module.
GENERAL_GROUPS: dict[str, list[tuple[str | None, tuple[int, ...]]]] = {
    "基本任务**及其**学科性质": [
        ("**心理学的基本任务包括：**", (1, 2, 3, 4)),
        ("**心理学的学科性质主要表现为：**", (5, 6)),
    ],
    "主要研究方法，并指出哪些方法可以获得": [
        ("**心理学的主要研究方法包括：**", (1, 2, 3, 4)),
        (None, (5,)),
    ],
    "自然观察法和实验法**的含义、优缺点及适用范围": [
        ("**观察法的含义、优点和局限如下：**", (1, 2, 3)),
        ("**实验法的含义、优点和局限如下：**", (4, 5, 6)),
        (None, (7, 8)),
    ],
    "因果关系和相关关系**，并说明解释相关结果": [
        ("**因果关系与相关关系的基本含义如下：**", (1, 2)),
        ("**解释相关结果时应注意：**", (3, 4, 5)),
        (None, (6,)),
    ],
    "神经元的**结构、功能和分类**": [
        (None, (1, 2, 3)),
        ("**神经冲动的传导方式如下：**", (4, 5, 6)),
    ],
    "中枢神经系统和周围神经系统": [
        ("**中枢神经系统的主要结构及功能如下：**", (1, 2, 3, 4, 5)),
        (None, (6,)),
    ],
    "大脑皮层的主要机能分区": [
        ("**大脑皮层的主要机能分区如下：**", (1, 2, 3, 4)),
        ("**大脑两半球的功能单侧化及协同关系如下：**", (5, 6)),
    ],
    "感觉的基本现象，并比较": [
        ("**感觉的基本现象主要包括：**", (1, 2, 3, 4)),
        ("**感觉适应、感觉对比和感觉相互作用的比较如下：**", (5, 6)),
    ],
    "声音的心理维度和声音掩蔽，并比较主要的": [
        ("**声音的主要心理维度如下：**", (1, 2)),
        (None, (6,)),
        ("**主要音高理论如下：**", (3, 4, 5)),
        (None, (7,)),
    ],
    "知觉组织的主要原则，并说明形状知觉": [
        ("**知觉组织的主要原则如下：**", (3, 4, 5)),
        ("**形状知觉的基本过程如下：**", (1, 2, 6)),
    ],
    "意识的含义、功能及主要无意识现象": [
        ("**意识的主要功能如下：**", (1, 2, 3)),
        ("**主要无意识现象如下：**", (4, 5, 6, 7)),
    ],
    "注意的含义、功能及主要种类": [
        ("**注意的主要功能如下：**", (1, 2, 3, 4)),
        ("**注意的主要种类如下：**", (5, 6, 7, 8)),
    ],
    "结合实验论述选择性注意理论": [
        ("**选择性注意理论的主要观点及其实验依据如下：**", (1, 2, 3, 4, 6)),
        ("**各理论的联系与区别如下：**", (5, 7)),
    ],
    "注意分配的**认知资源理论和双加工理论": [
        ("**认知资源理论的主要观点如下：**", (1, 2)),
        ("**双加工理论的主要观点如下：**", (3, 4, 5)),
        ("**两种理论的联系与区别如下：**", (6, 7)),
    ],
    "感觉记忆、短时记忆和长时记忆的特点": [
        ("**感觉记忆的主要特点如下：**", (1, 2)),
        ("**短时记忆的主要特点如下：**", (3, 4)),
        (None, (5,)),
        ("**三类记忆的转化及理论发展如下：**", (6, 7)),
        (None, (8,)),
    ],
    "长时记忆的编码、存储和提取": [
        ("**长时记忆的编码及影响因素如下：**", (1, 2)),
        ("**长时记忆的存储变化如下：**", (3, 4)),
        ("**长时记忆的提取方式及影响因素如下：**", (5, 6, 7)),
    ],
    "结合实例论述遗忘的原因": [
        ("**遗忘的主要原因及相应减少方法如下：**", (1, 2, 3, 4, 5, 6, 7)),
        (None, (8,)),
    ],
    "思维的含义、基本特征、主要种类和基本过程": [
        ("**思维的基本特征如下：**", (1, 2)),
        ("**思维的主要种类如下：**", (3, 4, 5)),
        (None, (6,)),
    ],
    "表象的含义、特征、作用及双重编码理论": [
        ("**表象的主要特征如下：**", (1, 2, 3)),
        (None, (4,)),
        ("**双重编码理论的主要观点如下：**", (5, 6)),
    ],
    "概念的含义、构成、功能、种类及形成理论": [
        (None, (1,)),
        ("**概念的主要种类如下：**", (2, 3)),
        ("**概念形成的主要理论如下：**", (4, 5, 6)),
    ],
    "演绎推理和归纳推理的含义": [
        ("**演绎推理的含义及主要形式如下：**", (1, 2, 3)),
        (None, (4,)),
        ("**演绎推理与归纳推理的关系如下：**", (5, 6, 7)),
    ],
    "问题解决的含义、主要策略及影响因素": [
        ("**问题解决的主要策略如下：**", (1, 2, 3)),
        ("**影响问题解决的主要因素如下：**", (4, 5, 6, 7, 8)),
    ],
    "决策的主要理论，并说明常见启发式": [
        ("**决策的主要理论如下：**", (1, 2, 3, 4)),
        ("**常见启发式策略及其偏差如下：**", (5, 6, 7, 8)),
        (None, (9,)),
    ],
    "语言的含义、基本特征及转换生成语法": [
        ("**语言的基本特征如下：**", (1, 2, 3, 4)),
        ("**转换生成语法理论的主要观点如下：**", (5, 6)),
    ],
    "语言加工的主要脑区、失语症表现及脑网络观": [
        ("**语言加工的主要脑区及相关失语症表现如下：**", (1, 2, 3)),
        ("**语言加工的脑模型与脑网络观如下：**", (4, 5, 6)),
    ],
    "动机的含义、主要功能和分类": [
        ("**动机的主要功能如下：**", (1, 2, 3)),
        ("**动机的主要分类如下：**", (4, 5, 6, 7)),
    ],
    "耶克斯—道德森定律，并说明": [
        ("**耶克斯—道德森定律的主要内容如下：**", (1, 2, 3)),
        ("**对学习和工作的启示如下：**", (4, 5)),
    ],
    "马斯洛需要层次理论的主要内容": [
        ("**马斯洛需要层次理论的主要内容如下：**", (1, 2, 3, 4, 5)),
        (None, (6, 7, 8)),
    ],
    "阿特金森成就动机理论": [
        ("**阿特金森成就动机理论的主要观点如下：**", (1, 2)),
        ("**力求成功者与避免失败者的比较如下：**", (3, 4, 7)),
        ("**理论评价如下：**", (5, 6)),
    ],
    "归因如何影响个体的情绪": [
        ("**归因对情绪、期待和后续行为的影响如下：**", (1, 2, 3, 4, 5)),
        (None, (6,)),
    ],
    "主要学习动机理论，并说明如何培养": [
        ("**主要学习动机理论如下：**", (1, 2, 3, 4, 5)),
        ("**培养和激发学习动机的方法如下：**", (6, 7, 8, 9)),
    ],
    "情绪的主要维度、种类及典型情绪状态": [
        (None, (1,)),
        ("**情绪的主要种类如下：**", (2, 3, 4)),
        ("**典型情绪状态如下：**", (5, 6, 7)),
    ],
    "情绪产生的主要理论，并比较": [
        ("**情绪产生的主要理论如下：**", (1, 2, 3, 4, 5, 6)),
        ("**各理论的联系与区别如下：**", (7, 8)),
    ],
    "情绪调节的含义、理论和主要策略": [
        (None, (1,)),
        ("**情绪调节的主要理论如下：**", (2, 3, 4)),
        ("**情绪调节的主要策略如下：**", (5, 6, 7, 8, 9)),
    ],
    "智力发展的一般趋势、个体差异及主要影响因素": [
        ("**智力发展的一般趋势如下：**", (1, 2, 3)),
        ("**智力发展的个体差异如下：**", (4, 5, 6, 7)),
        ("**影响智力发展的主要因素如下：**", (8, 9, 10)),
    ],
    "人格的含义、基本特性和主要结构": [
        ("**人格的基本特性如下：**", (1, 2, 3, 4)),
        ("**人格的主要结构如下：**", (5, 6, 7, 8, 9)),
    ],
    "弗洛伊德关于人格结构": [
        ("**弗洛伊德的人格结构观点如下：**", (1, 2, 3, 4)),
        (None, (5,)),
        ("**弗洛伊德的人格发展观点如下：**", (6, 7)),
        ("**弗洛伊德的心理防御机制观点如下：**", (8, 9)),
        (None, (10,)),
    ],
    "人本主义人格理论与班杜拉社会学习人格理论": [
        ("**人本主义人格理论的主要观点如下：**", (1, 2, 3)),
        ("**班杜拉社会学习人格理论的主要观点如下：**", (4, 5, 6, 7)),
        (None, (8,)),
    ],
    "主要人格特质理论，并说明大五人格": [
        ("**主要人格特质理论如下：**", (1, 2, 3, 4, 5, 6)),
        ("**大五人格模型的基本内容如下：**", (7, 8)),
        (None, (9,)),
    ],
    "人格测评的主要方法，并比较自陈量表": [
        ("**人格测评的主要方法如下：**", (1, 2, 3, 4, 5, 6)),
        (None, (7,)),
    ],
    "遗传、环境和自我因素在人格形成": [
        ("**遗传因素的作用如下：**", (1, 2)),
        ("**环境因素的作用如下：**", (3, 4, 5)),
        ("**自我因素的作用如下：**", (6, 7)),
        (None, (8,)),
    ],
    "学习的含义、基本特征和主要分类": [
        ("**学习的基本特征如下：**", (1, 2)),
        ("**学习的主要分类如下：**", (3, 4, 5, 6)),
    ],
    "学习进程的特点及提高学习效率": [
        ("**学习进程的主要特点如下：**", (1, 2, 3)),
        ("**提高学习效率的主要条件如下：**", (4, 5, 6)),
    ],
    "学习迁移的含义、类型及促进方法": [
        ("**学习迁移的主要类型如下：**", (1, 2, 3, 4, 5)),
        (None, (6,)),
    ],
    "经典条件作用的形成过程": [
        ("**经典条件作用的形成过程如下：**", (1, 2, 3)),
        ("**经典条件作用的主要规律如下：**", (4, 5, 6, 7, 8)),
        (None, (9, 10)),
    ],
    "操作性条件作用的基本原理": [
        ("**操作性条件作用的基本原理如下：**", (1, 2)),
        ("**操作性条件作用的主要规律如下：**", (3, 4, 5, 6, 7)),
        ("**操作性条件作用的教育应用如下：**", (8, 9, 10)),
    ],
    "观察学习的含义、基本过程和动机来源": [
        ("**观察学习的基本过程如下：**", (1, 2, 3, 4)),
        ("**观察学习的动机来源如下：**", (5, 6, 7)),
    ],
    "苛勒、托尔曼和建构主义学习理论": [
        ("**苛勒学习理论的主要观点如下：**", (1, 2)),
        ("**托尔曼学习理论的主要观点如下：**", (3, 4, 5)),
        ("**建构主义学习理论的主要观点如下：**", (6, 7, 8)),
    ],
    "认知学习的含义、种类和特点": [
        ("**认知学习的主要种类如下：**", (1, 2)),
        ("**认知学习的主要特点如下：**", (3, 4, 5)),
    ],
    "动作技能学习的含义、种类和形成特点": [
        ("**动作技能学习的主要种类如下：**", (1, 2, 3)),
        ("**动作技能学习的形成特点如下：**", (4, 5)),
    ],
    "语言发展的学习观、先天观和相互作用论": [
        ("**语言发展的学习观如下：**", (1, 2)),
        ("**语言发展的先天观如下：**", (3, 4, 5)),
        (None, (6, 7)),
    ],
    "皮亚杰的认知发展理论及其教育启示": [
        ("**皮亚杰认知发展理论的基本观点如下：**", (1, 2, 3, 4, 5)),
        ("**认知发展的四个阶段如下：**", (6, 7, 8, 9)),
        (None, (10, 11)),
    ],
    "依恋的发展阶段、主要类型及影响": [
        ("**依恋的发展阶段如下：**", (1, 2, 3, 4)),
        (None, (5, 6)),
    ],
    "皮亚杰和科尔伯格的道德认知发展理论": [
        ("**皮亚杰的道德认知发展理论如下：**", (1, 2, 3)),
        ("**科尔伯格的道德认知发展理论如下：**", (4, 5, 6, 7)),
        ("**两种理论的联系与区别如下：**", (8, 10)),
        (None, (9,)),
    ],
    "埃里克森心理社会性发展的八个阶段": [
        ("**埃里克森心理社会性发展的八个阶段如下：**", (1, 2, 3, 4, 5, 6, 7, 8)),
        (None, (9, 10)),
    ],
    "桑代克联结主义学习理论的基本观点和学习律": [
        (None, (1,)),
        ("**桑代克提出的主要学习律如下：**", (2, 3, 4)),
        (None, (5,)),
    ],
    "学习动机的强化理论与人本主义理论": [
        (None, (1,)),
        ("**人本主义学习动机理论的主要观点如下：**", (2, 3, 4, 5)),
        ("**两种理论的联系与区别如下：**", (6, 9)),
        ("**促进学生按时完成作业的方法如下：**", (7, 8)),
    ],
    "科温顿自我价值理论及其学生类型": [
        ("**科温顿划分的学生类型如下：**", (1, 2, 3, 4)),
        (None, (5,)),
    ],
    "促进聚焦与防御聚焦": [
        ("**促进聚焦的目标追求特点如下：**", (1, 2)),
        ("**防御聚焦的目标追求特点如下：**", (3, 4)),
        ("**二者的联系与区别如下：**", (5, 6)),
    ],
}


DROP_POINTS: dict[str, tuple[int, ...]] = {}


HEADING_REPLACEMENTS = {
    "### 押题1【简答】简述声音的心理维度，并比较主要的**音高理论**。":
        "### 押题1【简答】简述声音的心理维度和声音掩蔽，并比较主要的**音高理论**。",
    "### 押题1【简答】睡眠分为哪些阶段？各阶段有什么特点？":
        "### 押题1【论述】论述睡眠的主要阶段、周期规律和功能，并简述梦的主要解释。",
    "### 押题1【简答】什么是工作记忆？其核心成分有哪些？":
        "### 押题1【简答】什么是工作记忆？其核心成分、主要作用和常用测量任务有哪些？",
    "### 押题1【简答】简述思维的含义、基本特征和主要种类。":
        "### 押题1【简答】简述思维的含义、基本特征、主要种类和基本过程。",
    "### 押题1【论述】论述阿特金森成就动机理论，并比较力求成功者与避免失败者的行为特点。":
        "### 押题1【论述】论述并评价阿特金森成就动机理论，比较力求成功者与避免失败者的行为特点。",
    "### 押题1【论述】论述经典条件作用的形成过程、主要规律及其应用。":
        "### 押题1【论述】论述经典条件作用的形成过程、主要规律、应用及理论发展。",
    "### 押题2【简答】什么是归因？归因如何影响个体的情绪、期待和后续行为？":
        "### 押题2【简答】什么是归因？归因如何影响个体的情绪、期待和后续行为？并说明其教育启示。",
}


CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"


def question_ranges(text: str) -> list[tuple[re.Match[str], int]]:
    matches = list(re.finditer(r"^### 押题\d+【(?:简答|论述)】.*$", text, re.MULTILINE))
    result: list[tuple[re.Match[str], int]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        boundary = re.search(r"^#{1,2} ", text[match.end() : end], re.MULTILINE)
        result.append((match, match.end() + boundary.start() if boundary else end))
    return result


def replace_question(text: str, heading_fragment: str, new_block: str) -> str:
    hits = [item for item in question_ranges(text) if heading_fragment in item[0].group(0)]
    assert len(hits) == 1, (heading_fragment, len(hits))
    match, end = hits[0]
    suffix = "\n\n" if text[match.start() : end].endswith("\n\n") else "\n"
    return text[: match.start()] + new_block.strip() + suffix + text[end:]


def split_points(answer: str) -> tuple[str, dict[int, str], str]:
    matches = list(re.finditer(r"^(\d+)\.\s+", answer, re.MULTILINE))
    assert matches, answer[:160]
    summary = re.search(r"^综上，", answer, re.MULTILINE)
    assert summary, answer[-240:]
    points: dict[int, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else summary.start()
        if end > summary.start():
            end = summary.start()
        points[int(match.group(1))] = answer[match.start() : end].strip()
        if end == summary.start():
            break
    intro = answer[: matches[0].start()].strip()
    tail = answer[summary.start() :].strip()
    return intro, points, tail


def demote(chunk: str, child_number: int) -> str:
    lines = chunk.splitlines()
    lines[0] = re.sub(r"^\d+\.\s+", f"（{child_number}）", lines[0], count=1)
    secondary_counter = 0
    tertiary_counter = 0
    for index in range(1, len(lines)):
        if re.match(r"^（\d+）", lines[index]):
            secondary_counter += 1
            assert secondary_counter <= len(CIRCLED)
            lines[index] = re.sub(r"^（\d+）", CIRCLED[secondary_counter - 1], lines[index], count=1)
        elif re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]", lines[index]):
            tertiary_counter += 1
            lines[index] = re.sub(
                r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]",
                f"{chr(96 + tertiary_counter)}. ",
                lines[index],
                count=1,
            )
    return "\n".join(lines)


def renumber_top(chunk: str, number: int) -> str:
    return re.sub(r"^\d+\.\s+", f"{number}. ", chunk, count=1)


def regroup_answer(answer: str, groups: list[tuple[str | None, tuple[int, ...]]], drops: tuple[int, ...]) -> str:
    intro, points, tail = split_points(answer)
    used = {number for _, numbers in groups for number in numbers}
    assert used.isdisjoint(drops)
    assert used | set(drops) == set(points), (sorted(points), sorted(used), sorted(drops))

    rebuilt: list[str] = []
    top_number = 0
    for parent, numbers in groups:
        if parent is None:
            for number in numbers:
                top_number += 1
                rebuilt.append(renumber_top(points[number], top_number))
        else:
            top_number += 1
            rebuilt.append(f"{top_number}. {parent}")
            rebuilt.extend(demote(points[number], index) for index, number in enumerate(numbers, 1))
    return "\n\n".join(part for part in (intro, *rebuilt, tail) if part).strip()


def regroup_question(text: str, heading_fragment: str, groups: list[tuple[str | None, tuple[int, ...]]]) -> str:
    hits = [item for item in question_ranges(text) if heading_fragment in item[0].group(0)]
    assert len(hits) == 1, (heading_fragment, len(hits))
    match, end = hits[0]
    heading = match.group(0)
    answer = text[match.end() : end].strip()
    rebuilt = heading + "\n\n" + regroup_answer(answer, groups, DROP_POINTS.get(heading_fragment, ()))
    suffix = "\n\n" if text[match.start() : end].endswith("\n\n") else "\n"
    return text[: match.start()] + rebuilt + suffix + text[end:]


def update_frontmatter(text: str) -> str:
    return text.replace(
        "- `（）`内是扩容项，选背；用于丰富答题角度、锦上添花。如果其中是例子，可以根据题目灵活替换。",
        "- `（）`内是扩容项，选背；用于丰富答题角度、锦上添花。如果其中是例子，可以根据题目灵活替换。",
        1,
    )


def build_general() -> str:
    text = GENERAL_SOURCE.read_text(encoding="utf-8")
    text = replace_question(text, "心理学的**研究对象**", FIRST_QUESTION)
    for old, new in HEADING_REPLACEMENTS.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    for fragment, groups in GENERAL_GROUPS.items():
        text = regroup_question(text, fragment, groups)
    text = update_frontmatter(text)
    assert "个体性与社会性" not in text[
        text.index(FIRST_QUESTION.splitlines()[0]) : text.index("## 二、心理学的基本任务")
    ]
    return canonicalize_definitions(text)


def build_experiment() -> str:
    text = update_frontmatter(EXPERIMENT_SOURCE.read_text(encoding="utf-8"))
    old = (
        "（2）**内部效度**：指实验中自变量与因变量之间因果关系的明确程度，取决于额外变量控制是否充分。【名词解释：内部效度】\n"
        "（1）**主试—被试相互作用**"
    )
    new = old.replace("\n（1）", "\n①")
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    old = "（2）**其他威胁**：选择偏差、被试流失、成熟、历史、测验、统计回归和仪器变化等都会削弱因果解释。"
    assert text.count(old) == 1
    text = text.replace(old, old.replace("（2）", "②", 1), 1)
    return text


def build_measurement() -> str:
    return update_frontmatter(MEASUREMENT_SOURCE.read_text(encoding="utf-8"))


def main() -> None:
    for path, content in (
        (GENERAL_OUTPUT, build_general()),
        (EXPERIMENT_OUTPUT, build_experiment()),
        (MEASUREMENT_OUTPUT, build_measurement()),
    ):
        path.write_text(content, encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
