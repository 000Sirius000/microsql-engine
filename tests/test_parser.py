import pytest

from microsql.ast_nodes import Comparison, Logical
from microsql.exceptions import ParserException
from microsql.parser import ParserOptions, parse_query
from microsql.specifications import AndSpecification, NotSpecification, OrSpecification
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


def test_tokenize_where_supports_not_keyword() -> None:
    tokens = tokenize_where("NOT (role = 'guest')")

    assert [token.kind for token in tokens] == [
        "NOT",
        "LPAREN",
        "IDENT",
        "COMPOP",
        "STRING",
        "RPAREN",
    ]


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
    query = parse_query("SELECT name FROM users.csv WHERE salary > 1000 AND role = 'user'")

    assert isinstance(query.where, Logical)
    assert isinstance(query.where, AndSpecification)
    assert query.where.operator == "AND"


def test_parse_query_builds_nested_specification_tree() -> None:
    query = parse_query(
        "SELECT name FROM users.csv "
        "WHERE (age > 20 AND role = 'admin') OR (salary > 5000)"
    )

    assert isinstance(query.where, OrSpecification)
    assert isinstance(query.where.left, AndSpecification)
    assert query.where.is_satisfied_by({"age": 25, "role": "admin", "salary": 1000}) is True
    assert query.where.is_satisfied_by({"age": 18, "role": "guest", "salary": 6000}) is True
    assert query.where.is_satisfied_by({"age": 18, "role": "guest", "salary": 1000}) is False


def test_parse_query_supports_not_specification() -> None:
    query = parse_query("SELECT name FROM users.csv WHERE NOT (role = 'guest')")

    assert isinstance(query.where, NotSpecification)
    assert query.where.is_satisfied_by({"role": "admin"}) is True
    assert query.where.is_satisfied_by({"role": "guest"}) is False


def test_parse_query_can_disable_not_operator_by_config() -> None:
    options = ParserOptions(enable_not_operator=False)

    with pytest.raises(ParserException, match="NOT operator is disabled by configuration"):
        parse_query("SELECT name FROM users.csv WHERE NOT (role = 'guest')", options=options)


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
