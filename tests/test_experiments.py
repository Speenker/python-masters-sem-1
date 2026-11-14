from __future__ import annotations

from online_school.experiments import evaluate, tune_threshold


def test_tuning_selects_threshold_without_using_evaluation_values() -> None:
    samples = [(0.1, False), (0.2, True), (0.8, True), (0.9, False)]
    threshold = tune_threshold(samples)
    assert 0.1 < threshold <= 0.8
    result = evaluate(samples, threshold)
    assert result.recall == 1.0
    assert result.uncertain_rate == 0.0


def test_evaluation_counts_unknown_scores_as_uncertain() -> None:
    result = evaluate([(None, True), (0.9, False)], 0.5)
    assert result.uncertain == 1
    assert result.uncertain_rate == 0.5
    assert result.false_positive == 1
