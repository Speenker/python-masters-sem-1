"""Приём сдач онлайн-школы."""

from online_school.catalog import Assignment, AssignmentCatalog, catalog_from_payload, load_assignments
from online_school.errors import IntakeRejected
from online_school.analysis import (
    AnalysisContext,
    AnalysisReport,
    AnalysisService,
    Analyzer,
    AnalyzerRegistry,
    DefaultAnalysisContext,
    Evidence,
    LengthAnalyzer,
    RubricFeedback,
    TemplateAnalyzer,
    default_analyzer_registry,
)
from online_school.jsonl_import import import_jsonl, import_source
from online_school.models import AiDeclaration, Submission
from online_school.repository import InMemorySubmissionRepository
from online_school.service import AcceptOutcome, IntakeService
from online_school.similarity import (
    SimilarityScore,
    SourceEvidence,
    SubmissionPair,
    compare_ast_code,
    compare_submissions,
    compare_token_features,
    compare_token_code,
    jaccard,
    normalized_ast,
    read_validate_features,
    token_features,
)
from online_school.sources import (
    InMemorySubmissionSource,
    JsonlSubmissionSource,
    SubmissionSource,
)
from online_school.timing import timed
from online_school.validation import validate_submission

__version__ = "0.1.0"

__all__ = [
    "AcceptOutcome",
    "AnalysisContext",
    "AnalysisReport",
    "AnalysisService",
    "AiDeclaration",
    "Assignment",
    "AssignmentCatalog",
    "Analyzer",
    "AnalyzerRegistry",
    "DefaultAnalysisContext",
    "Evidence",
    "InMemorySubmissionRepository",
    "InMemorySubmissionSource",
    "IntakeRejected",
    "IntakeService",
    "JsonlSubmissionSource",
    "LengthAnalyzer",
    "RubricFeedback",
    "Submission",
    "SubmissionPair",
    "SimilarityScore",
    "SourceEvidence",
    "SubmissionSource",
    "TemplateAnalyzer",
    "catalog_from_payload",
    "default_analyzer_registry",
    "import_jsonl",
    "import_source",
    "load_assignments",
    "compare_ast_code",
    "compare_submissions",
    "compare_token_features",
    "compare_token_code",
    "jaccard",
    "normalized_ast",
    "read_validate_features",
    "token_features",
    "timed",
    "validate_submission",
]
