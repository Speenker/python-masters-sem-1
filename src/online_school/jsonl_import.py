"""Импорт JSONL. Повреждённая строка попадает в отчёт и не останавливает файл."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

from online_school.errors import FORMAT_ERROR, ErrorCode, IntakeRejected
from online_school.models import Submission
from online_school.service import IntakeService


@dataclass(frozen=True, slots=True)
class ImportIssue:
    line: int
    code: ErrorCode
    field: str | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "line": self.line,
            "code": self.code,
            "field": self.field,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ImportReport:
    accepted: tuple[Submission, ...]
    duplicate: tuple[Submission, ...]
    errors: tuple[ImportIssue, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "accepted": [item.to_dict() for item in self.accepted],
            "duplicate": [item.to_dict() for item in self.duplicate],
            "errors": [item.to_dict() for item in self.errors],
        }


def import_jsonl(lines: Iterable[str], service: IntakeService) -> ImportReport:
    """Разобрать поток строк JSONL через тот же ``IntakeService``, что и прямой вызов.

    Пустые строки пропускаются. Нумерация строк начинается с 1 и считает
    пустые строки тоже, чтобы номер совпадал с номером в редакторе.
    """

    accepted: list[Submission] = []
    duplicate: list[Submission] = []
    errors: list[ImportIssue] = []
    for line_number, raw_line in enumerate(lines, start=1):
        if line_number == 1:
            raw_line = raw_line.lstrip("\ufeff")
        line = raw_line.strip()
        if line == "":
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(
                ImportIssue(
                    line_number,
                    FORMAT_ERROR,
                    None,
                    f"Строка не является корректным JSON: {exc.msg}.",
                )
            )
            continue
        try:
            outcome = service.accept(payload)
        except IntakeRejected as exc:
            errors.extend(
                ImportIssue(line_number, detail.code, detail.field, detail.message)
                for detail in exc.errors
            )
            continue
        if outcome.kind == "accepted":
            accepted.append(outcome.submission)
        else:
            duplicate.append(outcome.submission)
    return ImportReport(tuple(accepted), tuple(duplicate), tuple(errors))
