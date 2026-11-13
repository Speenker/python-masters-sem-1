"""Сервис приёма: валидация, дубликат и конфликт идентификатора."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from online_school.catalog import AssignmentCatalog
from online_school.errors import CONFLICT, ErrorDetail, IntakeRejected
from online_school.models import Submission
from online_school.repository import SubmissionRepository
from online_school.validation import validate_submission

AcceptKind = Literal["accepted", "duplicate"]


@dataclass(frozen=True, slots=True)
class AcceptOutcome:
    """Результат успешного разбора. Отказ приходит исключением ``IntakeRejected``."""

    kind: AcceptKind
    submission: Submission


class IntakeService:
    """Принимает одну сдачу в переданный репозиторий.

    Сервис не читает stdin, не открывает файлы и не делает сетевых запросов.
    Каталог и хранилище передаются снаружи.
    """

    def __init__(self, repository: SubmissionRepository, catalog: AssignmentCatalog) -> None:
        self._repository = repository
        self._catalog = catalog

    def accept(self, payload: Mapping[str, Any]) -> AcceptOutcome:
        """Принять сдачу, вернуть уже лежащую при дубликате или отказать.

        Дубликат — тот же ``submission_id`` и тот же хеш содержимого.
        Конфликт — тот же идентификатор и другое содержимое. Исходная запись
        при конфликте остаётся на месте. Новая версия работы должна получить
        новый ``submission_id``.
        """

        submission = validate_submission(payload, self._catalog)
        existing = self._repository.get(submission.submission_id)
        if existing is None:
            self._repository.add(submission)
            return AcceptOutcome("accepted", submission)
        if existing.content_hash == submission.content_hash:
            return AcceptOutcome("duplicate", existing)
        raise IntakeRejected(
            (
                ErrorDetail(
                    CONFLICT,
                    "submission_id",
                    "Сдача с этим submission_id уже принята с другим содержимым.",
                ),
            )
        )

    def __len__(self) -> int:
        return len(self._repository)
