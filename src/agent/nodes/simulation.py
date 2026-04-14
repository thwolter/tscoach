"""Simulation nodes."""

from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import llm
from agent.prompts.simulation import (
    CALLER_SIMULATION,
    PHASE_DECISION,
    PROFILE_UPDATE_INPUT,
    PROFILE_UPDATE_SYSTEM,
)
from agent.schemas import CallerProfile, CallerProfileUpdate, PhaseDecision
from agent.state import TrainingState
from agent.utils import (
    bounded_step,
    clamp,
    format_conversation_history,
    trim_recent_lines,
)

_EMOTIONAL_LEVELS = ['calm', 'mild distress', 'moderate distress', 'severe distress']
_PROFILE_HISTORY_MAX_LINES = 16


def _bounded_complexity(current: int, target: int) -> int:
    """Step complexity gradually and keep it in the valid range."""
    return clamp(bounded_step(current, target, 1), 1, 5)


def _bounded_trait(current: float, target: float) -> float:
    """Step trait score gradually, clamp to [0, 1], and round for storage."""
    return round(clamp(bounded_step(current, target, 0.10), 0.0, 1.0), 2)


def _bounded_emotional_state(current: str, target: str) -> str:
    """Restrict emotional state transitions to at most one level."""
    if current not in _EMOTIONAL_LEVELS or target not in _EMOTIONAL_LEVELS:
        return current
    current_idx = _EMOTIONAL_LEVELS.index(current)
    target_idx = _EMOTIONAL_LEVELS.index(target)
    if target_idx > current_idx:
        return _EMOTIONAL_LEVELS[min(current_idx + 1, len(_EMOTIONAL_LEVELS) - 1)]
    if target_idx < current_idx:
        return _EMOTIONAL_LEVELS[max(current_idx - 1, 0)]
    return current


async def caller_simulation(state: TrainingState) -> dict:
    """Generate the next caller message from the current training state."""
    if not state.caller_profile:
        raise ValueError('Caller profile is not set')

    if not state.scenario:
        raise ValueError('Scenario is not set')

    formatted_history = await format_conversation_history(state)

    if not formatted_history.strip():
        formatted_history = '\n\nIMPORTANT: This is the first message. The first word MUST be a greeting.'

    system_prompt = CALLER_SIMULATION.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        emotional_state=state.caller_profile.emotional_state,
        complexity=state.caller_profile.complexity,
        volatility=state.caller_profile.volatility,
        cooperativeness=state.caller_profile.cooperativeness,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=formatted_history),
    ]

    response = await llm.ainvoke(messages)
    caller_message = response.model_copy(update={'name': 'caller'})

    return {
        'messages': [caller_message],
        'turn_index': state.turn_index + 1,
    }


async def update_caller_profile(state: TrainingState) -> dict:
    """Update caller profile using recent dialog evidence with bounded drift."""
    if not state.caller_profile:
        raise ValueError('Caller profile is not set')

    formatted_history = trim_recent_lines(
        await format_conversation_history(state),
        _PROFILE_HISTORY_MAX_LINES,
    )
    latest_evaluation = state.evaluations[-1] if state.evaluations else None

    update_msg = PROFILE_UPDATE_INPUT.format(
        emotional_state=state.caller_profile.emotional_state,
        complexity=state.caller_profile.complexity,
        volatility=state.caller_profile.volatility,
        cooperativeness=state.caller_profile.cooperativeness,
        empathy=(
            f'{latest_evaluation.empathy:.2f}'
            if latest_evaluation is not None
            else 'n/a'
        ),
        question_quality=(
            f'{latest_evaluation.question_quality:.2f}'
            if latest_evaluation is not None
            else 'n/a'
        ),
        advice_given=(
            'yes' if latest_evaluation and latest_evaluation.advice_given else 'no'
        ),
        notes=latest_evaluation.notes if latest_evaluation else 'n/a',
        turn_index=state.turn_index,
        formatted_history=formatted_history,
    )

    messages = [
        SystemMessage(
            content=PROFILE_UPDATE_SYSTEM.format(language=state.config.language)
        ),
        HumanMessage(content=update_msg),
    ]

    structured_llm = llm.with_structured_output(CallerProfileUpdate)
    proposed = cast(CallerProfileUpdate, await structured_llm.ainvoke(messages))

    current = state.caller_profile
    updated = CallerProfile(
        emotional_state=_bounded_emotional_state(
            current=current.emotional_state,
            target=proposed.emotional_state,
        ),
        complexity=_bounded_complexity(current.complexity, proposed.complexity),
        volatility=_bounded_trait(current.volatility, proposed.volatility),
        cooperativeness=_bounded_trait(
            current.cooperativeness, proposed.cooperativeness
        ),
    )

    return {'caller_profile': updated}


async def decide_phase(state: TrainingState) -> dict:
    """Decide the next conversation phase and whether training should stop."""
    if state.finished:
        return {'finished': True}

    if not state.caller_profile:
        raise ValueError('Caller profile is not set')

    if not state.scenario:
        raise ValueError('Scenario is not set')

    formatted_history = await format_conversation_history(state)

    system_prompt = PHASE_DECISION.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        emotional_state=state.caller_profile.emotional_state,
        volatility=state.caller_profile.volatility,
        cooperativeness=state.caller_profile.cooperativeness,
        phase=state.phase,
        turn_index=state.turn_index,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=formatted_history),
    ]

    structured_llm = llm.with_structured_output(PhaseDecision)
    decision = cast(PhaseDecision, await structured_llm.ainvoke(messages))

    finished = decision.finished
    if state.config.max_turns and state.turn_index >= state.config.max_turns:
        finished = True

    return {
        'phase': decision.phase,
        'finished': finished,
    }
