"""Потоковые признаки и сравнение сдач для лабораторной 2."""

from __future__ import annotations

import ast
import io
import tokenize
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from difflib import SequenceMatcher

from online_school.models import Submission


_IGNORED_TOKEN_TYPES = {
    tokenize.ENCODING,
    tokenize.COMMENT,
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENDMARKER,
}


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    start_line: int
    end_line: int
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class TokenFeatures:
    ngrams: frozenset[tuple[str, ...]]
    template_lines: tuple[int, ...]
    evidence: tuple[SourceEvidence, ...]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class SimilarityScore:
    method: str
    score: float | None
    status: str
    explanation: str
    evidence: tuple[SourceEvidence, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "score": self.score,
            "status": self.status,
            "explanation": self.explanation,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True, slots=True)
class SubmissionPair:
    left: Submission
    right: Submission
    token: SimilarityScore
    ast: SimilarityScore

    def to_dict(self) -> dict[str, object]:
        return {
            "left_submission_id": self.left.submission_id,
            "right_submission_id": self.right.submission_id,
            "left_student_id": self.left.student_id,
            "right_student_id": self.right.student_id,
            "assignment_id": self.left.assignment_id,
            "token": self.token.to_dict(),
            "ast": self.ast.to_dict(),
        }


def read_validate_features(
    lines: Iterable[str],
    validate: Callable[[object], Submission],
    *,
    template_lines: Iterable[str] = (),
) -> Iterator[TokenFeatures]:
    """Лениво разобрать строки JSONL через переданный валидатор и построить признаки.

    Валидатор получает разобранный JSON-объект и должен вернуть ``Submission``.
    """

    import json

    templates = frozenset(template_lines)
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        submission = validate(payload)
        yield token_features(submission.code, templates)


def token_features(code: str, template_lines: Iterable[str] = ()) -> TokenFeatures:
    """Построить token-признаки, не включая комментарии и служебные токены."""

    templates = frozenset(template_lines)
    lines = code.splitlines()
    matched_templates = tuple(
        index for index, line in enumerate(lines, start=1) if line in templates
    )
    try:
        tokens = [
            token
            for token in tokenize.generate_tokens(io.StringIO(code).readline)
            if token.type not in _IGNORED_TOKEN_TYPES
        ]
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        return TokenFeatures(
            frozenset(),
            matched_templates,
            _template_evidence(matched_templates),
            f"Некорректный Python-код: {exc.msg if hasattr(exc, 'msg') else exc}.",
        )
    values = tuple(token.string for token in tokens)
    ngrams = frozenset(
        tuple(values[index : index + 3]) for index in range(max(0, len(values) - 2))
    )
    return TokenFeatures(
        ngrams,
        matched_templates,
        _template_evidence(matched_templates),
    )


def jaccard(left: frozenset[tuple[str, ...]], right: frozenset[tuple[str, ...]]) -> float | None:
    """Вернуть Jaccard или ``None``, если объединение признаков пусто."""

    union = left | right
    if not union:
        return None
    return len(left & right) / len(union)


def compare_token_code(
    left_code: str,
    right_code: str,
    *,
    template_lines: Iterable[str] = (),
) -> SimilarityScore:
    left = token_features(left_code, template_lines)
    right = token_features(right_code, template_lines)
    evidence = left.evidence + right.evidence
    if left.error or right.error:
        errors = "; ".join(error for error in (left.error, right.error) if error)
        return SimilarityScore("token-jaccard", None, "invalid_code", errors, evidence)
    score = jaccard(left.ngrams, right.ngrams)
    if score is None:
        return SimilarityScore(
            "token-jaccard",
            None,
            "insufficient_data",
            "Недостаточно токеновых 3-грамм для сравнения.",
            evidence,
        )
    return SimilarityScore(
        "token-jaccard",
        score,
        "ok",
        "Сходство рассчитано как Jaccard токеновых 3-грамм.",
        evidence,
    )


def normalized_ast(code: str) -> tuple[str, ...]:
    """Сериализовать AST с последовательной нормализацией имён."""

    tree = ast.parse(code)
    names: dict[str, str] = {}

    class Normalizer(ast.NodeVisitor):
        def generic_visit(self, node: ast.AST) -> None:
            if isinstance(node, ast.Name):
                names.setdefault(node.id, f"name_{len(names)}")
            elif isinstance(node, ast.arg):
                names.setdefault(node.arg, f"name_{len(names)}")
            super().generic_visit(node)

    Normalizer().visit(tree)

    class Dump(ast.NodeVisitor):
        def __init__(self) -> None:
            self.items: list[str] = []

        def generic_visit(self, node: ast.AST) -> None:
            self.items.append(type(node).__name__)
            if isinstance(node, ast.Name):
                self.items.append(names[node.id])
            elif isinstance(node, ast.arg):
                self.items.append(names[node.arg])
            elif isinstance(node, ast.Constant):
                self.items.append(repr(node.value))
            super().generic_visit(node)

    dump = Dump()
    dump.visit(tree)
    return tuple(dump.items)


def compare_ast_code(left_code: str, right_code: str) -> SimilarityScore:
    try:
        left = normalized_ast(left_code)
        right = normalized_ast(right_code)
    except (SyntaxError, ValueError, TypeError) as exc:
        return SimilarityScore(
            "ast-normalized",
            None,
            "invalid_code",
            f"AST недоступен: {exc}.",
        )
    if not left or not right:
        return SimilarityScore(
            "ast-normalized",
            None,
            "insufficient_data",
            "Недостаточно AST-признаков для сравнения.",
        )
    score = SequenceMatcher(a=left, b=right, autojunk=False).ratio()
    return SimilarityScore(
        "ast-normalized",
        score,
        "ok",
        "AST сравнен после последовательной нормализации имён.",
    )


def compare_submissions(
    submissions: Iterable[Submission],
    *,
    assignment_id: str | None = None,
    template_lines: Iterable[str] = (),
) -> Iterator[SubmissionPair]:
    """Сравнить сдачи одного задания разных студентов лениво."""

    items = tuple(
        submission
        for submission in submissions
        if assignment_id is None or submission.assignment_id == assignment_id
    )
    for index, left in enumerate(items):
        for right in items[index + 1 :]:
            if left.submission_id == right.submission_id:
                continue
            if left.student_id == right.student_id:
                continue
            yield SubmissionPair(
                left,
                right,
                compare_token_code(left.code, right.code, template_lines=template_lines),
                compare_ast_code(left.code, right.code),
            )


def _template_evidence(lines: Iterable[int]) -> tuple[SourceEvidence, ...]:
    return tuple(
        SourceEvidence(line, line, "Строка совпадает с разрешённым шаблоном.")
        for line in lines
    )
