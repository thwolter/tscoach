"""Evaluation nodes."""

from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.llm import llm
from agent.prompts.evaluation import (
    EVALUATION_SUMMARY,
    LEARNER_EVALUATION,
    TRAINING_WRAP_UP,
    TURN_FEEDBACK,
)
from agent.schemas import Aggregates, TurnEvaluation
from agent.state import TrainingState
from agent.utils import (
    format_conversation_history,
    language_constraint,
    parse_session_command,
)


async def aggregate_evaluation(
    response: TurnEvaluation, state: TrainingState
) -> Aggregates:
    """Update aggregate metrics with the latest turn evaluation."""
    if state.aggregates is None:
        aggregate = Aggregates(
            total_turns=1,
            avg_empathy=response.empathy,
            avg_question_quality=response.question_quality,
            advice_ratio=int(response.advice_given),
        )
    else:
        total = state.aggregates.total_turns + 1
        aggregate = Aggregates(
            total_turns=total,
            avg_empathy=(
                (
                    state.aggregates.avg_empathy * state.aggregates.total_turns
                    + response.empathy
                )
                / total
            ),
            avg_question_quality=(
                (
                    state.aggregates.avg_question_quality * state.aggregates.total_turns
                    + response.question_quality
                )
                / total
            ),
            advice_ratio=(
                (
                    state.aggregates.advice_ratio * state.aggregates.total_turns
                    + int(response.advice_given)
                )
                / total
            ),
        )
    return aggregate


async def behaviour_analysis(state: TrainingState) -> dict:
    """Evaluate the latest learner reply and refresh aggregate metrics."""
    last_user_message = next(
        (
            message
            for message in reversed(state.messages)
            if isinstance(message, HumanMessage)
            and parse_session_command(message) is None
        ),
        None,
    )
    if last_user_message is None:
        raise ValueError('No analysable learner message found')

    formatted_history = await format_conversation_history(state)

    if not state.scenario:
        raise ValueError('Scenario is not set')

    evaluation_msg = LEARNER_EVALUATION.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        phase=state.phase,
        formatted_history=formatted_history,
        turn_index=state.turn_index,
    )

    messages = [
        SystemMessage(
            content=(
                'You evaluate counselling responses. '
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=evaluation_msg),
    ]

    structured_llm = llm.with_structured_output(TurnEvaluation)
    response = cast(TurnEvaluation, await structured_llm.ainvoke(messages))

    aggregates = await aggregate_evaluation(response, state)

    return {
        'evaluations': [response],
        'aggregates': aggregates,
    }


async def per_turn_feedback(state: TrainingState) -> dict:
    """Generate coaching feedback for the most recent evaluated turn."""
    if not state.scenario:
        raise ValueError('Scenario is not set')

    if not state.evaluations:
        return {}

    latest_evaluation = state.evaluations[-1]

    system_prompt = TURN_FEEDBACK.format(
        scenario_description=state.scenario.description,
        turn_index=latest_evaluation.turn_index,
        empathy=latest_evaluation.empathy,
        question_quality=latest_evaluation.question_quality,
        advice_given='yes' if latest_evaluation.advice_given else 'no',
        notes=latest_evaluation.notes or '',
        turn_feedbacks=state.per_turn_feedback,
    ) + language_constraint(state.config.language)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.messages[-1].content),
    ]

    response = await llm.ainvoke(messages)
    return {'messages': [response], 'per_turn_feedback': [response.content]}


async def end_summary(state: TrainingState) -> dict:
    """Generate a brief end-of-session wrap-up of the conversation trajectory."""
    if not state.scenario:
        raise ValueError('Scenario is not set')

    formatted_history = await format_conversation_history(state)

    summary_msg = TRAINING_WRAP_UP.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        phase=state.phase,
        formatted_history=formatted_history,
    )

    messages = [
        SystemMessage(
            content=(
                'You are a trainer for telephone counselling. '
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=summary_msg),
    ]

    response = await llm.ainvoke(messages)
    return {'messages': [response], 'end_summary': response.content}


def derive_training_result(aggregates: Aggregates) -> tuple[float, str]:
    """Convert aggregate metrics into a compact final score and performance band."""
    score = (
        aggregates.avg_empathy
        + aggregates.avg_question_quality
        + (1 - aggregates.advice_ratio)
    ) / 3

    if score >= 0.8:
        band = 'strong'
    elif score >= 0.6:
        band = 'developing'
    else:
        band = 'needs_practice'

    return score, band


async def final_feedback(state: TrainingState) -> dict:
    """Generate final feedback from aggregate metrics and chat history."""
    if not state.scenario:
        raise ValueError('Scenario is not set')

    aggregates = state.aggregates
    if aggregates is None:
        return {
            'messages': [AIMessage(content='No evaluations available.')],
        }

    score, performance_band = derive_training_result(aggregates)

    feedback_msg = EVALUATION_SUMMARY.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        avg_empathy=aggregates.avg_empathy,
        avg_question_quality=aggregates.avg_question_quality,
        advice_ratio=aggregates.advice_ratio,
        overall_score=score,
        performance_band=performance_band,
    )

    messages = [
        SystemMessage(
            content=(
                'You are a trainer for telephone counselling. '
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=feedback_msg),
    ]

    response = await llm.ainvoke(messages)

    return {'messages': [response], 'final_feedback': response.content}
