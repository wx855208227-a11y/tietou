from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import re
import statistics

from validate_baoming_full_v1 import (
    EXPANSION_RE,
    TAG_RE,
    normalized_definition,
    plain,
    question_blocks,
    visible_length,
)


MARKDOWN = Path("deliverables/华东师范大学347心理学导论保命手册_全本_来源严格重编版V2.md")
CHAPTERS = (
    "第一章", "第二章", "第三章", "第四章", "第五章", "第六章", "第七章", "第八章",
    "第九章", "第十章", "第十一章", "第十二章", "第十三章", "第十四章", "第十五章",
    "第十六章", "第十八章",
)
FORBIDDEN_BODY = (
    "XXXX", "待补充", "答题思路", "到此停笔", "【共用】", "【本题补充】",
    "格雷", "强化敏感性理论", "行为趋近系统", "行为抑制系统", "BAS", "BIS",
)


def main() -> None:
    text = MARKDOWN.read_text(encoding="utf-8")
    body = text[text.index("# 第一章 "):]

    chapters = [match.group(1) for match in re.finditer(r"^# (第[^\s]+章)", body, re.MULTILINE)]
    assert tuple(chapters) == CHAPTERS, chapters
    units = re.findall(r"^## ([^\n]+)【(一级|二级)】$", body, re.MULTILINE)
    assert len(units) == 120, len(units)
    assert Counter(level for _, level in units) == {"一级": 25, "二级": 95}
    assert not any(token in body for token in FORBIDDEN_BODY)
    assert "<u>" not in body and "==" not in body and "__" not in body
    assert not re.search(r"(?<!\*)\*(?!\*)", body), "正文存在斜体标记"

    blocks = question_blocks(body)
    kinds = Counter("简答" if "【简答】" in heading else "论述" for heading, _ in blocks)
    assert len(blocks) == 150, len(blocks)
    assert kinds == {"简答": 109, "论述": 41}, kinds

    definitions: dict[str, set[str]] = defaultdict(set)
    simple_lengths: list[tuple[int, int, str]] = []
    essay_lengths: list[tuple[int, int, str]] = []
    for heading, block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip() and line.strip() != "---"]
        assert lines, heading
        assert not re.match(r"^(?:\d+\.\s|（\d+）)", plain(lines[0])), f"缺少总起：{heading}"
        assert any(re.match(r"^1\.\s", plain(line)) for line in lines), f"缺少一级分点：{heading}"
        summary_positions = [index for index, line in enumerate(lines) if plain(line).startswith("综上")]
        assert summary_positions, f"缺少总结：{heading}"
        assert summary_positions[-1] in {len(lines) - 1, len(lines) - 2}, f"总结位置异常：{heading}"

        for line in lines:
            plain_line = plain(line)
            previous_tag_end = 0
            for match in TAG_RE.finditer(plain_line):
                definition = normalized_definition(plain_line, previous_tag_end, match.start())
                assert definition.endswith("。"), (heading, match.group(1), definition)
                definitions[match.group(1)].add(definition)
                previous_tag_end = match.end()
            for expansion in EXPANSION_RE.findall(line):
                assert expansion.endswith(("。】", "！】", "？】")), expansion

        lengths = (
            visible_length(block, include_expansion=False),
            visible_length(block, include_expansion=True),
            heading,
        )
        (simple_lengths if "【简答】" in heading else essay_lengths).append(lengths)

    conflicts = {name: values for name, values in definitions.items() if len(values) > 1}
    assert not conflicts, conflicts
    assert len(definitions) == 260, len(definitions)
    assert definitions["心理学"] == {
        "心理学是研究人的行为和心理活动规律的中间科学，兼有自然科学和社会科学的性质。"
    }
    assert definitions["偏见"] == {
        "偏见是个体仅因某人属于特定群体，而对其持有的缺乏事实依据、较为固定并带有情感色彩的消极态度。"
    }

    assert min(item[0] for item in simple_lengths) >= 150
    assert max(item[0] for item in simple_lengths) <= 480
    assert min(item[0] for item in essay_lengths) >= 350
    assert max(item[0] for item in essay_lengths) <= 700
    simple_median = statistics.median(item[0] for item in simple_lengths)
    essay_median = statistics.median(item[0] for item in essay_lengths)
    assert 1.5 <= essay_median / simple_median <= 2.1

    prejudice = body[body.index("## 十二、偏见的形成、后果与减少【一级】"):]
    shared_fragments = (
        "**偏见**是个体仅因某人属于特定群体，而对其持有的缺乏事实依据、较为固定并带有情感色彩的消极态度。",
        "**认知分类与刻板印象**：个体划分**内群体和外群体**，并以刻板印象概括外群体，容易忽视成员差异。",
        "**社会学习与群体规范**：偏见可通过**联结学习、强化学习和观察学习**习得，并受家庭、同伴、媒体及群体规范强化。",
        "**社会认同与利益冲突**：个体可能以**偏爱内群体、贬低外群体**维护自尊；群体竞争会加剧偏见。",
        "**人格与情绪因素**：挫折可能通过**替罪羊机制**转向弱势外群体，权威主义倾向也会增加偏见。",
        "在**平等地位、共同目标、合作任务和制度支持**条件下增加群体接触。",
        "提供**反刻板信息和个体化信息**，避免以群体标签代替个体判断。",
        "建立**共同身份**并培养换位思考，弱化“我们—他们”的分类。",
        "建立**公平规范和反歧视制度**，减少偏见的社会强化。",
    )
    for fragment in shared_fragments:
        assert prejudice.count(fragment) == 2, fragment

    prejudice_blocks = [item for item in blocks if "偏见" in item[0] or "他人和其他群体" in item[0]]
    assert len(prejudice_blocks) == 2, prejudice_blocks
    prejudice_lengths = {
        "简答" if "【简答】" in heading else "论述": visible_length(block, False)
        for heading, block in prejudice_blocks
    }
    assert 300 <= prejudice_lengths["简答"] <= 420, prejudice_lengths
    assert 600 <= prejudice_lengths["论述"] <= 780, prejudice_lengths
    assert 1.7 <= prejudice_lengths["论述"] / prejudice_lengths["简答"] <= 2.0

    print(
        "全本V2内容验证通过："
        f"{len(chapters)}章、{len(units)}个单元、{len(blocks)}道押题；"
        f"{len(definitions)}个名词解释无异文；"
        f"简答基础容量中位数{simple_median:.0f}字，论述{essay_median:.0f}字；"
        f"偏见简答{prejudice_lengths['简答']}字、论述{prejudice_lengths['论述']}字。"
    )


if __name__ == "__main__":
    main()
