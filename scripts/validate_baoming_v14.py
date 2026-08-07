from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT = Path("scripts/build_baoming_v14.py")
MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_前三章_分层扩容均衡版V14.md")
TAG_RE = re.compile(r"(?:\*\*)?【名词解释：([^】]+)】(?:\*\*)?")
FORBIDDEN = ("XXXX", "待补充", "可举例", "答题思路", "到此停笔", "【共用】", "【本题补充】")


def load_module():
    spec = importlib.util.spec_from_file_location("baoming_v14", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def plain(text: str) -> str:
    return re.sub(r"\*\*|__", "", text)


def answer_length(question) -> int:
    text = "".join(line.text for line in question.lines)
    text = TAG_RE.sub("", text)
    return len(plain(text))


def main() -> None:
    module = load_module()
    markdown = MARKDOWN.read_text(encoding="utf-8")
    questions = [
        question
        for _, units in module.CHAPTERS
        for unit in units
        for question in unit.questions
    ]

    assert [len(units) for _, units in module.CHAPTERS] == [13, 9, 11]
    assert len(questions) == 61
    assert Counter(question.kind for question in questions) == {"简答": 54, "论述": 7}
    assert markdown.count("### 押题") == 61
    assert "名词解释】" not in "\n".join(
        line for line in markdown.splitlines() if line.startswith("### 押题")
    )

    definitions: dict[str, set[str]] = defaultdict(set)
    child_count = 0
    expansion_count = 0
    for question in questions:
        parent_seen = False
        base_text = plain("".join(line.text for line in question.lines))
        for line in question.lines:
            assert line.level in {0, 1, 2}
            if line.level == 1:
                parent_seen = True
            elif line.level == 2:
                assert parent_seen, f"二级编号缺少上位一级采分点：{question.stem}"
                child_count += 1
            if not line.text:
                assert line.expansions, f"空正文行没有承载扩容：{question.stem}"
            for match in TAG_RE.finditer(line.text):
                definition = plain(line.text[: match.start()]).strip()
                assert definition.endswith("。"), (match.group(1), definition)
                definitions[match.group(1)].add(definition)
            for item in line.expansions:
                expansion_count += 1
                assert item.strip() and item.endswith("。")
                assert not any(token in item for token in FORBIDDEN), item
        for item in question.final_expansions:
            expansion_count += 1
            assert item.strip() and item.endswith("。")
            assert not any(token in item for token in FORBIDDEN), item
        if "实例" in plain(question.stem):
            assert any(token in base_text for token in ("例如", "例子", "实例", "巴甫洛夫")), question.stem

    assert child_count >= 30
    assert expansion_count >= 35
    conflicts = {name: values for name, values in definitions.items() if len(values) != 1}
    assert not conflicts, conflicts
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }

    psychology_questions = module.CHAPTERS[0][1][0].questions
    assert answer_length(psychology_questions[0]) * 2 >= answer_length(psychology_questions[1])
    assert [line.level for line in psychology_questions[1].lines] == [1, 2, 2, 2, 0, 1, 2, 2, 1]
    methods = module.CHAPTERS[0][1][8].questions[0]
    assert [line.level for line in methods.lines] == [1, 2, 2, 1, 2, 2, 1, 2, 2]
    assert module.CHAPTERS[2][1][6].questions[0].kind == "论述"

    simple_lengths = [answer_length(question) for question in questions if question.kind == "简答"]
    essay_lengths = [answer_length(question) for question in questions if question.kind == "论述"]
    assert min(simple_lengths) >= 95 and max(simple_lengths) <= 380, (min(simple_lengths), max(simple_lengths))
    assert min(essay_lengths) >= 280 and max(essay_lengths) <= 500, (min(essay_lengths), max(essay_lengths))

    assert not any(token in markdown for token in FORBIDDEN)
    assert "<u>" not in markdown and "==" not in markdown
    assert not re.search(r"^####\s+答案", markdown, re.MULTILINE)
    assert re.search(r"^（1）", markdown, re.MULTILINE)
    print(
        f"V14内容验证通过：{len(questions)}题，{len(definitions)}个名词解释，"
        f"{child_count}个二级采分点，{expansion_count}处选用扩容；"
        f"简答{min(simple_lengths)}—{max(simple_lengths)}字，论述{min(essay_lengths)}—{max(essay_lengths)}字。"
    )


if __name__ == "__main__":
    main()
