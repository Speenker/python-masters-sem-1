from online_school import timed


def test_timed_preserves_function_metadata_and_duration() -> None:
    @timed
    def add(left: int, right: int) -> int:
        """Add two numbers."""

        return left + right

    assert add(2, 3) == 5
    assert add.__name__ == "add"
    assert add.__doc__ == "Add two numbers."
    assert add.timing_function == "add"  # type: ignore[attr-defined]
    assert add.last_duration_seconds is not None  # type: ignore[attr-defined]
