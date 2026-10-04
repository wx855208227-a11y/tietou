from __future__ import annotations

from pathlib import Path
import re

from rebuild_shenzhen_baoming_v13_source_scope import (
    build_experiment as build_experiment_v13,
    build_general as build_general_v13,
    build_measurement as build_measurement_v13,
)
from rebuild_shenzhen_baoming_v3 import replace_question


ROOT = Path(__file__).resolve().parents[1]

GENERAL_OUTPUT = ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V15.md"
EXPERIMENT_OUTPUT = ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V14.md"
MEASUREMENT_OUTPUT = ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V14.md"


FORGETTING = r"""### 押题1【论述】论述遗忘的原因，并说明如何减少遗忘。

遗忘是记忆内容不能保持或提取困难的现象，可分为不完全遗忘和完全遗忘、临时性遗忘和永久性遗忘。（遗忘既可能反映记忆痕迹发生变化，也可能只是当前没有找到适当的提取线索。）【名词解释：遗忘】

1. 遗忘的主要**原因**如下：

（1）**衰退说**：遗忘是记忆痕迹得不到强化而逐渐减弱、最终消退的结果。（长期不复习时，记忆痕迹会逐渐减弱。）【名词解释：衰退说】

（2）**干扰说**：遗忘常由其他信息的干扰引起，排除干扰后记忆可以恢复；干扰包括前摄抑制和倒摄抑制。（先学习的内容干扰后续学习属于前摄抑制，后学习的内容干扰先前内容的回忆属于倒摄抑制。）【名词解释：干扰说】

（3）**压抑说**：遗忘由情绪或动机的压抑作用引起，压抑解除后记忆可以恢复。（个体可能回避提取引起强烈痛苦的经历。）【名词解释：压抑说】

（4）**提取失败说**：长时记忆中的信息并未丢失，遗忘是因为没有找到适当的提取线索。（考试时暂时想不起、在相关线索下又想起，可能属于提取失败。）【名词解释：提取失败说】

2. 遗忘的五个主要**影响因素**如下：

（1）**时间因素**：学习后立即开始遗忘，最初遗忘很快，以后逐渐缓慢。（艾宾浩斯以无意义音节为材料、采用节省法得出遗忘曲线。）【名词解释：艾宾浩斯遗忘曲线】

（2）**识记材料的性质和数量**：形象的、有意义的材料遗忘较慢；学习程度相同时，识记材料越多，遗忘越快。

（3）**学习的程度**：过度学习的材料比恰能背诵的材料记忆效果更好。

（4）**识记材料的系列位置**：最后呈现的材料遗忘最少，其次是最先呈现的材料，中间部分遗忘最多，即系列位置效应。（最后呈现材料的保持优势称为近因效应，最先呈现材料的保持优势称为首因效应。）【名词解释：系列位置效应】

（5）**识记者的态度**：识记者是否想记住，以及材料的重要性和趣味性，都会影响遗忘速度。

3. **减少遗忘的方法**如下：

（1）**编码阶段**：在清醒状态下集中注意，进行深层次的意义加工，并把材料形象化、韵律化。

（2）**存储阶段**：及时复习、经常复习，使用精细复述，正确分配复习时间，使阅读与回忆交替进行，并适当地过度学习。

（3）**提取阶段**：利用编码特异性原则和测试效应帮助记忆。

综上，遗忘可由痕迹衰退、信息干扰、动机压抑和提取失败造成；减少遗忘既要完整考虑五个影响因素，也要从编码、存储和提取三个阶段提高记忆效果。

---
"""


MEMORY_STRATEGIES = r"""### 押题1【论述】根据记忆活动规律，说明如何提高记忆效率，至少提出六种方法。

提高记忆效果需要围绕编码、存储和提取三个阶段采取策略，使材料得到充分加工、稳定保持并能够顺利提取。

1. **编码阶段**的策略如下：

（1）在**清醒状态**下去记忆，并**集中注意**于记忆材料。

（2）对材料进行**深层次的意义加工**。（理解材料含义并与已有知识建立联系，通常比只记表面形式保持更久。）

（3）把记忆材料**形象化、韵律化**。（可以借助表象、图示、口诀或节奏加工材料。）

2. **存储阶段**的策略如下：

（1）**及时复习、经常复习**。（可依据遗忘先快后慢的规律逐步延长复习间隔。）

（2）使用**精细复述**，把当前材料与已有知识建立意义联系。

（3）**正确分配复习的时间**，并使**阅读与回忆交替进行**。（主动回忆可以暴露薄弱点，再针对遗漏重新阅读。）

（4）适当地**过度学习**，达到正确回忆后继续学习一定次数。（过度学习应适量，避免无效重复和疲劳。）

3. **提取阶段**的策略如下：

（1）利用**编码特异性原则**，使提取线索与编码时的信息相匹配。

（2）利用**测试效应**帮助记忆，通过主动提取巩固所学内容。

综上，提高记忆效率要同时改善编码、存储和提取，不能只依靠机械重复或单次集中复习。

---
"""


ITEM_PATTERNS = {
    1: re.compile(r"^(\d+)\.\s+"),
    2: re.compile(r"^（(\d+)）"),
    3: re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩])"),
    4: re.compile(r"^([a-z])\.\s+"),
}


def item_level(line: str) -> int | None:
    for level, pattern in ITEM_PATTERNS.items():
        if pattern.match(line):
            return level
    return None


def first_marker(level: int, line: str) -> bool:
    match = ITEM_PATTERNS[level].match(line)
    assert match
    return match.group(1) in {"1", "①", "a"}


def strip_marker(level: int, line: str) -> str:
    return ITEM_PATTERNS[level].sub("", line, count=1).strip()


def numbered_groups(lines: list[str], level: int) -> dict[int, list[int]]:
    groups: dict[int, list[int]] = {}
    stack: list[tuple[int, int]] = []
    for index, line in enumerate(lines):
        if line.startswith("# ") or line.startswith("## ") or line.startswith("### ") or line == "---":
            stack.clear()
            continue
        current = item_level(line)
        if current is None:
            continue
        while stack and stack[-1][0] >= current:
            stack.pop()
        parent = stack[-1][1] if stack else -1
        if current == level:
            groups.setdefault(parent, []).append(index)
        stack.append((current, index))
    return groups


def has_numbered_descendant(lines: list[str], index: int, level: int) -> bool:
    for line in lines[index + 1 :]:
        child_level = item_level(line)
        if child_level is None:
            if line.startswith("# ") or line.startswith("## ") or line.startswith("### ") or line == "---":
                return False
            continue
        if child_level <= level:
            return False
        return True
    return False


def merge_child(parent: str, child: str) -> str:
    if parent.rstrip().endswith(("：", ":")):
        return parent.rstrip() + child
    return parent.rstrip() + " " + child


def collapse_singleton_subpoints(text: str) -> str:
    """A sublevel is used only when the same parent has at least two children."""
    lines = text.splitlines()
    for level in (4, 3, 2):
        groups = numbered_groups(lines, level)
        targets: list[tuple[int, int]] = []
        for parent, children in groups.items():
            if parent < 0 or len(children) != 1:
                continue
            child = children[0]
            if first_marker(level, lines[child]) and not has_numbered_descendant(lines, child, level):
                targets.append((parent, child))
        for parent, child in sorted(targets, key=lambda value: value[1], reverse=True):
            lines[parent] = merge_child(lines[parent], strip_marker(level, lines[child]))
            lines[child] = ""
    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    normalized: list[str] = []
    for line in result.splitlines():
        match = re.search(r"【名词解释：[^】]+】", line)
        if match and line[match.end() :].strip():
            trailing = line[match.end() :].strip()
            line = f"{line[:match.start()].rstrip()} {trailing}{match.group(0)}"
        normalized.append(line)
    return "\n".join(normalized).strip() + "\n"


def build_general() -> str:
    text = replace_question(build_general_v13(), "论述遗忘的原因", FORGETTING)
    text = replace_question(text, "如何提高记忆效率", MEMORY_STRATEGIES)
    return collapse_singleton_subpoints(text)


def build_experiment() -> str:
    return collapse_singleton_subpoints(build_experiment_v13())


def build_measurement() -> str:
    text = collapse_singleton_subpoints(build_measurement_v13())
    return text.replace("6. **测验标准化**：标准化是指", "6. 标准化是指", 1)


def main() -> None:
    outputs = (
        (GENERAL_OUTPUT, build_general()),
        (EXPERIMENT_OUTPUT, build_experiment()),
        (MEASUREMENT_OUTPUT, build_measurement()),
    )
    for path, content in outputs:
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
