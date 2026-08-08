from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "content/measurement_baoming_ch1_3.md",
    ROOT / "content/measurement_baoming_ch4_5.md",
    ROOT / "content/measurement_baoming_ch6_8.md",
    ROOT / "content/measurement_baoming_ch9_11.md",
)
OUTPUT = ROOT / "deliverables/华东师范大学347心理测量保命手册_全本_逐题直背版V1.md"


def build() -> str:
    header = (
        "# 华东师范大学347心理测量保命手册\n\n"
        "## 全本·逐题直背版V1\n\n"
    )
    body = "\n\n".join(
        source.read_text(encoding="utf-8").strip()
        for source in SOURCES
    )
    return header + body + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build(), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
