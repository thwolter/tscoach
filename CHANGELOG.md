## 0.4.0 (2026-04-14)

### BREAKING CHANGE

- Authentication database schema and admin user management are now handled by `langgraph-secure-gateway`. Update deployment workflows
- Authentication logic now relies on `langgraph-secure-gateway`. Remove old authentication code and update configurations and scripts to use the new package.
- Replaced `agent_api_keys` table with `users` and `panel_access` tables. Update schema, environment variables, and authentication logic accordingly.
- Deployments now require `AGENT_API_KEY_PEPPER` and a populated `agent_api_keys` Postgres table. Update environment variables and database schema accordingly.

### Feat

- **dependencies**: add `ipykernel` dependency and update lockfile
- **docker**: add health check and configurable port for `langgraph-app`
- **auth**: migrate from API key-based auth to JWT and user authentication system
- **auth**: implement API key-based authentication for LangGraph deployments
- **docker**: add pull policy and forwarded IPs to `langgraph-api` in `docker-compose.yaml`
- **docker**: add Dockerfile and update docker-compose with `langgraph-app` image
- **docker**: add build context for `langgraph-api` in `docker-compose.yaml`
- **config**: reintroduce `.env.example` with default environment variables

### Refactor

- **auth**: remove database initialization scripts and admin user creation logic
- **auth**: remove legacy authentication-related modules
- **docker**: remove unused port bindings from `docker-compose.yaml`
- **docker**: rename `docker-compose.yml` to `docker-compose.yaml`

## 0.3.0 (2026-04-13)

### Feat

- **docker**: add docker-compose setup for local development
- **agent**: add new handover state and update dependency constraints

## 0.2.0 (2026-04-12)

### Feat

- **agent**: add end_summary node and integrate into training flow
- **agent**: add trainer handover functionality with routing and node integration

### Refactor

- **agent**: remove handover command tests and update routing logic

## 0.1.0 (2026-04-12)

### Feat

- **agent**: add update_caller_profile node to training flow
- **agent**: add caller profile update functionality
- **agent**: restructure schemas and enhance state models
- **agent**: extract and modularize domain models into `schemas.py`
- **agent**: export core nodes and routers for training flow
- **agent**: add routing logic to enhance training flow
- **agent**: add phase decision and caller simulation nodes
- **agent**: add onboarding and scenario setup nodes
- **agent**: add evaluation and feedback mechanisms to training flow
- **agent**: add onboarding flow and improve scenario handling
- **agent**: improve flow and prompts for message handling
- **agent**: adjust cooperativeness mapping for improved behavior simulation
- **config**: add Pyrefly configuration to project settings
- **agent**: refactor node and graph structure for phase control and feedback flow
- **prompts**: enhance caller simulation prompt structure and behavioral rules
- **agent**: enhance `get_profile` with dynamic behavior simulation
- **tests**: add unit tests for training state routing logic
- **agent**: add utility functions for state formatting and profiling
- **agent**: add structured evaluation and coaching prompts for training simulations
- **agent**: define full state graph for training simulations
- **agent**: implement training nodes for counselling simulations
- **agent**: add core state models for training and evaluation

### Fix

- **pyproject**: update Python version and setuptools dependency constraints

### Refactor

- **agent**: rename `format_history` to `format_conversation_history`
- **agent**: optimize message filtering in `format_history`
- **agent**: move LLM initialization to dedicated module
- **prompts**: remove unused `formatted_history` variable from template
- **prompts**: rename prompt variables for clarity and consistency
