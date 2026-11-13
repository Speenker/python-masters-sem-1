"""Типизированный декоратор измерения времени вызова."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")


def timed(function: Callable[P, R]) -> Callable[P, R]:
    """Измерить последний вызов, сохранив имя, документацию и метаданные."""

    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        started = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            wrapper.last_duration_seconds = perf_counter() - started  # type: ignore[attr-defined]

    wrapped = cast(Callable[P, R], wrapper)
    wrapped.timing_function = function.__name__  # type: ignore[attr-defined]
    wrapped.last_duration_seconds = None  # type: ignore[attr-defined]
    return wrapped
