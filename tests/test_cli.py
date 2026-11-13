"""CLI вызывает тот же приём, что и прямой вызов сервиса."""

from __future__ import annotations

import json

import pytest

from online_school.cli import main
from tests.conftest import EXAMPLES


def test_cli_prints_accepted_duplicate_and_conflict(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            str(EXAMPLES / "submissions.jsonl"),
            "--assignments",
            str(EXAMPLES / "assignments.json"),
        ]
    )
    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert [item["submission_id"] for item in report["accepted"]] == ["sub-001", "sub-002"]
    assert [item["submission_id"] for item in report["duplicate"]] == ["sub-001"]
    assert report["errors"][0]["line"] == 4
    assert report["errors"][0]["code"] == "conflict"
    assert report["errors"][0]["field"] == "submission_id"
    assert report["errors"][0]["message"]


def test_cli_missing_file_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            str(EXAMPLES / "no-such.jsonl"),
            "--assignments",
            str(EXAMPLES / "assignments.json"),
        ]
    )
    assert exit_code == 2
    assert "Не удалось прочитать файл сдач" in capsys.readouterr().err


def test_cli_requires_assignments() -> None:
    with pytest.raises(SystemExit) as caught:
        main([str(EXAMPLES / "submissions.jsonl")])
    assert caught.value.code == 2
