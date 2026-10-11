from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

from rebuild_shenzhen_baoming_v22_scope import LATER_CHAPTERS


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"

GENERAL_SOURCE = DELIVERABLES / "深圳大学347普通心理学保命手册_V19原标准重新逐题校正版.md"
EXPERIMENT_SOURCE = DELIVERABLES / "深圳大学347实验心理学保命手册_V19原标准逐题校正版.md"
MEASUREMENT_SOURCE = DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19原标准逐题校正版.md"

GENERAL_OUTPUT = DELIVERABLES / "深圳大学347普通心理学保命手册_V19完整范围排版优化版V23.md"
EXPERIMENT_OUTPUT = DELIVERABLES / "深圳大学347实验心理学保命手册_V19完整范围排版优化版V23.md"
MEASUREMENT_OUTPUT = DELIVERABLES / "深圳大学347心理与教育测量保命手册_V19完整范围排版优化版V23.md"
SCOPE_REPORT = DELIVERABLES / "深圳大学347心理学保命手册_V19范围与星级复核报告V23.md"


STAR_GUIDE = """## 星级

- **★★★ 核心优先**：对应速背手册原一级；深大真题、命题风格和知识点可考性证据较强，主观题复用价值最高。
- **★★ 重点掌握**：同属速背手册原一级；能够形成稳定的主观题，但深大直接证据或综合优先度略低于三星。
- **★ 基础覆盖**：对应速背手册原二级；用于补足速背手册保留的基础范围。
"""


EXPECTED_CHAPTERS = {
    "普通心理学": (
        "第一章 心理学的研究对象和方法",
        "第二章 心理与行为的脑神经基础",
        "第三章 感觉",
        "第四章 知觉",
        "第五章 意识",
        "第六章 记忆",
        "第七章 思维",
        "第八章 语言",
        "第九章 动机",
        "第十章 情绪",
        "第十一章 智力",
        "第十二章 人格",
        "第十三章 学习",
        "第十四章 人生全程发展",
        "补充章 高频学习理论",
    ),
    "实验心理学": (
        "第一章 绪论",
        "第二章 实验研究的基本问题",
        "第四章 反应时",
        "第五章 心理物理学",
        "第六章 注意",
        "第七章 知觉",
        "第八章 记忆与学习",
        "第九章 思维",
        "第十章 情绪",
    ),
    "心理与教育测量": (
        "第一章 心理与教育测量概论",
        "第三章 经典测验理论的基本假设",
        "第四章 测量信度",
        "第五章 测量效度",
        "第六章 测验的项目分析",
        "第七章 心理与教育测验的编制与实施",
        "第八章 常模参照测验",
        "第九章 目标参照测验",
        "第十章 测验等值",
        "第十一章 能力测验",
        "第十三章 人格测量",
        "第十四章 其他心理与教育测验",
        "第十六章 测量理论与应用的新发展",
    ),
}


EXPECTED_COUNTS = {
    "普通心理学": (15, 75, 90),
    "实验心理学": (9, 37, 38),
    "心理与教育测量": (13, 41, 46),
}


EXPECTED_ONE_STAR = {
    "普通心理学": {
        "三、心理学的主要研究领域",
        "一、神经元与神经冲动",
        "五、错觉",
        "六、催眠",
        "二、记忆的生理机制",
        "七、认知学习与动作技能学习",
    },
    "实验心理学": {
        "二、实验心理学的科学属性与实证研究",
        "一、直接知觉与间接知觉",
        "三、内隐学习",
        "一、思维的实验研究方法",
        "二、情绪与认知的实验研究",
        "三、情绪的测量",
    },
    "心理与教育测量": {
        "二、心理测量的含义与特点",
        "一、测验编制的一般程序",
        "二、测验的施测",
        "三、测验结果的报告",
        "二、常模的编制",
        "三、百分等级分数",
        "五、组内常模与标准分数",
        "一、测验等值",
        "一、比内智力量表",
        "二、韦克斯勒智力量表",
        "三、常用团体智力测验",
        "四、自陈量表与投射测验的比较",
        "一、常见焦虑测验",
        "二、项目反应理论",
    },
}


def replace_star_guide(text: str) -> str:
    return re.sub(
        r"## 星级\n.*?(?=\n## 怎么用)",
        STAR_GUIDE.rstrip(),
        text,
        count=1,
        flags=re.DOTALL,
    )


def build_general() -> str:
    text = replace_star_guide(GENERAL_SOURCE.read_text(encoding="utf-8"))
    text = text.replace(
        "1. 埃里克森心理社会性发展的八个阶段如下：",
        "埃里克森心理社会性发展的八个阶段如下：",
        1,
    )
    erikson_start = text.index("埃里克森心理社会性发展的八个阶段如下：")
    erikson_stop = text.index("综上，埃里克森把人格发展扩展到生命全程", erikson_start)
    erikson = text[erikson_start:erikson_stop]
    for number in range(1, 9):
        erikson = erikson.replace(f"（{number}）", f"{number}. ", 1)
    text = text[:erikson_start] + erikson + text[erikson_stop:]

    text = text.replace(
        "1. **科温顿**划分的学生类型如下：",
        "**科温顿**划分的学生类型如下：",
        1,
    )
    covington_start = text.index("**科温顿**划分的学生类型如下：")
    covington_stop = text.index("综上，追求成功与避免失败两个维度", covington_start)
    covington = text[covington_start:covington_stop]
    for number in range(1, 5):
        covington = covington.replace(f"（{number}）", f"{number}. ", 1)
    text = text[:covington_start] + covington + text[covington_stop:]
    return text.rstrip() + "\n"


def build_experiment() -> str:
    text = replace_star_guide(EXPERIMENT_SOURCE.read_text(encoding="utf-8"))
    text = text.replace(
        "## 二、实验心理学的科学属性与实证研究【★★】",
        "## 二、实验心理学的科学属性与实证研究【★】",
        1,
    )
    text = text.replace("# 第三章 反应时", "# 第四章 反应时", 1)
    text = text.replace("# 第四章 心理物理学", "# 第五章 心理物理学", 1)
    later = LATER_CHAPTERS.replace(
        "## 二、情绪与认知的实验研究【★★】",
        "## 二、情绪与认知的实验研究【★】",
        1,
    )
    return f"{text.rstrip()}\n\n{later.rstrip()}\n"


def build_measurement() -> str:
    text = replace_star_guide(MEASUREMENT_SOURCE.read_text(encoding="utf-8"))
    text = text.replace(
        "## 二、心理测量的含义与特点【★★】",
        "## 二、心理测量的含义与特点【★】",
        1,
    )
    text = text.replace(
        "1. 四种测量水平及其性质分别如下：",
        "四种测量水平及其性质分别如下：",
        1,
    )
    scale_start = text.index("四种测量水平及其性质分别如下：")
    scale_stop = text.index("综上，四种量表由低到高依次增加", scale_start)
    scale = text[scale_start:scale_stop]
    for number in range(1, 5):
        scale = scale.replace(f"（{number}）", f"{number}. ", 1)
    text = text[:scale_start] + scale + text[scale_stop:]

    text = text.replace(
        "1. 认知诊断的核心概念包括以下几点：",
        "认知诊断的核心概念包括以下几点：",
        1,
    )
    diagnosis_start = text.index("认知诊断的核心概念包括以下几点：")
    diagnosis_stop = text.index("综上，认知诊断通过认知属性", diagnosis_start)
    diagnosis = text[diagnosis_start:diagnosis_stop]
    for number in range(1, 8):
        diagnosis = diagnosis.replace(f"（{number}）", f"{number}. ", 1)
    text = text[:diagnosis_start] + diagnosis + text[diagnosis_stop:]
    return text.rstrip() + "\n"


def chapters(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(1).strip()
        for match in re.finditer(r"^# ((?:第[^\n]+章|补充章)[^\n]*)$", text, re.MULTILINE)
    )


def units(text: str) -> list[tuple[str, str]]:
    return [
        (match.group(1).strip(), match.group(2))
        for match in re.finditer(
            r"^## ([一二三四五六七八九十百]+、[^\n【]+)【(★{1,3})】$",
            text,
            re.MULTILINE,
        )
    ]


def question_count(text: str) -> int:
    return len(re.findall(r"^### 押题\d+【(?:简答|论述)】", text, re.MULTILINE))


def validate(subject: str, text: str) -> dict[str, object]:
    found_chapters = chapters(text)
    found_units = units(text)
    found_questions = question_count(text)
    expected = EXPECTED_COUNTS[subject]
    assert found_chapters == EXPECTED_CHAPTERS[subject], (subject, found_chapters)
    assert (len(found_chapters), len(found_units), found_questions) == expected
    one_star = {title for title, star in found_units if star == "★"}
    assert one_star == EXPECTED_ONE_STAR[subject], (
        subject,
        sorted(one_star - EXPECTED_ONE_STAR[subject]),
        sorted(EXPECTED_ONE_STAR[subject] - one_star),
    )
    assert "速背手册或一本通" not in text
    assert "或虽被现行考纲收录" not in text
    return {
        "chapters": len(found_chapters),
        "units": len(found_units),
        "questions": found_questions,
        "stars": Counter(star for _title, star in found_units),
    }


def write_report(stats: dict[str, dict[str, object]]) -> None:
    report = f"""# 深圳大学347心理学保命手册V19范围与星级复核报告V23

## 范围结论

- 本版以V19原标准逐题终校内容为基线，未重写已成熟答案。
- 普通心理学覆盖速背手册保留的第一至十四章及高频学习理论补充章，未发现整章漏编。
- 实验心理学补回速背手册仍保留、但V19漏编的第六至第十章；反应时和心理物理学恢复为速背手册中的第四、第五章编号。
- 心理与教育测量覆盖速背手册保留的十三章；一本通独有而速背手册删去的第二、十二、十五章不编入。
- 实验第三章未在速背手册中保留，因此不编入；全书不设置要求考生自行设计实验的题目。

## 星级复核

- 三星、二星均只对应速背手册原一级；一星对应速背手册原二级。
- 纠正三处层级：实验心理学“科学属性与实证研究”由二星改为一星；实验心理学“情绪与认知的实验研究”由二星改为一星；测量“心理测量的含义与特点”由二星改为一星。
- 其余V19星级在速背层级边界内保留；三星与二星继续依据深大真题、命题风格和主观题可考性区分，不机械配比。

## 数量

- 普通心理学：{stats['普通心理学']['chapters']}章，{stats['普通心理学']['units']}个考点，{stats['普通心理学']['questions']}道题；三星{stats['普通心理学']['stars']['★★★']}、二星{stats['普通心理学']['stars']['★★']}、一星{stats['普通心理学']['stars']['★']}。
- 实验心理学：{stats['实验心理学']['chapters']}章，{stats['实验心理学']['units']}个考点，{stats['实验心理学']['questions']}道题；三星{stats['实验心理学']['stars']['★★★']}、二星{stats['实验心理学']['stars']['★★']}、一星{stats['实验心理学']['stars']['★']}。
- 心理与教育测量：{stats['心理与教育测量']['chapters']}章，{stats['心理与教育测量']['units']}个考点，{stats['心理与教育测量']['questions']}道题；三星{stats['心理与教育测量']['stars']['★★★']}、二星{stats['心理与教育测量']['stars']['★★']}、一星{stats['心理与教育测量']['stars']['★']}。
- 合计：{sum(int(value['chapters']) for value in stats.values())}章，{sum(int(value['units']) for value in stats.values())}个考点，{sum(int(value['questions']) for value in stats.values())}道题。
"""
    SCOPE_REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    outputs = {
        "普通心理学": (GENERAL_OUTPUT, build_general()),
        "实验心理学": (EXPERIMENT_OUTPUT, build_experiment()),
        "心理与教育测量": (MEASUREMENT_OUTPUT, build_measurement()),
    }
    stats: dict[str, dict[str, object]] = {}
    for subject, (path, text) in outputs.items():
        stats[subject] = validate(subject, text)
        path.write_text(text, encoding="utf-8")
        print(path)
    write_report(stats)
    print(SCOPE_REPORT)


if __name__ == "__main__":
    main()
