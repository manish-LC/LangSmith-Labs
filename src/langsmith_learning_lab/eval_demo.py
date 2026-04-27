from __future__ import annotations

from typing import Any

from langsmith import Client
from langsmith import traceable

from .config import Settings
from .graph_demo import run_graph_walkthrough
from .knowledge import SAMPLE_QUESTIONS
from .models import EvaluationResult, SupportQuestion
from .tracing_demo import grade_answer_helpfulness


DATASET_NAME = "Support Engineer Learning Lab Questions"
EXPERIMENT_PREFIX = "support-engineer-learning-lab"


@traceable(name="run_support_eval_case", run_type="chain")
def run_eval_case(
    example: SupportQuestion,
    settings: Settings,
    use_real_llm: bool = False,
) -> EvaluationResult:
    result = run_graph_walkthrough(
        example.question,
        settings,
        expected_keywords=example.expected_keywords,
        use_real_llm=use_real_llm,
    )
    grade = grade_answer_helpfulness(result.answer, example.expected_keywords)
    score = float(grade["score"])
    return EvaluationResult(
        question=example.question,
        answer=result.answer,
        score=score,
        passed=score >= 0.75 and not result.needs_escalation,
        missing_keywords=list(grade["missing_keywords"]),
    )


@traceable(name="run_support_eval_suite", run_type="chain")
def run_eval_suite(settings: Settings, use_real_llm: bool = False) -> list[EvaluationResult]:
    return [run_eval_case(example, settings, use_real_llm=use_real_llm) for example in SAMPLE_QUESTIONS]


def ensure_eval_dataset(client: Client, dataset_name: str = DATASET_NAME) -> str:
    """Create the LangSmith dataset once and add missing examples by question."""
    if client.has_dataset(dataset_name=dataset_name):
        dataset = client.read_dataset(dataset_name=dataset_name)
    else:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=(
                "Small support-engineering dataset for learning LangSmith offline "
                "evaluations, target functions, and code evaluators."
            ),
            metadata={"app": "langsmith-learning-lab"},
        )

    existing_questions = {
        example.inputs.get("question")
        for example in client.list_examples(dataset_id=dataset.id)
        if example.inputs
    }
    for example in SAMPLE_QUESTIONS:
        if example.question in existing_questions:
            continue
        client.create_example(
            dataset_id=dataset.id,
            inputs={
                "question": example.question,
                "category_hint": example.category_hint,
            },
            outputs={
                "expected_keywords": example.expected_keywords,
                "expected_category": example.category_hint,
            },
            metadata={"lesson": example.category_hint or "general"},
        )
    return dataset_name


def make_target(settings: Settings, use_real_llm: bool = False):
    def target(inputs: dict[str, Any]) -> dict[str, Any]:
        result = run_graph_walkthrough(
            str(inputs["question"]),
            settings,
            expected_keywords=[],
            use_real_llm=use_real_llm,
        )
        return {
            "answer": result.answer,
            "category": result.category,
            "needs_escalation": result.needs_escalation,
            "cited_docs": result.cited_docs,
        }

    return target


def keyword_coverage_evaluator(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    reference_outputs: dict[str, Any],
) -> dict[str, Any]:
    expected_keywords = list(reference_outputs.get("expected_keywords", []))
    grade = grade_answer_helpfulness(str(outputs.get("answer", "")), expected_keywords)
    return {
        "key": "keyword_coverage",
        "score": grade["score"],
        "comment": _format_missing_keywords(list(grade["missing_keywords"])),
    }


def category_match_evaluator(
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    reference_outputs: dict[str, Any],
) -> dict[str, Any]:
    expected = reference_outputs.get("expected_category")
    actual = outputs.get("category")
    score = 1 if expected == actual else 0
    return {
        "key": "category_match",
        "score": score,
        "comment": f"expected={expected}, actual={actual}",
    }


def run_langsmith_experiment(settings: Settings, use_real_llm: bool = False):
    client = Client()
    dataset_name = ensure_eval_dataset(client)
    return client.evaluate(
        make_target(settings, use_real_llm=use_real_llm),
        data=dataset_name,
        evaluators=[keyword_coverage_evaluator, category_match_evaluator],
        experiment_prefix=EXPERIMENT_PREFIX,
        description=(
            "Hands-on LangSmith evaluation experiment. Inspect per-example inputs, "
            "reference outputs, target outputs, and evaluator feedback."
        ),
        metadata={"app": "langsmith-learning-lab", "mode": "sdk-evaluation"},
        max_concurrency=1,
    )


def _format_missing_keywords(missing_keywords: list[str]) -> str:
    if not missing_keywords:
        return "All expected keywords were present."
    return "Missing expected keywords: " + ", ".join(missing_keywords)
