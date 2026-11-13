# Приём сдач, этап А

Учебный пакет онлайн-школы. Этап А лабораторной 1 принимает JSONL со сдачами, проверяет схему и различает новую сдачу, дубликат и конфликт идентификатора. Анализаторы, источники по протоколу и отчёты сходства относятся к следующим этапам.

Траектория: Python Core, основной уровень. Памятки с готовым контрактом в материалах не было, поэтому контракт зафиксирован ниже и в коде.

## Контракт сдачи

Обязательные поля объекта:

| Поле | Правило |
| --- | --- |
| `submission_id` | непустая строка; новая версия работы получает новый идентификатор |
| `student_id` | непустая строка, пробелы не считаются значением |
| `assignment_id` | непустая строка из `assignments.json` |
| `timestamp` | ISO 8601 с временной зоной: `+03:00` или `Z` |
| `text` | строка |
| `code` | строка; программа её не запускает |
| `ai_declaration` | объект с `used` (bool) и `description` (строка) |

При `used: true` описание непустое. При `used: false` описание можно опустить, тогда оно сохраняется как пустая строка. Любое другое поле — нарушение схемы.

Хеш содержимого — SHA-256 канонического JSON полей `assignment_id`, `student_id`, `text`, `code` и `ai_declaration`. В хеш не входят `submission_id` и `timestamp`.

Ошибки:

| `code` | Когда |
| --- | --- |
| `format_error` | строка не является JSON |
| `schema_violation` | JSON есть, но поля, типы, зона времени, декларация или задание неверны |
| `conflict` | тот же `submission_id`, другой хеш; первая сдача остаётся |

Тот же идентификатор и тот же хеш — дубликат: в хранилище по-прежнему первая сдача, счётчик не растёт.

Каталог заданий:

```json
{"assignments": [{"assignment_id": "py-intro-1", "title": "Функции и тесты"}]}
```

## Запуск

Из корня репозитория, PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\school-import examples\submissions.jsonl --assignments examples\assignments.json
.\.venv\Scripts\school-import examples\invalid_submissions.jsonl --assignments examples\assignments.json
```

Тот же импорт модулем: `.\.venv\Scripts\python -m online_school examples\submissions.jsonl --assignments examples\assignments.json`.

Код возврата `0` — отчёт напечатан. Ошибки строк лежат в `errors`. Код `2` — не открылся файл или каталог.

Проверка без CLI:

```python
from online_school import Assignment, AssignmentCatalog, validate_submission

catalog = AssignmentCatalog((Assignment("py-intro-1", "Функции и тесты"),))
submission = validate_submission({...}, catalog)
```

Отказ — исключение `IntakeRejected`. У каждой причины есть `code`, `field` и `message`.

## Где что происходит

- Схема проверяется в `validate_submission`. Её вызывают и сервис, и импорт, и CLI.
- Аннотации описывают типы. Плохой JSON отклоняет функция проверки, не аннотация.
- Вызывающий код библиотеки видит `IntakeRejected`. Пользователь CLI видит JSON-отчёт, без трассировки по строкам данных.
- Файл сдачи открывает и закрывает CLI. Доменные функции получают уже прочитанные строки или словарь и не читают stdin.

## Ограничения этапа

Хранилище в памяти одного запуска. Повторный запуск CLI прежние сдачи не видит. Повтор того же идентификатора с другим `timestamp`, но тем же текстом и кодом, считается дубликатом и не обновляет время. Код из сдачи не исполняется.
