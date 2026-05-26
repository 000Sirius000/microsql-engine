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
---

## Docker

Проєкт  можна запускати у Docker-контейнері без ручного встановлення Python-залежностей на локальній машині.

Docker використовується для того, щоб програма працювала однаково в різних середовищах. Усі необхідні залежності встановлюються всередині образу, а вхідні файли передаються в контейнер через монтування поточної папки як volume.

### Збірка Docker-образу

Перед виконанням команди потрібно перейти в кореневу папку проєкту, де знаходиться `Dockerfile`.

```bash
docker build -t microsql-engine:local .
```

Пояснення команди:

- `docker build` — збирає Docker-образ;
- `-t microsql-engine:local` — задає назву образу `microsql-engine` і тег `local`;
- `.` — означає, що контекстом збірки є поточна папка проєкту.

### Запуск контейнера

#### PowerShell

```powershell
docker run --rm -v "${PWD}:/data" microsql-engine:local /data/query.sql --data-dir /data --config /data/microsql.config.json
```

#### Git Bash / Linux

```bash
docker run --rm -v "$PWD:/data" microsql-engine:local /data/query.sql --data-dir /data --config /data/microsql.config.json
```

У цій команді:

- `docker run` — запускає контейнер;
- `--rm` — автоматично видаляє контейнер після завершення роботи;
- `-v "${PWD}:/data"` — монтує поточну папку проєкту всередину контейнера як `/data`;
- `microsql-engine:local` — назва Docker-образу, який запускається;
- `/data/query.sql` — шлях до SQL-файлу всередині контейнера;
- `--data-dir /data` — директорія з CSV-файлами;
- `--config /data/microsql.config.json` — файл конфігурації.

### Приклад результату запуску

Після запуску контейнера програма успішно виконала запит і вивела результат:

```text
name,salary
Olena,6500
Jane Smith,3000
Alex,2500
```

Це підтверджує, що контейнеризований застосунок працює коректно та отримує вхідні файли через Docker volume.

---

## CI/CD

У проєкті налаштовано автоматизований pipeline за допомогою GitHub Actions.

Файл конфігурації знаходиться за шляхом:

```text
.github/workflows/ci-cd.yml
```

Pipeline автоматично запускається при:

- push у головну гілку `master`;
- створенні Pull Request у гілку `master`;
- створенні Git-тегу версії у форматі `v*.*.*`, наприклад `v1.0.0`.

### Етапи CI

Pipeline виконує такі дії:

1. Завантажує код репозиторію.
2. Встановлює Python.
3. Встановлює Poetry.
4. Встановлює залежності проєкту.
5. Запускає лінтер Ruff.
6. Перевіряє форматування коду.
7. Запускає unit-тести.
8. Збирає Python wheel.
9. Збирає Docker-образ.
10. Виконує тестовий запуск Docker-контейнера.

Якщо лінтер або unit-тести завершуються з помилкою, pipeline отримує статус `failed`.

### Створення релізу

Реліз створюється автоматично після створення Git-тегу версії.

Приклад створення тегу:

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

Після цього GitHub Actions автоматично створює реліз на сторінці `Releases` і прикріплює до нього релізні артефакти:

- Python wheel;
- Docker image у форматі `.tar`.