"""Router for agent flow."""

from typing import Literal

from langchain_core.messages import AIMessage

from agent.state import TrainingState
from agent.utils import parse_handover_command


async def entry_router(
    state: TrainingState,
) -> Literal[
    "onboarding",
    "caller_simulation",
    "behaviour_analysis",
    "handover_command",
    "trainer_takeover",
]:
    """Route flow based on initial state."""
    if not state.scenario:
        return "onboarding"

    if not state.messages:
        return "caller_simulation"

    last_message = state.messages[-1]

    if last_message.type == "human":
        if parse_handover_command(str(last_message.content)) is not None:
            return "handover_command"
        return "behaviour_analysis"

    if (
        state.handover_active
        and isinstance(last_message, AIMessage)
        and getattr(last_message, "name", None) == "caller"
    ):
        return "trainer_takeover"

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
    if state.handover_active:
        if state.finished:
            return "end"
        return "caller_simulation"

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


async def route_after_handover_command(
    state: TrainingState,
) -> Literal["trainer_takeover", "end"]:
    """Route flow after command handling."""
    if state.command_mode == "trainer_takeover":
        return "trainer_takeover"
    return "end"
