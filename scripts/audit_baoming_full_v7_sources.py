from __future__ import annotations

from pathlib import Path

from audit_baoming_full_v6_sources import EXPECTED_HASHES, digest, main as audit_v6
from validate_baoming_full_v7 import V6, V7, body, normalize_to_v6


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        assert path.is_file(), path
        assert digest(path) == expected, path
    audit_v6()
    assert normalize_to_v6(body(V7.read_text(encoding="utf-8"))) == body(V6.read_text(encoding="utf-8"))
    print(
        "全本V7来源与基线审计通过：四份来源哈希一致；"
        "恢复星级、标签顺序和选用字样后，正文与已完成双源审计的V6逐字一致；"
        "未新增知识、押题或范围外模块。"
    )


if __name__ == "__main__":
    main()
