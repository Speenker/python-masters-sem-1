"""Сервис приёма: дубликат и конфликт."""

from __future__ import annotations

import pytest

from online_school import IntakeRejected
from tests.conftest import valid_payload


def test_duplicate_does_not_increase_count_and_returns_original(service, repository) -> None:
    first = service.accept(valid_payload())
    second = service.accept(valid_payload(timestamp="2026-09-02T10:15:00+03:00"))
    assert first.kind == "accepted"
    assert second.kind == "duplicate"
    assert second.submission is first.submission
    assert second.submission.timestamp == "2026-09-01T10:15:00+03:00"
    assert len(repository) == 1
    assert len(service) == 1


def test_same_content_without_empty_description_is_duplicate(service) -> None:
    service.accept(valid_payload())
    outcome = service.accept(
        valid_payload(ai_declaration={"used": False}),
    )
    assert outcome.kind == "duplicate"
    assert len(service) == 1


def test_conflict_does_not_overwrite_original(service, repository) -> None:
    original = service.accept(valid_payload())
    with pytest.raises(IntakeRejected) as caught:
        service.accept(valid_payload(code="def add(a, b):\n    return 0\n"))
    error = caught.value.errors[0]
    assert error.code == "conflict"
    assert error.field == "submission_id"
    stored = repository.get("sub-001")
    assert stored is original.submission
    assert stored is not None
    assert "return a + b" in stored.code
    assert len(repository) == 1


def test_changed_input_does_not_change_stored_submission(service) -> None:
    payload = valid_payload()
    outcome = service.accept(payload)
    payload["text"] = "изменено после приёма"
    payload["ai_declaration"]["description"] = "тоже изменено"  # type: ignore[index]
    assert outcome.submission.text == "Функция суммы."
    assert outcome.submission.ai_declaration.description == ""


def test_new_submission_id_is_a_new_record(service) -> None:
    service.accept(valid_payload())
    outcome = service.accept(valid_payload(submission_id="sub-002", student_id="student-2"))
    assert outcome.kind == "accepted"
    assert len(service) == 2
