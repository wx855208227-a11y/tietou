from __future__ import annotations

from pathlib import Path

import audit_baoming_full_v8_sources as base_audit
from audit_baoming_full_v6_sources import EXPECTED_HASHES, SPEED, YIBENTONG
from build_ecnu_baoming_combined_v2_sources import INTRO_OUTPUT, INTRO_SOURCE, transform


REPORT = Path("deliverables/华东师范大学347心理学导论保命手册_全本_任务适配精校版V10_来源审计报告.md")


def main() -> None:
    # V8/V9的知识主体只使用速背手册和一本通；公共题库负责命题判断，
    # 不参与答案正文的知识准入，因此本轮双源审计只校验这两份实体文件。
    base_audit.EXPECTED_HASHES = {
        SPEED: EXPECTED_HASHES[SPEED],
        YIBENTONG: EXPECTED_HASHES[YIBENTONG],
    }
    base_audit.main()

    source = INTRO_SOURCE.read_text(encoding="utf-8")
    output = INTRO_OUTPUT.read_text(encoding="utf-8")
    assert output == transform(source, version="V10", experiment=False)

    report = f"""# 华东心理学导论保命手册V10来源审计报告

## 结论

- V10以已完成双源逐采分点审计的V9为知识主体，保持17章、117单元、145道押题、296处名解和原有圆括号扩容。
- V9知识主体回查速背手册与一本通：789个叶子采分点全部通过同章双源覆盖检查；256个唯一名解均在来源正文或登记的规范别名中得到支持。
- 本轮新增内容仅为题干任务模块标题，以及根据既有分述归纳的“联系—主要区别”比较结论；没有增加新的理论、模型、机制、分类或范围外知识点。
- V10由固定构建脚本从V9确定性生成，已验证构建结果逐字一致。

## 来源文件

- 速背手册：`27_.docx`，SHA-256 `{EXPECTED_HASHES[SPEED]}`。
- 心理学导论一本通：`华东心理学导论一本通.docx`，SHA-256 `{EXPECTED_HASHES[YIBENTONG]}`。

## 审计边界

- 速背手册控制主体表述与知识边界，一本通只补齐范围内必要采分角度。
- 真题与辅助题库用于押题证据和问法判断，不作为正文新增知识的来源。
- 本报告证明知识边界与采分点可追溯，不宣称结构归纳句与来源逐字相同。
"""
    REPORT.write_text(report, encoding="utf-8")
    print(f"导论V10来源审计通过：{REPORT}")


if __name__ == "__main__":
    main()
