from __future__ import annotations

from .models import SupportQuestion


DOC_SNIPPETS: dict[str, str] = {
    "tracing": (
        "LangSmith traces show each application step, including inputs, outputs, "
        "latency, metadata, nested child runs, and errors."
    ),
    "langgraph": (
        "LangGraph represents agent workflows as nodes, edges, state, and conditional "
        "routing. LangSmith can visualize graph execution paths through traces."
    ),
    "evaluation": (
        "LangSmith evaluations compare application outputs against datasets and "
        "custom evaluators so teams can track quality over time."
    ),
    "prompts": (
        "LangSmith prompt engineering workflows help teams version prompts, run "
        "experiments, and inspect prompt behavior alongside traces."
    ),
    "deployment": (
        "LangSmith and LangGraph deployment workflows help move agents from local "
        "experiments to monitored production services."
    ),
}


SAMPLE_QUESTIONS: list[SupportQuestion] = [
    SupportQuestion(
        question="How do I turn on tracing for my LangChain app?",
        expected_keywords=["LANGSMITH_TRACING", "LANGSMITH_API_KEY", "project"],
        category_hint="tracing",
    ),
    SupportQuestion(
        question="Why would a support engineer use LangGraph instead of a single chain?",
        expected_keywords=["nodes", "edges", "state", "routing"],
        category_hint="langgraph",
    ),
    SupportQuestion(
        question="How can I measure whether my agent answers are getting better?",
        expected_keywords=["dataset", "evaluator", "score", "experiment"],
        category_hint="evaluation",
    ),
]


def choose_snippets(question: str, limit: int = 2) -> list[tuple[str, str]]:
    normalized = question.lower()
    matches = [
        (topic, snippet)
        for topic, snippet in DOC_SNIPPETS.items()
        if topic in normalized or any(word in normalized for word in topic.split())
    ]
    if not matches:
        matches = [("tracing", DOC_SNIPPETS["tracing"]), ("langgraph", DOC_SNIPPETS["langgraph"])]
    return matches[:limit]
