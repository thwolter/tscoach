"""Router for agent flow."""

from typing import Literal

from agent.state import TrainingState


async def entry_router(
    state: TrainingState,
) -> Literal["onboarding", "caller_simulation", "behaviour_analysis"]:
    """Route flow based on initial state."""
    if not state.scenario:
        return "onboarding"

    if not state.messages:
        return "caller_simulation"

    if state.messages[-1].type == "human":
        return "behaviour_analysis"

    return "caller_simulation"


async def route_after_onboarding(
    state: TrainingState,
) -> Literal["scenario_setup", "onboarding"]:
    """Route flow after onboarding based on scenario setup state."""
    if not state.scenario:
        return "onboarding"
    return "scenario_setup"


async def route_after_decide_phase(
    state: TrainingState,
) -> Literal["per_turn_feedback", "caller_simulation", "final_feedback", "end"]:
    """Route flow after control based on feedback mode and completion state."""
    mode = state.config.feedback_mode

    if mode in ("per_turn", "both"):
        return "per_turn_feedback"
    if state.finished:
        if mode == "final":
            return "final_feedback"
        return "end"
    return "caller_simulation"


async def route_after_per_turn_feedback(
    state: TrainingState,
) -> Literal["caller_simulation", "final_feedback", "end"]:
    """Route flow after per-turn feedback based on finish state and mode."""
    if not state.finished:
        return "caller_simulation"
    if state.config.feedback_mode == "both":
        return "final_feedback"
    return "end"
