from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

import validate_measurement_baoming_v6 as validator
from build_measurement_baoming_v7 import OUTPUT, SOURCE, transform


def main() -> None:
    validator.SOURCE = SOURCE
    validator.OUTPUT = OUTPUT
    validator.transform = transform
    buffer = StringIO()
    with redirect_stdout(buffer):
        validator.main()
    print(buffer.getvalue().replace("V6", "V7").strip())


if __name__ == "__main__":
    main()
