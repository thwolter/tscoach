"""Core domain models for the agent's state and evaluation."""

from operator import add
from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from agent.schemas import (
    Aggregates,
    CallerProfile,
    Scenario,
    TrainingConfig,
    TurnEvaluation,
)


class TrainingState(BaseModel):
    """State of the training session."""

    scenario: Scenario | None = None
    caller_profile: CallerProfile | None = None
    config: TrainingConfig = Field(default_factory=TrainingConfig)

    messages: Annotated[list[AnyMessage], add_messages]
    evaluations: Annotated[list[TurnEvaluation], add] = Field(default_factory=list)

    aggregates: Aggregates | None = None

    phase: Literal['opening', 'exploration', 'closing'] = 'opening'

    turn_index: int = 0
    finished: bool = False

    handover_requested: bool = False
    handover_active: bool = False
    command_mode: Literal[
        'none', 'await_confirmation', 'trainer_takeover', 'end_requested'
    ] = 'none'
    audit_log: Annotated[list[str], add] = Field(default_factory=list)

    per_turn_feedback: Annotated[list[str], add] = Field(default_factory=list)
    end_summary: str | None = None
    final_feedback: str | None = None
