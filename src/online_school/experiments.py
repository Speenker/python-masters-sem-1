"""Воспроизводимая оценка методов сходства лабораторной 2."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

from online_school.catalog import Assignment, AssignmentCatalog
from online_school.models import Submission
from online_school.similarity import (
    SimilarityScore,
    compare_ast_code,
    compare_token_code,
    token_features,
)
from online_school.validation import validate_submission


POSITIVE_RELATIONS = frozenset({"exact_copy", "renamed_variables"})


@dataclass(frozen=True, slots=True)
class PairLabel:
    left: str
    right: str
    relation: str
    template_only: bool
    split: str

    @property
    def positive(self) -> bool:
        return self.relation in POSITIVE_RELATIONS and not self.template_only


@dataclass(frozen=True, slots=True)
class ConfusionMetrics:
    threshold: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    uncertain: int
    precision: float
    recall: float
    f1: float
    uncertain_rate: float


def load_corpus(path: Path) -> dict[str, Submission]:
    """Лениво прочитать и валидировать JSONL, сохранив готовый индекс по ID."""

    catalog = AssignmentCatalog((Assignment("py-intro-1", "Функции и тесты"),))
    result: dict[str, Submission] = {}
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            if raw_line.strip():
                payload = json.loads(raw_line)
                submission = validate_submission(payload, catalog)
                result[submission.submission_id] = submission
    return result


def load_labels(path: Path) -> list[PairLabel]:
    with path.open(encoding="utf-8") as handle:
        return [
            PairLabel(
                left=item["left"],
                right=item["right"],
                relation=item["derivation_relation"],
                template_only=item["template_only"],
                split=item["split"],
            )
            for item in map(json.loads, handle)
            if item
        ]


def tune_threshold(scores: Iterable[tuple[float | None, bool]]) -> float:
    """Выбрать порог по tuning split, не используя evaluation split."""

    values = sorted({score for score, _ in scores if score is not None})
    if not values:
        return 1.0
    candidates = [0.0] + [
        (left + right) / 2 for left, right in zip(values, values[1:])
    ] + [values[-1]]
    best = (float("-1"), float("1"))
    for threshold in candidates:
        metrics = _metrics(threshold, scores)
        key = (metrics.f1, -threshold)
        if key > best:
            best = key
            selected = threshold
    return selected


def evaluate(
    scores: Iterable[tuple[float | None, bool]],
    threshold: float,
) -> ConfusionMetrics:
    return _metrics(threshold, scores)


def _metrics(
    threshold: float,
    scores: Iterable[tuple[float | None, bool]],
) -> ConfusionMetrics:
    tp = fp = tn = fn = uncertain = 0
    pairs = list(scores)
    for score, actual in pairs:
        if score is None:
            uncertain += 1
        elif score >= threshold and actual:
            tp += 1
        elif score >= threshold:
            fp += 1
        elif actual:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return ConfusionMetrics(
        threshold,
        tp,
        fp,
        tn,
        fn,
        uncertain,
        precision,
        recall,
        f1,
        uncertain / len(pairs) if pairs else 0.0,
    )


def method_scores(
    labels: Iterable[PairLabel],
    corpus: dict[str, Submission],
    method: str,
) -> list[tuple[PairLabel, SimilarityScore]]:
    result = []
    for label in labels:
        left = corpus[label.left]
        right = corpus[label.right]
        if method == "token":
            score = compare_token_code(left.code, right.code)
        elif method == "ast":
            score = compare_ast_code(left.code, right.code)
        else:
            raise ValueError(f"Unknown similarity method: {method}")
        result.append((label, score))
    return result


def profile_feature_extraction(
    sizes: Iterable[int] = (100, 1000, 5000),
    *,
    repeats: int = 3,
    seed: int = 20261114,
) -> dict[str, object]:
    """Измерить извлечение и хранение token-признаков на синтетической нагрузке."""

    results: dict[str, object] = {"seed": seed, "repeats": repeats, "sizes": {}}
    for size in sizes:
        samples: list[dict[str, float]] = []
        for repeat in range(repeats):
            codes = [
                f"def solve_{index}(a, b):\n    return a + b + {index % 7}\n"
                for index in range(size)
            ]
            tracemalloc.start()
            started = time.perf_counter()
            features = [token_features(code).ngrams for code in codes]
            wall_ms = (time.perf_counter() - started) * 1000
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            samples.append(
                {
                    "repeat": repeat + 1,
                    "wall_ms": wall_ms,
                    "peak_memory_kib": peak / 1024,
                    "feature_sets": float(len(features)),
                }
            )
        results["sizes"][str(size)] = {
            "runs": samples,
            "median_wall_ms": statistics.median(item["wall_ms"] for item in samples),
            "mean_wall_ms": statistics.fmean(item["wall_ms"] for item in samples),
            "median_peak_memory_kib": statistics.median(
                item["peak_memory_kib"] for item in samples
            ),
            "mean_peak_memory_kib": statistics.fmean(
                item["peak_memory_kib"] for item in samples
            ),
        }
    return results


def run_experiment(corpus_path: Path, labels_path: Path) -> dict[str, object]:
    corpus = load_corpus(corpus_path)
    labels = load_labels(labels_path)
    report: dict[str, object] = {
        "seed": 20261114,
        "corpus_size": len(corpus),
        "pair_count": len(labels),
        "positive_definition": sorted(POSITIVE_RELATIONS),
        "methods": {},
    }
    for method in ("token", "ast"):
        scored = method_scores(labels, corpus, method)
        tuning = [(score.score, label.positive) for label, score in scored if label.split == "tuning"]
        evaluation = [
            (score.score, label.positive) for label, score in scored if label.split == "evaluation"
        ]
        threshold = tune_threshold(tuning)
        report["methods"][method] = {
            "threshold": threshold,
            "review_required": "score is not null and score >= threshold",
            "tuning": asdict(evaluate(tuning, threshold)),
            "evaluation": asdict(evaluate(evaluation, threshold)),
            "errors": sorted(
                [
                {
                    "left": label.left,
                    "right": label.right,
                    "relation": label.relation,
                    "template_only": label.template_only,
                    "score": score.score,
                    "status": score.status,
                    "explanation": score.explanation,
                }
                for label, score in scored
                if label.split == "evaluation"
                and (
                    (score.score is not None and (score.score >= threshold) != label.positive)
                    or score.score is None
                )
                ],
                key=lambda item: (not item["template_only"], item["left"], item["right"]),
            )[:3],
        }
    report["profiling"] = profile_feature_extraction()
    report["notes"] = [
        "review_required означает сигнал для ручного разбора, а не доказательство нарушения.",
        "template_variant исключён из positive: разрешённый шаблон не должен превращаться в обвинение.",
        "Профилирование измеряет извлечение и хранение token-признаков, не качество на реальных работах.",
    ]
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Запустить эксперимент лабораторной 2.")
    parser.add_argument("--corpus", type=Path, default=Path("examples/similarity_corpus.jsonl"))
    parser.add_argument("--labels", type=Path, default=Path("examples/similarity_pair_labels.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/lab-2-experiment.json"))
    args = parser.parse_args(argv)
    report = run_experiment(args.corpus, args.labels)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
