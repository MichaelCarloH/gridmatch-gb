"""Validate a Phase 4 meter CSV without discarding invalid rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gridmatch.data.uploads import validate_csv_upload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--annotated-output", type=Path)
    arguments = parser.parse_args()
    result = validate_csv_upload(arguments.csv_path)
    print(json.dumps(result.report, indent=2))
    if arguments.annotated_output:
        arguments.annotated_output.parent.mkdir(parents=True, exist_ok=True)
        result.annotated_data.to_csv(arguments.annotated_output, index=False)


if __name__ == "__main__":
    main()
