from __future__ import annotations

from pathlib import Path

from microsql.cli import main


def test_cli_prints_csv_output(capsys, monkeypatch, tmp_path: Path) -> None:
    query_file = tmp_path / "query.sql"
    csv_file = tmp_path / "users.csv"
    query_file.write_text("SELECT name FROM users.csv WHERE salary > 2000", encoding="utf-8")
    csv_file.write_text("name,salary\nJane,3000\nJohn,1000\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["microsql", str(query_file), "--data-dir", str(tmp_path)],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "name" in captured.out
    assert "Jane" in captured.out
    assert captured.err == ""


def test_cli_formats_error_without_traceback(capsys, monkeypatch, tmp_path: Path) -> None:
    query_file = tmp_path / "query.sql"
    csv_file = tmp_path / "users.csv"
    query_file.write_text("SELECT missing FROM users.csv", encoding="utf-8")
    csv_file.write_text("name,salary\nJane,3000\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        ["microsql", str(query_file), "--data-dir", str(tmp_path)],
    )

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: ValidationException - Unknown column: missing" in captured.err
    assert "Traceback" not in captured.err
