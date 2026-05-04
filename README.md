# Micro-SQL Engine (CSV Query Interpreter)

Навчальний проєкт: інтерпретатор спрощених SQL-подібних запитів до CSV-файлів.

## Що додано

- складний рушій фільтрації даних для `WHERE`;
- патерн **Specification**: `ISpecification<Row>`, `AndSpecification`, `OrSpecification`, `NotSpecification`, `GreaterThanSpec`, `EqualsSpec` тощо;
- підтримка вкладених логічних умов:
  ```sql
  WHERE (age > 20 AND role = 'admin') OR (salary > 5000)
  ```
- підтримка `NOT`:
  ```sql
  WHERE NOT (role = 'guest')
  ```
- зовнішній JSON-файл конфігурації `microsql.config.json`;
- безпечні значення за замовчуванням, якщо конфігураційний файл відсутній;
- ADR-документ: `docs/ADR-0001-new-feature.md`;
- unit-тести для нового функціоналу та regression-тести для старої поведінки.

## Приклад запиту

```sql
SELECT name, salary
FROM users.csv
WHERE (age > 20 AND role = 'admin') OR (salary > 5000)
ORDER BY salary DESC
```

## Конфігурація

Файл `microsql.config.json`:

```json
{
  "filter": {
    "engine": "specification",
    "enable_not_operator": true,
    "case_sensitive_strings": true
  }
}
```

Параметри:

- `engine` — активний рушій фільтрації. Зараз безпечним значенням є `specification`;
- `enable_not_operator` — дозволяє або забороняє оператор `NOT`;
- `case_sensitive_strings` — визначає, чи порівняння рядків чутливе до регістру.

Якщо файл конфігурації відсутній, програма використовує безпечні стандартні значення.

## Запуск проєкту

```bash
poetry install
poetry run microsql query.sql --data-dir .
```

З явним конфігураційним файлом:

```bash
poetry run microsql query.sql --data-dir . --config microsql.config.json
```

## Запуск тестів

```bash
poetry run pytest
```

Або без Poetry, якщо залежності вже встановлені:

```bash
python -m pytest
```

## Перевірка стилю

```bash
poetry run ruff check .
poetry run ruff format .
```

## Приклад логічної історії комітів

Оскільки цей архів не змінює GitHub-репозиторій напряму, коміти можна зробити локально після розпакування:

```bash
git add docs/ADR-0001-new-feature.md
git commit -m "Add ADR for specification filter engine"

git add src/microsql/specifications.py src/microsql/ast_nodes.py
git commit -m "Add Specification pattern for row filters"

git add src/microsql/parser.py src/microsql/tokenizer.py src/microsql/engine.py
git commit -m "Use specifications in WHERE parser and engine"

git add src/microsql/config.py microsql.config.json src/microsql/cli.py
git commit -m "Add JSON configuration for filter engine"

git add tests/
git commit -m "Add unit and regression tests for complex filters"
```
