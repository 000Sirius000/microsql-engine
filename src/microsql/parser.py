from __future__ import annotations

import re

from microsql.ast_nodes import (
    Comparison,
    Expr,
    Identifier,
    Literal,
    Logical,
    Operand,
    OrderBy,
    SelectQuery,
)
from microsql.tokenizer import Token, tokenize_where

_QUERY_REGEX = re.compile(
    r"""
    ^\s*SELECT\s+(?P<select>.+?)
    \s+FROM\s+(?P<source>[^\s;]+)
    (?:\s+WHERE\s+(?P<where>.+?))?
    (?:\s+ORDER\s+BY\s+(?P<order_col>[A-Za-z_][A-Za-z0-9_]*)
       (?:\s+(?P<order_dir>ASC|DESC))?)?
    \s*;?\s*$
    """,
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)


class _WhereParser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.position = 0

    def parse(self) -> Expr:
        expr = self._parse_or()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token: {self._peek()}")
        return expr

    def _parse_or(self) -> Expr:
        expr = self._parse_and()
        while self._match("OR"):
            right = self._parse_and()
            expr = Logical(operator="OR", left=expr, right=right)
        return expr

    def _parse_and(self) -> Expr:
        expr = self._parse_comparison_or_group()
        while self._match("AND"):
            right = self._parse_comparison_or_group()
            expr = Logical(operator="AND", left=expr, right=right)
        return expr

    def _parse_comparison_or_group(self) -> Expr:
        if self._match("LPAREN"):
            expr = self._parse_or()
            self._consume("RPAREN", "Expected ')' after grouped expression")
            return expr

        left = self._parse_operand()
        operator = self._consume("COMPOP", "Expected comparison operator").value
        right = self._parse_operand()
        return Comparison(left=left, operator=operator, right=right)

    def _parse_operand(self) -> Operand:
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of WHERE expression")

        if token.kind == "IDENT":
            self.position += 1
            return Identifier(name=str(token.value))
        if token.kind in {"NUMBER", "STRING"}:
            self.position += 1
            return Literal(value=token.value)

        raise ValueError(f"Expected identifier or literal, got: {token}")

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

    def _consume(self, kind: str, message: str) -> Token:
        token = self._peek()
        if token is None or token.kind != kind:
            raise ValueError(message)
        self.position += 1
        return token


def parse_query(sql_text: str) -> SelectQuery:
    normalized = " ".join(sql_text.strip().split())
    match = _QUERY_REGEX.match(normalized)
    if match is None:
        raise ValueError(
            "Unsupported query syntax. Supported: SELECT ... FROM ... [WHERE ...] [ORDER BY ...]"
        )

    raw_columns = match.group("select")
    columns = [col.strip() for col in raw_columns.split(",") if col.strip()]
    if not columns:
        raise ValueError("At least one column must be selected")

    source = match.group("source").strip()
    where_text = match.group("where")
    order_col = match.group("order_col")
    order_dir = (match.group("order_dir") or "ASC").upper()

    where_expr = None
    if where_text:
        where_expr = _WhereParser(tokenize_where(where_text)).parse()

    order_by = None
    if order_col:
        order_by = OrderBy(column=order_col, descending=(order_dir == "DESC"))

    return SelectQuery(columns=columns, source=source, where=where_expr, order_by=order_by)
