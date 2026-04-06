from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from microsql.exceptions import FileSystemException

_INT_PATTERN = re.compile(r"^-?\d+$")
_FLOAT_PATTERN = re.compile(r"^-?\d+\.\d+$")


def load_csv_rows(csv_path: Path) -> list[dict[str, Any]]:
    try:
        with csv_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise FileSystemException(f"CSV file has no header: {csv_path}", 1)

            rows: list[dict[str, Any]] = []
            for row in reader:
                typed_row = {key: infer_scalar(value) for key, value in row.items()}
                rows.append(typed_row)
    except FileSystemException:
        raise
    except OSError as error:
        raise FileSystemException(f"Cannot read CSV file: {csv_path} ({error})", 1) from error
    except csv.Error as error:
        raise FileSystemException(f"Invalid CSV format in file: {csv_path} ({error})", 1) from error

    return rows


def infer_scalar(value: str | None) -> Any:
    if value is None:
        return None

    stripped = value.strip()
    if stripped == "":
        return None
    if _INT_PATTERN.match(stripped):
        return int(stripped)
    if _FLOAT_PATTERN.match(stripped):
        return float(stripped)
    return stripped
