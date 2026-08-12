from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

import validate_measurement_baoming_v6 as validator
import validate_measurement_baoming_v3 as definition_validator
from build_measurement_baoming_v8 import OUTPUT, SOURCE, transform


ADDED_TERMS = {"16PF", "MMPI", "EPQ"}
CHANGED_HEADING = "押题1【论述】比较**16PF、MMPI和EPQ**的理论基础、编制方法与结构特点。"


def main() -> None:
    validator.SOURCE = SOURCE
    validator.OUTPUT = OUTPUT
    validator.transform = transform
    validator.EXPECTED_ADMITTED_TERMS = validator.ADMITTED_TERMS | ADDED_TERMS
    validator.EXPECTED_DEFINITION_COUNT = 61
    validator.CONTENT_FRAGMENT_EXEMPT_HEADINGS = {CHANGED_HEADING}
    definition_validator.EXPANSIONS.update(
        {
            "16PF": "不同因素的组合构成个体独特的人格。",
            "MMPI": "它主要由**效度量表和临床量表**组成。",
            "EPQ": (
                "其测题经过**因素分析**测定，每个测题只负荷一个维度因素，量表包括"
                "**E、N、P、L四个分量表**。"
            ),
        }
    )
    buffer = StringIO()
    with redirect_stdout(buffer):
        validator.main()
    output = buffer.getvalue().replace("V6", "V8").strip()
    assert "42个准入名解、61处调用零异文" in output
    print(output)


if __name__ == "__main__":
    main()
