from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path


OUTPUT = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_分层扩容均衡版V14.md")
BASE_SCRIPT = Path(__file__).with_name("build_baoming_v13.py")


def load_base():
    spec = importlib.util.spec_from_file_location("baoming_v13_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取底稿：{BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base()


@dataclass(frozen=True)
class AnswerLine:
    level: int
    text: str
    expansions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Question:
    kind: str
    stem: str
    lines: tuple[AnswerLine, ...]
    final_expansions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Unit:
    title: str
    level: str
    questions: tuple[Question, ...]


def L(level: int, text: str, *expansions: str) -> AnswerLine:
    return AnswerLine(level, text, tuple(clean_expansion(item) for item in expansions))


def clean_expansion(text: str) -> str:
    text = re.sub(r"^【扩容（选用）：|】$", "", text.strip())
    text = text.replace("（例子可按题干灵活替换）", "（例子可灵活替换）")
    text = text.replace("（固定实验可按题干灵活选写）", "（固定实验可灵活选用）")
    text = re.sub(r"\s+", " ", text).strip()
    if not text.endswith(("。", "！", "？")):
        text += "。"
    return text


def expansion(text: str) -> str:
    return f"【扩容（选用）：{clean_expansion(text)}】"


def q13(chapter: int, unit: int, question: int):
    return BASE.CHAPTERS[chapter][1][unit].questions[question]


def generic_question(item) -> Question:
    lines: list[AnswerLine] = []
    if len(item.leads) == 1:
        module = item.leads[0]
        lines.append(L(0, module.base, *(module.expansion,) if module.expansion else ()))
    else:
        for module in item.leads:
            lines.append(L(1, module.base, *(module.expansion,) if module.expansion else ()))
    for module in item.points:
        lines.append(L(1, module.base, *(module.expansion,) if module.expansion else ()))
    return Question(
        item.kind,
        item.stem,
        tuple(lines),
        tuple(clean_expansion(text) for text in item.final_expansions),
    )


PSYCHOLOGY_DEFINITION = q13(0, 0, 0).leads[0].base

PSYCHOLOGY_OVERVIEW = Question(
    "简答",
    "简述心理学的**含义、研究对象及基本构成**。",
    (
        L(0, PSYCHOLOGY_DEFINITION),
        L(
            1,
            "**研究对象和基本构成**：人的心理现象由**心理过程**和**人格**两个方面构成，这也是心理学的主要研究对象。",
        ),
        L(
            1,
            "**心理过程**：反映心理活动的发生和变化，包括**认知过程、情绪情感过程和意志过程**。",
        ),
        L(
            1,
            "**人格**：反映个体稳定而独特的心理面貌，包括**心理动力**和**心理特征**。",
        ),
    ),
    (
        clean_expansion(
            "心理过程体现心理活动的动态过程，人格体现心理活动的稳定特征，二者共同构成人的心理现象。"
        ),
    ),
)

PSYCHOLOGY_STRUCTURE = Question(
    "简答",
    "简述**心理过程**和**人格**各自的构成，并说明**心理过程与人格的关系**。",
    (
        L(1, "**心理过程的构成**：心理过程包括**认知过程、情绪情感过程和意志过程**。"),
        L(
            2,
            "**认知过程**：指对信息进行加工处理的过程。",
            "包括**感觉、知觉、记忆、思维和想象**。",
        ),
        L(2, "**情绪情感过程**：指人脑对**客观事物是否满足需要**而产生的态度体验。"),
        L(2, "**意志过程**：指人自觉地确定目的，**克服内外部困难**，力求实现预定目的的心理过程。"),
        L(
            0,
            "",
            "认知、情绪情感和意志是**同一心理过程的不同方面**，其中认知过程是最基本的心理活动。",
        ),
        L(
            1,
            "**人格的构成**：人格包括**心理动力**和**心理特征**。",
        ),
        L(
            2,
            "**心理动力**：指人对客观事物的态度及对活动对象的选择和趋向，是人从事活动的**指向性和基本动力**。",
            "主要包括**需要、动机、兴趣、理想和价值观**。",
        ),
        L(
            2,
            "**心理特征**：指人在认知、情绪情感和意志过程中形成的**稳定而经常表现出来的心理特点**，是个体多种心理特点的独特结合。",
            "主要包括**能力、气质和性格**。",
        ),
        L(
            1,
            "**心理过程与人格的关系**：心理过程反映心理活动的发生和变化，人格反映个体稳定而独特的心理面貌，二者共同构成人的心理现象。",
            "例如，面对重要考试时，考生先分析题目、产生紧张或期待的情绪，再克服困难完成作答；这些心理过程又会受到其动机、能力和性格的影响（例子可灵活替换）。",
        ),
    ),
    (
        clean_expansion(
            "综上所述，心理过程体现心理活动的动态过程，人格体现个体稳定而独特的心理面貌，二者相互联系，共同构成人的心理现象。"
        ),
    ),
)


SCIENCE_BIRTH = Question(
    "简答",
    "简述科学心理学的**产生背景、诞生标志及意义**。",
    (
        L(1, "**产生背景**：科学心理学的产生具有哲学、生理学和生物学三方面背景。"),
        L(2, q13(0, 1, 1).points[0].base),
        L(2, q13(0, 1, 1).points[1].base),
        L(2, q13(0, 1, 1).points[2].base),
        L(1, q13(0, 1, 1).points[3].base),
        L(
            1,
            "**意义**：实验研究进入心理学，使心理学逐步摆脱哲学思辨，走上**实验研究道路**并成为一门独立科学。",
        ),
    ),
)


BEHAVIORISM = Question(
    "简答",
    q13(0, 3, 0).stem,
    (
        L(0, q13(0, 3, 0).leads[0].base),
        L(1, q13(0, 3, 0).points[0].base),
        L(1, q13(0, 3, 0).points[1].base),
        L(1, "**评价**：行为主义既推动了心理学的客观化，也存在忽视内部心理过程的局限。"),
        L(
            2,
            q13(0, 3, 0).points[2].base,
            q13(0, 3, 0).points[2].expansion or "",
        ),
        L(2, q13(0, 3, 0).points[3].base),
    ),
)


PSYCHOANALYSIS_CORE = (
    L(
        1,
        "**基本观点**：精神分析强调无意识、早期经验、内部冲突和人格结构对行为的影响。",
    ),
    L(
        2,
        "**无意识与行为动力**：潜意识会不断影响人的行为，并可用生的本能、死的本能和**力比多**等观念解释行为动力。",
    ),
    L(2, q13(0, 5, 0).points[2].base),
    L(
        2,
        q13(0, 5, 0).points[4].base,
        q13(0, 5, 0).points[4].expansion or "",
    ),
    L(
        2,
        "**人格发展**：儿童期不同阶段的经验会影响人格发展。",
        "弗洛伊德将人格发展划分为**口唇期、肛门期、性器期、潜伏期和生殖期**，并提出恋父情结和恋母情结。",
    ),
    L(2, q13(0, 5, 0).points[5].base),
    L(1, q13(0, 5, 0).points[6].base),
)

PSYCHOANALYSIS_SHORT = Question(
    "简答",
    q13(0, 5, 0).stem,
    (L(0, q13(0, 5, 0).leads[0].base), *PSYCHOANALYSIS_CORE),
)

PSYCHOANALYSIS_ESSAY = Question(
    "论述",
    q13(0, 5, 1).stem,
    (
        L(0, q13(0, 5, 1).leads[0].base),
        *PSYCHOANALYSIS_CORE,
        L(1, q13(0, 5, 1).points[7].base),
        L(1, q13(0, 5, 1).points[8].base),
    ),
    (
        clean_expansion(
            "总体而言，精神分析拓展了心理学对无意识和人格动力的研究，但其部分核心命题难以进行客观验证。"
        ),
    ),
)


METHOD_COMPARISON = Question(
    "简答",
    q13(0, 8, 0).stem,
    (
        L(1, q13(0, 8, 0).leads[0].base),
        L(2, "**优点**：能够在自然情境中获得较真实的资料。"),
        L(
            2,
            "**缺点**：难以重复验证和精确分析，容易受到干扰，并且**无法确定因果关系**。",
            "观察中还可能出现**观察者效应和观察者偏差**。",
        ),
        L(1, q13(0, 8, 0).leads[1].base),
        L(2, "**优点**：能够预测心理现象，数量化指标明确，并可反映变量关系的方向和程度。"),
        L(2, "**缺点**：只能说明变量之间存在关联，**无法确定因果关系**。"),
        L(1, q13(0, 8, 0).leads[2].base),
        L(2, "**优点**：能够控制研究条件、重复验证，并可揭示变量之间的因果关系。"),
        L(
            2,
            "**缺点**：实验情境可能偏离真实生活，研究结果的**外部效度较低**。",
            "自然实验的外部效度较高，但条件控制较弱，结果不如实验室实验精确。",
        ),
    ),
)


BRANCH_APPLICATION = Question(
    "简答",
    q13(0, 12, 0).stem,
    (
        L(0, PSYCHOLOGY_DEFINITION, "其研究对象主要包括**心理过程**和**人格**。"),
        L(1, q13(0, 12, 0).points[0].base),
        L(1, q13(0, 12, 0).points[1].base),
        L(1, q13(0, 12, 0).points[2].base),
    ),
    (
        clean_expansion(q13(0, 12, 0).points[3].base),
    ),
)

BRANCH_OVERVIEW = Question(
    "简答",
    q13(0, 12, 1).stem,
    tuple(L(1, q13(0, 12, 1).points[index].base) for index in range(4)),
    (
        clean_expansion(
            "心理学的主要分支还包括**社会心理学、工业心理学和临床心理学**等，分别研究群体情境中的个体心理、工业活动中的人机关系以及心理异常的诊断与治疗。"
        ),
    ),
)


NEURON = Question(
    "简答",
    q13(1, 0, 0).stem,
    (
        L(0, q13(1, 0, 0).leads[0].base),
        L(1, q13(1, 0, 0).points[0].base),
        L(1, "**神经元的种类**：按功能可分为感觉神经元、运动神经元和联络神经元。"),
        L(2, q13(1, 0, 0).points[1].base),
        L(2, q13(1, 0, 0).points[2].base),
        L(
            2,
            q13(1, 0, 0).points[3].base,
            q13(1, 0, 0).points[3].expansion or "",
        ),
    ),
)


NEURAL_TRANSMISSION = Question(
    "简答",
    q13(1, 1, 1).stem,
    (
        L(0, q13(1, 1, 1).leads[0].base),
        L(1, "**神经元内传导**：神经冲动在神经元内以电传导方式进行。"),
        L(2, q13(1, 1, 1).leads[1].base),
        L(2, q13(1, 1, 1).leads[2].base),
        L(
            2,
            q13(1, 1, 1).points[0].base,
            q13(1, 1, 1).points[0].expansion or "",
        ),
        L(1, "**神经元间传导**：神经冲动在神经元之间主要通过突触进行化学传递。"),
        L(2, q13(1, 1, 1).leads[3].base),
        L(2, q13(1, 1, 1).points[1].base),
    ),
)


NERVOUS_SYSTEM = Question(
    "简答",
    q13(1, 2, 0).stem,
    (
        L(0, q13(1, 2, 0).points[0].base),
        L(1, q13(1, 2, 0).points[1].base),
        L(2, q13(1, 2, 0).points[2].base),
        L(2, q13(1, 2, 0).points[3].base),
        L(
            0,
            "",
            "自主神经系统中的交感神经激活器官活动、提高唤醒水平，副交感神经使机体恢复或维持安静状态，二者共同维持机体的适应和平衡。",
        ),
        L(1, q13(1, 2, 0).points[5].base),
        L(2, "**脊髓**：是脑与周围神经之间的信息中转站，也是简单反射的控制中心。"),
        L(
            2,
            "**脑**：主要对输入信息进行分析、综合，并发出相应的动作指令。",
            "脑还承担感觉整合、运动调节、觉醒、情绪和高级认知等功能。",
        ),
    ),
)


ASSOCIATION_CORTEX = Question(
    "简答",
    "简述皮层联合区的**类型及功能**。",
    (
        L(0, q13(1, 4, 1).leads[0].base),
        L(1, "**感觉联合区**：对不同感觉通道的信息进行综合加工。"),
        L(1, "**运动联合区**：参与复杂运动的组织、计划和协调。"),
        L(1, "**前额联合区**：参与计划、决策和行为控制等高级认知活动。"),
    ),
    (
        clean_expansion(
            "复杂言语活动由多个言语区和联合区**分工协作**完成，不能简单归因于单一脑区。"
        ),
    ),
)


REFLEX_SYSTEM = Question(
    "简答",
    q13(2, 1, 0).stem,
    (
        L(1, "**反射与反射弧**：反射活动以反射弧为生理基础。"),
        L(2, q13(2, 1, 0).leads[0].base),
        L(2, q13(2, 1, 0).leads[1].base),
        L(2, q13(2, 1, 0).points[0].base),
        L(1, "**反射的类型**：反射可分为无条件反射和条件反射。"),
        L(2, q13(2, 1, 0).leads[2].base),
        L(2, q13(2, 1, 0).leads[3].base),
    ),
    (
        clean_expansion(
            "无条件反射先天形成、联系固定，是条件反射建立的基础；条件反射后天习得、联系暂时，能够灵活适应环境变化。"
        ),
        clean_expansion(
            "例如，强光引起瞳孔收缩属于无条件反射，铃声与食物多次配对后引起唾液分泌属于条件反射（例子可灵活替换）。"
        ),
    ),
)


CLASSICAL_CONDITIONING = Question(
    "简答",
    q13(2, 2, 0).stem,
    (
        L(0, q13(2, 2, 0).leads[0].base),
        L(1, "**形成过程**：经典条件反射通过中性刺激与无条件刺激的反复配对建立。"),
        L(2, q13(2, 2, 0).points[0].base),
        L(2, q13(2, 2, 0).points[1].base),
        L(2, q13(2, 2, 0).points[2].base),
        L(1, q13(2, 2, 0).points[3].base),
    ),
)


CONDITIONING_LAWS = Question(
    "简答",
    q13(2, 3, 0).stem,
    (
        L(1, "**条件反射的建立与变化**：主要包括习得、泛化、分化、消退、延迟和二级条件作用。"),
        L(
            2,
            q13(2, 3, 0).leads[0].base,
            "条件刺激与无条件刺激的时间关系包括同时性、延迟性和痕迹性条件作用，其中**延迟性条件作用最容易形成**。",
        ),
        L(2, q13(2, 3, 0).leads[1].base),
        L(2, q13(2, 3, 0).leads[2].base),
        L(2, q13(2, 3, 0).leads[3].base),
        L(2, q13(2, 3, 0).leads[4].base),
        L(2, q13(2, 3, 0).leads[5].base),
    ),
    (
        clean_expansion(
            "泛化使反应扩展到相似刺激，分化使反应变得精确，二者共同提高条件反射的适应性。"
        ),
    ),
)


CONSEQUENCE_EXAMPLES = Question(
    "简答",
    q13(2, 5, 1).stem,
    (
        L(1, "**强化**：通过行为后果提高行为出现的频率。"),
        L(
            2,
            f"{q13(2, 5, 1).leads[0].base} **实例**：完成作业后获得表扬（例子可灵活替换）。",
        ),
        L(
            2,
            f"{q13(2, 5, 1).leads[1].base} **实例**：完成作业后免做家务（例子可灵活替换）。",
        ),
        L(1, "**惩罚**：通过行为后果降低行为出现的频率。"),
        L(
            2,
            f"{q13(2, 5, 1).leads[2].base} **实例**：违规后增加值日（例子可灵活替换）。",
        ),
        L(
            2,
            f"{q13(2, 5, 1).leads[3].base} **实例**：违规后取消娱乐时间（例子可灵活替换）。",
        ),
        L(1, q13(2, 5, 1).points[4].base),
    ),
)


GENERALIZATION_EXAMPLES = Question(
    "简答",
    q13(2, 3, 1).stem,
    (
        L(
            1,
            f"{q13(2, 3, 1).leads[0].base} **实例**：被蛇咬后见到草绳也害怕（例子可灵活替换）。",
        ),
        L(
            1,
            f"{q13(2, 3, 1).leads[1].base} **实例**：经过辨别训练后，只对特定铃声作出反应（例子可灵活替换）。",
        ),
        L(
            1,
            f"{q13(2, 3, 1).leads[2].base} **实例**：铃声不再伴随食物后，唾液反应逐渐减少（例子可灵活替换）。",
        ),
    ),
)


HIGHER_NERVOUS_ACTIVITY = Question(
    "简答",
    q13(2, 4, 1).stem,
    (
        L(1, q13(2, 4, 1).points[0].base),
        L(1, q13(2, 4, 1).points[1].base),
        L(2, q13(2, 4, 1).points[2].base),
        L(2, q13(2, 4, 1).points[3].base),
        L(1, q13(2, 4, 1).points[4].base),
        L(2, q13(2, 4, 1).points[5].base),
        L(2, q13(2, 4, 1).points[6].base),
    ),
)


OBSERVATIONAL_FACTORS = Question(
    "简答",
    q13(2, 9, 1).stem,
    (
        L(0, q13(2, 9, 1).leads[0].base),
        L(1, q13(2, 9, 1).points[0].base),
        L(2, q13(2, 9, 1).points[1].base),
        L(2, q13(2, 9, 1).points[2].base),
        L(2, q13(2, 9, 1).points[3].base),
    ),
)


CLASSICAL_OPERANT_COMPARISON = Question(
    "论述",
    q13(2, 6, 0).stem,
    tuple(
        L(1, module.base, *(module.expansion,) if module.expansion else ())
        for module in (*q13(2, 6, 0).leads, *q13(2, 6, 0).points)
    ),
)


REWARD_PUNISHMENT_BIOLOGY = Question(
    "简答",
    q13(2, 10, 2).stem,
    (
        L(0, q13(2, 10, 2).leads[0].base),
        L(1, "**强化敏感系统**：BAS和BIS分别对不同强化信号敏感。"),
        L(2, q13(2, 10, 2).leads[1].base),
        L(2, q13(2, 10, 2).leads[2].base),
        L(1, q13(2, 10, 2).points[0].base),
        L(1, q13(2, 10, 2).points[1].base),
    ),
    (
        clean_expansion(
            "例如，BAS较敏感者在面对即时奖励时更容易趋近，BIS较敏感者在面对失败风险时更容易暂停并回避（例子可灵活替换）。"
        ),
    ),
)


QUESTION_OVERRIDES: dict[tuple[int, int, int], Question] = {
    (0, 0, 0): PSYCHOLOGY_OVERVIEW,
    (0, 0, 1): PSYCHOLOGY_STRUCTURE,
    (0, 3, 0): BEHAVIORISM,
    (0, 5, 0): PSYCHOANALYSIS_SHORT,
    (0, 5, 1): PSYCHOANALYSIS_ESSAY,
    (0, 8, 0): METHOD_COMPARISON,
    (0, 12, 0): BRANCH_APPLICATION,
    (0, 12, 1): BRANCH_OVERVIEW,
    (1, 0, 0): NEURON,
    (1, 1, 1): NEURAL_TRANSMISSION,
    (1, 2, 0): NERVOUS_SYSTEM,
    (1, 4, 1): ASSOCIATION_CORTEX,
    (2, 1, 0): REFLEX_SYSTEM,
    (2, 2, 0): CLASSICAL_CONDITIONING,
    (2, 3, 0): CONDITIONING_LAWS,
    (2, 3, 1): GENERALIZATION_EXAMPLES,
    (2, 4, 1): HIGHER_NERVOUS_ACTIVITY,
    (2, 5, 1): CONSEQUENCE_EXAMPLES,
    (2, 6, 0): CLASSICAL_OPERANT_COMPARISON,
    (2, 9, 1): OBSERVATIONAL_FACTORS,
    (2, 10, 2): REWARD_PUNISHMENT_BIOLOGY,
}


def build_chapters() -> tuple[tuple[str, tuple[Unit, ...]], ...]:
    chapters: list[tuple[str, tuple[Unit, ...]]] = []
    for chapter_index, (chapter_title, units) in enumerate(BASE.CHAPTERS):
        rebuilt_units: list[Unit] = []
        for unit_index, unit in enumerate(units):
            if (chapter_index, unit_index) == (0, 1):
                questions = (SCIENCE_BIRTH,)
            else:
                questions = tuple(
                    QUESTION_OVERRIDES.get(
                        (chapter_index, unit_index, question_index),
                        generic_question(item),
                    )
                    for question_index, item in enumerate(unit.questions)
                )
            rebuilt_units.append(Unit(unit.title, unit.level, questions))
        chapters.append((chapter_title, tuple(rebuilt_units)))
    return tuple(chapters)


CHAPTERS = build_chapters()


def append_line(lines: list[str], line: AnswerLine, first_number: int, second_number: int) -> None:
    if line.level == 0:
        prefix = ""
    elif line.level == 1:
        prefix = f"{first_number}. "
    elif line.level == 2:
        prefix = f"（{second_number}）"
    else:
        raise ValueError(f"不支持的答案层级：{line.level}")
    if line.text:
        lines.extend((f"{prefix}{line.text}", ""))
    for optional_text in line.expansions:
        lines.extend((expansion(optional_text), ""))


def render() -> str:
    lines = [
        "# 华东师范大学347心理学导论保命手册",
        "",
        "## 前三章·分层扩容均衡版V14",
        "",
        "> 每道押题下方内容均可直接背诵、直接书写；一级编号是主要采分角度，二级编号是其下位内容；`【名词解释：……】`前是完整定义，`【扩容（选用）：……】`中的内容可在对应位置灵活补充。",
        "",
        "---",
        "",
    ]
    for chapter_title, units in CHAPTERS:
        lines.extend((f"# {chapter_title}", ""))
        for unit in units:
            lines.extend((f"## {unit.title}【{unit.level}】", ""))
            for number, item in enumerate(unit.questions, start=1):
                lines.extend((f"### 押题{number}【{item.kind}】{item.stem}", ""))
                first_number = 0
                second_number = 0
                for line in item.lines:
                    if line.level == 1:
                        first_number += 1
                        second_number = 0
                    elif line.level == 2:
                        if first_number == 0:
                            raise AssertionError(f"二级采分点缺少上位一级采分点：{item.stem}")
                        second_number += 1
                    append_line(lines, line, first_number, second_number)
                for optional_text in item.final_expansions:
                    lines.extend((expansion(optional_text), ""))
            lines.extend(("---", ""))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
