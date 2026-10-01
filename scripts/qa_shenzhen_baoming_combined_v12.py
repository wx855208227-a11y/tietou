from __future__ import annotations

from pathlib import Path

import merge_shenzhen_baoming_manuals_v12 as merge_v12
import qa_shenzhen_baoming_combined_v11 as previous


ROOT = Path(__file__).resolve().parents[1]
qa_base = previous.previous.previous.base

qa_base.DOCX = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V12.docx"
qa_base.PDF = ROOT / "deliverables/深圳大学347心理学保命手册_普心实验测量合订精校版V12.pdf"
qa_base.PAGE_MAP = ROOT / "content/shenzhen_baoming_combined_v12_page_map.json"
qa_base.REPORT = ROOT / "deliverables/深圳大学347心理学保命手册_排版与结构质检报告V12.md"
qa_base.REPORT_VERSION = "V12"
qa_base.EXPECTED_DEFINITION_CALLS = 362
qa_base.SUBJECTS = (
    (
        "普通心理学",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V13.docx",
        ROOT / "deliverables/深圳大学347普通心理学保命手册_全本V13.pdf",
        ROOT / "content/shenzhen_general_baoming_v13_page_map.json",
        15, 75, 90,
    ),
    (
        "实验心理学",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V12.docx",
        ROOT / "deliverables/深圳大学347实验心理学保命手册_全本V12.pdf",
        ROOT / "content/shenzhen_experiment_baoming_v12_page_map.json",
        4, 25, 25,
    ),
    (
        "心理与教育测量",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V12.docx",
        ROOT / "deliverables/深圳大学347心理与教育测量保命手册_全本V12.pdf",
        ROOT / "content/shenzhen_measurement_baoming_v12_page_map.json",
        13, 39, 45,
    ),
)

# V11校验函数通过该模块全局引用合订来源；统一指向V12来源。
previous.merge_v11.base.SOURCES = merge_v12.base.SOURCES


def main() -> None:
    qa_base.main()
    previous.validate_exact_page_map()
    max_blank, continuation_pages = previous.validate_pagination()
    minimum_nonfinal_chars = previous.validate_sparse_chapter_tails()
    report = qa_base.REPORT.read_text(encoding="utf-8")
    report = report.replace(
        "- 章节：分章另起页；三科分册及合订版目录页码已校准",
        "- 章节：分章另起页；三科分册及合订版目录页码已校准\n"
        "- 题内分页：总起和总结不编号；各任务模块按1.→（1）→①→a.展开；"
        f"共检查{continuation_pages}个自然续页，续页前一页最大非必要底部空白为{max_blank:.1f}磅\n"
        f"- 稀疏页：除全书末页外，正文单页最少{minimum_nonfinal_chars}个文本字符；"
        "未发现仅有少量总结或尾点单独占页的章末稀疏页",
    )
    qa_base.REPORT.write_text(report, encoding="utf-8")
    print(
        f"PASS exact_page_map pagination continuation_pages={continuation_pages} "
        f"max_blank={max_blank:.1f}"
    )


if __name__ == "__main__":
    main()
