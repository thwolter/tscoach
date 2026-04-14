"""Handover nodes for trainer takeover commands."""

from datetime import UTC, datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.llm import llm
from agent.prompts.handover import TRAINER_TAKEOVER
from agent.state import TrainingState
from agent.utils import (
    format_conversation_history,
    language_constraint,
    parse_handover_command,
)


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec='seconds')


async def handover_command(state: TrainingState) -> dict:
    """Handle learner slash commands for trainer handover."""
    last_user_message = state.messages[-1]
    if last_user_message.type != 'human':
        raise ValueError('Last message is not from the user')

    action = parse_handover_command(last_user_message)
    if action is None:
        return {'command_mode': 'none'}

    if action == 'request':
        return {
            'handover_requested': True,
            'command_mode': 'await_confirmation',
            'messages': [
                AIMessage(
                    content=(
                        'Handover requested. Type `/handover confirm` to let the trainer '
                        'complete the conversation, or `/handover cancel` to continue yourself.'
                    )
                )
            ],
            'audit_log': [f'{_utc_now_iso()} handover_requested'],
        }

    if action == 'cancel':
        return {
            'handover_requested': False,
            'handover_active': False,
            'command_mode': 'none',
            'messages': [
                AIMessage(
                    content='Handover cancelled. You can continue as the learner.'
                )
            ],
            'audit_log': [f'{_utc_now_iso()} handover_cancelled'],
        }

    if not state.handover_requested:
        return {
            'command_mode': 'await_confirmation',
            'messages': [
                AIMessage(
                    content=(
                        'No pending handover request found. Start with `/handover trainer` '
                        'or `/handover` first.'
                    )
                )
            ],
        }

    return {
        'handover_requested': False,
        'handover_active': True,
        'command_mode': 'trainer_takeover',
        'messages': [
            AIMessage(
                content='Trainer handover confirmed. I will now continue with the caller.'
            )
        ],
        'audit_log': [f'{_utc_now_iso()} handover_confirmed'],
    }


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
        'handover_requested': False,
        'handover_active': False,
    }
