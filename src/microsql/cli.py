from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from microsql.config import load_config
from microsql.engine import execute_query
from microsql.exceptions import FileSystemException, MicroSQLException
from microsql.parser import parse_query

DEFAULT_CONFIG_PATH = Path("microsql.config.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Micro-SQL engine for CSV files")
    parser.add_argument("query_file", type=Path, help="Path to .sql query file")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("."),
        help="Directory that contains CSV files (default: current directory)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to optional JSON configuration file (default: microsql.config.json)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        sql_text = args.query_file.read_text(encoding="utf-8")
        query = parse_query(sql_text, options=config.to_parser_options())
        result_rows = execute_query(query, args.data_dir)
        _print_as_csv(result_rows)
        return 0
    except MicroSQLException as error:
        _print_error(error)
        return 1
    except OSError as error:
        wrapped = FileSystemException(
            f"Cannot read query file: {args.query_file} ({error})",
            1,
        )
        _print_error(wrapped)
        return 1


def _print_error(error: MicroSQLException) -> None:
    print(
        f"Error: {error.error_type} - {error.message} у рядку {error.line_number}",
        file=sys.stderr,
    )


def _print_as_csv(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("(no rows)")
        return

    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
