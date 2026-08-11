from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_任务模块编号版V6.md"
OUTPUT = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_紧凑排版版V7.md"


def transform(text: str) -> str:
    result = text.replace("## 全本·极简直背版V6", "## 全本·极简直背版V7", 1)
    assert result != text
    return result


def main() -> None:
    OUTPUT.write_text(transform(SOURCE.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"已生成{OUTPUT}。")


if __name__ == "__main__":
    main()
