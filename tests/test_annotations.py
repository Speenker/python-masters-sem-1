"""Публичные функции объявлены с аннотациями."""

from __future__ import annotations

import inspect

from online_school import import_jsonl, load_assignments, validate_submission
from online_school.cli import main
from online_school.models import content_hash
from online_school.service import IntakeService


def test_public_functions_have_annotations() -> None:
    functions = [
        validate_submission,
        import_jsonl,
        load_assignments,
        content_hash,
        IntakeService.accept,
        main,
    ]
    for function in functions:
        signature = inspect.signature(function)
        assert signature.return_annotation is not inspect.Signature.empty
        for name, parameter in signature.parameters.items():
            if name == "self":
                continue
            assert parameter.annotation is not inspect.Signature.empty, function.__name__
