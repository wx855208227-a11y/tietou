from __future__ import annotations

from pathlib import Path
import re

from rebuild_shenzhen_baoming_v3 import question_ranges, replace_question
from rebuild_shenzhen_baoming_v4 import (
    build_experiment as build_experiment_v4,
    build_general as build_general_v4,
    build_measurement as build_measurement_v4,
)


ROOT = Path(__file__).resolve().parents[1]

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V6.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V5.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V5.md"


GUIDE_OLD = (
    "- 圆括号外是速背手册已有的主体采分点，优先背诵。\n"
    "- `（）`内是一本通、教材、相关角度或例子等扩容内容，选背；例子可以根据题目灵活替换。"
)
GUIDE_NEW = (
    "- 圆括号外是背诵主体，写全可以拿到主要分数。\n"
    "- `（）`内是扩容项，选背；既可补充其他采分点，也可补充相关概念、解释或例子。例子可以根据题目灵活替换。"
)


RESEARCH_FIELDS = r"""### 押题1【简答】简述心理学的主要研究领域。

心理学包含多个基础和应用研究领域，各领域从不同层面研究心理现象和行为。

1. **普通心理学**：研究心理现象发生的**最一般规律**、最一般理论问题和最一般研究方法。（相关科学问题如“注意如何选择信息”。）

2. **生理心理学**：研究心理现象的**生理机制**。（相关科学问题如“记忆形成涉及哪些脑区和神经机制”。）

3. **发展心理学**：研究心理的**种系发展和个体发展**。（相关科学问题如“儿童思维如何随年龄发展”。）

4. **教育心理学**：研究教育过程中出现的心理现象，揭示**教育与心理发展的相互关系**。（相关科学问题如“如何根据学习规律提高教学效果”。）

5. **社会心理学**：系统研究**社会心理与社会行为**。（还研究人格倾向性、自我评价、自尊和自重等人格的社会心理学问题；相关科学问题如“群体规范如何影响个体判断和行为”。）

（**医学心理学**：研究心理因素在疾病的发生、诊断、治疗及预防中的作用，是心理学与医学相结合的产物。）

（**健康心理学**：研究人的思考、感受和行为方式与其生理健康的联系，探讨身心因素对人类行为的影响，并通过心理—社会干预增进健康、预防疾病；侧重人类健康的维护，而不是疾病的治疗。）

（**工业心理学**：研究工业劳动过程中人的心理特点和行为方式。）

（**军事心理学**：研究军事人员的选拔和培训、军事职业特点、军队中的人际关系和组织、人的因素和安全、人因工程及士气等。）

综上，各研究领域具有不同的研究对象，又共同服务于对人的心理和行为规律的理解与应用。
"""


REACTION_TIME_FACTORS = r"""### 押题1【简答】简述反应时的主要影响因素，并说明速度—准确性权衡。

反应时同时受**刺激变量和机体变量**影响，研究时必须在**反应速度与准确性**之间保持合理平衡。

速度—准确性权衡是反应速度与准确性之间存在**反向关系**，个体需要在二者之间作出权衡的现象。（只报告反应时而忽略错误率，可能把不谨慎的快速反应误判为较好成绩。）【名词解释：速度—准确性权衡】

1. 主要的**刺激变量**包括：

（1）**刺激强度**：刺激强度越弱，反应时越长；刺激强度越强，反应时越短。

（2）**刺激复杂度**：刺激数量越多、可分辨性越差、复杂度越高，反应时越长。

（3）**刺激的时空特征和通道效应**：刺激的位置、面积和呈现时间会影响反应时，不同感觉通道的反应时通常表现为触觉短于听觉、听觉短于视觉。

（**线索提示与相容性**：有提示时反应时缩短，不相容任务的反应时延长。）

2. 主要的**机体变量**包括：

（1）**适应水平**：适应水平不同，反应时不同。

（2）**动机**：常态下反应较慢，激励次之，惩罚条件下反应较快。

（3）**个体差异**：个体间以及同一个体在不同条件下的反应时均可能不同。（可以通过平衡实验效应和计算被试误差项加以处理。）

（**年龄与教育训练**：25岁前反应越来越快，60岁后反应逐渐迟缓；教育训练可以提高反应速度。）

3. 研究反应时时还应处理好**速度—准确性权衡**：应要求被试在保证正确的前提下尽快反应，同时记录反应时和正确率；单独考虑速度或准确性都会损害实验信度。

综上，解释反应时既要考虑刺激和机体变量，也要结合正确率判断被试的信息加工表现。
"""


CONSTRUCT_VALIDITY = r"""### 押题1【简答】简述结构效度的含义、用途及特点。

结构效度是指测验能说明心理学上的**理论结构或特质**的程度。（可以通过**因素分析、会聚效度和区分效度**等证据检验。）【名词解释：结构效度】

1. **用途**：结构效度主要用于智力测验、人格测验等心理测验。

2. **特点**：

（1）结构效度首先取决于事先假定的**心理特质理论**。

（2）测量资料无法证实理论假设时，不一定表示结构效度低，也可能是**理论假设不成立或实验设计不适当**。

（3）结构效度是通过测量什么、不测量什么的证据逐步累积确定的，**没有单一的数量指标**。

（**确定方法的一般步骤**：提出理论假设并建立理论框架，依据理论推演有关测验成绩的假设，再用逻辑和实证方法验证假设。）

综上，结构效度以心理特质理论为基础，主要用于智力和人格等测验，需要通过多方面证据逐步确定。
"""


def update_guide(text: str) -> str:
    assert text.count(GUIDE_OLD) == 1
    return text.replace(GUIDE_OLD, GUIDE_NEW, 1)


def _whole_expansion(line: str, prefix: re.Pattern[str]) -> str:
    content = prefix.sub("", line, count=1).strip()
    tag_match = re.search(r"(【名词解释：[^】]+】)$", content)
    tag = tag_match.group(1) if tag_match else ""
    if tag_match:
        content = content[: tag_match.start()].rstrip()

    point_expansion = re.search(r"（([^（）]+)）$", content)
    if point_expansion:
        main = content[: point_expansion.start()].rstrip().rstrip("。")
        extra = point_expansion.group(1).strip().rstrip("。")
        content = f"{main}；{extra}。"
    elif not content.endswith("。"):
        content += "。"
    return f"（{content}）{tag}"


def move_top_points(text: str, heading_fragment: str, numbers: tuple[int, ...]) -> str:
    hits = [item for item in question_ranges(text) if heading_fragment in item[0].group(0)]
    assert len(hits) == 1, (heading_fragment, len(hits))
    match, end = hits[0]
    block = text[match.start() : end]
    moved: list[str] = []
    retained: list[str] = []
    prefix = re.compile(r"^\d+\.\s+")

    for line in block.splitlines():
        point = re.match(r"^(\d+)\.\s+", line)
        if point and int(point.group(1)) in numbers:
            moved.append(_whole_expansion(line, prefix))
        else:
            retained.append(line)

    assert len(moved) == len(numbers), (heading_fragment, len(moved), numbers)
    counter = 0
    for index, line in enumerate(retained):
        if re.match(r"^\d+\.\s+", line):
            counter += 1
            retained[index] = re.sub(r"^\d+\.\s+", f"{counter}. ", line, count=1)

    summary = next(index for index, line in enumerate(retained) if line.startswith("综上，"))
    while summary > 0 and not retained[summary - 1].strip():
        retained.pop(summary - 1)
        summary -= 1
    insertion: list[str] = [""]
    for item in moved:
        insertion.extend((item, ""))
    retained[summary:summary] = insertion
    rebuilt = "\n".join(retained)
    rebuilt = re.sub(r"\n{3,}", "\n\n", rebuilt).strip()
    suffix = "\n\n" if block.endswith("\n\n") else "\n"
    return text[: match.start()] + rebuilt + suffix + text[end:]


def move_secondary_point(text: str, heading_fragment: str, keyword: str) -> str:
    hits = [item for item in question_ranges(text) if heading_fragment in item[0].group(0)]
    assert len(hits) == 1, (heading_fragment, len(hits))
    match, end = hits[0]
    block = text[match.start() : end]
    prefix = re.compile(r"^（\d+）")
    lines = block.splitlines()
    changed = 0
    for index, line in enumerate(lines):
        if keyword in line and prefix.match(line):
            lines[index] = _whole_expansion(line, prefix)
            changed += 1
    assert changed == 1, (heading_fragment, keyword, changed)
    rebuilt = "\n".join(lines).strip()
    suffix = "\n\n" if block.endswith("\n\n") else "\n"
    return text[: match.start()] + rebuilt + suffix + text[end:]


def build_general() -> str:
    text = update_guide(build_general_v4())
    text = replace_question(text, "简述心理学的主要研究领域", RESEARCH_FIELDS)
    for heading, numbers in (
        ("简述深度知觉的主要线索", (5, 6)),
        ("简述运动知觉的含义和主要类型", (5, 6)),
        ("简述错觉的含义、特点及主要理论解释", (2, 6)),
        ("简述记忆的主要生理机制和脑机制观点", (6,)),
        ("简述加德纳多元智力理论的主要内容", (5, 6)),
    ):
        text = move_top_points(text, heading, numbers)
    return text


def build_experiment() -> str:
    text = update_guide(build_experiment_v4())
    return replace_question(text, "简述反应时的主要影响因素", REACTION_TIME_FACTORS)


def build_measurement() -> str:
    text = update_guide(build_measurement_v4())
    text = move_top_points(text, "简述测验等值的含义及基本条件", (6,))
    text = replace_question(text, "简述结构效度", CONSTRUCT_VALIDITY)
    text = move_secondary_point(text, "简述标准化样组", "常模类型结合")
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
