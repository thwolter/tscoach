"""Handover nodes for trainer takeover commands."""

from datetime import UTC, datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.llm import llm
from agent.prompts.handover import TRAINER_TAKEOVER
from agent.state import TrainingState
from agent.utils import (
    format_conversation_history,
    language_constraint,
    parse_session_command,
)


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec='seconds')


async def handover_command(state: TrainingState) -> dict:
    """Handle learner slash commands for trainer handover/session termination."""
    last_user_message = state.messages[-1]
    if last_user_message.type != 'human':
        raise ValueError('Last message is not from the user')

    action = parse_session_command(last_user_message)
    if action is None:
        return {'command_mode': 'none'}

    if action == 'end':
        return {
            'handover_active': False,
            'command_mode': 'end_requested',
            'finished': True,
            'messages': [
                AIMessage(
                    content='Session ended. You can start a new training anytime.'
                )
            ],
            'audit_log': [f'{_utc_now_iso()} session_ended'],
        }

    if action == 'request':
        return {
            'handover_active': True,
            'command_mode': 'trainer_takeover',
            'messages': [
                AIMessage(
                    content='Trainer handover activated. I will now continue with the caller.'
                )
            ],
            'audit_log': [f'{_utc_now_iso()} handover_activated'],
        }

    return {'command_mode': 'none'}


async def trainer_takeover(state: TrainingState) -> dict:
    """Generate the trainer's next counsellor message after handover."""
    if not state.scenario:
        raise ValueError('Scenario is not set')

    formatted_history = await format_conversation_history(state)

    trainer_prompt = TRAINER_TAKEOVER.format(
        scenario_description=state.scenario.description,
        phase=state.phase,
        formatted_history=formatted_history,
    )

    messages = [
        SystemMessage(
            content=(trainer_prompt + language_constraint(state.config.language))
        ),
        HumanMessage(
            content=(
                "Write the trainer's next message to the caller and continue the call naturally."
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    trainer_message = response.model_copy(update={'name': 'trainer'})
    return {
        'messages': [trainer_message],
        'command_mode': 'none',
        'handover_active': False,
    }
