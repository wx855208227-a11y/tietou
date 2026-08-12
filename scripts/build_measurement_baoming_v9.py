from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_名解准入精校版V8.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_逐章分页精校版V9.md"


def transform(text: str) -> str:
    result = text.replace("## 全本·极简直背版V8", "## 全本·极简直背版V9", 1)
    assert result != text
    return result


def main() -> None:
    OUTPUT.write_text(transform(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"已生成{OUTPUT}。")


if __name__ == "__main__":
    main()
