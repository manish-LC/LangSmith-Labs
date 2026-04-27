from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from .config import Settings
from .models import SupportAnswer
from .tracing_demo import (
    classify_question,
    draft_support_answer,
    grade_answer_helpfulness,
    retrieve_support_context,
)


class SupportGraphState(TypedDict, total=False):
    question: str
    expected_keywords: list[str]
    category: str
    context: list[tuple[str, str]]
    answer: str
    score: float
    missing_keywords: list[str]
    needs_escalation: bool
    escalation_note: str
    cited_docs: list[str]


def build_support_graph(settings: Settings, use_real_llm: bool = False):
    graph = StateGraph(SupportGraphState)

    @traceable(name="graph_classify_question", run_type="chain")
    def classify_node(state: SupportGraphState) -> SupportGraphState:
        return {"category": classify_question(state["question"])}

    @traceable(name="graph_retrieve_context", run_type="retriever")
    def retrieve_node(state: SupportGraphState) -> SupportGraphState:
        return {"context": retrieve_support_context(state["question"])}

    @traceable(name="graph_draft_answer", run_type="chain")
    def answer_node(state: SupportGraphState) -> SupportGraphState:
        answer = draft_support_answer(
            state["question"],
            state["context"],
            state["category"],
            settings,
            use_real_llm,
        )
        return {"answer": answer, "cited_docs": [topic for topic, _ in state["context"]]}

    @traceable(name="graph_evaluate_answer", run_type="chain")
    def evaluate_node(state: SupportGraphState) -> SupportGraphState:
        grade = grade_answer_helpfulness(state["answer"], state.get("expected_keywords", []))
        return {
            "score": float(grade["score"]),
            "missing_keywords": list(grade["missing_keywords"]),
        }

    @traceable(name="graph_escalate_low_confidence", run_type="chain")
    def escalate_node(state: SupportGraphState) -> SupportGraphState:
        return {
            "needs_escalation": True,
            "escalation_note": (
                "Escalate to the product specialist because the answer missed expected concepts: "
                + ", ".join(state.get("missing_keywords", []))
            ),
        }

    @traceable(name="graph_finalize_answer", run_type="chain")
    def finalize_node(state: SupportGraphState) -> SupportGraphState:
        return {"needs_escalation": False, "escalation_note": "Ready for customer response."}

    def route_after_evaluation(state: SupportGraphState) -> Literal["escalate", "finalize"]:
        if state.get("score", 0) < 0.6 or "urgent" in state["question"].lower():
            return "escalate"
        return "finalize"

    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", "evaluate")
    graph.add_conditional_edges("evaluate", route_after_evaluation)
    graph.add_edge("escalate", END)
    graph.add_edge("finalize", END)

    return graph.compile()


def run_graph_walkthrough(
    question: str,
    settings: Settings,
    expected_keywords: list[str] | None = None,
    use_real_llm: bool = False,
) -> SupportAnswer:
    app = build_support_graph(settings, use_real_llm=use_real_llm)
    result = app.invoke({"question": question, "expected_keywords": expected_keywords or []})
    return SupportAnswer(
        category=result["category"],
        answer=result["answer"],
        needs_escalation=result["needs_escalation"],
        cited_docs=result.get("cited_docs", []),
    )
