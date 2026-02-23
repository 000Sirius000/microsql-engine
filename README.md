# Micro-SQL Engine (CSV Query Interpreter)

Навчальний проєкт: інтерпретатор спрощених SQL-подібних запитів до CSV-файлів.

## Опис

Програма виконує спрощені SQL-подібні запити до CSV-файлів.

На поточному етапі підтримується базовий сценарій:
- `SELECT ...`
- `FROM ...`
- `WHERE ...`
- `ORDER BY ...`

### Приклад запиту

```sql
SELECT name, salary
FROM users.csv
WHERE salary > 2000 AND role = 'user'
ORDER BY salary DESC
```

---

## Технології

- **Мова програмування:** Python 3.13+
- **Система керування залежностями:** Poetry
- **Стандарт кодування:** PEP8
- **Лінтер:** Ruff

---

## Як встановити залежності

У корені проєкту виконайте:

```powershell
poetry install
```

---

## Як запустити проєкт

У корені проєкту виконайте:

```powershell
poetry run microsql query.sql --data-dir .
```

### Очікуваний результат (для тестових файлів `users.csv` і `query.sql`)

```csv
name,salary
Jane Smith,3000
Alex,2500
```

---

## Як запустити перевірку лінтером

```powershell
poetry run ruff check .
```
