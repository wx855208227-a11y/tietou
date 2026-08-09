from __future__ import annotations

from build_measurement_baoming_v3 import OUTPUT, SOURCE, transform
from validate_measurement_baoming_v2 import main as validate_v2
from validate_measurement_baoming_v3 import main as validate_v3


def main() -> None:
    validate_v2()
    validate_v3()
    assert OUTPUT.read_text(encoding="utf-8") == transform(SOURCE.read_text(encoding="utf-8"))
    print(
        "测量保命手册V3双源审计通过：沿用V2已完成的最新版速背手册主核与一本通辅助核对结论；"
        "V3只调整星级、扩容标记、说明和排版，不改变题目、答案、关键词、名解及扩容内容。"
    )


if __name__ == "__main__":
    main()
