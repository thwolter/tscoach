# TSCoach

TSCoach is a LangGraph-based training agent for telephone counselling practice. It simulates a caller, evaluates each learner response, and provides coaching feedback during and/or after the session.

## What It Does

- Runs a structured training loop with onboarding, simulation, evaluation, and feedback.
- Generates realistic caller behavior based on scenario difficulty.
- Tracks per-turn quality (empathy, question quality, advice tendency).
- Produces per-turn feedback, final feedback, or both.

## Flow Overview

The graph is defined in `src/agent/graph.py`.

1. `onboarding`: extracts scenario setup (category + difficulty required).
2. `scenario_setup`: generates scenario description and initial caller profile.
3. `caller_simulation`: produces the next caller utterance.
4. `behaviour_analysis`: evaluates the latest learner reply.
5. `update_caller_profile`: updates caller state with bounded drift.
6. `decide_phase`: decides whether to continue or finish.
7. `per_turn_feedback` and/or `final_feedback`: returns coaching output.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key (default model is `openai:gpt-5.4-mini`)

## Quickstart

1. Install dependencies.

```bash
uv sync --group dev
```

2. Configure environment variables.

```bash
cp .env.example .env
```

Add at least:

```env
OPENAI_API_KEY=your_key_here
```

Optional for tracing:

```env
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=tscoach
```

3. Start LangGraph locally.

```bash
uv run langgraph dev
```

4. Open LangGraph Studio from the URL printed in the terminal and run the `agent` graph.

## Example Onboarding Prompt

Your first learner message should include at least scenario category and difficulty. Example:

```text
I want to practice counselling for family conflict, difficulty 7, language de, feedback both, max_turns 5.
```

## Configuration

Runtime config is stored in `TrainingConfig` (`src/agent/schemas.py`):

- `language`: output language (default `de` in schema, onboarding fallback currently `en` in node logic)
- `max_turns`: maximum conversation turns (default `3` in schema)
- `feedback_mode`: `none`, `per_turn`, `final`, `both` (default `both`)

## Development

Useful commands from the `Makefile`:

```bash
make lint
make format
make test
make integration_tests
```

## Project Structure

```text
src/agent/
  graph.py              # LangGraph assembly
  router.py             # Conditional routing logic
  schemas.py            # Pydantic schemas
  state.py              # Training state model
  nodes/
    onboarding.py       # Setup extraction + scenario creation
    simulation.py       # Caller simulation + phase decisions
    evaluation.py       # Turn evaluation + feedback
  prompts.py            # Prompt templates
  llm.py                # Model initialization
```

## Notes

- This repository currently has test scaffolding under `tests/`, but no concrete test cases yet.
- To switch model/provider, update `src/agent/llm.py`.
