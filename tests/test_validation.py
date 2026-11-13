"""Прямая валидация, без CLI."""

from __future__ import annotations

import copy

import pytest

from online_school import IntakeRejected, validate_submission
from tests.conftest import valid_payload


def test_valid_submission_is_accepted(catalog) -> None:
    submission = validate_submission(valid_payload(), catalog)
    assert submission.submission_id == "sub-001"
    assert submission.student_id == "student-1"
    assert submission.content_hash


def test_timestamp_with_z_is_accepted(catalog) -> None:
    submission = validate_submission(
        valid_payload(timestamp="2026-09-01T07:15:00Z"),
        catalog,
    )
    assert submission.timestamp.endswith("Z")


def test_naive_timestamp_is_schema_violation(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(valid_payload(timestamp="2026-09-01T10:15:00"), catalog)
    error = caught.value.errors[0]
    assert error.code == "schema_violation"
    assert error.field == "timestamp"
    assert "временн" in error.message


def test_unparseable_timestamp_is_schema_violation(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(valid_payload(timestamp="вчера"), catalog)
    assert caught.value.errors[0].field == "timestamp"


def test_empty_student_id_is_schema_violation(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(valid_payload(student_id="   "), catalog)
    error = caught.value.errors[0]
    assert error.code == "schema_violation"
    assert error.field == "student_id"
    assert error.message


def test_unknown_field_is_schema_violation(catalog) -> None:
    payload = valid_payload()
    payload["grade"] = 5
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(payload, catalog)
    error = caught.value.errors[0]
    assert error.code == "schema_violation"
    assert error.field == "grade"
    assert "grade" in error.message


def test_several_schema_errors_are_reported_together(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(
            valid_payload(student_id="", timestamp="2026-09-01T10:15:00"),
            catalog,
        )
    fields = {error.field for error in caught.value.errors}
    assert fields == {"student_id", "timestamp"}


def test_unknown_assignment_is_schema_violation(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(valid_payload(assignment_id="missing"), catalog)
    assert caught.value.errors[0].field == "assignment_id"


def test_used_true_requires_description(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission(
            valid_payload(ai_declaration={"used": True, "description": " "}),
            catalog,
        )
    assert caught.value.errors[0].field == "ai_declaration.description"


def test_json_array_is_schema_violation_not_format_error(catalog) -> None:
    with pytest.raises(IntakeRejected) as caught:
        validate_submission([], catalog)  # type: ignore[arg-type]
    assert caught.value.errors[0].code == "schema_violation"
    assert caught.value.errors[0].field is None


def test_payload_is_not_modified_on_success_or_rejection(catalog) -> None:
    accepted = valid_payload()
    accepted_before = copy.deepcopy(accepted)
    validate_submission(accepted, catalog)
    assert accepted == accepted_before

    rejected = valid_payload(student_id="")
    rejected["grade"] = 5
    rejected_before = copy.deepcopy(rejected)
    with pytest.raises(IntakeRejected):
        validate_submission(rejected, catalog)
    assert rejected == rejected_before
