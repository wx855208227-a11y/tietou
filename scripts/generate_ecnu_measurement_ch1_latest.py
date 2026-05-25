from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import re
from zipfile import ZipFile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from lxml import etree
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs/ecnu-347/measurement-psychology"
DELIVER = ROOT / "deliverables/ecnu-measurement-ch1-latest"
SOURCE_V11 = BASE / "chapter-01-yibentong-v11.md"
LATEST_MD = DELIVER / "华东347测量心理学一本通_第1章_最新标准版.md"
OUTPUT_DOCX = DELIVER / "华东347测量心理学一本通_第1章_最新标准版.docx"
OUTPUT_XLSX = DELIVER / "华东347测量心理学一本通_第1章_审核表.xlsx"
FORMAT_SAMPLE = ROOT / "skills/tietou-yibentong-compilation/references/format-samples/shenda-general-psychology-yibentong-format-sample.docx"

TIP_LABELS = {"**Tips**", "Tips", "**铁头tips**", "铁头tips"}

REVISED_MARKDOWN = r"""# 第一章 心理测量和测验的历史回顾

现代**心理测量和测验**形成于**19世纪欧洲**，直接动因是<u>评定心理特征的个别差异</u>。

心理测验是一种**工具性实用技术**，核心任务是<u>用有效方法对心理差异进行定量刻画</u>。

心理测量与**实验方法**共同构成心理学实证研究的两大范式：心理测量偏重<u>个体差异的测定</u>，实验方法偏重<u>变量关系的控制与解释</u>。

## 第一节 中国古代的心理测量思想和实践P3（三级）

1.**心理测量完整实践的三个前提**

（1）**可测性**：<u>肯定心理特征存在个别差异，并且这种差异可以测量</u>。

（2）**测量内容**：明确<u>要测量何种心理特征</u>，并能用相应理论加以说明。

（3）**测量方法**：在阐明心理内容差异的基础上，<u>把测量内容操作化，并以适当形式呈现</u>。

2.**关于个别差异的思想**

（1）**孔子**提出“**性相近也，习相远也**”，说明人的后天行为表现存在明显差异。

（2）孔子提出“**上智**”“**下愚**”等说法，体现<u>把人的智力划分为不同类别的分类思想</u>。

3.**关于心理可测性的思想**

（1）**孟子**提出“**权，然后知轻重；度，然后知长短。物皆然，心为甚**”。

（2）这句话的测量意义在于：<u>心理能力和心理特征也具有可以测量的特性</u>。

4.**关于人才评定的思想**

（1）**刘劭**《**人物志**》服务于**察举用人**和**品鉴人才**，关注人的形质、人性、才具和志业。

（2）刘劭提出“**考课核实**”，实质是<u>从外部行为观察内部心理</u>，体现内部心理与外部行为相统一的原则。

（3）“**八观与五视**”用于减少观察误差，针对的是<u>观察者主观偏好和被观察者表里不一</u>两类问题。

5.**中国古代的测量实践**

（1）**科举取士制度**是最有代表性的心理与教育测量实践，初萌于**商周**，兴盛于**隋唐**，延续至清末。

（2）科举制度的测量意义在于：有**选拔目的**、相对稳定的**测验内容**，并形成**帖经**、**墨义**、**口义**、**策论**、**诗赋**等形式。

（3）民间与教育测量活动包括《**学记**》、《**礼记·本命**》、“**周岁试儿**”、**七巧板**和**九连环**等，分别涉及教育测验、年龄发展线索、婴儿行为诊断、空间想象和问题解决。

## 第二节 近代心理测量的早期尝试与先驱者的探索P6（二级）

### 一、早期对智力落后儿童的分类与训练的兴趣P6

1.**产生原因**

19世纪以前，**智力落后者**常被与**精神异常者**混同。特殊医疗与教育机构的发展，使人们需要<u>建立标准而客观的分类方法</u>。

2.**艾斯克罗的贡献**

（1）**艾斯克罗**正式区分**智力落后者**和**精神异常者**。

（2）他认为智力落后在程度上连续分布，并发现<u>语言能力是判断智力水平的重要指标</u>。

3.**沈干的贡献**

（1）**沈干**是**训练智力落后者的先驱**，反对把智力落后简单看作不可治疗。

（2）他提出“**心理训练法**”，于**1837年**创办第一所教育智力落后儿童的学校。

（3）他的训练方法包括**感官训练**和**肌肉训练**，目的是<u>通过感觉辨别力训练促进动作控制的发展</u>。

（4）**沈氏拼图板**被心理测验中的非语言测验采用，要求受测者<u>尽快把不同形状的图片嵌入相应凹槽</u>。

4.**比奈的前期推动**

比奈后来推动建立鉴别<u>不能适应正常学校学习但仍可教育的儿童</u>的方法；以比奈为首的专门研究小组成立，是心理测验发展史上的重要事件。

### 二、冯特实验心理学的影响P7（三级）

1.**基本立场**

19世纪实验心理学主要寻找行为的一般原则，关注**一致性**而非**差异性**；个体差异常被视为误差。

2.**研究内容的影响**

早期实验心理学重视**视觉**、**听觉**、感觉器官敏感性和**反应时**，这些内容进入早期心理测验。

3.**研究方法的影响**

实验心理学强调**情境控制**，这种思想后来演变为心理测验中的**标准化**。

**标准化**的核心意义是：<u>在统一情境下观察所有受试者</u>。

### 三、高尔顿的理想和贡献P8

1.**地位**

**高尔顿**首先提出“**测验**”和“**心理测量**”两个术语，是<u>直接推动测验运动发展的第一人</u>。

2.**测量理想**

高尔顿从遗传研究出发，主张测量人的各种特质，并试图<u>通过感觉器官辨别力估量智力</u>。

3.**实际测验活动**

**1884年**，高尔顿设立“**人体测量学实验室**”，测量身高、体重、视觉和听觉敏锐度、肌肉强度、反应时等，并积累**9337人**资料。

4.**方法与工具贡献**

高尔顿设计**高尔顿棒**、**高尔顿哨**等仪器，并较早采用**评定量表**、**问卷法**和**自由联想技术**。

5.**统计贡献**

高尔顿发展个别差异资料的统计分析方法，提出**相关**概念；其学生**皮尔逊**后来完善相关计算方法。

### 四、卡特尔及其早期个别差异研究P9

1.**地位**

**卡特尔**在**1890年**发表《**心理测验与测量**》，这是“**心理测验**”一词第一次出现在心理学文献中。

2.**测验编制观点**

（1）心理学必须建立在**实验与测量**基础上，才能具有自然科学的准确性。

（2）测验必须规定**统一程序**，使不同时间、地点获得的结果<u>能够比较和综合</u>。

3.**测验项目**

卡特尔的测验项目包括**握力**、**动作速度**、**触觉两点阈**、**痛觉阈**、**重量辨别**、**声音反应时**、**颜色命名速度**、**线段平分**、**时间判断**和**字母复述**。

4.**不足与意义**

这些测验试图<u>通过感觉辨别力和反应时测量智力功能</u>，但与教师评定、学习成绩等外部指标相关较低，促使研究者转向复杂心理功能测量。

5.**复杂心理功能测验的转向**

（1）**克雷丕林**建议在**精神病理学**中使用测验，测量练习效果、记忆力、疲劳和分心易感性等。

（2）**艾宾浩斯**于**1896年**首创复杂的**语句完成测验**，该测验与儿童学业成就显著相关。

（3）**比奈与亨利**批评早期测验过分强调感觉，主张测量**记忆力**、**想象力**、**注意力**、**理解力**、**受暗示性**、**道德情感**和**意志力**等复杂功能。

（4）这一转向说明：心理测验逐渐从<u>简单感觉和反应时测量</u>，转向<u>复杂高级心理功能测量</u>。

**铁头tips**

现代智力测验形成路径P7-P11

![现代智力测验形成路径](assets/modern-intelligence-test-path.png)

## 第三节 社会需要是心理测量和测验发展的动力P10（二级）

科学的发展源于实际需要，**心理测量**的发展也是如此。社会需要是<u>心理测量和测验发展的动力</u>。

### 一、比奈和世界上第一个智力测验P11（一级）【20年真题】【选择】

1.**地位**

**比奈**被称为**心理测验的鼻祖**。世界上第一个真正意义上的智力测验，是**比奈—西蒙量表**（又译**比内—西蒙量表**）。

2.**测量路径的转变**

（1）比奈早期尝试用头盖骨、脸形、手形、字迹等指标评定智力，但这些指标无法有效判断个体智力。

（2）比奈由此转向<u>从智力本身及其外显操作结果入手</u>，用更接近智力活动的任务进行测量。

3.**比奈的智力观**

（1）**1903年**，比奈出版《**智力的实验研究**》。

（2）他认为智力包含一切高级心理过程，主要表现为**推理**、**判断**和**运用旧知识解决新问题**的能力。

（3）比奈的核心主张是：<u>直接选择广泛而复杂的课题来测量智力</u>。

4.**比奈—西蒙量表的产生**

（1）**1904年**，法国教育部委托比奈研究教育智力落后儿童的方法。

（2）比奈与**西蒙**合作完成**比奈—西蒙量表**。

（3）**1905年**，比奈在《**心理学年报**》发表《**诊断异常儿童的新方法**》，详细介绍该量表，因此又称**1905年量表**。

（4）**1908年**和**1911年**，比奈两次修订该量表；**1916年**，美国斯坦福大学**推孟**修订该量表，形成**斯坦福—比奈量表**。

5.**真题对应**

**1905年**对应**比奈—西蒙量表**，其地位是<u>世界上第一个真正意义上的智力测验</u>。

**铁头tips**

例如  比奈不再用“头大不大、手长不长”判断儿童聪不聪明，而是让儿童完成词语、图片解释、推理判断等任务。这样更像直接观察儿童怎样思考，而不是只看身体外形这些间接线索。

**铁头tips**

易混提示：**比奈/比内译名**

教材常写作**比奈**，部分真题或资料会写作**比内**，二者通常指同一人 **A. Binet**。看到“**比内—西蒙量表**”时，要对应到教材中的**比奈—西蒙量表**。

**铁头tips**

易混辨析：**比奈—西蒙量表**与**斯坦福—比奈量表**P11

| 对比项 | **比奈—西蒙量表** | **斯坦福—比奈量表** |
| --- | --- | --- |
| 时间 | **1905年** | **1916年** |
| 编制/修订者 | **比奈**与**西蒙** | 斯坦福大学**推孟**修订 |
| 地位 | <u>世界上第一个真正意义上的智力测验</u> | 比奈量表在美国的重要修订版 |
| 易混点 | “1905年第一个智力测验”对应它 | 不要把1916年的修订版误当成1905年原始量表 |

### 二、团体测验的产生P11

1.**产生原因**

**团体测验**的产生，是<u>大规模筛查和分类需要</u>推动的结果。

2.**个别测验的限制**

**比奈—西蒙量表**属于**个别测验**：每次只能施测一名受测者，许多题目需要口头反应或操作材料，主试训练要求较高，更适合临床个案分析。

3.**第一次世界大战的推动**

**1917年**，美国心理学会在**耶克斯**指导下，试图根据士兵一般智力水平进行快速分类、安置和选拔，个别测验无法满足这种大规模需要。

4.**奥提斯的贡献**

**奥提斯**的团体智力测验是重要基础，其主要贡献是<u>首先使用多项选择题和其他客观题形式</u>。

5.**陆军测验**

（1）**陆军A式量表**，又称**陆军甲种测验**，属于**文字测验**。

（2）**陆军B式量表**，又称**陆军乙种测验**，属于**非文字测验**，适用于文盲和不懂英语的新兵。

6.**意义**

团体测验能够同时施测大量受测者，并简化指导语和施测程序，<u>推动了20世纪20年代测验运动的蓬勃发展</u>。

**铁头tips**

易混辨析：**个别测验**与**团体测验**P11

| 对比项 | **个别测验** | **团体测验** |
| --- | --- | --- |
| 施测对象 | 每次主要测一名受测者 | 可同时测很多人 |
| 施测要求 | 主试训练要求较高，常需口头反应或操作材料 | 指导语和程序更简化，适合大规模施测 |
| 代表测验 | **比奈—西蒙量表** | **陆军甲种测验**、**陆军乙种测验** |
| 适用场景 | 临床个案、深入分析 | 军队、学校、选拔、筛查 |
| 记忆抓手 | “一对一精细测” | “一批人快速筛” |

## 第四节 心理测量和测验在我国的发展P13（三级）

### 一、1949年之前心理测验的发展和停滞P13

1.**西方心理测验的引入及其迅猛发展**

（1）20世纪初，科学心理测验传入中国，并首先在教育领域发展。

（2）关键节点包括：**1916年**樊炳清介绍**比奈—西蒙智力量表**；**1922年**费培杰将比奈—西蒙量表译成中文，命名为“**儿童心智发展测量法**”。

（3）中国早期心理测量运动的发展，主要得益于<u>教育部门倡导新法考试</u>和<u>心理学者探索测验方法</u>。

2.**中国测验学会成立与繁荣**

（1）**1931年**，**中国测验学会**在南京成立，标志着中国心理和教育测验进入新的历史时期。

（2）**1932年**，学会会刊《**测验**》创刊，心理测验理论研究、量表编制和使用范围继续扩大。

3.**停滞原因**

测验运动后来走向停滞，主要与<u>滥用测验、施测训练不足、结果解释不慎重</u>以及抗日战争后工作中断有关。

### 二、1949年之后心理测量和测验的发展P14

1.**停止发展的时期**

**1949年至1978年**，心理测验在我国长期被视为禁区，教学、研究和应用基本停止。

这一阶段的主要影响因素包括：苏联批判**儿童学**、否认个别差异，以及特殊社会环境对心理学的批判。

2.**重新蓬勃发展的时期**

（1）**1978年**以后，心理学恢复，心理测量和测验重新发展。

（2）**1978年**，北京师范大学和**华东师范大学**等高校招收首批心理测量专业研究生。

（3）**1979年**，武汉举办第一个全国性心理测验培训班，标志着系统的心理测验工作在我国再度出现。

（4）恢复初期引进**经典测验理论（CTT）**、**概化理论（GT）**和**项目反应理论（IRT）**；20世纪80年代中期以后，开始编制适合中国人的心理测验工具。

## 第五节 改革开放40多年来我国心理测量和测验发展概述P15（三级）

### 一、往事回顾P16

改革开放初期的重要事件主要包括：**心理测量专业研究生招生和培养**、**全国性心理测验培训班**、**全国范围心理量表协作修订**、**心理测量专业委员会成立**、一批有影响的专著与论文出版，以及**海峡两岸心理与教育测量学术研讨会**开展。

这些事件共同推动了我国心理测量从恢复走向规范化、组织化和专业化。

### 二、心理测量迅猛发展的特点评述P18

1.**心理测验和量表增多，质量提升**

认知类、非认知类、职业类、临床类、儿童发展类等测验不断增加，量表标准化程度也在提高。

2.**应用领域不断扩大**

心理测验进入教育、医学、企业、组织人事、司法、心理健康和特殊儿童评估等领域。

3.**理论与技术现代化**

测验研发依托**CTT**、**IRT**、**GT**等测量理论，并结合多元统计、结构方程模型、计算机化测验和**计算机自适应测验（CAT）**。

### 三、对存在问题和未来前景的几点思考P23

1.**组织与研究机构建设**

心理测量发展需要发挥专业学会作用，并建立专门研究机构，推动测验修订、编制、鉴定和培训。

2.**产学研与商业化**

心理测验具有强应用性，研究成果需要转化为实际产品和服务，但必须以科学性、规范性和版权意识为前提。

3.**量表修订与自主编制**

修订国外量表要重视**版权**、**跨文化改造**和**标准化**；自主编制量表要扎根中国文化情境，并遵循规范的测验理论和编制程序。

4.**未来方向**

我国心理测量未来发展的关键是<u>规范化、标准化、本土化和计算机化</u>。
"""


def set_east_asia_font(run, name="宋体"):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)


def format_run(run, *, size=12, bold=False, underline=False, font="宋体"):
    set_east_asia_font(run, font)
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0, 0, 0)
    if bold:
        run.bold = True
    if underline:
        run.underline = True


def set_p_shading(paragraph, fill="DAE3F3"):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = p_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        p_pr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)


def set_p_double_border(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    borders = p_pr.find(qn("w:pBdr"))
    if borders is None:
        borders = OxmlElement("w:pBdr")
        p_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        element = borders.find(qn("w:" + edge))
        if element is None:
            element = OxmlElement("w:" + edge)
            borders.append(element)
        element.set(qn("w:val"), "double")
        element.set(qn("w:color"), "000000")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")


def set_paragraph_spacing(paragraph, *, before=0, after=0, line=1.5):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def set_keep(paragraph, *, together=False, next=False):
    fmt = paragraph.paragraph_format
    fmt.keep_together = together
    fmt.keep_with_next = next


def force_style_black(doc, style_ids):
    for style in doc.styles:
        if style.style_id not in style_ids:
            continue
        if hasattr(style, "font"):
            style.font.color.rgb = RGBColor(0, 0, 0)
        for color in style._element.xpath(".//w:color"):
            color.set(qn("w:val"), "000000")
            for attr in ("themeColor", "themeTint", "themeShade"):
                color.attrib.pop(qn("w:" + attr), None)


def add_inline_runs(paragraph, text, *, size=12, force_bold=False):
    pattern = re.compile(r"(\*\*.*?\*\*|<u>.*?</u>)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            run = paragraph.add_run(text[pos:match.start()])
            format_run(run, size=size, bold=force_bold)
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            format_run(run, size=size, bold=True)
        else:
            run = paragraph.add_run(token[3:-4])
            format_run(run, size=size, underline=True, bold=force_bold)
        pos = match.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        format_run(run, size=size, bold=force_bold)


def clean_source_text():
    return REVISED_MARKDOWN.strip() + "\n"


def setup_document(doc):
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.18)
    section.right_margin = Cm(3.18)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.75)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    h1 = doc.styles["Heading 1"]
    h1.font.name = "宋体"
    h1._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor(0, 0, 0)
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.line_spacing = 2.4
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(12)
    h1.paragraph_format.keep_with_next = True

    h2 = doc.styles["Heading 2"]
    h2.font.name = "宋体"
    h2._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    h2.font.size = Pt(14)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor(0, 0, 0)
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h2.paragraph_format.line_spacing = 1.73
    h2.paragraph_format.space_before = Pt(8)
    h2.paragraph_format.space_after = Pt(8)
    h2.paragraph_format.keep_with_next = True

    h3 = doc.styles["Heading 3"]
    h3.font.name = "宋体"
    h3._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    h3.font.size = Pt(12)
    h3.font.bold = True
    h3.font.color.rgb = RGBColor(0, 0, 0)
    h3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h3.paragraph_format.line_spacing = 1.72
    h3.paragraph_format.space_before = Pt(8)
    h3.paragraph_format.space_after = Pt(8)
    h3.paragraph_format.keep_with_next = True

    force_style_black(doc, {
        "Heading1", "Heading2", "Heading3",
        "Heading1Char", "Heading2Char", "Heading3Char",
        "TOCHeading", "TOC1", "TOC2", "Hyperlink", "FollowedHyperlink",
        "LightShading-Accent1",
    })


def add_center_paragraph(doc, text, *, size, font="华文楷体", bold=True, before=0, after=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, before=before, after=after, line=1.0)
    run = p.add_run(text)
    format_run(run, size=size, bold=bold, font=font)
    return p


def add_cover(doc):
    add_center_paragraph(doc, "铁头心理", size=26, before=28, after=18)
    add_center_paragraph(doc, "重难点一本通", size=48, before=8, after=16)
    add_center_paragraph(doc, "（华东师范大学347应用心理专用）", size=26, before=6, after=36)
    add_center_paragraph(doc, "测量心理学", size=72, before=12, after=46)
    add_center_paragraph(doc, "参考书目：", size=26, before=10, after=8)
    add_center_paragraph(doc, "《测量心理学》（第三版）", size=26, before=0, after=70)
    add_center_paragraph(doc, "版权所有，违者必究", size=10, before=40, after=0)
    doc.add_section(WD_SECTION.NEW_PAGE)


def add_toc(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_spacing(p, after=16)
    run = p.add_run("目录")
    format_run(run, size=26, bold=True)

    toc_entries = [
        (1, "第一章 心理测量和测验的历史回顾", "1"),
        (2, "第一节 中国古代的心理测量思想和实践", "1"),
        (2, "第二节 近代心理测量的早期尝试与先驱者的探索", "2"),
        (2, "第三节 社会需要是心理测量和测验发展的动力", "5"),
        (2, "第四节 心理测量和测验在我国的发展", "7"),
        (2, "第五节 改革开放40多年来我国心理测量和测验发展概述", "8"),
    ]

    for idx, (level, title, page) in enumerate(toc_entries):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0 if level == 1 else 0.74)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(14.6), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        set_paragraph_spacing(p, after=1, line=1.15)
        run = p.add_run()
        if idx == 0:
            fld_begin = OxmlElement("w:fldChar")
            fld_begin.set(qn("w:fldCharType"), "begin")
            instr = OxmlElement("w:instrText")
            instr.set(qn("xml:space"), "preserve")
            instr.text = 'TOC \\o "1-2" \\h \\u'
            fld_separate = OxmlElement("w:fldChar")
            fld_separate.set(qn("w:fldCharType"), "separate")
            run._r.append(fld_begin)
            run._r.append(instr)
            run._r.append(fld_separate)
        run.add_text(title)
        run.add_tab()
        run.add_text(page)
        if idx == len(toc_entries) - 1:
            fld_end = OxmlElement("w:fldChar")
            fld_end.set(qn("w:fldCharType"), "end")
            run._r.append(fld_end)
        format_run(run, size=11)

    set_update_fields(doc)
    doc.add_section(WD_SECTION.NEW_PAGE)


def set_update_fields(doc):
    settings = doc.settings.element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def add_page_number(section):
    section.footer.is_linked_to_previous = False
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    format_run(run, size=14)


def is_markdown_image(line):
    return re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", line.strip()) is not None


def image_path_from_line(line):
    match = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", line.strip())
    if not match:
        return None
    path = Path(match.group(1))
    return path if path.is_absolute() else BASE / path


def is_markdown_table_start(lines, index):
    if index + 1 >= len(lines):
        return False
    first = lines[index].strip()
    second = lines[index + 1].strip()
    return first.startswith("|") and first.endswith("|") and re.match(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|$", second) is not None


def parse_markdown_table(lines, start):
    table_lines = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
        table_lines.append(lines[i].strip())
        i += 1
    rows = []
    for idx, line in enumerate(table_lines):
        if idx == 1:
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows, i


@lru_cache(maxsize=1)
def sample_tip_label_element():
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(FORMAT_SAMPLE) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
    for paragraph in root.xpath(".//w:p", namespaces=ns):
        text = "".join(paragraph.xpath(".//w:t/text()", namespaces=ns)).strip()
        if text == "铁头tips铁头tips":
            return paragraph
    return None


def insert_tip_label(doc):
    sample = sample_tip_label_element()
    if sample is not None:
        label = deepcopy(sample)
        doc._body._element.insert_element_before(label, "w:sectPr")
        return
    p = doc.add_paragraph()
    run = p.add_run("铁头tips")
    format_run(run, size=10, bold=True)


def add_body_paragraph(doc, text):
    p = doc.add_paragraph()
    set_paragraph_spacing(p, after=2)
    stripped = text.strip()
    is_list = bool(re.match(r"^(\d+\.|（\d+）|[①②③④⑤⑥⑦⑧⑨⑩]|[A-Z]\.|[a-z]\.)", stripped))
    if not is_list:
        p.paragraph_format.first_line_indent = Cm(0.74)
    add_inline_runs(p, stripped, size=12)
    return p


def add_heading(doc, level, text):
    style = f"Heading {level}"
    p = doc.add_paragraph(style=style)
    p.clear()
    add_inline_runs(p, text, size=16 if level == 1 else 14 if level == 2 else 12, force_bold=True)
    set_keep(p, together=True, next=True)
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def set_cell_margins(cell, *, top=80, start=120, bottom=80, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.find(qn("w:tcMar"))
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for name, value in {"top": top, "start": start, "bottom": bottom, "end": end}.items():
        element = margins.find(qn("w:" + name))
        if element is None:
            element = OxmlElement("w:" + name)
            margins.append(element)
        element.set(qn("w:w"), str(value))
        element.set(qn("w:type"), "dxa")


def set_cell_shading(cell, fill="F2F2F2"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    if tr_pr.find(qn("w:cantSplit")) is None:
        tr_pr.append(OxmlElement("w:cantSplit"))


def add_markdown_table(doc, rows, *, font_size=10, in_tip=False):
    table = doc.add_table(rows=len(rows), cols=max(len(r) for r in rows))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for r_idx, row in enumerate(rows):
        prevent_row_split(table.rows[r_idx])
        for c_idx, cell in enumerate(table.rows[r_idx].cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            if r_idx == 0:
                set_cell_shading(cell, "DBE3F4" if in_tip else "EDEDED")
            elif in_tip:
                set_cell_shading(cell, "DAE3F3")
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_paragraph_spacing(para, after=0, line=1.15)
            text = row[c_idx] if c_idx < len(row) else ""
            add_inline_runs(para, text, size=font_size)
            if r_idx == 0:
                for run in para.runs:
                    run.bold = True
    spacer = doc.add_paragraph()
    set_paragraph_spacing(spacer, after=3)


def add_tip_table_block(doc, title, rows):
    doc.add_page_break()
    insert_tip_label(doc)
    if title:
        add_tip_paragraph(doc, title, title=True)
    add_markdown_table(doc, rows, font_size=10, in_tip=True)
    doc.add_paragraph()


def add_tip_paragraph(doc, text="", *, title=False, source=False):
    p = doc.add_paragraph()
    set_p_shading(p, "DBE3F4" if title else "DAE3F3")
    set_paragraph_spacing(p, after=0)
    if title:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_inline_runs(p, text, size=12, force_bold=True)
    elif source:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        add_inline_runs(p, text, size=12)
    else:
        p.paragraph_format.first_line_indent = Cm(0.74)
        add_inline_runs(p, text, size=12)
    return p


def add_tip_block(doc, tip_lines):
    if not tip_lines:
        return
    insert_tip_label(doc)
    first = tip_lines[0]
    body = tip_lines[:]
    title = None
    if not first.startswith("例如") and not is_markdown_image(first) and not first.startswith("|"):
        plain = re.sub(r"\*\*|<u>|</u>", "", first)
        if len(plain) <= 45 or first.startswith(("易混", "图示", "现代")):
            title = first
            body = tip_lines[1:]
    if title:
        add_tip_paragraph(doc, title, title=True)
    for line in body:
        if is_markdown_image(line):
            p = doc.add_paragraph()
            set_p_shading(p, "DAE3F3")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(str(image_path_from_line(line)), width=Cm(14.5))
            continue
        if line.startswith("|"):
            continue
        if line.startswith("【") and line.endswith("】"):
            add_tip_paragraph(doc, line, source=True)
        else:
            add_tip_paragraph(doc, line)
    doc.add_paragraph()


def add_supplement_box(doc, lines):
    for idx, line in enumerate(lines):
        p = doc.add_paragraph()
        set_p_double_border(p)
        set_paragraph_spacing(p, after=0)
        if idx == 0:
            add_inline_runs(p, line, size=12, force_bold=True)
        elif len(line) <= 24 and not line.endswith("。"):  # title line
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline_runs(p, line, size=12, force_bold=True)
        else:
            p.paragraph_format.first_line_indent = Cm(0.74)
            add_inline_runs(p, line, size=12)
    doc.add_paragraph()


def collect_tip_lines(lines, start):
    collected = []
    i = start
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped in TIP_LABELS or stripped.startswith("#"):
            break
        if not stripped:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j >= len(lines) or lines[j].strip() in TIP_LABELS or lines[j].strip().startswith("#"):
                break
            i += 1
            continue
        collected.append(stripped)
        i += 1
    return collected, i


def build_docx(markdown_text):
    doc = Document()
    setup_document(doc)
    add_cover(doc)
    add_toc(doc)
    add_page_number(doc.sections[-1])
    lines = markdown_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line in TIP_LABELS:
            tip_lines, i = collect_tip_lines(lines, i + 1)
            if tip_lines and tip_lines[0].startswith("补充内容："):
                add_supplement_box(doc, tip_lines)
            else:
                table_idx = next((idx for idx in range(len(tip_lines)) if is_markdown_table_start(tip_lines, idx)), None)
                if table_idx is not None:
                    title_lines = tip_lines[:table_idx]
                    title = title_lines[0] if title_lines else ""
                    rows, _ = parse_markdown_table(tip_lines, table_idx)
                    add_tip_table_block(doc, title, rows)
                else:
                    add_tip_block(doc, tip_lines)
            continue
        if line.startswith("# "):
            add_heading(doc, 1, line[2:].strip())
        elif line.startswith("## "):
            add_heading(doc, 2, line[3:].strip())
        elif line.startswith("### "):
            add_heading(doc, 3, line[4:].strip())
        elif is_markdown_table_start(lines, i):
            rows, i = parse_markdown_table(lines, i)
            add_markdown_table(doc, rows)
            continue
        elif is_markdown_image(line):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(image_path_from_line(line)), width=Cm(15.0))
        else:
            add_body_paragraph(doc, line)
        i += 1
    doc.save(OUTPUT_DOCX)


def build_review_xlsx():
    wb = Workbook()
    ws = wb.active
    ws.title = "强二级复核"
    headers = ["知识点", "位置", "当前层级", "强二级理由", "目标院校证据", "考纲证据", "可能题型", "建议", "负责人确认"]
    ws.append(headers)
    rows = [
        ["心理测量完整实践的三个前提", "P3", "二级", "属于历史章节中的一般原理线索，有独立简答/选择可能", "无直接真题", "心理测量基本原理和方法", "选择/简答", "保留二级，若后续真题强化可升一级", ""],
        ["早期对智力落后儿童的分类与训练的兴趣", "P6", "二级", "智力测验起源的重要现实需求，含艾斯克罗、沈干、比奈前期推动", "无直接真题", "智力测验的起源", "选择/简答", "保留二级偏强", ""],
        ["高尔顿的理想和贡献", "P8", "二级", "测验运动先驱，人物贡献稳定可考", "无直接真题", "心理测量和测验的历史、发展", "选择/名词解释", "保留二级偏强", ""],
        ["卡特尔及早期心理测验", "P9", "二级", "“心理测验”术语和统一程序是历史核心线索", "无直接真题", "心理测量和测验的历史、发展", "选择/名词解释", "保留二级偏强", ""],
        ["复杂心理功能测验的探索", "P10", "二级", "承接早期感觉测验不足，并直接引出比奈智力测验", "无直接真题", "智力测验的起源", "选择/简答", "保留二级偏强", ""],
        ["团体测验的产生", "P11", "二级", "与智力测验起源相邻，含陆军甲/乙种测验等稳定选择题点", "无直接真题", "智力测验的起源", "选择/简答", "保留二级偏强", ""],
    ]
    for row in rows:
        ws.append(row)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    widths = [24, 10, 10, 36, 18, 26, 16, 30, 16]
    for idx, width in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + idx)].width = width

    ev = wb.create_sheet("证据与自检")
    ev.append(["项目", "结论"])
    evidence_rows = [
        ["材料", "教材第1章OCR/PDF核对、2025华东347考纲、华东题册/真题解析抽取文本、深大普心格式母版"],
        ["题型池", "第1章直接证据为选择题；非直接题型仅用于审核表，不在成品正文乱标"],
        ["真题一级", "比奈/比内—西蒙量表：1905年第一个智力测验，题册显示为选择题"],
        ["考纲覆盖", "心理测量基本原理和方法、心理测量和测验的历史发展、智力测验的起源"],
        ["教材结构核对", "正文标题已按教材目录改为第一节至第五节；编制者自拟概括不再作为结构标题"],
        ["专名核对", "教材P6写作“沈干（E. Sequin）”，成品按教材写法保留“沈干”"],
        ["分点分层", "按定义/原因/贡献/观点/项目/意义等类型重编，避免只把原文切成短段"],
        ["过程话术检查", "成品正文不含了解即可、无真题支撑、不展开背诵等话术"],
        ["Tips", "保留现代智力测验形成路径、比奈生活化例子、比奈/比内译名、比奈量表辨析、个别/团体测验辨析"],
        ["格式", "使用深大母版的封面/TOC字段/Heading 1-3/宋体小四/铁头tips标签/浅蓝底/表格样式；标题与目录强制黑色"],
        ["风险", "本地无 Word/WPS 渲染能力，已尽量用TOC字段和黑色可见目录模拟生成效果；最终页码可在Word/WPS中刷新"],
    ]
    for row in evidence_rows:
        ev.append(row)
    for cell in ev[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9EAF7")
    ev.column_dimensions["A"].width = 20
    ev.column_dimensions["B"].width = 90
    for row in ev.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    wb.save(OUTPUT_XLSX)


def main():
    DELIVER.mkdir(parents=True, exist_ok=True)
    markdown = clean_source_text()
    LATEST_MD.write_text(markdown, encoding="utf-8")
    build_docx(markdown)
    build_review_xlsx()
    print(OUTPUT_DOCX)
    print(OUTPUT_XLSX)


if __name__ == "__main__":
    main()
