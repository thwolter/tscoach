"""Core domain models for the agent's state and evaluation."""

from operator import add
from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class OnboardingSetup(BaseModel):
    category: str | None = Field(
        description="Scenario topic or context explicitly provided by the user"
    )
    difficulty: int | None = Field(
        description="Difficulty level from 1 (easy) to 10 (very difficult)"
    )
    language: str | None = Field(
        description="Language for the conversation. Inferred from the user prompt if not stated explicitly.",
        max_length=2
    )
    feedback_mode: Literal["none", "per_turn", "final", "both"] | None = Field(
        description="Feedback mode: none, per_turn, final, or both; only if explicitly stated"
    )
    max_turns: int | None = Field(
        description="Maximum number of turns in the conversation; only if explicitly stated",
        ge=1, le=10
    )

    missing_fields: list[str] = Field(
        description="List of required fields that are missing or invalid"
    )
    clarification_question: str | None = Field(
        description="Short question asking for missing required fields"
    )

# --- Core domain models ---
class Scenario(BaseModel):
    """Scenario description."""

    category: str | None = None
    difficulty: int | None = Field(None, ge=1, le=10)
    description: str | None = None


class CallerProfile(BaseModel):
    """Profile of the caller."""

    emotional_state: str
    complexity: int
    volatility: float
    cooperativeness: float


class TurnEvaluation(BaseModel):
    """Evaluation of the learner's response to the caller."""

    turn_index: int = Field(..., description="Index of the turn in the conversation")
    empathy: float = Field(
        ...,
        description="Degree to which the learner shows understanding and emotional resonance with the caller (0 = none, 1 = very strong empathy",
        ge=0,
        le=1,
    )
    question_quality: float = Field(
        ...,
        description="Quality of questions asked by the learner (0 = none, 1 = very good)",
        ge=0,
        le=1,
    )
    advice_given: bool = Field(
        ...,
        description="Indicates whether the learner gives direct advice or solutions instead of facilitating self-exploration",
    )
    notes: str | None = Field(
        ..., description="Short explanation (1–2 sentences) justifying the evaluation"
    )


class PhaseDecision(BaseModel):
    """Decision about the next phase of the conversation."""

    phase: Literal["opening", "exploration", "closing"] = Field(
        ..., description="Current phase of the counselling conversation."
    )
    finished: bool = Field(
        ..., description="Whether the conversation should end based on caller state."
    )
    rationale: str = Field(..., description="Short explanation of the decision.")


# --- Aggregated metrics (continuously updated) ---


class Aggregates(BaseModel):
    """Aggregated metrics for the training session."""

    avg_empathy: float = 0.0
    avg_question_quality: float = 0.0
    advice_ratio: float = 0.0
    total_turns: int = 0


# --- Config ---


class TrainingConfig(BaseModel):
    """Configuration for the training session."""

    max_turns: int = 3
    feedback_mode: Literal["none", "per_turn", "final", "both"] = "both"
    language: str = "de"


# --- Main State ---

class TrainingState(TrainingInputState):
    """State of the training session."""

    caller_profile: CallerProfile | None = None

    evaluations: Annotated[list[TurnEvaluation], add] = Field(default_factory=list)

    aggregates: Aggregates | None = None
    per_turn_feedback: Annotated[list[str], add] = Field(default_factory=list)
    final_feedback: str | None = None

    phase: Literal["opening", "exploration", "closing"] = "opening"

    turn_index: int = 0
    finished: bool = False

    next: str | None = None
