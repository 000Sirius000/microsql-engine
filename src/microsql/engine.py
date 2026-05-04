from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from microsql.ast_nodes import SelectQuery
from microsql.csv_utils import load_csv_rows
from microsql.exceptions import ValidationException
from microsql.specifications import ISpecification, Row

RowLoader = Callable[[Path], list[dict[str, Any]]]


def execute_query(
    query: SelectQuery,
    data_dir: Path,
    row_loader: RowLoader = load_csv_rows,
) -> list[dict[str, Any]]:
    csv_path = (data_dir / query.source).resolve()
    rows = row_loader(csv_path)

    _validate_columns_exist(rows, query.columns, query.column_lines)
    if query.order_by is not None:
        _validate_columns_exist(
            rows,
            [query.order_by.column],
            {query.order_by.column: query.order_by.line_number},
        )

    if query.where is not None:
        _validate_where_identifiers(rows, query.where)
        rows = [row for row in rows if query.where.is_satisfied_by(row)]

    if query.order_by is not None:
        order_column = query.order_by.column
        rows = sorted(
            rows,
            key=lambda row: _sort_key(row.get(order_column)),
            reverse=query.order_by.descending,
        )

    return [{column: row.get(column) for column in query.columns} for row in rows]


def _validate_columns_exist(
    rows: list[dict[str, Any]],
    required_columns: list[str],
    column_lines: dict[str, int],
) -> None:
    if not rows:
        return
    available = set(rows[0].keys())
    for column in required_columns:
        if column not in available:
            raise ValidationException(
                f"Unknown column: {column}",
                column_lines.get(column, 1),
            )


def _validate_where_identifiers(rows: list[dict[str, Any]], spec: ISpecification[Row]) -> None:
    if not rows:
        return
    available = set(rows[0].keys())
    for identifier in spec.collect_identifiers():
        if identifier.name not in available:
            raise ValidationException(
                f"Unknown column in WHERE clause: {identifier.name}",
                identifier.line_number,
            )


def _sort_key(value: Any) -> tuple[int, Any]:
    if value is None:
        return (1, "")
    return (0, value)
