# Отчёт: лабораторная 1, этап А

Точка сдачи ещё не создана: нет коммита и тега `lab-1-stage-a`. Этот файл описывает то, что уже можно проверить.

- Траектория: Python Core.
- Уровень: основной. Углубление этапа Б (entry points, декоратор времени) не входило в этап А.
- Сделано: устанавливаемый пакет, модель `Submission`, разбор JSONL, валидация, in-memory репозиторий, CLI `school-import`, примеры `assignments.json`, `submissions.jsonl`, `invalid_submissions.jsonl`.

## Требования этапа А

- Корректная запись принимается.
- Неверный `timestamp`, пустой `student_id` и неизвестное поле дают `schema_violation` с полем и сообщением.
- Повреждённый JSON даёт `format_error` и не останавливает файл.
- Дубликат не увеличивает число сдач и возвращает первую запись.
- Конфликт не перезаписывает исходную запись.
- Входной словарь не изменяется.
- Проверка вызывается напрямую и из CLI.
- Доменный слой не читает stdin и не ходит в сеть.

## Команды

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\school-import examples\submissions.jsonl --assignments examples\assignments.json
.\.venv\Scripts\school-import examples\invalid_submissions.jsonl --assignments examples\assignments.json
```

Отдельная проверка установки: новое виртуальное окружение и `pip install .` без режима editable, затем тот же `school-import`.

## Измерения

На этапе А замеры времени и памяти не требуются. Их нет.

## Ограничения

- Контракт собран по PDF: отдельной памятки `Submission` / `AnalysisReport` в папке задания не было.
- Хеш не включает `submission_id` и `timestamp`.
- Репозиторий живёт только до конца процесса.
- Анализаторы, `Protocol`, реестр и контекстный менеджер источника — этап Б, тег `lab-1`.
