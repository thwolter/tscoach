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

### Trainer Handover Command

The learner can hand over the live call to the trainer or end the current session:

- Send `/handover trainer` (or `/handover`) to activate trainer takeover.
- Send `/end` to terminate the current session immediately.

After handover, the trainer continues the counsellor side of the conversation and the caller keeps responding until the conversation ends.

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

For Docker deployments behind the external gateway, also set the shared upstream
secret:

```env
GATEWAY_UPSTREAM_SECRET=your-long-random-shared-secret
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

## Gateway Deployment

Authentication is handled by the external gateway, matching the setup in `../agents`.

The LangGraph server requires requests to include the shared `GATEWAY_UPSTREAM_SECRET`
that is injected by the gateway. Set the same strong value in this LangGraph
deployment and in the gateway deployment.

The LangGraph `base_url` configured in the gateway admin panel must be reachable
from the gateway container, for example a Coolify service URL or another internal
HTTP endpoint. Redis and Postgres remain private; this compose file does not
publish those service ports.

Direct callers that do not know `GATEWAY_UPSTREAM_SECRET` are rejected by the
LangGraph auth handler in `auth.py`.

## How To Use (Docker)

1. Set env vars in `.env` (copy from `.env.example`), especially:
   - `LANGSMITH_API_KEY`
   - `LANGSMITH_PROJECT`
   - `OPENAI_API_KEY`
   - `GATEWAY_UPSTREAM_SECRET`
2. Start the stack:

```bash
docker compose up --build
```

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
  prompts/             # Prompt templates clustered by topic
  llm.py                # Model initialization
```

## Notes

- This repository includes unit tests under `tests/unit_tests/`.
- To switch model/provider, update `src/agent/llm.py`.
