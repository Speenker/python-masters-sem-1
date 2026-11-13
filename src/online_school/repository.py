"""Хранение принятых сдач. На этом этапе репозиторий только в памяти."""

from __future__ import annotations

from typing import Protocol

from online_school.models import Submission


class SubmissionRepository(Protocol):
    def get(self, submission_id: str) -> Submission | None:
        """Вернуть принятую сдачу или ``None``, если идентификатор ещё не встречался."""

    def add(self, submission: Submission) -> None:
        """Сохранить новую сдачу. Повторный идентификатор — ошибка вызывающего кода."""

    def __len__(self) -> int:
        """Число хранимых сдач."""


class InMemorySubmissionRepository:
    """Словарь в памяти процесса. После завершения CLI данные исчезают."""

    def __init__(self) -> None:
        self._items: dict[str, Submission] = {}

    def get(self, submission_id: str) -> Submission | None:
        return self._items.get(submission_id)

    def add(self, submission: Submission) -> None:
        if submission.submission_id in self._items:
            raise ValueError(
                f"submission_id «{submission.submission_id}» уже есть в репозитории"
            )
        self._items[submission.submission_id] = submission

    def __len__(self) -> int:
        return len(self._items)
