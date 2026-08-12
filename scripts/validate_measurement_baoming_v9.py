from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO

import validate_measurement_baoming_v8 as validator
from build_measurement_baoming_v9 import OUTPUT, SOURCE, transform


def main() -> None:
    validator.SOURCE = SOURCE
    validator.OUTPUT = OUTPUT
    validator.transform = transform
    buffer = StringIO()
    with redirect_stdout(buffer):
        validator.main()
    output = buffer.getvalue().replace("V8", "V9").strip()
    assert "42个准入名解、61处调用零异文" in output
    print(output)


if __name__ == "__main__":
    main()
