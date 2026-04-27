from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import load_settings
from .eval_demo import DATASET_NAME, run_eval_suite, run_langsmith_experiment
from .graph_demo import build_support_graph, run_graph_walkthrough
from .lessons import LESSONS, lesson_names, print_lesson
from .tracing_demo import run_tracing_walkthrough


console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="langsmith-lab",
        description="Hands-on LangChain, LangGraph, and LangSmith learning lab.",
    )
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Use OpenAI if OPENAI_API_KEY is set. Default uses deterministic local answers.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="Check local LangSmith learning-lab configuration.")

    learn_parser = subparsers.add_parser("learn", help="Run a guided teaching lesson.")
    learn_parser.add_argument(
        "lesson",
        choices=["all", *lesson_names()],
        nargs="?",
        default="all",
        help="Lesson to print. Defaults to all lessons.",
    )
    learn_parser.add_argument(
        "--no-quiz",
        action="store_true",
        help="Hide self-check answers.",
    )
    learn_parser.add_argument(
        "--run-demo",
        action="store_true",
        help="Run the lesson's demo after printing the teaching guide.",
    )

    trace_parser = subparsers.add_parser("trace", help="Run a nested tracing walkthrough.")
    trace_parser.add_argument(
        "--question",
        default="How do I turn on tracing for my LangChain app?",
    )

    graph_parser = subparsers.add_parser("graph", help="Run a LangGraph support workflow.")
    graph_parser.add_argument(
        "--question",
        default="Why would a support engineer use LangGraph instead of a single chain?",
    )
    graph_parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Print the graph structure as Mermaid text.",
    )

    eval_parser = subparsers.add_parser("eval", help="Run a LangSmith evaluation experiment.")
    eval_parser.add_argument(
        "--local",
        action="store_true",
        help="Only print the local score table; do not create a LangSmith experiment.",
    )

    args = parser.parse_args()
    settings = load_settings()

    if args.command == "doctor":
        _print_doctor(settings)
    elif args.command == "learn":
        _print_lessons(args.lesson, include_quiz=not args.no_quiz)
        if args.run_demo:
            _run_lesson_demo(args.lesson, settings, use_real_llm=args.real_llm)
    elif args.command == "trace":
        _print_result(
            run_tracing_walkthrough(args.question, settings, use_real_llm=args.real_llm)
        )
    elif args.command == "graph":
        if args.mermaid:
            app = build_support_graph(settings, use_real_llm=args.real_llm)
            console.print(app.get_graph().draw_mermaid())
        _print_result(run_graph_walkthrough(args.question, settings, use_real_llm=args.real_llm))
    elif args.command == "eval":
        if args.local or not settings.has_langsmith_api_key:
            _print_eval_results(run_eval_suite(settings, use_real_llm=args.real_llm))
            if not settings.has_langsmith_api_key:
                console.print(
                    Panel(
                        "LANGSMITH_API_KEY is missing, so this stayed local. "
                        "Add it to .env to create a dataset-backed LangSmith experiment.",
                        title="Local Evaluation",
                    )
                )
        else:
            _print_experiment(run_langsmith_experiment(settings, use_real_llm=args.real_llm))


def _print_doctor(settings) -> None:
    table = Table(title="LangSmith Learning Lab Status")
    table.add_column("Check")
    table.add_column("Status")
    table.add_row("LANGSMITH_API_KEY", "set" if settings.has_langsmith_api_key else "missing")
    table.add_row("LANGSMITH_TRACING", "enabled" if settings.langsmith_tracing else "disabled")
    table.add_row("LANGSMITH_PROJECT", settings.langsmith_project)
    table.add_row("OPENAI_API_KEY", "set" if settings.has_openai_api_key else "missing")
    table.add_row("OPENAI_MODEL", settings.openai_model)
    console.print(table)
    console.print(
        Panel(
            "No secret values were printed. Add keys to .env locally, then rerun this command.",
            title="Security",
        )
    )


def _print_lessons(selected: str, include_quiz: bool) -> None:
    lessons = LESSONS.values() if selected == "all" else [LESSONS[selected]]
    for lesson in lessons:
        print_lesson(console, lesson, include_quiz=include_quiz)


def _run_lesson_demo(selected: str, settings, use_real_llm: bool) -> None:
    lessons = lesson_names() if selected == "all" else [selected]
    for lesson in lessons:
        console.rule(f"Demo: {lesson}")
        if lesson == "tracing":
            _print_result(
                run_tracing_walkthrough(
                    "How do I turn on tracing for my LangChain app?",
                    settings,
                    expected_keywords=["LANGSMITH_TRACING", "LANGSMITH_API_KEY", "project"],
                    use_real_llm=use_real_llm,
                )
            )
        elif lesson == "graph":
            console.print(build_support_graph(settings, use_real_llm=use_real_llm).get_graph().draw_mermaid())
            _print_result(
                run_graph_walkthrough(
                    "Why would a support engineer use LangGraph instead of a single chain?",
                    settings,
                    expected_keywords=["nodes", "edges", "state", "routing"],
                    use_real_llm=use_real_llm,
                )
            )
        elif lesson == "evaluation":
            if settings.has_langsmith_api_key:
                _print_experiment(run_langsmith_experiment(settings, use_real_llm=use_real_llm))
            else:
                _print_eval_results(run_eval_suite(settings, use_real_llm=use_real_llm))
        elif lesson == "support":
            _print_result(
                run_graph_walkthrough(
                    "urgent: why did my agent give a vague answer?",
                    settings,
                    expected_keywords=["evidence", "cause", "next step"],
                    use_real_llm=use_real_llm,
                )
            )


def _print_result(result) -> None:
    console.print(
        Panel(
            result.answer,
            title=f"{result.category} | escalation={result.needs_escalation}",
            subtitle=f"cited docs: {', '.join(result.cited_docs)}",
        )
    )


def _print_eval_results(results) -> None:
    table = Table(title="Support Evaluation Suite")
    table.add_column("Question")
    table.add_column("Score")
    table.add_column("Passed")
    table.add_column("Missing Keywords")

    for result in results:
        table.add_row(
            result.question,
            f"{result.score:.2f}",
            "yes" if result.passed else "no",
            ", ".join(result.missing_keywords) or "-",
        )
    console.print(table)


def _print_experiment(results) -> None:
    console.print(
        Panel(
            "Created a dataset-backed LangSmith experiment.\n\n"
            f"Dataset: {DATASET_NAME}\n"
            "Open LangSmith Datasets & Experiments to inspect inputs, reference outputs, "
            "target outputs, and evaluator feedback columns.",
            title="LangSmith Evaluation",
        )
    )
    console.print(results)


if __name__ == "__main__":
    main()
