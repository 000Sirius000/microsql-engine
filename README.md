# Micro-SQL Engine (CSV Query Interpreter)

Навчальний проєкт: інтерпретатор спрощених SQL-подібних запитів до CSV-файлів.

## Що додано

- власна ієрархія виключень: `ParserException`, `ValidationException`, `TypeConflictException`, `FileSystemException`;
- контрольована обробка помилок у CLI без stacktrace;
- формат повідомлення: `Error: [Тип помилки] - [Детальний опис] у рядку N`;
- модульні тести на позитивні та негативні сценарії;
- запуск тестів і перевірка покриття через `pytest`;
- покриття коду налаштовано з порогом не менше 70%.

## Приклади помилок

- звернення до неіснуючої колонки;
- конфлікт типів у порівнянні;
- синтаксична помилка через пропущене `FROM` або `WHERE`.

## Запуск проєкту

```bash
poetry install
poetry run microsql query.sql --data-dir .
```

## Запуск тестів

```bash
poetry run pytest
```
