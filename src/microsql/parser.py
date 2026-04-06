from __future__ import annotations

import re

from microsql.ast_nodes import (
    Comparison,
    Expr,
    Identifier,
    Literal,
    Operand,
    OrderBy,
    SelectQuery,
    Logical,
)
from microsql.exceptions import ParserException
from microsql.tokenizer import Token, tokenize_where

_ORDER_BY_REGEX = re.compile(
    r"^ORDER\s+BY\s+(?P<column>[A-Za-z_][A-Za-z0-9_]*)(?:\s+(?P<direction>ASC|DESC))?\s*;?\s*$",
    re.IGNORECASE | re.DOTALL,
)
_IDENTIFIER_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class _WhereParser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> Expr:
        expr = self._parse_or()
        if self._peek() is not None:
            token = self._peek()
            raise ParserException(f"Unexpected token: {token.value}", token.line_number)
        return expr

    def _parse_or(self) -> Expr:
        expr = self._parse_and()
        while self._match("OR"):
            operator = self.tokens[self.position - 1]
            right = self._parse_and()
            expr = Logical(operator="OR", left=expr, right=right, line_number=operator.line_number)
        return expr

    def _parse_and(self) -> Expr:
        expr = self._parse_comparison_or_group()
        while self._match("AND"):
            operator = self.tokens[self.position - 1]
            right = self._parse_comparison_or_group()
            expr = Logical(operator="AND", left=expr, right=right, line_number=operator.line_number)
        return expr

    def _parse_comparison_or_group(self) -> Expr:
        if self._match("LPAREN"):
            lparen = self.tokens[self.position - 1]
            expr = self._parse_or()
            self._consume("RPAREN", "Expected ')' after grouped expression", lparen.line_number)
            return expr

        left = self._parse_operand()
        operator = self._consume("COMPOP", "Expected comparison operator", left.line_number)
        right = self._parse_operand()
        return Comparison(
            left=left,
            operator=operator.value,
            right=right,
            line_number=operator.line_number,
        )

    def _parse_operand(self) -> Operand:
        token = self._peek()
        if token is None:
            fallback_line = self.tokens[-1].line_number if self.tokens else 1
            raise ParserException("Unexpected end of WHERE expression", fallback_line)

        if token.kind == "IDENT":
            self.position += 1
            return Identifier(name=str(token.value), line_number=token.line_number)
        if token.kind in {"NUMBER", "STRING"}:
            self.position += 1
            return Literal(value=token.value, line_number=token.line_number)

        raise ParserException(
            f"Expected identifier or literal, got: {token.value}",
            token.line_number,
        )

    def _peek(self) -> Token | None:
        if self.position >= len(self.tokens):
            return None
        return self.tokens[self.position]

    def _match(self, kind: str) -> bool:
        token = self._peek()
        if token is not None and token.kind == kind:
            self.position += 1
            return True
        return False

    def _consume(self, kind: str, message: str, fallback_line: int) -> Token:
        token = self._peek()
        if token is None or token.kind != kind:
            raise ParserException(message, fallback_line)
        self.position += 1
        return token


def parse_query(sql_text: str) -> SelectQuery:
    stripped_text = sql_text.strip()
    if not stripped_text:
        raise ParserException("Query is empty", 1)

    select_match = re.match(r"^\s*SELECT\b", sql_text, re.IGNORECASE)
    if select_match is None:
        raise ParserException("Query must start with SELECT", 1)

    from_match = _search_keyword(sql_text, "FROM", start=select_match.end())
    if from_match is None:
        line_number = _line_number_from_offset(sql_text, select_match.end())
        raise ParserException("Expected keyword FROM after SELECT clause", line_number)

    select_part = sql_text[select_match.end() : from_match.start()]
    columns, column_lines = _parse_select_columns(select_part, sql_text, select_match.end())

    source_start = _skip_whitespace(sql_text, from_match.end())
    if source_start >= len(sql_text):
        raise ParserException(
            "Expected CSV file name after FROM",
            _line_number_from_offset(sql_text, from_match.end()),
        )

    source_end = _read_source_end(sql_text, source_start)
    source = sql_text[source_start:source_end].strip().rstrip(";")
    if not source:
        raise ParserException(
            "Expected CSV file name after FROM",
            _line_number_from_offset(sql_text, source_start),
        )

    rest = sql_text[source_end:]
    where_match = _search_keyword(rest, "WHERE")
    order_match = _search_order_by(rest)

    if where_match is not None and order_match is not None and order_match.start() < where_match.start():
        raise ParserException(
            "WHERE clause cannot appear after ORDER BY",
            _line_number_from_offset(sql_text, source_end + order_match.start()),
        )

    where_expr = None
    order_by = None

    if where_match is None and order_match is None:
        trailing = rest.strip().rstrip(";")
        if trailing:
            line_number = _line_number_from_offset(sql_text, source_end + rest.index(trailing))
            if _looks_like_filter(trailing):
                raise ParserException("Expected keyword WHERE before filter condition", line_number)
            raise ParserException("Expected WHERE or ORDER BY after FROM clause", line_number)
    else:
        if where_match is not None:
            where_content_start = source_end + where_match.end()
            where_content_end = source_end + (order_match.start() if order_match is not None else len(rest))
            where_text = sql_text[where_content_start:where_content_end].strip()
            if not where_text:
                raise ParserException(
                    "WHERE clause must contain a condition",
                    _line_number_from_offset(sql_text, where_content_start),
                )
            base_line = _line_number_from_offset(sql_text, where_content_start)
            where_expr = _WhereParser(tokenize_where(where_text, base_line=base_line)).parse()

        if order_match is not None:
            order_text = rest[order_match.start() :].strip()
            order_by = _parse_order_by(
                order_text,
                sql_text,
                source_end + order_match.start(),
            )

    return SelectQuery(
        columns=columns,
        source=source,
        where=where_expr,
        order_by=order_by,
        column_lines=column_lines,
        source_line=_line_number_from_offset(sql_text, source_start),
    )


def _parse_select_columns(select_part: str, sql_text: str, select_start: int) -> tuple[list[str], dict[str, int]]:
    columns: list[str] = []
    column_lines: dict[str, int] = {}

    running_offset = 0
    for raw_column in select_part.split(","):
        stripped = raw_column.strip()
        if not stripped:
            continue
        if _IDENTIFIER_REGEX.match(stripped) is None:
            line_number = _line_number_from_offset(sql_text, select_start + running_offset)
            raise ParserException(f"Invalid column name in SELECT clause: {stripped}", line_number)
        columns.append(stripped)
        column_position = select_start + running_offset + raw_column.find(stripped)
        column_lines[stripped] = _line_number_from_offset(sql_text, column_position)
        running_offset += len(raw_column) + 1

    if not columns:
        raise ParserException(
            "At least one column must be selected",
            _line_number_from_offset(sql_text, select_start),
        )

    return columns, column_lines


def _parse_order_by(order_text: str, sql_text: str, offset: int) -> OrderBy:
    match = _ORDER_BY_REGEX.match(order_text)
    if match is None:
        raise ParserException(
            "Invalid ORDER BY clause. Supported: ORDER BY column [ASC|DESC]",
            _line_number_from_offset(sql_text, offset),
        )

    column = match.group("column")
    direction = (match.group("direction") or "ASC").upper()
    column_offset = offset + order_text.upper().find(column.upper())
    return OrderBy(
        column=column,
        descending=(direction == "DESC"),
        line_number=_line_number_from_offset(sql_text, column_offset),
    )


def _search_keyword(text: str, keyword: str, start: int = 0) -> re.Match[str] | None:
    pattern = re.compile(rf"\b{keyword}\b", re.IGNORECASE)
    return pattern.search(text, pos=start)


def _search_order_by(text: str) -> re.Match[str] | None:
    return re.search(r"\bORDER\s+BY\b", text, re.IGNORECASE)


def _skip_whitespace(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def _read_source_end(text: str, start: int) -> int:
    position = start
    while position < len(text):
        if text[position] == ";":
            return position
        if text[position].isspace():
            break
        position += 1
    return position


def _line_number_from_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _looks_like_filter(text: str) -> bool:
    return any(operator in text for operator in ("=", "!=", "<>", ">=", "<=", ">", "<"))
