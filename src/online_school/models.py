"""Модель принятой сдачи и хеш её содержимого."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AiDeclaration:
    """Декларация об использовании ИИ.

    При ``used=True`` описание непустое: это проверяет валидация,
    а не аннотация типа.
    """

    used: bool
    description: str

    def to_dict(self) -> dict[str, object]:
        return {"used": self.used, "description": self.description}


@dataclass(frozen=True, slots=True)
class Submission:
    """Принятая сдача. Экземпляр не изменяется после создания.

    ``content_hash`` считается по содержимому работы, без ``submission_id``
    и без ``timestamp``. Повтор того же идентификатора с тем же хешем —
    дубликат, с другим хешем — конфликт.
    """

    submission_id: str
    student_id: str
    assignment_id: str
    timestamp: str
    text: str
    code: str
    ai_declaration: AiDeclaration
    content_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "submission_id": self.submission_id,
            "student_id": self.student_id,
            "assignment_id": self.assignment_id,
            "timestamp": self.timestamp,
            "text": self.text,
            "code": self.code,
            "ai_declaration": self.ai_declaration.to_dict(),
            "content_hash": self.content_hash,
        }


def content_hash(
    *,
    assignment_id: str,
    student_id: str,
    text: str,
    code: str,
    ai_declaration: AiDeclaration,
) -> str:
    """SHA-256 канонического JSON содержимого сдачи."""

    canonical = {
        "ai_declaration": {
            "description": ai_declaration.description,
            "used": ai_declaration.used,
        },
        "assignment_id": assignment_id,
        "code": code,
        "student_id": student_id,
        "text": text,
    }
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
