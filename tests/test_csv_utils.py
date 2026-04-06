from pathlib import Path

import pytest

from microsql.csv_utils import infer_scalar, load_csv_rows
from microsql.exceptions import FileSystemException


def test_infer_scalar_converts_numbers_and_empty_values() -> None:
    assert infer_scalar("42") == 42
    assert infer_scalar("3.14") == 3.14
    assert infer_scalar("  text  ") == "text"
    assert infer_scalar("") is None
    assert infer_scalar(None) is None


def test_load_csv_rows_reads_and_types_values(tmp_path: Path) -> None:
    csv_file = tmp_path / "users.csv"
    csv_file.write_text("id,name,salary\n1,Anna,2500\n", encoding="utf-8")

    rows = load_csv_rows(csv_file)

    assert rows == [{"id": 1, "name": "Anna", "salary": 2500}]


def test_load_csv_rows_raises_filesystem_exception_for_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(FileSystemException, match="Cannot read CSV file"):
        load_csv_rows(missing_file)
