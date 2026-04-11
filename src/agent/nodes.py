"""Run training nodes for counselling simulations."""

from typing import Literal, cast

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.types import interrupt

from agent.prompts import (
    CALLER_PROMPT,
    EVALUATION_SUMMARY,
    HUMAN_INPUT_EVALUATION,
    PHASE_DECISION_PROMPT,
    TURN_FEEDBACK_PROMPT,
)
from agent.state import (
    Aggregates,
    PhaseDecision,
    Scenario,
    TrainingInputState,
    TrainingState,
    TurnEvaluation,
)
from agent.utils import format_history, get_profile, language_constraint

llm = init_chat_model("openai:gpt-5.4-mini")


async def scenario_setup(state: TrainingInputState) -> dict:
    """Build the scenario description and caller profile for a new session."""
    category = state.scenario.category
    if category is None:
        raise ValueError("Scenario category cannot be None")

    difficulty = state.scenario.difficulty
    if difficulty is None:
        raise ValueError("Scenario difficulty cannot be None")

    messages = [
        SystemMessage(
            content=(
                "You generate realistic telephone counselling scenarios. "
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(
            content=f"Category: {category}\nDifficulty: {difficulty}\n"
            "Create a short, realistic scenario (max 4 sentences).\n"
            f"Language: {state.config.language}"
        ),
    ]

    chain = llm | StrOutputParser()
    description = await chain.ainvoke(messages)

    scenario = Scenario(
        category=category, difficulty=difficulty, description=description
    )
    profile = get_profile(difficulty)

    return {
        "scenario": scenario,
        "caller_profile": profile,
    }


async def caller_simulation(state: TrainingState) -> dict:
    """Generate the next caller message from the current training state."""
    if not state.caller_profile:
        raise ValueError("Caller profile is not set")

    formatted_history = await format_history(state)

    caller_msg = CALLER_PROMPT.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        difficulty=state.scenario.difficulty,
        emotional_state=state.caller_profile.emotional_state,
        volatility=state.caller_profile.volatility,
        cooperativeness=state.caller_profile.cooperativeness,
        formatted_history=formatted_history,
    )

    messages = [
        SystemMessage(
            content=(
                "You simulate a telephone counselling caller. Stay in role. "
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=caller_msg),
    ]

    response = await llm.ainvoke(messages)

    return {
        "messages": [response],
        "turn_index": state.turn_index + 1,
    }


def await_learner_input(state: TrainingState) -> dict:
    """Prompt for learner input and return it as a human message."""
    prompt = "What do you want to say to the caller?"
    if state.per_turn_feedback:
        latest_feedback = state.per_turn_feedback[-1]
        prompt = (
            "Feedback on your last response:\n"
            f"{latest_feedback}\n\n"
            "What do you want to say to the caller?"
        )

    learner_input = interrupt(prompt)

    return {
        "messages": [HumanMessage(content=learner_input)],
    }


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

    formatted_history = await format_history(state)

    evaluation_msg = HUMAN_INPUT_EVALUATION.format(
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


async def control_node(state: TrainingState) -> dict:
    """Decide the next conversation phase and whether training should stop."""
    if not state.caller_profile:
        raise ValueError("Caller profile is not set")

    formatted_history = await format_history(state)

    decision_msg = PHASE_DECISION_PROMPT.format(
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


async def continue_conversation(state: TrainingState) -> Literal["continue", "finish"]:
    """Return whether the graph should continue or finish."""
    return "finish" if state.finished else "continue"


async def per_turn_feedback_node(state: TrainingState) -> dict:
    """Generate coaching feedback for the most recent evaluated turn."""
    if not state.evaluations:
        return {}

    latest_evaluation = state.evaluations[-1]
    feedback_msg = TURN_FEEDBACK_PROMPT.format(
        scenario_description=state.scenario.description,
        language=state.config.language,
        turn_index=latest_evaluation.turn_index,
        empathy=latest_evaluation.empathy,
        question_quality=latest_evaluation.question_quality,
        advice_given="yes" if latest_evaluation.advice_given else "no",
        notes=latest_evaluation.notes or "",
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
    return {"per_turn_feedback": [response.content]}


async def route_after_control(
    state: TrainingState,
) -> Literal["per_turn_feedback", "continue", "final_feedback", "end"]:
    """Route flow after control based on feedback mode and completion state."""
    mode = state.config.feedback_mode

    if mode in ("per_turn", "both"):
        return "per_turn_feedback"
    if state.finished:
        if mode == "final":
            return "final_feedback"
        return "end"
    return "continue"


async def route_after_per_turn_feedback(
    state: TrainingState,
) -> Literal["continue", "final_feedback", "end"]:
    """Route flow after per-turn feedback based on finish state and mode."""
    if not state.finished:
        return "continue"
    if state.config.feedback_mode == "both":
        return "final_feedback"
    return "end"


async def feedback_node(state: TrainingState) -> dict:
    """Generate final feedback from aggregate metrics and chat history."""
    if not state.aggregates:
        raise ValueError("Aggregates are not set")

    formatted_history = await format_history(state)

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

    return {"final_feedback": response.content}
