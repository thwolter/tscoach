"""Provide helper functions for training state formatting and profile setup."""

from agent.state import CallerProfile, TrainingState


async def format_history(state: TrainingState) -> str:
    """Format conversation history from training state as a single string."""
    history = []
    for msg in state.messages:
        role = "Caller" if msg.type == "ai" else "Learner"
        history.append(f"{role}: {msg.content}")
    return "\n".join(history)


def language_constraint(language: str) -> str:
    """Build the language constraint instruction string."""
    return (
        "All natural-language output must be in "
        f"'{language}'. "
        "Do not switch to other languages."
    )


def get_profile(difficulty: int):
    """Return a caller profile for the given difficulty level."""
    if difficulty <= 2:
        return CallerProfile(
            emotional_state="mild distress",
            volatility=0.2,
            cooperativeness=0.8,
        )
    elif difficulty == 3:
        return CallerProfile(
            emotional_state="moderate distress",
            volatility=0.5,
            cooperativeness=0.5,
        )
    else:
        return CallerProfile(
            emotional_state="severe distress",
            volatility=0.8,
            cooperativeness=0.3,
        )
