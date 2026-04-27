from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table


@dataclass(frozen=True)
class Lesson:
    slug: str
    title: str
    goal: str
    concept: str
    command: str
    langsmith_inspection: list[str]
    support_questions: list[str]
    code_map: list[tuple[str, str]]
    quiz: list[tuple[str, str]]


LESSONS: dict[str, Lesson] = {
    "tracing": Lesson(
        slug="tracing",
        title="Lesson 1: Tracing A Support Answer",
        goal="Learn how one customer question becomes a LangSmith trace tree.",
        concept=(
            "A trace is the execution story of an application request. The root run is the "
            "user-facing workflow, and child runs show the internal steps: retrieval, model "
            "or answer drafting, grading, tool calls, errors, latency, inputs, and outputs. "
            "Support engineers use this to answer: what happened, where did it happen, and "
            "which input caused it?"
        ),
        command='uv run langsmith-lab trace --question "How do I turn on tracing for my LangChain app?"',
        langsmith_inspection=[
            "Open the support-engineer-learning-lab project.",
            "Find the support_tracing_walkthrough root run.",
            "Expand child runs and locate retrieve_support_context, draft_support_answer, and grade_answer_helpfulness.",
            "Compare each child run input and output. Notice which data is passed between steps.",
            "Check whether latency belongs to retrieval, answer drafting, or grading.",
        ],
        support_questions=[
            "If a user says the answer is wrong, which child run would you inspect first?",
            "If the trace is slow, where would you look for the bottleneck?",
            "What metadata or project name would you ask the customer to confirm?",
        ],
        code_map=[
            ("Root traced workflow", "tracing_demo.py: run_tracing_walkthrough"),
            ("Retrieval child run", "tracing_demo.py: retrieve_support_context"),
            ("Answer child run", "tracing_demo.py: draft_support_answer"),
            ("Quality child run", "tracing_demo.py: grade_answer_helpfulness"),
        ],
        quiz=[
            (
                "What is the difference between a root run and a child run?",
                "The root run represents the whole request; child runs represent nested steps inside it.",
            ),
            (
                "Why should you never print API keys while debugging tracing?",
                "Traces and logs are shared debugging surfaces; secrets should only be referenced by env var name.",
            ),
        ],
    ),
    "graph": Lesson(
        slug="graph",
        title="Lesson 2: Reading A LangGraph Workflow",
        goal="Learn how state, nodes, edges, and conditional routing appear in code and traces.",
        concept=(
            "LangGraph is useful when a workflow needs explicit control flow. In this lab, "
            "the graph classifies a support question, retrieves context, drafts an answer, "
            "evaluates the answer, then routes to finalize or escalate. This mirrors real "
            "support debugging: you can explain not only the final answer, but the path taken."
        ),
        command='uv run langsmith-lab graph --mermaid',
        langsmith_inspection=[
            "Run the graph command once with --mermaid to see the static structure.",
            "Run it again without --mermaid to create a trace.",
            "In LangSmith, compare the graph node order with the trace child runs.",
            "Find the evaluate node output and confirm why it routed to finalize or escalate.",
            "Change the question to include urgent and observe the escalation path.",
        ],
        support_questions=[
            "Which node made the routing decision?",
            "What state fields existed before and after answer generation?",
            "How would you explain an unexpected escalation to a customer?",
        ],
        code_map=[
            ("Graph state schema", "graph_demo.py: SupportGraphState"),
            ("Graph construction", "graph_demo.py: build_support_graph"),
            ("Conditional edge", "graph_demo.py: route_after_evaluation"),
            ("Escalation node", "graph_demo.py: escalate_node"),
        ],
        quiz=[
            (
                "What does graph state do?",
                "It carries shared data between nodes, such as question, category, context, answer, and score.",
            ),
            (
                "Why are conditional edges helpful for support cases?",
                "They make routing decisions visible and explainable instead of hidden inside one large function.",
            ),
        ],
    ),
    "evaluation": Lesson(
        slug="evaluation",
        title="Lesson 3: Evaluating Answer Quality",
        goal="Learn the difference between a trace and an evaluation-style experiment.",
        concept=(
            "Tracing explains one run. Evaluation compares many runs against examples and scoring rules. "
            "In production support, this distinction matters: a trace helps debug a customer incident, "
            "while an evaluation helps decide whether a prompt, model, tool, or graph change improved quality. "
            "This lab's eval command creates a dataset-backed LangSmith experiment when LANGSMITH_API_KEY is set."
        ),
        command="uv run langsmith-lab eval",
        langsmith_inspection=[
            "Run the eval command and copy the experiment link if the SDK prints one.",
            "Open Datasets & Experiments and find Support Engineer Learning Lab Questions.",
            "Open the latest support-engineer-learning-lab experiment.",
            "Compare inputs, reference outputs, target outputs, keyword_coverage, and category_match.",
            "Use eval --local only when you want a terminal table without uploading an experiment.",
        ],
        support_questions=[
            "When would you ask for a trace instead of an evaluation result?",
            "What makes a scoring rule too brittle?",
            "How could a customer use datasets to reproduce regressions?",
        ],
        code_map=[
            ("Dataset examples", "knowledge.py: SAMPLE_QUESTIONS"),
            ("Single eval case", "eval_demo.py: run_eval_case"),
            ("Eval suite", "eval_demo.py: run_eval_suite"),
            ("Scoring logic", "tracing_demo.py: grade_answer_helpfulness"),
        ],
        quiz=[
            (
                "What question does tracing answer?",
                "What happened during this specific request?",
            ),
            (
                "What question does evaluation answer?",
                "Did the application perform well across a representative set of examples?",
            ),
        ],
    ),
    "support": Lesson(
        slug="support",
        title="Lesson 4: Support Engineer Debugging Playbook",
        goal="Practice turning customer symptoms into LangSmith investigation steps.",
        concept=(
            "A support engineer usually starts with a symptom, not a code path. Your job is to gather "
            "the project, run ID or trace URL, time window, expected behavior, actual behavior, and "
            "recent changes. Then use LangSmith to narrow the issue to configuration, retrieval, model "
            "behavior, tool execution, graph routing, or evaluation drift."
        ),
        command='uv run langsmith-lab graph --question "urgent: why did my agent give a vague answer?"',
        langsmith_inspection=[
            "Confirm the trace is in the expected project.",
            "Check root inputs and outputs before diving into child runs.",
            "Identify the first child run where expected and actual behavior diverge.",
            "Look for errors, high latency, missing context, bad routing, or weak scoring.",
            "Write a short customer-facing summary: symptom, evidence, likely cause, next step.",
        ],
        support_questions=[
            "What exact artifact would you ask the customer for?",
            "Which part is evidence from LangSmith and which part is your hypothesis?",
            "What next step can the customer safely try without exposing secrets?",
        ],
        code_map=[
            ("Env checks", "config.py: load_settings"),
            ("Trace walkthrough", "tracing_demo.py: run_tracing_walkthrough"),
            ("Graph routing", "graph_demo.py: route_after_evaluation"),
            ("CLI entrypoint", "cli.py: main"),
        ],
        quiz=[
            (
                "What should a good support answer separate?",
                "Observed evidence, likely cause, and recommended next step.",
            ),
            (
                "Why ask for project and run information?",
                "Because LangSmith investigations depend on finding the exact trace or experiment.",
            ),
        ],
    ),
}


def lesson_names() -> list[str]:
    return list(LESSONS)


def print_lesson(console: Console, lesson: Lesson, include_quiz: bool = True) -> None:
    console.print(Panel(lesson.goal, title=lesson.title))
    console.print(Markdown(f"### Core Idea\n{lesson.concept}"))
    console.print(Markdown(f"### Run This\n```bash\n{lesson.command}\n```"))

    inspection_table = Table(title="What To Inspect In LangSmith")
    inspection_table.add_column("#", justify="right")
    inspection_table.add_column("Step")
    for idx, step in enumerate(lesson.langsmith_inspection, start=1):
        inspection_table.add_row(str(idx), step)
    console.print(inspection_table)

    support_table = Table(title="Support Engineer Questions")
    support_table.add_column("#", justify="right")
    support_table.add_column("Question")
    for idx, question in enumerate(lesson.support_questions, start=1):
        support_table.add_row(str(idx), question)
    console.print(support_table)

    code_table = Table(title="Code To Read After The Run")
    code_table.add_column("Concept")
    code_table.add_column("Location")
    for concept, location in lesson.code_map:
        code_table.add_row(concept, location)
    console.print(code_table)

    if include_quiz:
        quiz_table = Table(title="Quick Self Check")
        quiz_table.add_column("Question")
        quiz_table.add_column("Expected Answer")
        for question, answer in lesson.quiz:
            quiz_table.add_row(question, answer)
        console.print(quiz_table)
