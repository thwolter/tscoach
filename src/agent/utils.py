"""Provide helper functions for training state formatting and profile setup."""

import random

from agent.schemas import CallerProfile
from agent.state import TrainingState


async def format_history(state: TrainingState) -> str:
    """Format conversation history starting from the first caller message."""
    history = []
    started = False

    for msg in state.messages:
        if msg.name == "caller":
            started = True

        if not started:
            continue

        if msg.type == "ai" and msg.name == "caller":
            history.append(f"Caller: {msg.content}")

        if msg.type == "human":
            history.append(f"Learner: {msg.content}")

    return "\n".join(history)


def language_constraint(language: str) -> str:
    """Build the language constraint instruction string."""
    return (
        "All natural-language output must be in "
        f"'{language}'. "
        "Do not switch to other languages."
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
        ["calm", "mild distress", "moderate distress", "severe distress"],
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
