from __future__ import annotations

from pathlib import Path

import pytest

from online_school import InMemorySubmissionSource, JsonlSubmissionSource


def test_in_memory_source_has_stable_line_numbers() -> None:
    payload = {"submission_id": "one"}
    records = list(InMemorySubmissionSource((payload,)).records())
    assert records[0].line == 1
    assert records[0].payload == payload


def test_jsonl_source_continues_after_bad_json(tmp_path: Path) -> None:
    path = tmp_path / "submissions.jsonl"
    path.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")
    with JsonlSubmissionSource(path) as source:
        records = list(source.records())
    assert records[0].payload == {"ok": True}
    assert records[1].format_error is not None


def test_jsonl_source_closes_on_early_stop(tmp_path: Path) -> None:
    path = tmp_path / "submissions.jsonl"
    path.write_text('{"ok": true}\n{"ok": false}\n', encoding="utf-8")
    source = JsonlSubmissionSource(path)
    with pytest.raises(RuntimeError):
        next(source.records())
    with source:
        iterator = source.records()
        next(iterator)
    with pytest.raises(RuntimeError):
        next(source.records())

