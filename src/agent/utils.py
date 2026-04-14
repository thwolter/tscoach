"""Provide helper functions for training state formatting and profile setup."""

import random
from typing import Literal, TypeVar

from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string

from agent.schemas import CallerProfile
from agent.state import TrainingState

Number = TypeVar('Number', int, float)


def parse_session_command(
    message: HumanMessage,
) -> Literal['request', 'end'] | None:
    """Parse handover/session termination slash commands from the message."""
    text = (message.text or '').strip().lower()
    if text == '/end':
        return 'end'

    if not text.startswith('/handover'):
        return None

    return 'request'


async def format_conversation_history(state: TrainingState) -> str:
    """Format conversation history starting from the first caller message."""
    messages = state.messages

    # find first caller (AIMessage with name="caller")
    start_idx = next(
        (
            i
            for i, msg in enumerate(messages)
            if isinstance(msg, AIMessage) and getattr(msg, 'name', None) == 'caller'
        ),
        None,
    )

    if start_idx is None:
        return ''

    filtered: list[HumanMessage | AIMessage] = []
    for msg in messages[start_idx:]:
        if isinstance(msg, HumanMessage):
            if parse_session_command(msg) is None:
                filtered.append(msg)
            continue

        if isinstance(msg, AIMessage):
            role_name = getattr(msg, 'name', None)
            if role_name == 'caller':
                filtered.append(msg)
            elif role_name == 'trainer':
                filtered.append(HumanMessage(content=str(msg.content)))

    return get_buffer_string(
        filtered,
        human_prefix='Learner',
        ai_prefix='Caller',
    )


def language_constraint(language: str) -> str:
    """Build the language constraint instruction string."""
    return (
        'All natural-language output must be in '
        f"'{language}'. "
        'Do not switch to other languages.'
    )


def get_profile(difficulty: int) -> CallerProfile:
    """Return a caller profile for the given learner difficulty."""
    # --- Normalise difficulty (1–10 → 0–1)
    d = max(1, min(10, difficulty))
    x = (d - 1) / 9  # 0.0 – 1.0

    # --- Core behavioural drivers (smooth mapping)
    base_volatility = 0.2 + 0.6 * x  # 0.2 → 0.8
    base_cooperativeness = 0.85 - 0.7 * x  # 0.85 → 0.15
    base_complexity = 1 + 4 * x  # 1 → 5

    # --- Add realistic noise (Gaussian)
    volatility = min(1.0, max(0.0, random.gauss(base_volatility, 0.1)))
    cooperativeness = min(1.0, max(0.0, random.gauss(base_cooperativeness, 0.12)))
    complexity = int(round(min(5, max(1, random.gauss(base_complexity, 0.8)))))

    # --- Emotional state (weakly coupled to difficulty)
    emotional_state = random.choices(
        ['calm', 'mild distress', 'moderate distress', 'severe distress'],
        weights=[
            max(0.1, 1 - x),  # calm decreases with difficulty
            0.4,
            0.3 + 0.2 * x,  # moderate increases slightly
            0.1 + 0.3 * x,  # severe increases but not dominant
        ],
        k=1,
    )[0]

    return CallerProfile(
        emotional_state=emotional_state,
        complexity=complexity,
        volatility=round(volatility, 2),
        cooperativeness=round(cooperativeness, 2),
    )


def clamp(value: Number, lower: Number, upper: Number) -> Number:
    """Clamp value into the inclusive [lower, upper] range."""
    return max(lower, min(upper, value))


def bounded_step(current: Number, target: Number, max_delta: Number) -> Number:
    """Move from current toward target by at most max_delta."""
    if max_delta < 0:
        raise ValueError('max_delta must be non-negative')
    return clamp(target, current - max_delta, current + max_delta)


def trim_recent_lines(text: str, max_lines: int) -> str:
    """Return only the most recent max_lines from text."""
    if max_lines < 0:
        raise ValueError('max_lines must be non-negative')
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return '\n'.join(lines[-max_lines:])
