"""Router for agent flow."""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage

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
    "end",
]:
    """Route flow based on initial state."""
    if not state.scenario:
        return "onboarding"

    if not state.messages:
        return "caller_simulation"

    last_message = state.messages[-1]

    if isinstance(last_message, HumanMessage):
        if parse_handover_command(last_message) is not None:
            return "handover_command"
        return "behaviour_analysis"

    if (
        isinstance(last_message, AIMessage)
        and state.handover_active
        and getattr(last_message, "name", None) == "caller"
    ):
        return "trainer_takeover"

    return "end"


async def route_after_onboarding(
    state: TrainingState,
) -> Literal["scenario_setup", "end"]:
    """Route flow after onboarding based on scenario setup state."""
    if not state.scenario:
        return "end"
    return "scenario_setup"


async def route_after_decide_phase(
    state: TrainingState,
) -> Literal["per_turn_feedback", "caller_simulation", "end_summary"]:
    """Route flow after control based on feedback mode and completion state."""
    if state.handover_active:
        if state.finished:
            return "end_summary"
        return "caller_simulation"

    mode = state.config.feedback_mode

    if mode in ("per_turn", "both") and not state.finished:
        return "per_turn_feedback"
    if state.finished:
        return "end_summary"
    return "caller_simulation"


async def route_after_per_turn_feedback(
    state: TrainingState,
) -> Literal["caller_simulation", "end_summary"]:
    """Route flow after per-turn feedback based on finish state and mode."""
    if not state.finished:
        return "caller_simulation"
    return "end_summary"


async def route_after_end_summary(
    state: TrainingState,
) -> Literal["final_feedback", "end"]:
    """Route flow after end summary based on evaluation availability."""
    if state.evaluations:
        return "final_feedback"
    return "end"


async def route_after_handover_command(
    state: TrainingState,
) -> Literal["trainer_takeover", "end"]:
    """Route flow after command handling."""
    if state.command_mode == "trainer_takeover":
        return "trainer_takeover"
    return "end"
