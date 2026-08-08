from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path

from lxml import etree


BUILD_SCRIPT = Path("scripts/build_baoming_v16.py")
SPEED = Path(
    "/home/yileiyang/multi_agent/.work/workspaces/github.com/agiamason/"
    "tietou/agents/tietou_course/inbox/feishu/"
    "om_x100b690fde5974a0b10d419cacda419/27_.docx"
)
YIBENTONG = Path("/tmp/tietou_hf_sources_20260725/ecnu_yibentong.docx")
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


UNIT_ANCHORS = {
    "一、心理学的含义与研究对象": ("心理学是研究", "心理过程"),
    "二、科学心理学的诞生": ("冯特",),
    "三、构造主义与机能主义": ("构造主义", "机能主义"),
    "四、行为主义": ("行为主义",),
    "五、格式塔心理学": ("格式塔心理学",),
    "六、精神分析学派": ("精神分析",),
    "七、人本主义心理学": ("人本主义",),
    "八、认知心理学": ("认知心理学",),
    "九、观察法、相关研究法与实验法": ("相关研究法", "实验法"),
    "十、实验变量": ("自变量", "因变量", "控制变量"),
    "十一、测验法与信效度": ("测验法", "信度", "效度"),
    "十二、投射法与投射测验": ("投射法", "罗夏墨渍测验"),
    "十三、心理学的主要分支": ("生理心理学", "发展心理学"),
    "一、神经元": ("神经元",),
    "二、神经冲动与突触传递": ("神经冲动", "突触"),
    "三、神经系统的构成与功能": ("神经系统", "交感神经"),
    "四、大脑皮层的感觉区与运动区": ("感觉区", "运动区"),
    "五、大脑皮层的言语区与联合区": ("言语区", "联合区"),
    "六、大脑两半球的功能分工": ("割裂脑", "斯佩里"),
    "七、丘脑与下丘脑": ("丘脑", "下丘脑"),
    "八、边缘系统、海马与杏仁核": ("边缘系统", "海马", "杏仁核"),
    "九、脑功能的主要学说": ("定位说", "整体说"),
    "一、学习的含义与特征": ("学习是", "学习的特征"),
    "二、反射、反射弧与反射类型": ("反射弧", "无条件反射"),
    "三、经典条件反射": ("经典条件反射",),
    "四、经典条件反射的基本规律": ("泛化", "分化", "消退"),
    "五、信号系统与高级神经活动": ("第一信号系统", "兴奋和抑制"),
    "六、操作条件反射的强化、惩罚与强化程序": ("操作条件反射", "连续强化", "间断强化"),
    "七、经典条件反射与操作条件反射的比较": ("经典条件反射和操作条件反射",),
    "八、顿悟学习": ("顿悟学习", "苛勒"),
    "九、目的行为学习理论": ("目的行为学习理论", "托尔曼"),
    "十、观察学习": ("观察学习", "班杜拉"),
}


def load_build():
    spec = importlib.util.spec_from_file_location("baoming_v16_source_audit", BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法读取：{BUILD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    return "".join(node.text or "" for node in root.findall(f".//{{{W_NS}}}t"))


def main() -> None:
    assert SPEED.is_file(), SPEED
    assert YIBENTONG.is_file(), YIBENTONG
    build = load_build()
    speed_text = docx_text(SPEED)
    yibentong_text = docx_text(YIBENTONG)
    combined = speed_text + yibentong_text

    unit_titles = {unit.title for _, units in build.CHAPTERS for unit in units}
    assert unit_titles == set(UNIT_ANCHORS), sorted(unit_titles ^ set(UNIT_ANCHORS))
    missing = {
        title: anchors
        for title, anchors in UNIT_ANCHORS.items()
        if not all(anchor in combined for anchor in anchors)
    }
    assert not missing, missing

    # 这些内容在两份来源正文中均无对应条目，因此不得进入本版学生正文。
    source_absent = (
        "格雷",
        "强化敏感性理论",
        "行为趋近系统",
        "行为抑制系统",
        "奖励学习",
        "随机分配",
        "行为塑造",
    )
    assert not any(token in combined for token in source_absent), {
        token for token in source_absent if token in combined
    }

    final_text = build.OUTPUT.read_text(encoding="utf-8")
    removed_from_final = source_absent + (
        "行为调控",
        "使用原则",
        "实施反馈",
        "迁移与保持",
        "评价投射测验的**优点**与**缺点**",
    )
    assert not any(token in final_text for token in removed_from_final), {
        token for token in removed_from_final if token in final_text
    }

    assert "简述操作条件反射的**基本规律**和**主要强化程序**" in final_text
    assert "简述投射法的**含义与作答特点**、**代表测验**" in final_text
    print(
        "V16来源核验通过："
        f"32个单元均在速背手册或一本通中检出对应正文；"
        f"已排除{len(source_absent)}项双源缺失内容。"
    )


if __name__ == "__main__":
    main()
