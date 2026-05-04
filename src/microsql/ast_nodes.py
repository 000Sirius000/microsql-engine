from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from microsql.exceptions import TypeConflictException, ValidationException

Row = dict[str, Any]
RowT = TypeVar("RowT", bound=dict[str, Any])


@dataclass(slots=True)
class OrderBy:
    column: str
    descending: bool = False
    line_number: int = 1


@dataclass(slots=True)
class SelectQuery:
    columns: list[str]
    source: str
    where: ISpecification[Row] | None = None
    order_by: OrderBy | None = None
    column_lines: dict[str, int] = field(default_factory=dict)
    source_line: int = 1


class ISpecification(ABC, Generic[RowT]):
    """Base abstraction for composable row filtering specifications."""

    line_number: int

    @abstractmethod
    def is_satisfied_by(self, row: RowT) -> bool:
        """Return True when the row satisfies this specification."""

    def IsSatisfiedBy(self, row: RowT) -> bool:  # noqa: N802 - required by assignment wording
        return self.is_satisfied_by(row)

    def evaluate(self, row: RowT) -> bool:
        """Compatibility alias for the previous expression-tree API."""

        return self.is_satisfied_by(row)

    def And(self, spec: ISpecification[RowT]) -> ISpecification[RowT]:  # noqa: N802
        return AndSpecification(self, spec, self.line_number)

    def Or(self, spec: ISpecification[RowT]) -> ISpecification[RowT]:  # noqa: N802
        return OrSpecification(self, spec, self.line_number)

    def Not(self) -> ISpecification[RowT]:  # noqa: N802
        return NotSpecification(self, self.line_number)

    def and_spec(self, spec: ISpecification[RowT]) -> ISpecification[RowT]:
        return self.And(spec)

    def or_spec(self, spec: ISpecification[RowT]) -> ISpecification[RowT]:
        return self.Or(spec)

    def not_spec(self) -> ISpecification[RowT]:
        return self.Not()

    @abstractmethod
    def collect_identifiers(self) -> list[Identifier]:
        """Return identifiers used by this specification for validation."""


class Expr(ISpecification[Row]):
    """Compatibility name for the previous WHERE expression abstraction."""


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
    case_sensitive_strings: bool = True

    def is_satisfied_by(self, row: Row) -> bool:
        left_value = _resolve_operand(self.left, row)
        right_value = _resolve_operand(self.right, row)
        operator = "!=" if self.operator == "<>" else self.operator

        if operator in {"=", "!="}:
            left_value, right_value = _normalize_equality_values(
                left_value,
                right_value,
                self.case_sensitive_strings,
            )
            result = left_value == right_value
            return result if operator == "=" else not result

        if left_value is None or right_value is None:
            return False

        left_value, right_value = _coerce_for_comparison(
            left_value,
            right_value,
            self.line_number,
            self.case_sensitive_strings,
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


class EqualsSpec(Comparison):
    def __init__(
        self,
        column: str,
        value: Any,
        line_number: int = 1,
        case_sensitive_strings: bool = True,
    ) -> None:
        super().__init__(
            left=Identifier(column, line_number),
            operator="=",
            right=Literal(value, line_number),
            line_number=line_number,
            case_sensitive_strings=case_sensitive_strings,
        )


class NotEqualsSpec(Comparison):
    def __init__(
        self,
        column: str,
        value: Any,
        line_number: int = 1,
        case_sensitive_strings: bool = True,
    ) -> None:
        super().__init__(
            left=Identifier(column, line_number),
            operator="!=",
            right=Literal(value, line_number),
            line_number=line_number,
            case_sensitive_strings=case_sensitive_strings,
        )


class GreaterThanSpec(Comparison):
    def __init__(self, column: str, value: Any, line_number: int = 1) -> None:
        super().__init__(
            left=Identifier(column, line_number),
            operator=">",
            right=Literal(value, line_number),
            line_number=line_number,
        )


class LessThanSpec(Comparison):
    def __init__(self, column: str, value: Any, line_number: int = 1) -> None:
        super().__init__(
            left=Identifier(column, line_number),
            operator="<",
            right=Literal(value, line_number),
            line_number=line_number,
        )


class GreaterOrEqualSpec(Comparison):
    def __init__(self, column: str, value: Any, line_number: int = 1) -> None:
        super().__init__(
            left=Identifier(column, line_number),
            operator=">=",
            right=Literal(value, line_number),
            line_number=line_number,
        )


class LessOrEqualSpec(Comparison):
    def __init__(self, column: str, value: Any, line_number: int = 1) -> None:
        super().__init__(
            left=Identifier(column, line_number),
            operator="<=",
            right=Literal(value, line_number),
            line_number=line_number,
        )


@dataclass(slots=True)
class Logical(Expr):
    operator: str
    left: ISpecification[Row]
    right: ISpecification[Row]
    line_number: int = 1

    def is_satisfied_by(self, row: Row) -> bool:
        op = self.operator.upper()
        if op == "AND":
            return self.left.is_satisfied_by(row) and self.right.is_satisfied_by(row)
        if op == "OR":
            return self.left.is_satisfied_by(row) or self.right.is_satisfied_by(row)
        raise ValidationException(
            f"Unsupported logical operator: {self.operator}",
            self.line_number,
        )

    def collect_identifiers(self) -> list[Identifier]:
        return [*self.left.collect_identifiers(), *self.right.collect_identifiers()]


class AndSpecification(Logical):
    def __init__(
        self,
        left: ISpecification[Row],
        right: ISpecification[Row],
        line_number: int = 1,
    ) -> None:
        super().__init__(operator="AND", left=left, right=right, line_number=line_number)


class OrSpecification(Logical):
    def __init__(
        self,
        left: ISpecification[Row],
        right: ISpecification[Row],
        line_number: int = 1,
    ) -> None:
        super().__init__(operator="OR", left=left, right=right, line_number=line_number)


@dataclass(slots=True)
class NotSpecification(Expr):
    specification: ISpecification[Row]
    line_number: int = 1

    def is_satisfied_by(self, row: Row) -> bool:
        return not self.specification.is_satisfied_by(row)

    def collect_identifiers(self) -> list[Identifier]:
        return self.specification.collect_identifiers()


def build_comparison_specification(
    left: Operand,
    operator: str,
    right: Operand,
    line_number: int = 1,
    case_sensitive_strings: bool = True,
) -> Comparison:
    """Factory for comparison specifications used by the WHERE parser."""

    return Comparison(
        left=left,
        operator=operator,
        right=right,
        line_number=line_number,
        case_sensitive_strings=case_sensitive_strings,
    )


def _resolve_operand(operand: Operand, row: Row) -> Any:
    if isinstance(operand, Identifier):
        return row.get(operand.name)
    return operand.value


def _normalize_equality_values(
    left: Any,
    right: Any,
    case_sensitive_strings: bool,
) -> tuple[Any, Any]:
    if not case_sensitive_strings and isinstance(left, str) and isinstance(right, str):
        return left.lower(), right.lower()
    return left, right


def _coerce_for_comparison(
    left: Any,
    right: Any,
    line_number: int,
    case_sensitive_strings: bool = True,
) -> tuple[Any, Any]:
    numeric_types = (int, float)
    if isinstance(left, numeric_types) and isinstance(right, numeric_types):
        return float(left), float(right)

    if isinstance(left, str) and isinstance(right, str):
        if case_sensitive_strings:
            return left, right
        return left.lower(), right.lower()

    raise TypeConflictException(
        "Cannot compare values of different types: "
        f"{type(left).__name__} and {type(right).__name__}",
        line_number,
    )
