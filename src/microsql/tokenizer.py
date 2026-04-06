from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from microsql.exceptions import ParserException

_TOKEN_REGEX = re.compile(
    r"""
    (?P<SPACE>\s+)
    |(?P<LPAREN>\()
    |(?P<RPAREN>\))
    |(?P<COMPOP><=|>=|<>|!=|=|<|>)
    |(?P<STRING>'(?:[^']|'')*')
    |(?P<NUMBER>-?\d+(?:\.\d+)?)
    |(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


@dataclass(slots=True)
class Token:
    kind: str
    value: Any
    line_number: int


def tokenize_where(expression: str, base_line: int = 1) -> list[Token]:
    tokens: list[Token] = []
    position = 0

    while position < len(expression):
        match = _TOKEN_REGEX.match(expression, position)
        if match is None:
            snippet = expression[position : position + 20]
            line_number = base_line + expression[:position].count("\n")
            raise ParserException(f"Unexpected token near: {snippet!r}", line_number)

        kind = match.lastgroup
        raw_value = match.group()
        line_number = base_line + expression[: match.start()].count("\n")

        if kind == "SPACE":
            position = match.end()
            continue

        if kind == "IDENT":
            upper = raw_value.upper()
            if upper in {"AND", "OR"}:
                tokens.append(Token(kind=upper, value=upper, line_number=line_number))
            else:
                tokens.append(Token(kind="IDENT", value=raw_value, line_number=line_number))
        elif kind == "NUMBER":
            value = float(raw_value) if "." in raw_value else int(raw_value)
            tokens.append(Token(kind="NUMBER", value=value, line_number=line_number))
        elif kind == "STRING":
            inner = raw_value[1:-1].replace("''", "'")
            tokens.append(Token(kind="STRING", value=inner, line_number=line_number))
        else:
            tokens.append(Token(kind=kind, value=raw_value, line_number=line_number))

        position = match.end()

    return tokens
