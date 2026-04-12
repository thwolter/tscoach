"""Simulation nodes."""

from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import llm
from agent.prompts import CALLER_SIMULATION, PHASE_DECISION
from agent.state import PhaseDecision, TrainingState
from agent.utils import format_history, language_constraint


async def caller_simulation(state: TrainingState) -> dict:
    """Generate the next caller message from the current training state."""
    if not state.caller_profile:
        raise ValueError("Caller profile is not set")

    if not state.scenario:
        raise ValueError("Scenario is not set")

    formatted_history = await format_history(state)

    if not formatted_history.strip():
        formatted_history = "\n\nIMPORTANT: This is the first message. The first word MUST be a greeting."

    system_prompt = CALLER_SIMULATION.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        emotional_state=state.caller_profile.emotional_state,
        complexity=state.caller_profile.complexity,
        volatility=state.caller_profile.volatility,
        cooperativeness=state.caller_profile.cooperativeness,
    )

    messages = [
        SystemMessage(
            content=(system_prompt + language_constraint(state.config.language))
        ),
        HumanMessage(content=formatted_history),
    ]

    response = await llm.ainvoke(messages)
    caller_message = response.model_copy(update={"name": "caller"})

    return {
        "messages": [caller_message],
        "turn_index": state.turn_index + 1,
    }


async def decide_phase(state: TrainingState) -> dict:
    """Decide the next conversation phase and whether training should stop."""
    if not state.caller_profile:
        raise ValueError("Caller profile is not set")

    if not state.scenario:
        raise ValueError("Scenario is not set")

    formatted_history = await format_history(state)

    decision_msg = PHASE_DECISION.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        emotional_state=state.caller_profile.emotional_state,
        volatility=state.caller_profile.volatility,
        cooperativeness=state.caller_profile.cooperativeness,
        phase=state.phase,
        formatted_history=formatted_history,
        turn_index=state.turn_index,
        max_turns=state.config.max_turns,
    )

    messages = [
        SystemMessage(
            content=(
                "You control the flow of a counselling conversation. "
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=decision_msg),
    ]

    structured_llm = llm.with_structured_output(PhaseDecision)
    decision = cast(PhaseDecision, await structured_llm.ainvoke(messages))

    finished = decision.finished
    if state.turn_index >= state.config.max_turns:
        finished = True

    return {
        "phase": decision.phase,
        "finished": finished,
    }
