"""Onboarding nodes."""

from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from agent.llm import llm
from agent.prompts.onboarding import PARSE_ONBOARDING, SCENARIO_SETUP
from agent.schemas import OnboardingSetup, Scenario, TrainingConfig
from agent.state import TrainingState
from agent.utils import get_profile, language_constraint

DEFAULT_LANGUAGE = 'en'
DEFAULT_MAX_TURNS = 10
DEFAULT_FEEDBACK_MODE = 'both'


async def onboarding(state: TrainingState) -> dict:
    """Extract the scenario description from the training state."""
    formatted_messages = '\n'.join(str(msg.content) for msg in state.messages)

    messages = [
        SystemMessage(content=PARSE_ONBOARDING),
        HumanMessage(content=formatted_messages),
    ]

    structured_llm = llm.with_structured_output(OnboardingSetup)
    setup = cast(OnboardingSetup, await structured_llm.ainvoke(messages))

    if any(f in setup.missing_fields for f in ('category', 'difficulty')):
        return {
            'messages': [AIMessage(content=setup.clarification_question)],
        }

    scenario = Scenario(category=setup.category, difficulty=setup.difficulty)
    config = TrainingConfig(
        language=setup.language or DEFAULT_LANGUAGE,
        max_turns=setup.max_turns or DEFAULT_MAX_TURNS,
    )

    return {'scenario': scenario, 'config': config}


async def scenario_setup(state: TrainingState) -> dict:
    """Build the scenario description and caller profile for a new session."""
    if not state.scenario:
        raise ValueError('Scenario is not set')

    category = state.scenario.category
    difficulty = state.scenario.difficulty

    if not difficulty:
        raise ValueError('Scenario difficulty is not set')

    create_scenario = SCENARIO_SETUP.format(category=category, difficulty=difficulty)

    messages = [
        SystemMessage(
            content=(
                'You generate realistic telephone counselling scenarios.'
                + language_constraint(state.config.language)
            )
        ),
        HumanMessage(content=create_scenario),
    ]

    chain = llm | StrOutputParser()
    scenario_description = await chain.ainvoke(messages)

    scenario = Scenario(
        category=category, difficulty=difficulty, description=scenario_description
    )
    profile = get_profile(difficulty)

    return {
        'scenario': scenario,
        'caller_profile': profile,
    }


async def introduction(state: TrainingState) -> dict:
    """Introduce the agent to the user."""
    system_prompt = 'You are a helpful assistant.' + language_constraint(
        state.config.language
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content='How can I help you today?'),
    ]
    return {
        'messages': [await llm.ainvoke(messages)],
    }
