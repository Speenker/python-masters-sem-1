from __future__ import annotations

from online_school import (
    compare_ast_code,
    compare_submissions,
    compare_token_code,
    jaccard,
    token_features,
)
from tests.conftest import valid_payload
from online_school.validation import validate_submission


def test_token_jaccard_is_maximal_for_identical_code() -> None:
    result = compare_token_code("def add(a, b):\n    return a + b\n", "def add(a, b):\n    return a + b\n")
    assert result.status == "ok"
    assert result.score == 1.0


def test_comments_are_excluded_and_empty_features_are_explicit() -> None:
    assert token_features("# comment\n").ngrams == frozenset()
    result = compare_token_code("", "")
    assert result.score is None
    assert result.status == "insufficient_data"


def test_invalid_code_has_explanation() -> None:
    result = compare_token_code("def broken(:", "x = 1")
    assert result.status == "invalid_code"
    assert result.score is None
    assert result.explanation


def test_ast_normalizes_variable_names() -> None:
    result = compare_ast_code("def add(x, y):\n    return x + y\n", "def sum(a, b):\n    return a + b\n")
    assert result.status == "ok"
    assert result.score == 1.0


def test_jaccard_is_symmetric() -> None:
    left = frozenset({("a", "b", "c")})
    right = frozenset({("b", "c", "d")})
    assert jaccard(left, right) == jaccard(right, left)


def test_compare_submissions_filters_assignment_and_students(catalog) -> None:
    first = validate_submission(valid_payload(), catalog)
    second = validate_submission(
        valid_payload(
            submission_id="sub-002",
            student_id="student-2",
            code="def sub(a, b):\n    return a - b\n",
        ),
        catalog,
    )
    same_student = validate_submission(
        valid_payload(
            submission_id="sub-003",
            student_id="student-1",
            code="def other(a, b):\n    return a * b\n",
        ),
        catalog,
    )
    pairs = list(compare_submissions((first, second, same_student), assignment_id="py-intro-1"))
    assert [(pair.left.submission_id, pair.right.submission_id) for pair in pairs] == [
        ("sub-001", "sub-002"),
        ("sub-002", "sub-003"),
    ]
