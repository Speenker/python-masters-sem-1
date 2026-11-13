"""Ошибки приёма, которые видит вызывающий код."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

ErrorCode = Literal["format_error", "schema_violation", "conflict"]

FORMAT_ERROR: ErrorCode = "format_error"
SCHEMA_VIOLATION: ErrorCode = "schema_violation"
CONFLICT: ErrorCode = "conflict"


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    """Одна объяснимая ошибка: код, поле и сообщение.

    ``field`` равен ``None``, когда ошибка относится ко всей строке,
    а не к одному полю. Примеры: повреждённый JSON и JSON-массив вместо объекта.
    """

    code: ErrorCode
    field: str | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code, "field": self.field, "message": self.message}


class IntakeRejected(Exception):
    """Сдача не принята. В ``errors`` одна или несколько причин."""

    def __init__(self, errors: Sequence[ErrorDetail]) -> None:
        details = tuple(errors)
        if not details:
            raise ValueError("IntakeRejected требует хотя бы одну ошибку")
        self.errors: tuple[ErrorDetail, ...] = details
        super().__init__(details[0].message)


class CatalogError(Exception):
    """Каталог заданий не удалось прочитать или он нарушает свою схему."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
