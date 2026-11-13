"""Каталог заданий. Доменный слой получает уже собранный каталог."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from online_school.errors import CatalogError


@dataclass(frozen=True, slots=True)
class Assignment:
    assignment_id: str
    title: str


class AssignmentCatalog:
    """Набор заданий, по которому проверяется ``assignment_id``."""

    def __init__(self, assignments: Iterable[Assignment]) -> None:
        by_id: dict[str, Assignment] = {}
        for assignment in assignments:
            if assignment.assignment_id in by_id:
                raise CatalogError(
                    f"В каталоге повторяется assignment_id «{assignment.assignment_id}»."
                )
            by_id[assignment.assignment_id] = assignment
        self._by_id = by_id

    def contains(self, assignment_id: str) -> bool:
        return assignment_id in self._by_id

    def get(self, assignment_id: str) -> Assignment | None:
        return self._by_id.get(assignment_id)

    def __len__(self) -> int:
        return len(self._by_id)


def load_assignments(path: Path) -> AssignmentCatalog:
    """Прочитать каталог из JSON-файла. Файл открывает этот адаптер, не валидатор."""

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CatalogError(f"Файл каталога недоступен: {exc.filename or path}") from exc
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Каталог не является корректным JSON: {exc.msg}.") from exc
    return catalog_from_payload(raw)


def catalog_from_payload(raw: object) -> AssignmentCatalog:
    """Собрать каталог из уже разобранного JSON."""

    if not isinstance(raw, Mapping):
        raise CatalogError("Корень каталога должен быть объектом.")
    unknown = [key for key in raw if key != "assignments"]
    if unknown:
        raise CatalogError(f"Неизвестное поле каталога «{unknown[0]}».")
    items = raw.get("assignments")
    if not isinstance(items, list):
        raise CatalogError("Поле assignments должно быть массивом.")
    assignments: list[Assignment] = []
    for index, item in enumerate(items, start=1):
        assignments.append(_assignment_from_item(item, index))
    return AssignmentCatalog(assignments)


def _assignment_from_item(item: object, index: int) -> Assignment:
    if not isinstance(item, Mapping):
        raise CatalogError(f"Задание №{index} должно быть объектом.")
    allowed = {"assignment_id", "title"}
    for key in item:
        if key not in allowed:
            raise CatalogError(f"Неизвестное поле задания №{index}: «{key}».")
    assignment_id = item.get("assignment_id")
    title = item.get("title")
    if not isinstance(assignment_id, str) or assignment_id.strip() == "":
        raise CatalogError(f"У задания №{index} пустой или нестроковый assignment_id.")
    if not isinstance(title, str) or title.strip() == "":
        raise CatalogError(f"У задания №{index} пустой или нестроковый title.")
    return Assignment(assignment_id, title)
