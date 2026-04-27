from __future__ import annotations

from pydantic import BaseModel, Field


class SupportQuestion(BaseModel):
    question: str = Field(description="Customer or internal support question.")
    expected_keywords: list[str] = Field(default_factory=list)
    category_hint: str | None = None


class SupportAnswer(BaseModel):
    category: str
    answer: str
    needs_escalation: bool = False
    cited_docs: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    question: str
    answer: str
    score: float
    passed: bool
    missing_keywords: list[str]
