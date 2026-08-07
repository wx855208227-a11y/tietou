from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path


OUTPUT = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_基础作答选用扩容版V13.md")
BASE_SCRIPT = Path(__file__).with_name("build_baoming_v12.py")


def load_base():
    spec = importlib.util.spec_from_file_location("baoming_v12_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取底稿：{BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base()


@dataclass(frozen=True)
class AnswerModule:
    base: str
    expansion: str | None = None


@dataclass(frozen=True)
class Question:
    kind: str
    stem: str
    leads: tuple[AnswerModule, ...]
    points: tuple[AnswerModule, ...]
    final_expansions: tuple[str, ...]


@dataclass(frozen=True)
class Unit:
    title: str
    level: str
    questions: tuple[Question, ...]


def clean_expansion(text: str) -> str:
    """把旧版整条加分内容改成可以直接放入扩容括号的正文。"""
    text = text.replace("**【加分项】**", "")
    text = text.replace("（可按题干和时间灵活选写）", "")
    text = text.replace("（可按题干灵活选写）", "")
    text = text.replace("（例子可按题干灵活替换）", "（例子可灵活替换）")
    text = text.replace("（固定实验可按题干灵活选写）", "（固定实验可灵活选用）")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:-1] if text.endswith("。") else text


def expansion(text: str) -> str:
    return f"【扩容（选用）：{clean_expansion(text)}】"


BEHAVIORISM_CONTRIBUTION = AnswerModule(
    "**贡献**：强调用客观方法研究可以观察的行为，使心理学发展成一门自然科学。",
    "行为主义关于强化和惩罚的研究可用于行为矫正，例如对按时完成作业的行为给予奖励（例子可灵活替换）",
)

GESTALT_VIEW = AnswerModule(
    "**主要观点**：一切心理现象在意识经验中具有**结构性和整体性**；整体不能还原成部分，整体大于部分之和，先于部分存在并决定部分的性质。",
    "例如，同一部分置于不同整体结构中可能具有不同意义（例子可灵活替换）",
)

FREUD_PERSONALITY_STRUCTURE = AnswerModule(
    "**人格结构**：用**本我、自我和超我**解释人格结构，并用焦虑和心理防御机制解释三者之间的矛盾。",
    "本我、自我和超我分别遵循快乐原则、现实原则和道德原则",
)

HUMANISTIC_VIEW = AnswerModule(
    "**主要观点**：人具有发展潜力和主动成长的倾向，重视人的需要、主观经验、价值和尊严。",
    "可联系马斯洛的自我实现需要或罗杰斯的以人为中心疗法",
)

COGNITIVE_METHODS = AnswerModule(
    "**研究方法**：主要采用**反应时记录法、口语报告法和计算机模拟**等。",
    "例如，可通过不同任务的反应时推断内部信息加工过程（例子可灵活替换）",
)

METHOD_SELECTION = AnswerModule(
    "**选择依据**：研究自然发生的行为可用观察法，研究变量关系和预测问题可用相关研究法，检验可操纵变量之间的因果关系可用实验法。",
    "同一问题可以先观察现象、再考察相关，最后通过实验检验因果",
)

VARIABLE_RELATION = AnswerModule(
    "**三者关系**：研究者操纵自变量、观察或测量因变量，并控制可能影响实验结果的无关变量。",
    "例如，研究学习时间对记忆成绩的影响时，学习时间是自变量，记忆成绩是因变量，材料难度是控制变量（例子可灵活替换）",
)

RELIABILITY_VALIDITY_RELATION = AnswerModule(
    "**信效度关系**：信度是效度的必要而非充分条件；效度高，信度必须高，信度高，效度不一定高。",
    "例如，一个工具每次都稳定地产生同方向偏差，可能信度较高而效度较低（例子可灵活替换）",
)

PROJECTION_LIMITATION = AnswerModule(
    "**缺点**：评分缺乏客观标准，结果难以量化，解释容易受主试影响，信度和效度不易建立。",
    "投射测验应由经过训练的专业人员使用，并与访谈、观察或自陈量表等资料结合",
)

INTERNEURON = AnswerModule(
    "**联络神经元**：又称中间神经元，负责联结感觉神经元和运动神经元并加工信息。",
    "三类神经元共同构成“传入—加工—传出”的神经活动通路",
)

INTRANEURON_TRANSMISSION = AnswerModule(
    "**神经元内传导**：神经冲动以电传导方式沿神经纤维传递，服从**全或无定律**；神经纤维中的传导具有双向性。",
    "生理状态下，神经冲动通常由胞体方向传向轴突末梢",
)

AUTONOMIC_COMPARISON = AnswerModule(
    "**交感神经系统与副交感神经系统**：交感神经系统激活器官活动、提高有机体的唤醒水平；副交感神经系统使有机体消除兴奋、恢复或维持安静状态。二者作用方向通常相反，但共同维持机体的适应和平衡。",
    "例如，面临危险时交感神经使心率加快，危险解除后副交感神经使机体恢复安静（例子可灵活替换）",
)

ASSOCIATION_CORTEX = AnswerModule(
    "**皮层联合区的功能**：感觉联合区整合感觉信息，运动联合区组织复杂运动，前额联合区参与计划、决策和行为控制。",
    "复杂言语活动由多个言语区和联合区分工协作完成，不能简单归因于单一脑区",
)

SPLIT_BRAIN_CONCLUSION = AnswerModule(
    "**割裂脑实验的主要结论**：呈现在右视野的信息进入左半球后通常能够被言语命名；呈现在左视野的信息进入右半球后可能不能命名，却能用左手选择相应物体。",
    "例如，投射到右视野的“笔”能被说出，投射到左视野的信息不能用言语描述（固定实验可灵活选用）",
)

HYPOTHALAMUS_FUNCTION = AnswerModule(
    "**下丘脑的功能**：参与摄食、饮水、体温、睡眠—觉醒、性行为和情绪反应的调节，维持机体内环境稳定。",
    "例如，机体缺水时下丘脑参与产生口渴动机并推动饮水（例子可灵活替换）",
)

HIPPOCAMPUS_AMYGDALA = AnswerModule(
    "**海马与杏仁核的比较**：海马侧重事件内容的记忆，杏仁核侧重事件的情绪意义。",
    "例如，个体既能记住事故发生的时间地点，又会对事故产生恐惧，前者主要涉及海马，后者主要涉及杏仁核（例子可灵活替换）",
)

BRAIN_THEORY_DEVELOPMENT = AnswerModule(
    "**学说发展**：模块说强调功能专门化，神经网络说强调节点之间的分布式联系；现代研究重视脑功能的**相对分工与整体协同**。",
    "失语症支持功能定位，而复杂言语活动又依赖多个脑区协作",
)

LEARNING_EXPERIENCE = AnswerModule(
    "**基于经验的过程**：学习由练习或经验引起，先天成熟和本能反应不属于学习。",
    "例如，持续练习后打字速度稳定提高属于学习，疲劳导致速度暂时下降不属于学习（例子可灵活替换）",
)

REFLEX_FUNCTION = AnswerModule(
    "**功能特点**：无条件反射直接维持生存和种族繁衍，是条件反射建立的基础；条件反射具有概括性和灵活性，能够适应环境变化。",
    "例如，强光引起瞳孔收缩属于无条件反射，铃声与食物多次配对后引起唾液分泌属于条件反射（例子可灵活替换）",
)

SIGNAL_SYSTEM_COMPARISON = AnswerModule(
    "**第一信号系统与第二信号系统**：第一信号系统以具体事物为信号，人和动物共有；第二信号系统以言语和文字为信号，为人类独有，并以第一信号系统为基础。",
    "例如，看到红灯停车主要依赖第一信号系统，听到“红灯”二字并理解其意义主要依赖第二信号系统（例子可灵活替换）",
)

INSIGHT_RELATION = AnswerModule(
    "**关系领悟**：学习者领悟目标与手段之间的关系，解决办法会突然出现。",
    "例如，黑猩猩突然把箱子叠起来取得高处的香蕉（固定实验可灵活选用）",
)

COGNITIVE_MAP_FUNCTION = AnswerModule(
    "**认知地图的作用**：个体能够主动综合环境信息形成认知地图，并根据对情境的认知选择达到目的的途径。",
    "例如，熟悉校园后能够选择一条从未走过的新路线到达目的地（例子可灵活替换）",
)

MODELING_APPLICATION = AnswerModule(
    "**榜样示范**：选择具有吸引力和行为价值的榜样，使示范行为清晰可辨；帮助学习者记忆行为步骤、及时练习并给予反馈和强化。",
    "例如，学习者先观察操作示范，记住步骤，再尝试复现，并因积极反馈而继续练习（例子可灵活替换）",
)

BAS_BIS_COMPARISON = AnswerModule(
    "**行为趋近系统与行为抑制系统**：BAS使个体关注奖励并接近目标；BIS使个体关注威胁、暂停行为并回避可能受罚的情境。",
    "例如，面对即时奖励时，BAS较敏感者更容易趋近；面对可能失败时，BIS较敏感者更容易暂停并评估风险（例子可灵活替换）",
)


# 逐题审定的“基础采分点—选用扩容”边界。重复模块直接复用同一常量，
# 防止在不同题目中出现同义改写或信息增减。
POINT_OVERRIDES: dict[tuple[int, int, int, int], AnswerModule] = {
    (0, 3, 0, 2): BEHAVIORISM_CONTRIBUTION,
    (0, 4, 0, 0): GESTALT_VIEW,
    (0, 5, 0, 4): FREUD_PERSONALITY_STRUCTURE,
    (0, 5, 1, 4): FREUD_PERSONALITY_STRUCTURE,
    (0, 6, 0, 0): HUMANISTIC_VIEW,
    (0, 7, 0, 1): COGNITIVE_METHODS,
    (0, 8, 1, 0): METHOD_SELECTION,
    (0, 9, 0, 0): VARIABLE_RELATION,
    (0, 10, 1, 0): RELIABILITY_VALIDITY_RELATION,
    (0, 11, 1, 1): PROJECTION_LIMITATION,
    (1, 0, 0, 3): INTERNEURON,
    (1, 1, 0, 0): INTRANEURON_TRANSMISSION,
    (1, 1, 1, 0): INTRANEURON_TRANSMISSION,
    (1, 2, 0, 4): AUTONOMIC_COMPARISON,
    (1, 2, 1, 0): AUTONOMIC_COMPARISON,
    (1, 4, 1, 0): ASSOCIATION_CORTEX,
    (1, 5, 0, 0): SPLIT_BRAIN_CONCLUSION,
    (1, 6, 0, 1): HYPOTHALAMUS_FUNCTION,
    (1, 7, 1, 2): HIPPOCAMPUS_AMYGDALA,
    (1, 8, 1, 3): BRAIN_THEORY_DEVELOPMENT,
    (2, 0, 0, 2): LEARNING_EXPERIENCE,
    (2, 1, 0, 2): REFLEX_FUNCTION,
    (2, 1, 1, 1): REFLEX_FUNCTION,
    (2, 4, 0, 0): SIGNAL_SYSTEM_COMPARISON,
    (2, 7, 0, 1): INSIGHT_RELATION,
    (2, 8, 0, 1): COGNITIVE_MAP_FUNCTION,
    (2, 8, 1, 0): COGNITIVE_MAP_FUNCTION,
    (2, 9, 2, 7): MODELING_APPLICATION,
    (2, 10, 0, 0): BAS_BIS_COMPARISON,
}


def ordinary_module(text: str) -> AnswerModule:
    if "【加分项】" in text:
        raise AssertionError(f"存在未逐题审定的旧加分模块：{text}")
    text = text.replace("（例子可按题干灵活替换）", "（例子可灵活替换）")
    text = text.replace("（固定实验可按题干灵活选写）", "（固定实验可灵活选用）")
    return AnswerModule(text)


def build_chapters() -> tuple[tuple[str, tuple[Unit, ...]], ...]:
    chapters: list[tuple[str, tuple[Unit, ...]]] = []
    for chapter_index, (chapter_title, units) in enumerate(BASE.CHAPTERS):
        rebuilt_units: list[Unit] = []
        for unit_index, unit in enumerate(units):
            rebuilt_questions: list[Question] = []
            for question_index, item in enumerate(unit.questions):
                leads = tuple(ordinary_module(text) for text in item.leads)
                points = tuple(
                    POINT_OVERRIDES.get(
                        (chapter_index, unit_index, question_index, point_index),
                        ordinary_module(text) if "【加分项】" not in text else None,
                    )
                    for point_index, text in enumerate(item.points)
                )
                if any(module is None for module in points):
                    raise AssertionError(
                        f"存在未逐题审定的旧加分模块：{chapter_index, unit_index, question_index}"
                    )
                final_expansions = tuple(clean_expansion(text) for text in item.bonus_points)
                rebuilt_questions.append(
                    Question(
                        item.kind,
                        item.stem,
                        leads,
                        points,  # type: ignore[arg-type]
                        final_expansions,
                    )
                )
            rebuilt_units.append(Unit(unit.title, unit.level, tuple(rebuilt_questions)))
        chapters.append((chapter_title, tuple(rebuilt_units)))
    return tuple(chapters)


CHAPTERS = build_chapters()


def append_module(lines: list[str], module: AnswerModule, number: int | None = None) -> None:
    prefix = f"{number}. " if number is not None else ""
    lines.extend((f"{prefix}{module.base}", ""))
    if module.expansion:
        lines.extend((expansion(module.expansion), ""))


def render() -> str:
    lines = [
        "# 华东师范大学347心理学导论保命手册",
        "",
        "## 前三章·基础作答选用扩容版V13",
        "",
        "> 每道押题下方内容均可直接背诵、直接书写；`【名词解释：……】`前是可独立提取的完整定义，`【扩容（选用）：……】`中的内容根据题目分值和时间选写。",
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

                if len(item.leads) == 1:
                    append_module(lines, item.leads[0])
                    numbered = item.points
                else:
                    numbered = (*item.leads, *item.points)
                for point_number, module in enumerate(numbered, start=1):
                    append_module(lines, module, point_number)

                for optional_text in item.final_expansions:
                    lines.extend((expansion(optional_text), ""))

            lines.extend(("---", ""))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
