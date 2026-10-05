from __future__ import annotations

import argparse
from pathlib import Path

import render_shenzhen_baoming_v5 as guide
import render_shenzhen_general_baoming as base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page-map", type=Path)
    parser.add_argument("--subject-label", required=True)
    parser.add_argument("--header-text", required=True)
    arguments = parser.parse_args()

    base.add_student_guide = guide.add_student_guide
    base.render(
        arguments.input,
        arguments.output,
        arguments.page_map,
        subject_label=arguments.subject_label,
        header_text=arguments.header_text,
        compact_answers=True,
    )


if __name__ == "__main__":
    main()
