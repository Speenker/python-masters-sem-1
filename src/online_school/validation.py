"""Проверка схемы сдачи.

Валидация выполняется здесь, в обычном коде. Аннотации типов только
подсказывают читателю и проверщику типов; они не отклоняют плохой JSON.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from online_school.catalog import AssignmentCatalog
from online_school.errors import SCHEMA_VIOLATION, ErrorDetail, IntakeRejected
from online_school.models import AiDeclaration, Submission, content_hash

_REQUIRED_FIELDS = (
    "submission_id",
    "student_id",
    "assignment_id",
    "timestamp",
    "text",
    "code",
    "ai_declaration",
)
_ALLOWED_FIELDS = frozenset(_REQUIRED_FIELDS)
_STRING_FIELDS = (
    "submission_id",
    "student_id",
    "assignment_id",
    "timestamp",
    "text",
    "code",
)
_NONEMPTY_FIELDS = ("submission_id", "student_id", "assignment_id")
_MISSING = object()


def validate_submission(payload: Mapping[str, Any], catalog: AssignmentCatalog) -> Submission:
    """Проверить одну сдачу и вернуть неизменяемую модель.

    Функция ничего не записывает во входной объект и не открывает файлы.
    При любой ошибке схемы выбрасывает ``IntakeRejected`` и не возвращает
    частично принятую модель.
    """

    if not isinstance(payload, Mapping):
        raise IntakeRejected(
            (
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    None,
                    "Сдача должна быть JSON-объектом.",
                ),
            )
        )

    errors: list[ErrorDetail] = []
    for key in payload:
        if key not in _ALLOWED_FIELDS:
            errors.append(
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    str(key),
                    f"Неизвестное поле «{key}».",
                )
            )

    present: dict[str, Any] = {}
    for field in _REQUIRED_FIELDS:
        if field not in payload:
            errors.append(
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    field,
                    f"Отсутствует обязательное поле «{field}».",
                )
            )
        else:
            present[field] = payload[field]

    strings: dict[str, str] = {}
    for field in _STRING_FIELDS:
        if field not in present:
            continue
        raw = present[field]
        if not isinstance(raw, str):
            errors.append(
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    field,
                    f"Поле «{field}» должно быть строкой.",
                )
            )
            continue
        strings[field] = raw

    for field in _NONEMPTY_FIELDS:
        value = strings.get(field)
        if value is not None and value.strip() == "":
            errors.append(
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    field,
                    f"Поле «{field}» не может быть пустым.",
                )
            )

    if "timestamp" in strings:
        timestamp_error = _timestamp_error(strings["timestamp"])
        if timestamp_error is not None:
            errors.append(timestamp_error)

    declaration: AiDeclaration | None = None
    if "ai_declaration" in present:
        declaration, declaration_errors = _parse_declaration(present["ai_declaration"])
        errors.extend(declaration_errors)

    assignment_id = strings.get("assignment_id")
    if assignment_id is not None and assignment_id.strip() and not catalog.contains(assignment_id):
        errors.append(
            ErrorDetail(
                SCHEMA_VIOLATION,
                "assignment_id",
                "Задание с таким assignment_id не найдено в каталоге.",
            )
        )

    if errors:
        raise IntakeRejected(errors)
    if declaration is None or any(field not in strings for field in _STRING_FIELDS):
        raise IntakeRejected(
            (
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    None,
                    "Сдача не прошла проверку.",
                ),
            )
        )

    return Submission(
        submission_id=strings["submission_id"],
        student_id=strings["student_id"],
        assignment_id=strings["assignment_id"],
        timestamp=strings["timestamp"],
        text=strings["text"],
        code=strings["code"],
        ai_declaration=declaration,
        content_hash=content_hash(
            assignment_id=strings["assignment_id"],
            student_id=strings["student_id"],
            text=strings["text"],
            code=strings["code"],
            ai_declaration=declaration,
        ),
    )


def _timestamp_error(value: str) -> ErrorDetail | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return ErrorDetail(
            SCHEMA_VIOLATION,
            "timestamp",
            "timestamp не является датой и временем ISO 8601.",
        )
    offset = parsed.tzinfo.utcoffset(parsed) if parsed.tzinfo is not None else None
    if offset is None:
        return ErrorDetail(
            SCHEMA_VIOLATION,
            "timestamp",
            "У timestamp должна быть временная зона, например +03:00 или Z.",
        )
    return None


def _parse_declaration(raw: object) -> tuple[AiDeclaration | None, list[ErrorDetail]]:
    if not isinstance(raw, Mapping):
        return None, [
            ErrorDetail(
                SCHEMA_VIOLATION,
                "ai_declaration",
                "ai_declaration должен быть объектом.",
            )
        ]

    errors: list[ErrorDetail] = []
    for key in raw:
        if key not in {"used", "description"}:
            errors.append(
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    f"ai_declaration.{key}",
                    f"Неизвестное поле «ai_declaration.{key}».",
                )
            )

    used = raw.get("used", _MISSING)
    description = raw.get("description", _MISSING)
    used_value: bool | None
    if used is _MISSING:
        errors.append(
            ErrorDetail(
                SCHEMA_VIOLATION,
                "ai_declaration.used",
                "В ai_declaration отсутствует поле used.",
            )
        )
        used_value = None
    elif not isinstance(used, bool):
        errors.append(
            ErrorDetail(
                SCHEMA_VIOLATION,
                "ai_declaration.used",
                "Поле ai_declaration.used должно быть логическим значением.",
            )
        )
        used_value = None
    else:
        used_value = used

    description_value = ""
    if description is _MISSING:
        if used_value is True:
            errors.append(
                ErrorDetail(
                    SCHEMA_VIOLATION,
                    "ai_declaration.description",
                    "При used=true нужно непустое описание в ai_declaration.description.",
                )
            )
    elif not isinstance(description, str):
        errors.append(
            ErrorDetail(
                SCHEMA_VIOLATION,
                "ai_declaration.description",
                "Поле ai_declaration.description должно быть строкой.",
            )
        )
    elif used_value is True and description.strip() == "":
        errors.append(
            ErrorDetail(
                SCHEMA_VIOLATION,
                "ai_declaration.description",
                "При used=true описание в ai_declaration.description не может быть пустым.",
            )
        )
    else:
        description_value = description

    if errors or used_value is None:
        return None, errors
    return AiDeclaration(used_value, description_value), []
