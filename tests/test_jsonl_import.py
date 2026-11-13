"""Импорт JSONL и примеры из задания."""

from __future__ import annotations

import json

from online_school import import_jsonl, load_assignments
from tests.conftest import EXAMPLES, valid_payload


def test_broken_json_does_not_stop_the_rest(service) -> None:
    lines = [
        "{",
        "",
        json.dumps(valid_payload(submission_id="sub-2"), ensure_ascii=False),
    ]
    report = import_jsonl(lines, service)
    assert [item.submission_id for item in report.accepted] == ["sub-2"]
    assert report.errors[0].line == 1
    assert report.errors[0].code == "format_error"
    assert report.errors[0].field is None
    assert len(service) == 1


def test_blank_line_keeps_editor_line_numbers(service) -> None:
    lines = ["", json.dumps(valid_payload())]
    report = import_jsonl(lines, service)
    assert report.accepted[0].submission_id == "sub-001"
    assert report.errors == ()


def test_example_submissions_match_acceptance_counts(service) -> None:
    catalog_service_lines = (EXAMPLES / "submissions.jsonl").read_text(encoding="utf-8").splitlines()
    report = import_jsonl(catalog_service_lines, service)
    assert [item.submission_id for item in report.accepted] == ["sub-001", "sub-002"]
    assert [item.submission_id for item in report.duplicate] == ["sub-001"]
    assert [(issue.line, issue.code, issue.field) for issue in report.errors] == [
        (4, "conflict", "submission_id")
    ]
    assert len(service) == 2


def test_example_invalid_file_keeps_the_valid_line(catalog) -> None:
    from online_school import InMemorySubmissionRepository, IntakeService

    service = IntakeService(InMemorySubmissionRepository(), load_assignments(EXAMPLES / "assignments.json"))
    assert catalog.contains("py-intro-1")
    report = import_jsonl(
        (EXAMPLES / "invalid_submissions.jsonl").read_text(encoding="utf-8").splitlines(),
        service,
    )
    assert [item.submission_id for item in report.accepted] == ["sub-900"]
    assert [(issue.line, issue.code, issue.field) for issue in report.errors] == [
        (1, "format_error", None),
        (2, "schema_violation", "student_id"),
        (3, "schema_violation", "timestamp"),
        (4, "schema_violation", "grade"),
        (6, "schema_violation", "ai_declaration.description"),
    ]
