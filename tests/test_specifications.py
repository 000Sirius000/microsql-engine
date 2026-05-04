from microsql.specifications import AndSpecification, EqualsSpec, GreaterThanSpec, OrSpecification


def test_specification_methods_can_be_composed_directly() -> None:
    specification = GreaterThanSpec("age", 20).And(EqualsSpec("role", "admin"))

    assert isinstance(specification, AndSpecification)
    assert specification.IsSatisfiedBy({"age": 25, "role": "admin"}) is True
    assert specification.IsSatisfiedBy({"age": 25, "role": "user"}) is False


def test_specification_or_and_not_composition() -> None:
    specification = GreaterThanSpec("age", 20).Or(EqualsSpec("role", "admin").Not())

    assert isinstance(specification, OrSpecification)
    assert specification.is_satisfied_by({"age": 19, "role": "user"}) is True
    assert specification.is_satisfied_by({"age": 19, "role": "admin"}) is False
