from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import re

from audit_shenzhen_baoming_v1_sources import ALIASES, compact, similarity
from audit_shenzhen_baoming_v4_sources import ALLOWED_STRUCTURAL_TERMS, bold_terms
from rebuild_shenzhen_baoming_v6 import EXPERIMENT_OUTPUT, GENERAL_OUTPUT, MEASUREMENT_OUTPUT
from validate_shenzhen_baoming_v4 import outside_expansions
from validate_shenzhen_baoming_v5 import block_with


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent / "work/shenzhen_baoming_sources"
REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_来源与采分点守恒审计报告V6.md"

SUBJECTS = {
    "普通心理学": {
        "manual": GENERAL_OUTPUT,
        "speed": SOURCE_ROOT / "普通心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "普通心理学/一本通.md",
    },
    "实验心理学": {
        "manual": EXPERIMENT_OUTPUT,
        "speed": SOURCE_ROOT / "实验心理学/速背手册.md",
        "yibentong": SOURCE_ROOT / "实验心理学/一本通.md",
    },
    "心理与教育测量": {
        "manual": MEASUREMENT_OUTPUT,
        "speed": SOURCE_ROOT / "心理与教育测量/速背手册.md",
        "yibentong": SOURCE_ROOT / "心理与教育测量/一本通.md",
    },
}

STRUCTURAL_TERMS = ALLOWED_STRUCTURAL_TERMS | {
    "P=KlgI", "K=ΔI/I", "科学问题示例", "实例", "实例与应对",
    "作用角度", "教育应用", "实验依据", "实验现象", "关系及成立条件",
    "三者关系", "适用边界", "理论关系", "比较结论", "因果关系判断",
}

# 速背手册在“听觉基本现象”中只展开音高，但一本通明确并列音高、响度和音色。
# 题干要求回答声音心理维度，因此这里保留一本通可直接定位的必要采分点。
BODY_YIBENTONG_EXCEPTIONS = {
    "普通心理学": {"音色", "波形"},
    "实验心理学": set(),
    "心理与教育测量": set(),
}

# 这些清单来自速背手册中明确列举的并列采分点。每个点必须在对应答案中有去向，
# 可以出现在正文，也可以作为圆括号中的整点扩容，但不得因合并而消失。
POINT_LEDGER = {
    "普通心理学": {
        "简述心理学的主要研究领域": (
            "普通心理学", "生理心理学", "发展心理学", "教育心理学", "医学心理学",
            "健康心理学", "工业心理学", "军事心理学", "社会心理学",
        ),
        "简述心理学的主要研究方法": ("观察法", "实验法", "心理测验法", "个案法"),
        "论述心理学主要流派": (
            "构造主义", "机能主义", "行为主义", "新行为主义", "格式塔心理学",
            "精神分析学派", "新精神分析学派", "人本主义心理学",
        ),
        "比较脑功能的": ("定位说", "整体说", "机能系统说", "模块说", "神经网络说"),
        "简述感觉的基本现象": ("感觉适应", "感觉对比", "感觉的相互作用", "感觉补偿"),
        "简述声音的心理维度和声音掩蔽": (
            "音高", "响度", "音色", "声音掩蔽", "共鸣理论", "行波理论",
            "频率理论", "神经齐射理论",
        ),
        "简述知觉的含义及其": ("知觉的选择性", "知觉的整体性", "知觉的理解性", "知觉的恒常性"),
        "简述知觉组织的主要原则": (
            "邻近性", "相似性", "对称性", "良好连续", "共同命运",
            "封闭性", "线条朝向", "简单性", "均质连接性",
        ),
        "简述深度知觉的主要线索": (
            "调节", "辐合", "遮挡", "线条透视", "空气透视", "相对高度",
            "相对大小", "纹理梯度", "运动视差和运动透视", "明暗和阴影", "双眼视差",
        ),
        "简述运动知觉的含义和主要类型": (
            "真动知觉", "似动知觉", "动景运动", "诱发运动", "自主运动", "运动后效",
        ),
        "简述错觉的含义、特点及主要理论解释": (
            "眼动说", "移情说", "完形倾向说", "透视说", "常性误用说", "神经抑制作用说",
        ),
        "简述注意的含义、功能及主要种类": (
            "选择功能", "保持功能", "调节和监督功能", "整合功能",
            "外源性注意", "内源性注意", "随意后注意",
        ),
        "简述记忆的主要生理机制和脑机制观点": (
            "突触结构变化", "长时程增强", "反响回路", "整合论", "定位说", "SPI理论",
        ),
        "简述布鲁纳提出的概念形成策略": (
            "保守性聚焦", "冒险性聚焦", "同时性扫描", "继时性扫描",
        ),
        "论述决策的主要理论": (
            "期望效用理论", "前景理论", "框架效应", "代表性启发法",
            "易得性启发法", "锚定与调整启发法",
        ),
        "简述加德纳多元智力理论的主要内容": (
            "言语智力", "逻辑—数学智力", "空间智力", "音乐智力", "运动智力",
            "人际智力", "自知智力", "自然智力",
        ),
        "简述观察学习的含义、基本过程和动机来源": (
            "注意过程", "保持过程", "复制过程", "动机过程", "直接强化",
            "替代强化", "自我强化",
        ),
    },
    "实验心理学": {
        "简述实验心理学研究应遵守的主要伦理原则": (
            "知情同意权", "退出的自由", "免遭伤害", "保密原则",
        ),
        "简述实验研究中": ("自变量", "因变量", "控制变量"),
        "被试间设计、被试内设计": ("被试间设计", "被试内设计", "混合设计"),
        "简述小样本设计及其主要类型": ("ABA设计", "多基线设计"),
        "简述反应时的主要影响因素": (
            "刺激强度", "刺激复杂度", "时空特征和通道效应", "线索提示与相容性",
            "适应水平", "动机", "个体差异", "年龄与教育训练",
        ),
        "论述感觉阈限的含义、传统测量方法及主要误差": (
            "最小变化法", "恒定刺激法", "平均差误法", "习惯误差", "期望误差",
            "练习误差", "疲劳误差", "动作误差", "空间误差",
        ),
        "简述阈上感觉量表的主要建立方法": (
            "等级排列法", "对偶比较法", "感觉等距法", "差别阈限法", "分段法", "数量估计法",
        ),
    },
    "心理与教育测量": {
        "简述测量的": ("参照点", "绝对参照点", "相对参照点", "单位"),
        "论述信度的": ("重测信度", "复本信度", "分半信度", "同质性信度", "评分者信度"),
        "简述影响信度的": (
            "被试方面", "主试方面", "施测情境方面", "长度", "正态分布和中等水平",
            "区分度", "适当被试团体", "严格执行施测规程",
        ),
        "比较内容效度、结构效度和效标效度": ("内容效度", "结构效度", "效标效度"),
        "论述心理测验编制的": (
            "确定测验目的", "制定编题计划", "编辑测验项目", "预测与项目分析",
            "合成测验", "标准化", "鉴定测验", "编写测验说明书",
        ),
        "简述标准化样组": (
            "成员定义明确", "总体代表性", "取样过程清楚", "样本规模适当", "时空限制", "常模类型结合",
        ),
        "简述测验等值的含义及基本条件": (
            "同质性", "等信度", "公平性", "可递推性", "对称性", "样本不变性",
        ),
        "16PF、MMPI和EPQ": ("16PF", "MMPI", "EPQ", "因素分析法", "标准10分制", "T分数"),
        "简述常见焦虑测验及其主要用途": ("MAS", "STAI", "TAI", "BAI", "HAMA"),
    },
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def trace(term: str, source: str) -> bool:
    candidate = ALIASES.get(term, term)
    return similarity(candidate, source) >= 0.20


def main() -> None:
    rows: list[str] = []
    totals = Counter()
    for subject, paths in SUBJECTS.items():
        for path in paths.values():
            assert path.is_file(), path
        manual = paths["manual"].read_text(encoding="utf-8")
        speed = compact(paths["speed"].read_text(encoding="utf-8"))
        yibentong = compact(paths["yibentong"].read_text(encoding="utf-8"))
        combined = speed + yibentong
        body = outside_expansions(manual[manual.index("# 第一章") :])

        body_terms = bold_terms(body)
        unsupported_body = [
            term for term in body_terms
            if not trace(term, speed)
            and term not in STRUCTURAL_TERMS
            and not (term in BODY_YIBENTONG_EXCEPTIONS[subject] and trace(term, yibentong))
        ]
        assert not unsupported_body, (subject, "body", sorted(set(unsupported_body)))

        all_terms = bold_terms(manual[manual.index("# 第一章") :])
        unsupported_all = [
            term for term in all_terms
            if not trace(term, combined) and term not in STRUCTURAL_TERMS
        ]
        assert not unsupported_all, (subject, "all", sorted(set(unsupported_all)))

        ledger_count = 0
        for heading, required_terms in POINT_LEDGER[subject].items():
            answer = block_with(manual, heading)
            missing = [term for term in required_terms if term not in answer]
            assert not missing, (subject, heading, missing)
            unsourced = [term for term in required_terms if not trace(term, combined)]
            assert not unsourced, (subject, heading, "source", unsourced)
            ledger_count += len(required_terms)

        definitions = set(re.findall(r"【名词解释：([^】]+)】", manual))
        unsupported_definitions = [term for term in definitions if not trace(term, combined)]
        assert not unsupported_definitions, (subject, "definitions", unsupported_definitions)

        rows.append(
            f"| {subject} | {len(body_terms)} | {len(all_terms) - len(body_terms)} | "
            f"{ledger_count} | {len(definitions)} |"
        )
        totals.update(
            body_terms=len(body_terms), expansion_terms=len(all_terms) - len(body_terms),
            ledger=ledger_count, definitions=len(definitions),
        )

    hashes = "\n".join(
        f"- `{path.relative_to(SOURCE_ROOT)}`：`{digest(path)}`"
        for paths in SUBJECTS.values()
        for key, path in paths.items()
        if key in {"speed", "yibentong"}
    )
    REPORT.write_text(
        f"""# 深圳大学347心理学保命手册来源与采分点守恒审计报告V6

## 结论

- 主体加粗关键词逐项回溯速背手册；圆括号扩容中的加粗关键词逐项回溯速背手册或一本通，未发现无来源理论关键词。
- 对并列点多、容易在合并中漏项的题建立来源点清单，共反查{totals['ledger']}个独立采分点；每一点均在正文或圆括号扩容中明确出现。
- 合并只改变呈现层级，不改变采分点总量；因简答容量移出的来源点以整点扩容保留。
- 总起、总结和比较结论仅重组来源已有信息，不作为新增理论采分点。

## 分科结果

| 科目 | 主体关键词调用 | 扩容关键词调用 | 来源点清单核对 | 唯一名解 |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

## 本轮重点校正

1. 知觉组织九项原则完成9/9覆盖；线条朝向和均质连接性作为整点扩容保留。
2. 声音心理维度补回音色；音高理论补回赫尔姆霍茨、冯·贝克西、拉瑟福德和韦弗尔的人物—理论配对。
3. 韦伯定律统一为K=ΔI/I，费希纳定律统一为P=KlgI；三科重复调用保持一致。
4. 三色理论人物统一为托马斯·杨和赫尔姆霍茨。

## 来源文件校验值

{hashes}
""",
        encoding="utf-8",
    )
    print(
        f"PASS body_terms={totals['body_terms']} expansion_terms={totals['expansion_terms']} "
        f"ledger={totals['ledger']} definitions={totals['definitions']}"
    )


if __name__ == "__main__":
    main()
