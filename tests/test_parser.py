import pytest

from microsql.ast_nodes import Comparison, Logical
from microsql.exceptions import ParserException
from microsql.parser import parse_query
from microsql.tokenizer import tokenize_where


def test_tokenize_where_preserves_line_numbers() -> None:
    expression = "salary > 1000\nAND role = 'user'"

    tokens = tokenize_where(expression, base_line=3)

    assert [token.kind for token in tokens] == [
        "IDENT",
        "COMPOP",
        "NUMBER",
        "AND",
        "IDENT",
        "COMPOP",
        "STRING",
    ]
    assert tokens[0].line_number == 3
    assert tokens[3].line_number == 4


def test_parse_query_handles_multiline_query() -> None:
    query = parse_query(
        "SELECT name, salary\nFROM users.csv\nWHERE salary > 1000\nORDER BY salary DESC"
    )

    assert query.columns == ["name", "salary"]
    assert query.source == "users.csv"
    assert query.order_by is not None
    assert query.order_by.column == "salary"
    assert query.order_by.descending is True
    assert isinstance(query.where, Comparison)


def test_parse_query_supports_logical_expressions() -> None:
    query = parse_query(
        "SELECT name FROM users.csv WHERE salary > 1000 AND role = 'user'"
    )

    assert isinstance(query.where, Logical)
    assert query.where.operator == "AND"


@pytest.mark.parametrize(
    ("sql_text", "message"),
    [
        ("SELECT name users.csv", "Expected keyword FROM after SELECT clause"),
        (
            "SELECT name\nFROM users.csv\nsalary > 10",
            "Expected keyword WHERE before filter condition",
        ),
        ("SELECT name FROM users.csv WHERE", "WHERE clause must contain a condition"),
    ],
)
def test_parse_query_raises_parser_exceptions(sql_text: str, message: str) -> None:
    with pytest.raises(ParserException, match=message):
        parse_query(sql_text)
