from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from microsql.exceptions import TypeConflictException, ValidationException


@dataclass(slots=True)
class OrderBy:
    column: str
    descending: bool = False
    line_number: int = 1


@dataclass(slots=True)
class SelectQuery:
    columns: list[str]
    source: str
    where: Expr | None = None
    order_by: OrderBy | None = None
    column_lines: dict[str, int] = field(default_factory=dict)
    source_line: int = 1


class Expr:
    line_number: int

    def evaluate(self, row: dict[str, Any]) -> bool:
        raise NotImplementedError

    def collect_identifiers(self) -> list[Identifier]:
        raise NotImplementedError


@dataclass(slots=True)
class Identifier:
    name: str
    line_number: int = 1


@dataclass(slots=True)
class Literal:
    value: Any
    line_number: int = 1


Operand = Identifier | Literal


@dataclass(slots=True)
class Comparison(Expr):
    left: Operand
    operator: str
    right: Operand
    line_number: int = 1

    def evaluate(self, row: dict[str, Any]) -> bool:
        left_value = _resolve_operand(self.left, row)
        right_value = _resolve_operand(self.right, row)
        operator = "!=" if self.operator == "<>" else self.operator

        if operator == "=":
            return left_value == right_value
        if operator == "!=":
            return left_value != right_value
        if left_value is None or right_value is None:
            return False

        left_value, right_value = _coerce_for_comparison(
            left_value,
            right_value,
            self.line_number,
        )

        if operator == ">":
            return left_value > right_value
        if operator == "<":
            return left_value < right_value
        if operator == ">=":
            return left_value >= right_value
        if operator == "<=":
            return left_value <= right_value

        raise ValidationException(f"Unsupported operator: {self.operator}", self.line_number)

    def collect_identifiers(self) -> list[Identifier]:
        identifiers: list[Identifier] = []
        if isinstance(self.left, Identifier):
            identifiers.append(self.left)
        if isinstance(self.right, Identifier):
            identifiers.append(self.right)
        return identifiers


@dataclass(slots=True)
class Logical(Expr):
    operator: str
    left: Expr
    right: Expr
    line_number: int = 1

    def evaluate(self, row: dict[str, Any]) -> bool:
        op = self.operator.upper()
        if op == "AND":
            return self.left.evaluate(row) and self.right.evaluate(row)
        if op == "OR":
            return self.left.evaluate(row) or self.right.evaluate(row)
        raise ValidationException(f"Unsupported logical operator: {self.operator}", self.line_number)

    def collect_identifiers(self) -> list[Identifier]:
        return [*self.left.collect_identifiers(), *self.right.collect_identifiers()]


def _resolve_operand(operand: Operand, row: dict[str, Any]) -> Any:
    if isinstance(operand, Identifier):
        return row.get(operand.name)
    return operand.value


def _coerce_for_comparison(left: Any, right: Any, line_number: int) -> tuple[Any, Any]:
    numeric_types = (int, float)
    if isinstance(left, numeric_types) and isinstance(right, numeric_types):
        return float(left), float(right)

    if isinstance(left, str) and isinstance(right, str):
        return left, right

    raise TypeConflictException(
        f"Cannot compare values of different types: {type(left).__name__} and {type(right).__name__}",
        line_number,
    )
