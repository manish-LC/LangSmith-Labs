from __future__ import annotations

from langsmith import traceable

from .config import Settings
from .knowledge import choose_snippets
from .models import SupportAnswer


def classify_question(question: str) -> str:
    normalized = question.lower()
    if "graph" in normalized or "langgraph" in normalized or "routing" in normalized:
        return "langgraph"
    if "eval" in normalized or "measure" in normalized or "score" in normalized:
        return "evaluation"
    if "prompt" in normalized:
        return "prompts"
    if "deploy" in normalized or "production" in normalized:
        return "deployment"
    return "tracing"


@traceable(name="retrieve_support_context", run_type="retriever")
def retrieve_support_context(question: str) -> list[tuple[str, str]]:
    return choose_snippets(question)


@traceable(name="draft_support_answer", run_type="chain")
def draft_support_answer(
    question: str,
    context: list[tuple[str, str]],
    category: str,
    settings: Settings,
    use_real_llm: bool,
) -> str:
    if use_real_llm and settings.has_openai_api_key:
        return _draft_with_openai(question, context, settings)

    context_text = " ".join(snippet for _, snippet in context)
    if category == "tracing":
        return (
            "Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY in your local environment, "
            "choose a LANGSMITH_PROJECT, then run the app. In LangSmith, open the project "
            f"to inspect nested runs, inputs, outputs, latency, and errors. Context: {context_text}"
        )
    if category == "langgraph":
        return (
            "Use LangGraph when you want explicit nodes, edges, state, and routing. "
            "For support work, this makes it easier to explain why a request went to retrieval, "
            f"answering, or escalation. Context: {context_text}"
        )
    if category == "evaluation":
        return (
            "Create a dataset of representative support questions, run the app over each example, "
            "and attach evaluators that produce a score. Compare experiments over time before "
            f"shipping changes. Context: {context_text}"
        )
    return f"Use the LangSmith docs and traces to debug this {category} workflow. Context: {context_text}"


def _draft_with_openai(question: str, context: list[tuple[str, str]], settings: Settings) -> str:
    from langchain_openai import ChatOpenAI

    context_text = "\n".join(f"- {topic}: {snippet}" for topic, snippet in context)
    model = ChatOpenAI(model=settings.openai_model, temperature=0)
    response = model.invoke(
        [
            (
                "system",
                "You are a LangChain support engineer. Answer concisely and cite the provided context.",
            ),
            ("human", f"Question: {question}\n\nContext:\n{context_text}"),
        ]
    )
    return str(response.content)


@traceable(name="grade_answer_helpfulness", run_type="chain")
def grade_answer_helpfulness(answer: str, expected_keywords: list[str]) -> dict[str, object]:
    normalized = answer.lower()
    missing = [keyword for keyword in expected_keywords if keyword.lower() not in normalized]
    score = 1.0 if not expected_keywords else (len(expected_keywords) - len(missing)) / len(expected_keywords)
    return {"score": round(score, 2), "missing_keywords": missing}


@traceable(name="support_tracing_walkthrough", run_type="chain")
def run_tracing_walkthrough(
    question: str,
    settings: Settings,
    expected_keywords: list[str] | None = None,
    use_real_llm: bool = False,
) -> SupportAnswer:
    expected_keywords = expected_keywords or []
    category = classify_question(question)
    context = retrieve_support_context(question)
    answer = draft_support_answer(question, context, category, settings, use_real_llm)
    grade = grade_answer_helpfulness(answer, expected_keywords)
    return SupportAnswer(
        category=category,
        answer=answer,
        needs_escalation=grade["score"] < 0.5,
        cited_docs=[topic for topic, _ in context],
    )
