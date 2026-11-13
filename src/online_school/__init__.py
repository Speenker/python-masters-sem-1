"""Приём сдач онлайн-школы."""

from online_school.catalog import Assignment, AssignmentCatalog, catalog_from_payload, load_assignments
from online_school.errors import IntakeRejected
from online_school.jsonl_import import import_jsonl
from online_school.models import AiDeclaration, Submission
from online_school.repository import InMemorySubmissionRepository
from online_school.service import AcceptOutcome, IntakeService
from online_school.validation import validate_submission

__version__ = "0.1.0"

__all__ = [
    "AcceptOutcome",
    "AiDeclaration",
    "Assignment",
    "AssignmentCatalog",
    "InMemorySubmissionRepository",
    "IntakeRejected",
    "IntakeService",
    "Submission",
    "catalog_from_payload",
    "import_jsonl",
    "load_assignments",
    "validate_submission",
]
