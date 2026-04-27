from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_PROJECT = "support-engineer-learning-lab"


@dataclass(frozen=True)
class Settings:
    langsmith_tracing: bool
    langsmith_project: str
    has_langsmith_api_key: bool
    has_openai_api_key: bool
    openai_model: str


def load_settings() -> Settings:
    """Load local environment without exposing secret values."""
    load_dotenv()

    if os.getenv("LANGSMITH_PROJECT") is None:
        os.environ["LANGSMITH_PROJECT"] = DEFAULT_PROJECT

    if os.getenv("LANGSMITH_API_KEY") and os.getenv("LANGSMITH_TRACING") is None:
        os.environ["LANGSMITH_TRACING"] = "true"

    tracing = os.getenv("LANGSMITH_TRACING", "false").lower() in {"1", "true", "yes"}
    return Settings(
        langsmith_tracing=tracing,
        langsmith_project=os.getenv("LANGSMITH_PROJECT", DEFAULT_PROJECT),
        has_langsmith_api_key=bool(os.getenv("LANGSMITH_API_KEY")),
        has_openai_api_key=bool(os.getenv("OPENAI_API_KEY")),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
