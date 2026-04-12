"""Evaluation nodes."""

from typing import cast

from langchain_core.messages import HumanMessage, SystemMessage

from agent.llm import llm
from agent.prompts import EVALUATION_SUMMARY, LEARNER_EVALUATION, TURN_FEEDBACK
from agent.schemas import Aggregates, TurnEvaluation
from agent.state import TrainingState
from agent.utils import format_conversation_history, language_constraint


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
    last_user_message = state.messages[-1]
    if last_user_message.type != "human":
        raise ValueError("Last message is not from the user")

    formatted_history = await format_conversation_history(state)

    if not state.scenario:
        raise ValueError("Scenario is not set")

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
                "You evaluate counselling responses. "
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=evaluation_msg),
    ]

    structured_llm = llm.with_structured_output(TurnEvaluation)
    response = cast(TurnEvaluation, await structured_llm.ainvoke(messages))

    aggregates = await aggregate_evaluation(response, state)

    return {
        "evaluations": [response],
        "aggregates": aggregates,
    }


async def per_turn_feedback(state: TrainingState) -> dict:
    """Generate coaching feedback for the most recent evaluated turn."""
    if not state.scenario:
        raise ValueError("Scenario is not set")

    if not state.evaluations:
        return {}

    latest_evaluation = state.evaluations[-1]

    system_prompt = TURN_FEEDBACK.format(
        scenario_description=state.scenario.description,
        turn_index=latest_evaluation.turn_index,
        empathy=latest_evaluation.empathy,
        question_quality=latest_evaluation.question_quality,
        advice_given="yes" if latest_evaluation.advice_given else "no",
        notes=latest_evaluation.notes or "",
    ) + language_constraint(state.config.language)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=state.messages[-1].content),
    ]

    response = await llm.ainvoke(messages)
    return {"messages": [response], "per_turn_feedback": [response.content]}


async def final_feedback(state: TrainingState) -> dict:
    """Generate final feedback from aggregate metrics and chat history."""
    if not state.aggregates:
        raise ValueError("Aggregates are not set")

    if not state.scenario:
        raise ValueError("Scenario is not set")

    formatted_history = await format_conversation_history(state)

    feedback_msg = EVALUATION_SUMMARY.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        formatted_history=formatted_history,
        avg_empathy=state.aggregates.avg_empathy,
        avg_question_quality=state.aggregates.avg_question_quality,
        advice_ratio=state.aggregates.advice_ratio,
    )

    messages = [
        SystemMessage(
            content=(
                "You are a trainer for telephone counselling. "
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=feedback_msg),
    ]

    response = await llm.ainvoke(messages)

    return {"messages": [response], "final_feedback": response.content}
