# LangSmith Learning Lab

A guided Python lab for learning LangChain, LangGraph, and LangSmith through support-engineering scenarios.

The app is intentionally small, but it now teaches in layers: each lesson explains the concept, runs a concrete workflow, tells you what to inspect in LangSmith, and gives you support-style questions to answer from the trace.

## What You Will Practice

- LangSmith observability: nested traces, inputs, outputs, latency, metadata, and failures.
- LangGraph workflows: state, nodes, edges, conditional routing, and escalation paths.
- Evaluation concepts: small datasets, expected keywords, scoring, pass/fail decisions, and experiment comparison.
- Secure local configuration: API keys live in `.env`, which is ignored by git.

Docs used while shaping this lab:

- [LangChain docs home](https://docs.langchain.com/)
- [LangSmith docs](https://docs.langchain.com/langsmith/home)
- [LangChain Python overview](https://docs.langchain.com/oss/python/langchain/overview)
- [LangGraph Python quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)

## Setup

Install dependencies with `uv`:

```bash
uv sync
```

Create a local env file:

```bash
cp .env.example .env
```

Fill in `.env` locally. Keep secret values out of commits, screenshots, and logs.

Required for LangSmith tracing:

```bash
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=support-engineer-learning-lab
LANGSMITH_ENDPOINT=https://beta.api.smith.langchain.com
```

Optional for real LLM calls:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
```

Without `OPENAI_API_KEY`, the lab still runs with deterministic local answers so you can learn trace structure before connecting a model provider.

## Commands

Start with the guided curriculum:

```bash
uv run langsmith-lab learn
```

Run one lesson at a time:

```bash
uv run langsmith-lab learn tracing
uv run langsmith-lab learn graph
uv run langsmith-lab learn evaluation
uv run langsmith-lab learn support
```

Print the lesson and run its demo immediately:

```bash
uv run langsmith-lab learn tracing --run-demo
```

Check configuration without printing secret values:

```bash
uv run langsmith-lab doctor
```

Run a nested tracing walkthrough:

```bash
uv run langsmith-lab trace --question "How do I turn on tracing for my LangChain app?"
```

Run the LangGraph support workflow:

```bash
uv run langsmith-lab graph --question "Why would a support engineer use LangGraph instead of a single chain?"
```

Print the graph as Mermaid:

```bash
uv run langsmith-lab graph --mermaid
```

Run the evaluation-style suite:

```bash
uv run langsmith-lab eval
```

With `LANGSMITH_API_KEY` configured, this creates a real LangSmith dataset-backed experiment named from `support-engineer-learning-lab`. In LangSmith, open Datasets & Experiments and look for the `Support Engineer Learning Lab Questions` dataset. You should see one row per example, reference outputs, target outputs, and evaluator feedback columns like `keyword_coverage` and `category_match`.

Run only the local terminal table:

```bash
uv run langsmith-lab eval --local
```

Use a real OpenAI model for answer drafting:

```bash
uv run langsmith-lab --real-llm trace --question "How can I debug a slow agent run?"
```

## Suggested Learning Path

1. Run `doctor` and confirm tracing is enabled.
2. Run `learn tracing --run-demo`; inspect the root run and child runs in LangSmith.
3. Run `learn graph --run-demo`; compare the Mermaid graph with the trace node order.
4. Run `learn evaluation --run-demo`; open the dataset-backed experiment and compare per-example scores, reference outputs, target outputs, and feedback.
5. Run `learn support --run-demo`; write a short support response from trace evidence.
6. Change a sample question in `src/langsmith_learning_lab/knowledge.py`, rerun `learn evaluation --run-demo`, and explain what changed.

## Lesson Goals

### Tracing

You should be able to explain the root run, child runs, inputs, outputs, latency, and why nested traces are useful when debugging a single customer issue.

### Graph

You should be able to explain graph state, nodes, edges, and conditional routing, then connect those concepts to the trace you see in LangSmith.

### Evaluation

You should be able to explain why a trace debugs one request, while an evaluation compares behavior across examples or experiments.

Important distinction:

- `trace`, `graph`, and `learn ... --run-demo` show application execution under the Runs/Traces views.
- `eval` creates a LangSmith dataset experiment, which is the better UI for comparing examples, outputs, references, and scores.
- `eval --local` is only a terminal learning aid and does not create the full experiment view.

### Support

You should be able to turn a customer symptom into an investigation: project, trace or run ID, time window, expected behavior, actual behavior, evidence, likely cause, and next step.

## Project Layout

```text
src/langsmith_learning_lab/
  cli.py           # uv script entrypoint
  config.py        # secure env loading and status checks
  eval_demo.py     # evaluation-style suite
  graph_demo.py    # LangGraph support workflow
  knowledge.py     # sample docs and examples
  lessons.py       # guided curriculum content
  tracing_demo.py  # traceable nested support workflow
```

## Support Engineer Exercises

- Find a trace where `needs_escalation=true` and explain why the graph routed there.
- Add a new `DOC_SNIPPETS` topic and verify it appears in cited docs.
- Add a new `SAMPLE_QUESTIONS` case with expected keywords, then compare the eval score before and after improving the answer logic.
- Temporarily raise the pass threshold in `eval_demo.py` and inspect which cases fail.
- Run with `--real-llm`, then compare deterministic and model-generated traces in LangSmith.
