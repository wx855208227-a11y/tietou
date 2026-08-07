from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


OUTPUT = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_精炼直背版V12.md")
BASE_SCRIPT = Path(__file__).with_name("build_baoming_v10.py")


def load_base():
    spec = importlib.util.spec_from_file_location("baoming_v10_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取底稿：{BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base()
Question = BASE.Question
Unit = BASE.Unit


def clean_module(text: str) -> str:
    """把旧版双标签和生硬的选写说明统一为句末加分标注。"""
    text = text.replace("**【采分点加分】**", "**【加分项】**")
    text = text.replace("；例子可灵活替换。", "（例子可按题干灵活替换）。")
    text = text.replace("；可灵活选写。", "（可按题干灵活选写）。")
    text = text.replace("；按题干灵活选写。", "（可按题干灵活选写）。")
    text = text.replace("；可按题干和时间灵活选写。", "（可按题干和时间灵活选写）。")
    text = text.replace("；固定实验可按题干选写。", "（固定实验可按题干灵活选写）。")
    text = text.replace("。 ", "。")
    return re.sub(r"\s+", " ", text).strip()


def as_bonus(text: str) -> str:
    text = clean_module(text)
    if "【加分项】" not in text:
        text += "**【加分项】**"
    return text


def p(name: str) -> str:
    return clean_module(BASE.P[name])


def d(name: str) -> str:
    return clean_module(BASE.D[name])


PSYCHOLOGY_PROCESS_OVERVIEW = (
    "**心理过程的构成**：心理过程包括**认知过程、情绪情感过程和意志过程**。"
)
PERSONALITY_OVERVIEW = (
    "**人格的构成**：人格包括**心理动力**和**心理特征**。"
)
PSYCHOLOGY_PROCESS_BONUS = (
    "认知、情绪情感和意志是**同一心理过程的不同方面**，其中认知过程是最基本的心理活动。"
    "**【加分项】**"
)

PHILOSOPHY_BACKGROUND = (
    "**哲学背景**：亚里士多德的心理学思想、笛卡尔的**心身二元论**和洛克的**白板说**，"
    "为心理学提供了早期理论基础。"
)
PHYSIOLOGY_BACKGROUND = (
    "**生理学背景**：缪勒的神经特殊能量说、赫尔姆霍兹对视觉和听觉的研究以及费希纳的"
    "**心理物理学实验方法**，推动心理现象进入实验研究。"
)
BIOLOGY_BACKGROUND = (
    "**生物学背景**：达尔文的进化论使**遗传、环境、个别差异和适应**等成为心理学研究主题。"
)

PROJECTION_FEATURES = (
    "**特点**：刺激材料的意义模糊，被试可以自由作答，测验目的具有掩蔽性，主试根据反应对人格作整体解释。"
)

WRITING_AREA = (
    "**书写区**位于优势半球额叶中回后部，主要负责书面言语表达；受损会产生失写症，即“写不出”。"
    "**【名词解释：书写区】**"
)

IMPULSIVITY_EXAMPLE = (
    "例如，高冲动者在即时奖励任务中更容易选择眼前的小奖励，而忽视延迟惩罚或长期损失"
    "（例子可按题干灵活替换）。**【加分项】**"
)


def base_question(chapter_index: int, unit_index: int, question_index: int) -> Question:
    item = BASE.CHAPTERS[chapter_index][1][unit_index].questions[question_index]
    return Question(
        item.kind,
        item.stem,
        tuple(clean_module(x) for x in item.leads),
        tuple(clean_module(x) for x in item.points),
        tuple(as_bonus(x) for x in item.bonus_points),
    )


OVERRIDES: dict[tuple[int, int, int], Question] = {
    # 心理学的定义只保留正常名解容量，研究对象另补一句加分项。
    (0, 0, 0): Question(
        "简答",
        "简述心理学的**含义**。",
        (d("心理学"),),
        (),
        (as_bonus(p("心理学研究对象")),),
    ),
    # “构成”题必须先交代两个上位分类，再分别解释下位成分。
    (0, 0, 1): Question(
        "简答",
        "简述**心理过程**和**人格**各自的构成，并说明**心理过程与人格的关系**。",
        (),
        (
            PSYCHOLOGY_PROCESS_OVERVIEW,
            p("认知过程"),
            p("情绪情感过程"),
            p("意志过程"),
            PERSONALITY_OVERVIEW,
            p("心理动力"),
            p("心理特征"),
            p("心理过程人格关系"),
        ),
        (PSYCHOLOGY_PROCESS_BONUS,),
    ),
    # 题干要求“产生背景”时，哲学、生理学、生物学不能只报三个名称。
    (0, 1, 1): Question(
        "简答",
        "简述科学心理学的**产生背景**与**诞生标志**。",
        (),
        (
            PHILOSOPHY_BACKGROUND,
            PHYSIOLOGY_BACKGROUND,
            BIOLOGY_BACKGROUND,
            p("心理学诞生标志"),
        ),
        (as_bonus(p("心理学诞生意义")),),
    ),
    # “含义与特点”中的特点必须作为独立采分点写出。
    (0, 11, 0): Question(
        "简答",
        "简述投射测验的**含义与特点**、**代表测验**。",
        (d("投射法"),),
        (PROJECTION_FEATURES, p("投射代表")),
        (),
    ),
    # 言语区题补齐书写区的位置、功能和受损表现。
    (1, 4, 0): Question(
        "简答",
        "简述主要言语区的**位置、功能及受损表现**。",
        (d("布洛卡区"), d("威尔尼克区"), d("角回"), WRITING_AREA),
        (),
        (
            "复杂言语活动由多个言语区和联合区**分工协作**完成，不能简单归因于单一脑区。"
            "**【加分项】**",
        ),
    ),
    # 冲动者奖励学习增加一个紧贴机制的短例证，不拉长原采分点。
    (2, 10, 1): Question(
        "论述",
        "根据格雷的强化敏感性理论，分析**冲动者的奖励学习**。",
        (d("强化敏感性理论"), d("行为趋近系统（BAS）"), d("行为抑制系统（BIS）")),
        (p("奖惩敏感差异"), p("冲动奖励学习")),
        (IMPULSIVITY_EXAMPLE,),
    ),
}


def build_chapters() -> tuple[tuple[str, tuple[Unit, ...]], ...]:
    chapters: list[tuple[str, tuple[Unit, ...]]] = []
    for chapter_index, (chapter_title, units) in enumerate(BASE.CHAPTERS):
        rebuilt_units: list[Unit] = []
        for unit_index, unit in enumerate(units):
            questions = tuple(
                OVERRIDES.get(
                    (chapter_index, unit_index, question_index),
                    base_question(chapter_index, unit_index, question_index),
                )
                for question_index in range(len(unit.questions))
            )
            rebuilt_units.append(Unit(unit.title, unit.level, questions))
        chapters.append((chapter_title, tuple(rebuilt_units)))
    return tuple(chapters)


CHAPTERS = build_chapters()


def render() -> str:
    lines = [
        "# 华东师范大学347心理学导论保命手册",
        "",
        "## 前三章·精炼直背版V12",
        "",
        "> 每道押题下方内容均可直接背诵、直接书写；`【加分项】`只补充一个新的得分角度，可按题目分值和时间灵活选写。",
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

                # 单一定义作开头时不机械编号；多个并列定义本身就是采分点，统一连续编号。
                all_base = (*item.leads, *item.points)
                if len(item.leads) == 1:
                    lines.extend((item.leads[0], ""))
                    numbered = item.points
                else:
                    numbered = all_base
                for point_number, point in enumerate(numbered, start=1):
                    lines.extend((f"{point_number}. {point}", ""))

                for bonus in item.bonus_points:
                    lines.extend((bonus, ""))

            lines.extend(("---", ""))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
