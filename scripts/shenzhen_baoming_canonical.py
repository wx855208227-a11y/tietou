from __future__ import annotations

import re


CANONICAL_DEFINITIONS = {
    "观察法": "观察法是在**自然条件**下，对表现心理现象的外部活动进行**有系统、有计划**的观察，从中发现心理现象产生和发展的规律。（适用于无法控制研究对象、控制会影响行为出现或因伦理要求不能控制的情形。）",
    "实验法": "实验法是在**控制条件**下对某种心理现象进行观察的方法，包括实验室实验法和自然实验法。（实验法通常由研究者操纵**自变量**、测量**因变量**并控制额外变量。）",
    "费希纳定律": "费希纳定律认为心理量与物理量之间呈**对数关系**，即**S=KlgI**；刺激强度按几何级数增加时，感觉强度按算术级数上升。（该定律主要适用于中等强度刺激。）",
    "投射测验": "投射测验是向被试提供**未经组织的刺激情境**，让其在不受限制的情况下自由表现，然后分析其反应，从而推断人格结构。（常用的投射测验包括**罗夏墨迹测验和主题统觉测验**。）",
    "标准化": "标准化是指测验的**内容、实施、记分和分数解释的一致性**。（主要包括测验内容、施测条件、评分规则和测验常模的标准化。）",
    "信度": "信度是指**测量结果的稳定性和一致性程度**，也叫测量的可靠性。（同一工具反复测量同一种心理特质时，结果越一致，信度越高；信度系数越高，随机误差的影响通常越小。）",
    "内容效度": "内容效度是指测验题目对测验内容范围的**代表性程度**。（通常通过**专家判断和双向细目表**等方法加以确定。）",
    "结构效度": "结构效度是指测验能说明心理学上的**理论结构或特质**的程度。（可以通过**因素分析、会聚效度和区分效度**等证据检验。）",
    "效标效度": "效标效度是指测验分数对某一行为表现的**预测能力高低**。（按收集效标资料的时间，可分为**同时效度和预测效度**。）",
    "自陈量表": "自陈量表是由受测者根据自身情况进行**自我报告的标准化人格问卷**。（代表性自陈量表包括**EPPS、16PF和MMPI**。）",
}


PREFIX_RE = re.compile(r"^(\d+\.\s*|（\d+）\s*|[①②③④⑤⑥⑦⑧⑨⑩]\s*)")


def canonicalize_definitions(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        tags = re.findall(r"【名词解释：([^】]+)】", line)
        if len(tags) == 1 and tags[0] in CANONICAL_DEFINITIONS:
            prefix_match = PREFIX_RE.match(line)
            prefix = prefix_match.group(1) if prefix_match else ""
            line = f"{prefix}{CANONICAL_DEFINITIONS[tags[0]]}【名词解释：{tags[0]}】"
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _normalize_answer_block(block: str) -> str:
    lines = block.splitlines()
    numbered = [
        (index, int(match.group(1)))
        for index, line in enumerate(lines)
        if (match := re.match(r"^(\d+)\.\s+", line))
    ]
    values = [value for _, value in numbered]
    if values.count(1) <= 1:
        return block
    starts = [offset for offset, (_, value) in enumerate(numbered) if value == 1]
    for module_index, start_offset in enumerate(starts, 1):
        stop_offset = starts[module_index] if module_index < len(starts) else len(numbered)
        first_line = numbered[start_offset][0]
        header_index = first_line - 1
        while header_index >= 0 and not lines[header_index].strip():
            header_index -= 1
        assert header_index >= 0 and not re.match(r"^\d+\.\s+", lines[header_index])
        header = lines[header_index].strip()
        if "**" not in header:
            header = f"**{header}**"
        lines[header_index] = f"{module_index}. {header}"
        for offset in range(start_offset, stop_offset):
            line_index, value = numbered[offset]
            lines[line_index] = re.sub(r"^\d+\.\s+", f"（{value}）", lines[line_index], count=1)
    return "\n".join(lines)


def normalize_task_modules(text: str) -> str:
    matches = list(re.finditer(r"^### 押题\d+【(?:简答|论述)】.*$", text, re.MULTILINE))
    parts: list[str] = []
    cursor = 0
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading_boundary = re.search(r"^#{1,2} ", text[match.end() : end], re.MULTILINE)
        block_end = match.end() + heading_boundary.start() if heading_boundary else end
        parts.append(text[cursor : match.end()])
        parts.append(_normalize_answer_block(text[match.end() : block_end]))
        cursor = block_end
    parts.append(text[cursor:])
    return "".join(parts)
