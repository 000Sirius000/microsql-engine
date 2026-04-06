from pathlib import Path

import pytest

from microsql.engine import execute_query
from microsql.exceptions import TypeConflictException, ValidationException
from microsql.parser import parse_query


@pytest.fixture
def stub_rows() -> list[dict[str, object]]:
    return [
        {"id": 1, "name": "John", "role": "admin", "salary": 1500},
        {"id": 2, "name": "Jane", "role": "user", "salary": 3000},
        {"id": 3, "name": "Alex", "role": "user", "salary": 2500},
    ]


def test_execute_query_filters_and_orders_rows_with_stub_loader(
    stub_rows: list[dict[str, object]],
) -> None:
    query = parse_query(
        "SELECT name, salary FROM users.csv WHERE salary > 2000 AND role = 'user' ORDER BY salary DESC"
    )

    def loader(_: Path) -> list[dict[str, object]]:
        return stub_rows

    result = execute_query(query, Path("."), row_loader=loader)

    assert result == [
        {"name": "Jane", "salary": 3000},
        {"name": "Alex", "salary": 2500},
    ]


def test_execute_query_raises_validation_exception_for_unknown_select_column(
    stub_rows: list[dict[str, object]],
) -> None:
    query = parse_query("SELECT missing FROM users.csv")

    with pytest.raises(ValidationException, match="Unknown column: missing"):
        execute_query(query, Path("."), row_loader=lambda _: stub_rows)


def test_execute_query_raises_validation_exception_for_unknown_where_column(
    stub_rows: list[dict[str, object]],
) -> None:
    query = parse_query("SELECT name FROM users.csv WHERE unknown > 1")

    with pytest.raises(ValidationException, match="Unknown column in WHERE clause: unknown"):
        execute_query(query, Path("."), row_loader=lambda _: stub_rows)


def test_execute_query_raises_type_conflict_exception(
    stub_rows: list[dict[str, object]],
) -> None:
    query = parse_query("SELECT name FROM users.csv WHERE salary > 'high'")

    with pytest.raises(TypeConflictException, match="Cannot compare values of different types"):
        execute_query(query, Path("."), row_loader=lambda _: stub_rows)
