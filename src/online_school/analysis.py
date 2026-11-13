"""Контракты, анализаторы и явный реестр анализаторов."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Protocol

from online_school.catalog import Assignment
from online_school.models import Submission


@dataclass(frozen=True, slots=True)
class Evidence:
    """Фрагмент исходной сдачи, на который ссылается анализатор."""

    start_line: int
    end_line: int
    message: str
    source: str = "submission"

    def to_dict(self) -> dict[str, object]:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "message": self.message,
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class RubricFeedback:
    score: float | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {"score": self.score, "message": self.message}


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    analyzer_id: str
    analyzer_version: str
    rubric_feedback: RubricFeedback
    similarity: float | None = None
    evidence: tuple[Evidence, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "rubric_feedback": self.rubric_feedback.to_dict(),
            "similarity": self.similarity,
            "evidence": [item.to_dict() for item in self.evidence],
        }


class AnalysisContext(Protocol):
    """Данные, доступные анализатору без привязки к конкретному хранилищу."""

    assignment: Assignment

    def submissions(self) -> Iterable[Submission]:
        """Вернуть доступные сдачи, если конкретному анализатору они нужны."""


@dataclass(frozen=True, slots=True)
class DefaultAnalysisContext:
    assignment: Assignment
    _items: tuple[Submission, ...] = ()

    def submissions(self) -> Iterable[Submission]:
        return self._items


class Analyzer(Protocol):
    analyzer_id: str
    analyzer_version: str

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        """Построить отчёт по принятой сдаче."""


class LengthAnalyzer:
    analyzer_id = "length"
    analyzer_version = "1.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        text_lines = sum(bool(line.strip()) for line in submission.text.splitlines())
        code_lines = sum(bool(line.strip()) for line in submission.code.splitlines())
        message = (
            f"Непустых строк: text={text_lines}, code={code_lines}. "
            "Анализ длины не выставляет оценку."
        )
        return AnalysisReport(
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            rubric_feedback=RubricFeedback(None, message),
        )


class TemplateAnalyzer:
    analyzer_id = "template"
    analyzer_version = "1.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        templates = set(context.assignment.allowed_templates)
        evidence_items: list[Evidence] = []
        nonempty_count = 0
        for source, content in (("text", submission.text), ("code", submission.code)):
            lines = content.splitlines()
            nonempty_count += sum(bool(line.strip()) for line in lines)
            evidence_items.extend(
                Evidence(
                    index,
                    index,
                    "Точная строка совпадает с разрешённым шаблоном.",
                    source,
                )
                for index, line in enumerate(lines, start=1)
                if line in templates
            )
        evidence = tuple(evidence_items)
        similarity = len(evidence) / nonempty_count if nonempty_count else 0.0
        message = (
            "Совпадения с разрешёнными шаблонами не считаются подозрительным "
            f"сходством: найдено строк={len(evidence)}."
        )
        return AnalysisReport(
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            rubric_feedback=RubricFeedback(None, message),
            similarity=similarity,
            evidence=evidence,
        )


AnalyzerFactory = Callable[[], Analyzer]


class AnalyzerRegistry:
    """Явный реестр фабрик; сервис не знает конкретные классы анализаторов."""

    def __init__(self, factories: dict[str, AnalyzerFactory] | None = None) -> None:
        self._factories = dict(factories or {})

    def register(self, analyzer_id: str, factory: AnalyzerFactory) -> None:
        if not analyzer_id.strip():
            raise ValueError("Идентификатор анализатора не может быть пустым.")
        if analyzer_id in self._factories:
            raise ValueError(f"Анализатор «{analyzer_id}» уже зарегистрирован.")
        self._factories[analyzer_id] = factory

    def create(self, analyzer_id: str) -> Analyzer:
        try:
            return self._factories[analyzer_id]()
        except KeyError as exc:
            raise LookupError(f"Анализатор «{analyzer_id}» не зарегистрирован.") from exc

    def load_entry_points(self, group: str = "online_school.analyzers") -> None:
        """Подключить внешние фабрики из entry points без изменения сервиса."""

        discovered = entry_points().select(group=group)
        for item in discovered:
            factory = item.load()
            self.register(item.name, factory)


def default_analyzer_registry() -> AnalyzerRegistry:
    registry = AnalyzerRegistry()
    registry.register(LengthAnalyzer.analyzer_id, LengthAnalyzer)
    registry.register(TemplateAnalyzer.analyzer_id, TemplateAnalyzer)
    return registry


class AnalysisService:
    """Выбирает анализатор только через реестр и запускает его."""

    def __init__(self, registry: AnalyzerRegistry) -> None:
        self._registry = registry

    def analyze(
        self,
        submission: Submission,
        analyzer_id: str,
        context: AnalysisContext,
    ) -> AnalysisReport:
        return self._registry.create(analyzer_id).analyze(submission, context)
