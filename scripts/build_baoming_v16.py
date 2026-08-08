from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path


OUTPUT = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_来源严格版V16.md")
BASE_SCRIPT = Path(__file__).with_name("build_baoming_v15.py")


def load_base():
    spec = importlib.util.spec_from_file_location("baoming_v15_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取底稿：{BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = load_base()
AnswerLine = BASE.AnswerLine
Question = BASE.Question
Unit = BASE.Unit
first_keyword = BASE.first_keyword
expansion = BASE.expansion


def projection_unit(unit) -> Unit:
    definition = unit.questions[0].lines[0]
    question = Question(
        "简答",
        "简述投射法的**含义与作答特点**、**代表测验**。",
        (
            definition,
            AnswerLine(
                1,
                "**作答特点**：刺激材料的意义模糊，被试在不受限制的情况下自由反应，再由心理学专家进行解释和分析。",
            ),
            AnswerLine(
                1,
                "**代表测验**：投射法的经典测验包括**罗夏墨渍测验**和**主题统觉测验**。",
            ),
            AnswerLine(
                0,
                "综上，投射法通过模糊刺激和自由反应了解个体的内在心理，经典工具是罗夏墨渍测验和主题统觉测验。",
            ),
        ),
    )
    return Unit(unit.title, unit.level, (question,))


def research_methods_unit(unit) -> Unit:
    questions = []
    for question in unit.questions:
        lines = tuple(
            replace(
                line,
                expansions=tuple(
                    item for item in line.expansions if "随机分配" not in item
                ),
            )
            for line in question.lines
        )
        questions.append(replace(question, lines=lines))
    return Unit(unit.title, unit.level, tuple(questions))


def operant_unit(unit) -> Unit:
    definition = unit.questions[2].lines[0]
    schedule_question = Question(
        "简答",
        "简述操作条件反射的**基本规律**和**主要强化程序**。",
        (
            definition,
            AnswerLine(
                1,
                "**基本规律**：操作条件反射与经典条件反射的规律相似，同样存在消退、泛化、分化和延迟等过程。",
                ("在复杂的条件反射活动中，经典条件反射与操作条件反射往往相互作用。",),
            ),
            AnswerLine(1, "**主要强化程序**：强化可以按照反应次数或时间间隔进行连续、间断、定比率、定时距、变比率和变时距安排。"),
            AnswerLine(
                2,
                "**连续强化与间断强化**：连续强化对每次正确反应都给予强化，行为容易形成，但停止强化后也容易消退；间断强化只强化部分正确反应，形成后较难消退。",
                ("连续强化适合行为建立初期，间断强化形成的行为更能抵抗消退。",),
            ),
            AnswerLine(
                2,
                "**定比率强化与定时距强化**：定比率强化按照固定反应次数给予强化；定时距强化按照固定时间间隔给予强化。",
                ("例如，计件工资属于定比率强化，每两周提交一次课程报告属于定时距强化（例子可灵活替换）。",),
            ),
            AnswerLine(
                2,
                "**变比率强化与变时距强化**：变比率强化中两次强化之间的反应次数不固定；变时距强化中两次强化之间的时间间隔不固定。",
                ("例如，玩老虎机属于变比率强化，钓鱼属于变时距强化（例子可灵活替换）。",),
            ),
            AnswerLine(
                0,
                "综上，操作条件反射既遵循一般条件反射规律，又可通过不同强化程序影响行为的形成速度和抗消退性。",
            ),
        ),
    )
    return Unit(
        "六、操作条件反射的强化、惩罚与强化程序",
        unit.level,
        (unit.questions[0], unit.questions[1], schedule_question),
    )


def observation_unit(unit) -> Unit:
    questions = list(unit.questions)
    application = questions[2]
    retained = tuple(
        line
        for line in application.lines
        if first_keyword(line.text) not in {"实施反馈", "迁移与保持"}
        and not line.text.startswith("综上")
    )
    retained += (
        AnswerLine(
            0,
            "综上，有效榜样示范必须同时促进注意、保持、动作复现和动机，并结合榜样特征、观察者特点和奖赏结果进行。",
        ),
    )
    questions[2] = Question(
        application.kind,
        application.stem,
        retained,
        application.final_expansions,
    )
    return Unit(unit.title, unit.level, tuple(questions))


def build_chapters():
    chapters = []
    for chapter_title, units in BASE.CHAPTERS:
        rebuilt_units = []
        for unit in units:
            if unit.title == "十一、格雷的强化敏感性理论":
                continue
            if unit.title == "九、观察法、相关研究法与实验法":
                rebuilt_units.append(research_methods_unit(unit))
            elif unit.title == "十、实验变量":
                rebuilt_units.append(Unit(unit.title, unit.level, (unit.questions[0],)))
            elif unit.title == "十二、投射法与投射测验":
                rebuilt_units.append(projection_unit(unit))
            elif unit.title == "六、操作条件反射与行为调控":
                rebuilt_units.append(operant_unit(unit))
            elif unit.title == "十、观察学习":
                rebuilt_units.append(observation_unit(unit))
            else:
                rebuilt_units.append(Unit(unit.title, unit.level, unit.questions))
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
    content = f"{prefix}{line.text}"
    if line.expansions:
        content += "".join(expansion(item) for item in line.expansions)
    lines.extend((content, ""))


def render() -> str:
    lines = [
        "# 华东师范大学347心理学导论保命手册",
        "",
        "## 前三章·逐题直背版V16",
        "",
        "> 每道押题均按“总起—分点—总结”组织；一级编号是主要采分角度，二级编号是其下位内容；单点`【扩容（选用）：……】`紧跟对应采分句，按题目分值和时间选写。",
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
