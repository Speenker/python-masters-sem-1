"""Командный импорт JSONL. Файл открывается здесь и закрывается по выходе из with."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from online_school.catalog import load_assignments
from online_school.errors import CatalogError
from online_school.jsonl_import import import_jsonl
from online_school.repository import InMemorySubmissionRepository
from online_school.service import IntakeService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="school-import",
        description="Импортировать сдачи из JSONL и напечатать JSON-отчёт.",
    )
    parser.add_argument("file", type=Path, help="Файл JSONL, одна сдача на строку")
    parser.add_argument(
        "--assignments",
        required=True,
        type=Path,
        help="JSON-каталог заданий",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Прочитать файл, вызвать общий сервис приёма и напечатать отчёт.

    Код возврата 0 означает, что отчёт построен. Ошибки отдельных строк
    лежат в поле ``errors``, а не в коде возврата. Код 2 — ошибка запуска:
    нет файла или сломан каталог.
    """

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        catalog = load_assignments(args.assignments)
    except CatalogError as exc:
        print(f"Не удалось прочитать каталог заданий: {exc.message}", file=sys.stderr)
        return 2
    service = IntakeService(InMemorySubmissionRepository(), catalog)
    try:
        with args.file.open(encoding="utf-8") as handle:
            report = import_jsonl(handle, service)
    except OSError as exc:
        name = exc.filename or args.file
        print(f"Не удалось прочитать файл сдач: {name}", file=sys.stderr)
        return 2
    json.dump(report.to_dict(), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0
