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
