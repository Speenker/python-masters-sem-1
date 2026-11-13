"""Общие фикстуры приёма."""

from __future__ import annotations

from pathlib import Path

import pytest

from online_school import (
    Assignment,
    AssignmentCatalog,
    InMemorySubmissionRepository,
    IntakeService,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


@pytest.fixture
def catalog() -> AssignmentCatalog:
    return AssignmentCatalog((Assignment("py-intro-1", "Функции и тесты"),))


@pytest.fixture
def repository() -> InMemorySubmissionRepository:
    return InMemorySubmissionRepository()


@pytest.fixture
def service(
    repository: InMemorySubmissionRepository,
    catalog: AssignmentCatalog,
) -> IntakeService:
    return IntakeService(repository, catalog)


def valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "submission_id": "sub-001",
        "student_id": "student-1",
        "assignment_id": "py-intro-1",
        "timestamp": "2026-09-01T10:15:00+03:00",
        "text": "Функция суммы.",
        "code": "def add(a, b):\n    return a + b\n",
        "ai_declaration": {"used": False, "description": ""},
    }
    payload.update(overrides)
    return payload
