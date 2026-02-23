from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OrderBy:
    column: str
    descending: bool = False


@dataclass(slots=True)
class SelectQuery:
    columns: list[str]
    source: str
    where: Expr | None = None
    order_by: OrderBy | None = None


class Expr:
    def evaluate(self, row: dict[str, Any]) -> bool:
        raise NotImplementedError


@dataclass(slots=True)
class Identifier:
    name: str


@dataclass(slots=True)
class Literal:
    value: Any


Operand = Identifier | Literal


@dataclass(slots=True)
class Comparison(Expr):
    left: Operand
    operator: str
    right: Operand

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

        left_value, right_value = _coerce_for_comparison(left_value, right_value)

        if operator == ">":
            return left_value > right_value
        if operator == "<":
            return left_value < right_value
        if operator == ">=":
            return left_value >= right_value
        if operator == "<=":
            return left_value <= right_value

        raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass(slots=True)
class Logical(Expr):
    operator: str
    left: Expr
    right: Expr

    def evaluate(self, row: dict[str, Any]) -> bool:
        op = self.operator.upper()
        if op == "AND":
            return self.left.evaluate(row) and self.right.evaluate(row)
        if op == "OR":
            return self.left.evaluate(row) or self.right.evaluate(row)
        raise ValueError(f"Unsupported logical operator: {self.operator}")


def _resolve_operand(operand: Operand, row: dict[str, Any]) -> Any:
    if isinstance(operand, Identifier):
        return row.get(operand.name)
    return operand.value


def _coerce_for_comparison(left: Any, right: Any) -> tuple[Any, Any]:
    numeric_types = (int, float)
    if isinstance(left, numeric_types) and isinstance(right, numeric_types):
        return float(left), float(right)
    return str(left), str(right)
