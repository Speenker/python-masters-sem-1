"""Источники сдач с единым контрактом и управлением ресурсом."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, TextIO


@dataclass(frozen=True, slots=True)
class SourceRecord:
    line: int
    payload: object | None
    format_error: str | None = None


class SubmissionSource(Protocol):
    def records(self) -> Iterable[SourceRecord]:
        """Отдать записи с номерами строк и ошибками формата."""


class InMemorySubmissionSource:
    def __init__(self, payloads: Iterable[Mapping[str, object]]) -> None:
        self._payloads = tuple(payloads)

    def records(self) -> Iterator[SourceRecord]:
        for line, payload in enumerate(self._payloads, start=1):
            yield SourceRecord(line, payload)


class JsonlSubmissionSource:
    """JSONL-источник. Файл закрывается и при ошибке, и при раннем выходе."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._handle: TextIO | None = None

    def __enter__(self) -> JsonlSubmissionSource:
        self._handle = self._path.open(encoding="utf-8")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def records(self) -> Iterator[SourceRecord]:
        if self._handle is None:
            raise RuntimeError("JSONL-источник нужно использовать внутри with.")
        for line_number, raw_line in enumerate(self._handle, start=1):
            if line_number == 1:
                raw_line = raw_line.lstrip("\ufeff")
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                yield SourceRecord(
                    line_number,
                    None,
                    f"Строка не является корректным JSON: {exc.msg}.",
                )
                continue
            yield SourceRecord(line_number, payload)
