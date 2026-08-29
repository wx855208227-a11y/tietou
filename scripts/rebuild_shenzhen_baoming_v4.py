from __future__ import annotations

from pathlib import Path
import re

from rebuild_shenzhen_baoming_v3 import replace_question
from shenzhen_baoming_canonical import canonicalize_definitions


ROOT = Path(__file__).resolve().parents[1]

GENERAL_SOURCE = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V4.md"
EXPERIMENT_SOURCE = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V3.md"
MEASUREMENT_SOURCE = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V3.md"

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V5.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V4.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V4.md"


GUIDE_OLD = (
    "- 圆括号外是背诵主体，写全可以拿到主要分数。\n"
    "- `（）`内是扩容项，选背；用于丰富答题角度、锦上添花。如果其中是例子，可以根据题目灵活替换。"
)
GUIDE_NEW = (
    "- 圆括号外是速背手册已有的主体采分点，优先背诵。\n"
    "- `（）`内是一本通、教材、相关角度或例子等扩容内容，选背；例子可以根据题目灵活替换。"
)


def align_shared_definitions(text: str) -> str:
    text = text.replace(
        "投射测验是向被试提供**未经组织的刺激情境**，让其在不受限制的情况下自由表现，然后分析其反应，"
        "从而推断人格结构。（常用的投射测验包括**罗夏墨迹测验和主题统觉测验**。）",
        "投射测验是通过**分析被试在刺激情景下的自由表现来推断其人格结构**的方法。"
        "（常用的投射测验包括罗夏墨迹测验和主题统觉测验。）",
    )
    text = text.replace(
        "标准化是指测验的**内容、实施、记分和分数解释的一致性**。"
        "（主要包括测验内容、施测条件、评分规则和测验常模的标准化。）",
        "标准化是指测验的**内容、施测过程、评分和分数解释采用一致标准**。"
        "（具体包括相同或等值的测验内容、相同的施测条件、统一评分规则和统一分数解释。）",
    )
    return text


BASIC_TASKS = r"""### 押题1【简答】简述心理学的**基本任务**及其**学科性质**。

心理学的基本任务和学科性质分别如下：

1. 心理学的基本任务是**描述、解释、预测与控制心理现象和行为**。

（1）**描述心理现象和行为**。（对心理现象和行为的表现、特征及变化作出客观说明，回答“是什么”。）

（2）**解释心理现象和行为**。（分析心理现象和行为产生、发展的原因及作用机制，回答“为什么发生”。）

（3）**预测与控制心理现象和行为**。（根据已发现的规律预测特定条件下可能出现的心理和行为，并在遵守伦理的前提下，通过改变有关条件使其向预期方向发展。）

2. 心理学具有**自然科学和社会科学的性质**，因此可以叫作**交叉学科或中间学科**。（心理学既研究心理现象的生理基础，也研究社会环境对人的心理和行为的影响。）

综上，心理学以描述、解释、预测与控制心理现象和行为为基本任务，兼具自然科学和社会科学的性质。
"""


RESEARCH_FIELDS = r"""### 押题1【简答】简述心理学的主要研究领域。

心理学包含多个基础和应用研究领域，各领域从不同层面研究心理现象和行为。

1. **普通心理学**：研究心理现象发生的**最一般规律**、最一般理论问题和最一般研究方法。（相关科学问题如“注意如何选择信息”。）

2. **生理心理学**：研究心理现象的**生理机制**。（相关科学问题如“记忆形成涉及哪些脑区和神经机制”。）

3. **发展心理学**：研究心理的**种系发展和个体发展**。（相关科学问题如“儿童思维如何随年龄发展”。）

4. **教育心理学**：研究教育过程中出现的心理现象，揭示**教育与心理发展的相互关系**。（相关科学问题如“如何根据学习规律提高教学效果”。）

5. **医学心理学和健康心理学**：前者研究心理因素在疾病发生、诊断、治疗和预防中的作用；后者研究思考、感受和行为方式与生理健康的联系，侧重**健康维护和疾病预防**。（相关科学问题如“长期压力如何影响身心健康”。）

6. **工业心理学**：研究工业劳动过程中的心理特点和行为方式。（相关科学问题如“如何根据岗位要求选拔合适人员”。）

7. **社会心理学**：系统研究**社会心理与社会行为**。（相关科学问题如“群体规范如何影响个体判断和行为”。）

综上，各研究领域具有不同的研究对象，又共同服务于对人的心理和行为规律的理解与应用。
"""


EXPERIMENT_SCIENCE = r"""### 押题1【简答】简述科学方法的主要特点，并说明实证研究的优越性。

实验心理学运用科学方法开展实证研究，其主要特点和优越性如下：

1. 科学方法的主要特点包括：

（1）**系统的经验观察**。（按照明确程序收集可以观察和记录的事实资料。）

（2）**自我校正**。（科学结论可以在新的证据和重复检验中得到修正。）

（3）由科学系统的经验观察得出的科学事实具有**可公开、可反复获得**的特点。

（4）心理学研究应遵循**可证伪原则、操作定义和概率推断**。

①**可证伪原则**：只有理论的预测**可被证伪**，该理论才可能是科学的。

②**操作定义**：根据**测定程序**对心理现象下定义。

③**概率推断**：科学结论是指现象发生的**概率高**，而不是必定发生。

2. 实证研究的优越性主要包括：

（1）实证研究比个人经验更具优势，因为研究包含**合适的对照组**。

（2）实证研究结果具有**概率性**，虽然不能预测和解释所有情况，但能预测和解释较高比例的可能情况。

综上，科学方法强调系统观察、自我校正和可检验性，实证研究则借助合适对照和概率推断提高结论的可信程度。
"""


EXPERIMENT_ETHICS = r"""### 押题1【简答】简述实验心理学研究应遵守的主要伦理原则。

实验心理学研究必须同时遵循科学原则和伦理原则，在保障被试权益的前提下开展研究。

实验心理学研究人类被试时应遵守以下原则：

1. 保障被试的**知情同意权**。（研究者应说明与参与决定有关的信息，并在被试自愿的基础上获得同意。）

2. 保障被试**退出的自由**。（被试有权在研究过程中退出，不应因此受到惩罚或不利影响。）

3. 保护被试**免遭伤害**。（研究者应尽可能降低身体、心理和社会风险。）

4. 遵守**保密原则**。（研究者应妥善保护被试身份和个人资料，公开结果时进行匿名化处理。）

（研究者还应坚持实事求是的科学精神和严谨审慎的工作作风。）

综上，实验心理学研究应切实保障被试的知情、自愿、安全和隐私。
"""


TRADITIONAL_PSYCHOPHYSICS = r"""### 押题1【论述】论述感觉阈限的含义、传统测量方法及主要误差。

感觉阈限包括绝对阈限和差别阈限，传统心理物理法主要包括最小变化法、恒定刺激法和平均差误法。

绝对阈限是刚好引起心理感受的**最小刺激量**。（绝对阈限越低，通常表示对该刺激越敏感。）【名词解释：绝对阈限】

差别阈限是刚好引起差异感受的**最小刺激变化量**。（差别阈限又称最小可觉差。）【名词解释：差别阈限】

1. 感觉阈限的传统测量方法包括：

（1）**最小变化法**：刺激按递增或递减顺序变化，找出反应转换点或阈限位置。（被试报告是否感觉到刺激或两个刺激是否有差异。）【名词解释：最小变化法】

（2）**恒定刺激法**：随机呈现特定恒定刺激，统计出现反应的频率。（它是心理物理学中应用较广、较准确的方法。）【名词解释：恒定刺激法】

（3）**平均差误法**：主试呈现标准刺激，被试调整比较刺激，直到认为二者相等。（它又称调整法。）【名词解释：平均差误法】

2. 传统心理物理法的主要误差包括：

（1）**习惯误差、期望误差**。（习惯误差指被试倾向保持同一种判断；期望误差指被试期待反应转折点尽快到来。）

（2）**练习误差、疲劳误差**。（练习会使反应逐渐熟练，疲劳则可能使反应能力下降。）

（3）平均差误法还可能出现**动作误差和空间误差**。（动作误差可以用多层次ABBA法控制，空间误差可以通过改变比较刺激的调整方向控制。）

3. 三种方法的联系与区别在于：三者都通过多次刺激判断估计感觉阈限，但刺激呈现顺序、被试任务和主要误差不同。

综上，传统心理物理法用不同刺激呈现和反应程序估计绝对阈限与差别阈限，使用时应控制相应误差。
"""


SUPRATHRESHOLD_SCALING = r"""### 押题1【简答】简述阈上感觉量表的主要建立方法。

阈上感觉的量化由心理物理量表完成，根据量表是否等距和有无绝对零点，可分为顺序量表、等距量表和比例量表。

1. 顺序量表的建立：

（1）**等级排列法**。（同时呈现多个刺激，要求被试按一定标准排序。）

（2）**对偶比较法**。（把刺激两两配对，由被试判断哪个刺激在某一特性上更突出。）

2. 等距量表的建立：

（1）**感觉等距法**：制作等距量表的最直接方法，主观上将一个感觉分成相等距离。

（2）**差别阈限法**：制作等距量表的间接方法，以绝对阈限为零点、最小可觉差为等距单位。

3. 比例量表的建立：

（1）**分段法**：制作比例量表的最直接方法，把感觉量取一定比例来建立心理量表。（可以要求被试把一个感觉量加倍或减半。）

（2）**数量估计法**：制作比例量表的直接方法。（被试参照某个刺激所对应的数值，直接估计其他刺激的感觉量值。）

综上，等级排列法和对偶比较法建立顺序量表，感觉等距法和差别阈限法建立等距量表，分段法和数量估计法建立比例量表。
"""


MEASUREMENT_MEANING = r"""### 押题1【简答】简述测量的**含义和基本要素**。

测量是**依据一定的法则，用量尺对事物的属性进行定量描述**。（测量包括对象、规则和结果三个构成部分。）【名词解释：测量】

1. **一定的法则**：基于科学规则和方法完成测量。

2. **事物的属性**：所测量的客体或事件的特定特征。

3. **量尺**：测量中使用的度量工具。

4. **定量描述**：测量结果是事物属性的量的确定。

5. 测量的基本要素包括：

（1）**参照点**：测量的原始起点。

①**绝对参照点**：绝对零点。（绝对零点表示被测属性不存在，可以进行倍数比较。）

②**相对参照点**：人为确定的零点。（摄氏温度的零点是相对参照点。）

（2）**单位**：应有**确定的意义和相等的价值**。（单位等值是对测量结果进行数量比较的重要条件。）

综上，测量依据一定法则，用量尺对事物属性进行定量描述，参照点和单位是其基本要素。
"""


PERSONALITY_SCALES = r"""### 押题1【论述】比较**16PF、MMPI和EPQ**的编制或测量特点、常模及适用对象。

16PF、MMPI和EPQ都是常用的**人格自陈量表**，均要求被试根据实际情况回答问题，从而衡量人格特质的表现程度。

1. 三种量表的基本内容如下：

（1）**16PF**：卡特尔16种人格因素量表采用**因素分析法**编制，能在约45分钟内测量16种主要人格特质，属于**团体测验**，常模采用**标准10分制**，适用于16岁以上且具有初中以上文化程度的人。（卡特尔还通过二阶因素分析得到四个二阶公共因素。）【名词解释：16PF】

（2）**MMPI**：明尼苏达多项人格调查表常模采用**T分数**，适合**16岁以上具有初中文化**的人。（该量表由临床量表和效度量表构成，可同时反映临床特征并检查作答可信性。）【名词解释：MMPI】

（3）**EPQ**：艾森克人格问卷采用**因素分析法**编制，属于**团体测验**，常模采用**T分数**；测量精神质（P）、外倾性（E）和神经质（N），L是说谎量表，用于识别诚实程度。（问卷分为儿童版和成人版。）【名词解释：EPQ】

2. 三种量表的联系在于：三者均属于人格自陈量表，都以标准化题目收集被试的自我报告，并用于衡量人格特质。

3. 三种量表的主要区别如下：

（1）**编制或测量特点不同**：16PF和EPQ都采用因素分析法编制；16PF测量16种主要人格特质，EPQ测量P、E、N三个维度并用L量表识别诚实程度；MMPI则侧重临床人格评估。

（2）**常模不同**：16PF采用标准10分制，MMPI和EPQ采用T分数。

（3）**适用对象不同**：16PF和MMPI均适用于16岁以上且具有一定文化程度的人；EPQ属于团体测验。（EPQ设儿童版和成人版，适用年龄范围更宽。）

综上，三者同属人格自陈量表，但16PF突出16种人格特质，MMPI侧重临床人格评估，EPQ以P、E、N和L构成较简明的测量框架。
"""


RELIABILITY_FACTORS = r"""### 押题1【简答】简述影响信度的**主要因素**及提高信度的方法。

信度是指**测量结果的稳定性和一致性程度**，也叫测量的可靠性。（信度越高，随机测量误差对测验分数的影响通常越小。）【名词解释：信度】

1. 影响测量信度的主要因素包括：

（1）**被试方面**：个体的身心健康、应试动机、注意力和耐心会影响信度；团体的同质性、离散程度和平均水平也会影响信度，得分分布窄或得分过高、过低都会低估信度。（解释信度时应说明被试样本的性质。）

（2）**主试方面**：不按规定施测、制造紧张气氛、评分标准不一，都会降低信度。

（3）**施测情境方面**：测量工具的稳定性、试题取样和同质性会影响测验稳定性；两次施测间隔越短，信度值越大，间隔越长，信度值越小。（时间间隔的影响还取决于所测特质的稳定性。）

2. 提高测量信度的方法包括：

（1）增加测验**长度**。（新增题目应与原测验内容同质且质量合格。）

（2）控制试题难度接近**正态分布和中等水平**。

（3）提高试题**区分度**。

（4）选取**适当被试团体**，提高在同质性较强的亚团体上的信度。

（5）**严格执行施测规程**。

综上，影响信度的因素来自被试、主试和施测情境，提高信度则应同时改进测验质量、被试选择和施测过程。
"""


ANXIETY_TESTS = r"""### 押题1【简答】简述常见焦虑测验及其主要用途。

焦虑测验用于评估个体的焦虑表现、焦虑倾向或焦虑严重程度，常见工具如下：

1. **显性焦虑量表（MAS）**：由泰勒按理论推理法建构，依据卡默龙的慢性焦虑反应概念编制；初始项目从MMPI中选出，由反应项目和缓冲项目组成。

2. **状态—特质焦虑量表（STAI）**：由斯皮尔伯格等人根据状态—特质理论编制，包括状态焦虑和特质焦虑两个部分。【名词解释：状态—特质焦虑量表】

3. **测验焦虑量表（TAI）**：由斯皮尔伯格等人根据状态—特质理论编制，测量W因素和E因素。（W因素涉及对失败结果的认知，E因素涉及评价紧张引起的自主神经系统反应。）

4. **贝克焦虑量表（BAI）**：主要测量受测者主观感受到的焦虑程度。

5. **汉密尔顿焦虑量表（HAMA）**：用于评定神经症病人和其他病人的焦虑严重程度。

综上，不同焦虑测验分别侧重显性焦虑、状态与特质焦虑、测验焦虑和临床焦虑严重程度，应依据测量目的选用。
"""


def update_guide(text: str) -> str:
    assert text.count(GUIDE_OLD) == 1
    return text.replace(GUIDE_OLD, GUIDE_NEW, 1)


def parenthesize_example_lines(text: str) -> str:
    lines: list[str] = []
    pattern = re.compile(r"^(（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])\*\*(实例|应用实例)\*\*：(.+)$")
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            prefix, label, content = match.groups()
            line = f"{prefix}（**{label}**：{content}）"
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def fold_standalone_expansions(text: str) -> str:
    lines = text.splitlines()
    rebuilt: list[str] = []
    pattern = re.compile(
        r"^(?:（\d+）|[①②③④⑤⑥⑦⑧⑨⑩])（\*\*(?:实例|应用实例)\*\*：(.+)）$"
    )
    for line in lines:
        match = pattern.match(line)
        if not match:
            rebuilt.append(line)
            continue
        index = len(rebuilt) - 1
        while index >= 0 and not rebuilt[index].strip():
            index -= 1
        assert index >= 0
        expansion = match.group(1)
        tag = re.search(r"【名词解释：[^】]+】$", rebuilt[index])
        if tag:
            rebuilt[index] = rebuilt[index][: tag.start()] + f"（{expansion}）" + tag.group(0)
        else:
            rebuilt[index] += f"（{expansion}）"
    return "\n".join(rebuilt) + ("\n" if text.endswith("\n") else "")


def remove_unit(text: str, title: str) -> str:
    match = re.search(rf"^## [^\n]*{re.escape(title)}[^\n]*\n", text, re.MULTILINE)
    assert match, title
    next_heading = re.search(r"^# ", text[match.end() :], re.MULTILINE)
    assert next_heading, title
    end = match.end() + next_heading.start()
    start = match.start()
    while start > 1 and text[start - 2 : start] == "\n\n":
        start -= 1
    return text[:start] + text[end:]


def remove_chapter(text: str, title: str) -> str:
    match = re.search(rf"^# [^\n]*{re.escape(title)}[^\n]*\n", text, re.MULTILINE)
    assert match, title
    next_heading = re.search(r"^# ", text[match.end() :], re.MULTILINE)
    assert next_heading, title
    end = match.end() + next_heading.start()
    return text[: match.start()] + text[end:]


def remove_unit_block(text: str, title: str) -> str:
    match = re.search(rf"^## [^\n]*{re.escape(title)}[^\n]*\n", text, re.MULTILINE)
    assert match, title
    next_heading = re.search(r"^#{1,2} ", text[match.end() :], re.MULTILINE)
    assert next_heading, title
    end = match.end() + next_heading.start()
    return text[: match.start()] + text[end:]


def build_general() -> str:
    text = update_guide(GENERAL_SOURCE.read_text(encoding="utf-8"))
    text = replace_question(text, "心理学的**基本任务**", BASIC_TASKS)
    text = replace_question(text, "心理学的主要研究领域", RESEARCH_FIELDS)

    heading_replacements = {
        "### 押题1【论述】论述记忆的主要类型，并结合实例说明。":
            "### 押题1【论述】论述记忆的主要类型及其特点。",
        "### 押题1【论述】结合实例论述遗忘的原因，并说明如何减少遗忘。":
            "### 押题1【论述】论述遗忘的原因，并说明如何减少遗忘。",
        "### 押题1【简答】情绪的核心功能有哪些？请举例说明。":
            "### 押题1【简答】简述情绪的核心功能。",
        "### 押题1【论述】结合实例论述皮亚杰的认知发展理论及其教育启示。":
            "### 押题1【论述】论述皮亚杰的认知发展理论及其教育启示。",
        "### 押题1【论述】结合实例论述埃里克森心理社会性发展的八个阶段及其教育启示。":
            "### 押题1【论述】论述埃里克森心理社会性发展的八个阶段及其教育启示。",
    }
    for old, new in heading_replacements.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)

    text = parenthesize_example_lines(text)
    replacements = {
        "①**实例与应对**：学习后长期不复习，内容会逐渐模糊；因此应及时复习并合理重复。":
            "①应**及时复习、经常复习**。（长期不复习时记忆痕迹会逐渐减弱。）",
        "①**实例与应对**：先学内容干扰后学内容称前摄抑制，后学内容干扰先学内容称倒摄抑制；应减少相似材料连续学习并交替安排不同科目。":
            "①干扰包括**前摄抑制和倒摄抑制**。（复习时可减少相似材料连续学习，并交替安排不同科目。）",
        "①**实例与应对**：个体可能回避提取引起强烈痛苦的经历；调节情绪和形成安全情境有助于恢复提取。":
            "①压抑解除后，记忆可能恢复。（个体可能回避提取引起强烈痛苦的经历，可通过调节情绪和形成安全情境帮助恢复提取。）",
        "①**实例与应对**：考试时暂时想不起、离开考场后在相关线索下想起，可能属于提取失败；可利用编码特异性和多重线索。":
            "①应使用**有效的提取线索**。（考试时暂时想不起、在相关线索下又想起，可能属于提取失败。）",
        "①**实例与应对**：复习应及时开始，并根据遗忘速度逐步延长间隔。":
            "①应**及时复习、正确分配复习时间**。（可以根据遗忘速度逐步延长复习间隔。）",
        "①**应对**：可将材料意义化、形象化并控制每次学习量。":
            "①应**控制学习材料数量，并把材料形象化**。（还可以通过意义加工提高编码质量。）",
        "①**实例与应对**：可调整复习顺序，使不同内容轮流处于开头或结尾位置。":
            "①应合理安排材料顺序。（可使不同内容轮流处于开头或结尾位置。）",
    }
    for old, new in replacements.items():
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    text = fold_standalone_expansions(text)
    text = text.replace(
        "（它可进一步分为情景记忆和语义记忆。）（能够说出某一历史事件属于陈述性记忆。）",
        "（它可进一步分为情景记忆和语义记忆；例如，能够说出某一历史事件属于陈述性记忆。）",
        1,
    )
    return align_shared_definitions(canonicalize_definitions(text))


def build_experiment() -> str:
    text = update_guide(EXPERIMENT_SOURCE.read_text(encoding="utf-8"))
    text = replace_question(text, "科学方法的主要特征", EXPERIMENT_SCIENCE)
    text = replace_question(text, "主要伦理原则", EXPERIMENT_ETHICS)
    text = remove_chapter(text, "如何读和写心理实验报告")
    assert "# 第三章 如何读和写心理实验报告" not in text
    text = text.replace("# 第四章 反应时", "# 第三章 反应时", 1)
    text = text.replace("# 第五章 心理物理学", "# 第四章 心理物理学", 1)
    text = remove_unit_block(text, "反应时研究的历史")
    for old, new in (
        ("## 二、反应时的含义与种类", "## 一、反应时的含义与种类"),
        ("## 三、反应时的影响因素", "## 二、反应时的影响因素"),
        ("## 四、减数法与加因素法", "## 三、减数法与加因素法"),
        ("## 五、序列反应时与内隐联想测验", "## 四、序列反应时与内隐联想测验"),
    ):
        assert text.count(old) == 1
        text = text.replace(old, new, 1)
    text = replace_question(text, "传统测量方法及主要误差", TRADITIONAL_PSYCHOPHYSICS)
    text = replace_question(text, "阈上感觉量表的主要建立方法", SUPRATHRESHOLD_SCALING)
    text = text.replace(
        "创造**最小变化法、恒定刺激法和平均差误法**，使心理现象得以量化描述",
        "创造**最小可觉差法、正误法和均差法**，使心理现象得以量化描述",
        1,
    )
    return align_shared_definitions(canonicalize_definitions(text))


def build_measurement() -> str:
    text = update_guide(MEASUREMENT_SOURCE.read_text(encoding="utf-8"))
    text = replace_question(text, "测量的**含义、构成和基本要素**", MEASUREMENT_MEANING)
    text = replace_question(text, "比较**16PF、MMPI和EPQ**", PERSONALITY_SCALES)
    text = replace_question(text, "影响信度系数的**主要因素**", RELIABILITY_FACTORS)
    text = replace_question(text, "常见的焦虑、抑郁及发展测验", ANXIETY_TESTS)
    text = text.replace("## 一、常见临床心理测验【★】", "## 一、常见焦虑测验【★】", 1)
    old = "### 押题1【简答】组内常模指的是什么？请**举例说明**其应用。"
    new = "### 押题1【简答】简述组内常模的含义、种类及分数解释。"
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    text = parenthesize_example_lines(text)
    text = fold_standalone_expansions(text)
    old = (
        "（4）**认知诊断模型**：把题目属性变量、被试认知状态变量和作答反应变量联系起来，"
        "用于估计每名被试的属性掌握模式。（DINA模型只引入失误和猜测两个参数，是常用模型之一。）"
    )
    new = (
        "（4）**认知诊断模型**：是指认知诊断所用的测量模型。"
        "（它把题目属性变量、被试认知状态变量和作答反应变量联系起来；DINA模型只引入失误和猜测两个参数。）"
    )
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    text = text.replace(
        "1. **罗夏克墨迹测验**：使用墨迹图，要求受测者自由联想并表达对图案的看法，适合个别施测，常用于人格和精神障碍评估；其主要局限是评分困难、对主试要求高。【名词解释：罗夏克墨迹测验】",
        "1. **罗夏克墨迹测验**：使用墨迹图，要求受测者自由联想并表达对图案的看法，适合个别施测，常用于人格和精神障碍评估；其主要局限是评分困难、对主试要求高。（典型材料为10张墨迹图，作答没有固定答案。）【名词解释：罗夏克墨迹测验】",
        1,
    )
    old = (
        "（2）**离差智商**：个体智力测验分数在**同年龄组中的标准分数**，**由韦克斯勒在儿童智力量表中首先采用**。"
        "（常用形式为**IQ＝100＋15Z**，表示个体相对同龄常模团体的位置。）【名词解释：离差智商】"
    )
    new = old.replace(
        "。）【名词解释",
        "；例如，离差智商115表示高于同龄组平均数一个标准差，并不表示智力是平均水平的1.15倍。）【名词解释",
    )
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    old = (
        "2. 组内常模的**应用实例及解释限制**如下："
        "（某儿童在同年龄常模中获得离差智商115，表示其成绩高于同龄组平均数一个标准差，"
        "而不是表示其智力是**平均儿童的1.15倍**。）\n\n\n（2）**解释限制**："
    )
    new = "2. 组内常模的**解释限制**如下：\n\n（1）**解释限制**："
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    return align_shared_definitions(canonicalize_definitions(text))


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
