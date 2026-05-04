from pathlib import Path

import pytest

from microsql.engine import execute_query
from microsql.exceptions import TypeConflictException, ValidationException
from microsql.parser import parse_query


@pytest.fixture
def stub_rows() -> list[dict[str, object]]:
    return [
        {"id": 1, "name": "John", "role": "admin", "age": 25, "salary": 1500},
        {"id": 2, "name": "Jane", "role": "user", "age": 30, "salary": 3000},
        {"id": 3, "name": "Alex", "role": "user", "age": 22, "salary": 2500},
        {"id": 4, "name": "Maria", "role": "guest", "age": 19, "salary": 8000},
    ]


def test_execute_query_filters_and_orders_rows_with_stub_loader(
    stub_rows: list[dict[str, object]],
) -> None:
    query = parse_query(
        "SELECT name, salary FROM users.csv "
        "WHERE salary > 2000 AND role = 'user' "
        "ORDER BY salary DESC"
    )

    def loader(_: Path) -> list[dict[str, object]]:
        return stub_rows

    result = execute_query(query, Path("."), row_loader=loader)

    assert result == [
        {"name": "Jane", "salary": 3000},
        {"name": "Alex", "salary": 2500},
    ]


def test_execute_query_filters_nested_or_and_grouped_conditions(
    stub_rows: list[dict[str, object]],
) -> None:
    query = parse_query(
        "SELECT name FROM users.csv "
        "WHERE (age > 20 AND role = 'admin') OR (salary > 5000) "
        "ORDER BY name ASC"
    )

    result = execute_query(query, Path("."), row_loader=lambda _: stub_rows)

    assert result == [{"name": "John"}, {"name": "Maria"}]


def test_execute_query_supports_not_operator(stub_rows: list[dict[str, object]]) -> None:
    query = parse_query("SELECT name FROM users.csv WHERE NOT (role = 'guest') ORDER BY name ASC")

    result = execute_query(query, Path("."), row_loader=lambda _: stub_rows)

    assert result == [{"name": "Alex"}, {"name": "Jane"}, {"name": "John"}]


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
