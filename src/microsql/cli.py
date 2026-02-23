from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from microsql.engine import execute_query
from microsql.parser import parse_query


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Micro-SQL engine for CSV files")
    parser.add_argument("query_file", type=Path, help="Path to .sql query file")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("."),
        help="Directory that contains CSV files (default: current directory)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    sql_text = args.query_file.read_text(encoding="utf-8")
    query = parse_query(sql_text)
    result_rows = execute_query(query, args.data_dir)

    _print_as_csv(result_rows)


def _print_as_csv(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("(no rows)")
        return

    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
