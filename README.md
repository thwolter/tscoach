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

- Send `/handover trainer` (or `/handover`) to request handover.
- Send `/handover confirm` to activate trainer takeover.
- Send `/handover cancel` to abort the request.
- Send `/end` to terminate the current session immediately.

After confirmation, the trainer continues the counsellor side of the conversation and the caller keeps responding until the conversation ends.

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

Add authentication settings:

```env
JWT_SECRET=your-long-random-secret
ADMIN_SESSION_SECRET=your-admin-session-secret
AUTH_DB_AUTO_INIT=true
AUTH_GATEWAY_HOST_PORT=8123
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

## JWT Authentication and Admin Panel

Docker Compose deployments are protected by `auth-gateway` (FastAPI) in front of `langgraph-api`, powered by the shared package [`langgraph-secure-gateway`](https://github.com/thwolter/langgraph-secure-gateway).

- Login endpoint: `POST /auth/login` with JSON body `{ "username": "...", "password": "..." }`
- Session endpoint: `GET /auth/me` with header `Authorization: Bearer <jwt>`
- Validation model: user passwords are stored as bcrypt hashes in Postgres.
- Auth tables are auto-created by the gateway when `AUTH_DB_AUTO_INIT=true`.
- JWTs are signed with backend-only `JWT_SECRET`.
- Only `auth-gateway` should be exposed publicly by your platform ingress; `langgraph-api` stays internal.

Create the initial admin user:

```bash
docker compose exec -T auth-gateway \
  secure-langgraph create-admin-user --username admin --password 'ChangeMe123!'
```

Then use:

- `http://localhost:8123/admin` for SQLAdmin-based admin user and panel management.
- The admin can create users, set/update user passwords, and assign panel access rows.

To disable access, set `is_active=false` for the target user.

## How To Use (Docker Auth Setup)

1. Set env vars in `.env` (copy from `.env.example`), especially:
   - `JWT_SECRET`
   - `ADMIN_SESSION_SECRET`
   - `JWT_ALGORITHM`
   - `JWT_EXPIRE_MINUTES`
   - `AUTH_DB_AUTO_INIT`
   - `AUTH_GATEWAY_HOST_PORT`
2. Start the stack:

```bash
docker compose up --build
```

3. Create the first admin user:

```bash
docker compose exec -T auth-gateway \
  secure-langgraph create-admin-user --username admin --password 'ChangeMe123!'
```

4. Open Admin UI:
   - `http://localhost:8123/admin/`

5. Frontend login flow:
   - Call `POST /auth/login` with `username` and `password`.
   - Store returned `access_token` for the session.
   - Send `Authorization: Bearer <access_token>` on API requests.

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
