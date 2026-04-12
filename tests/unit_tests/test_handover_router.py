import asyncio

from langchain_core.messages import AIMessage, HumanMessage

from agent.router import (
    entry_router,
    route_after_decide_phase,
    route_after_handover_command,
)
from agent.schemas import Scenario
from agent.state import TrainingState


def test_entry_router_routes_handover_command():
    state = TrainingState(
        scenario=Scenario(category="family conflict", difficulty=5, description="x"),
        messages=[HumanMessage(content="/handover trainer")],
    )

    assert asyncio.run(entry_router(state)) == "handover_command"


def test_entry_router_routes_trainer_takeover_when_active_and_last_is_caller():
    state = TrainingState(
        scenario=Scenario(category="family conflict", difficulty=5, description="x"),
        handover_active=True,
        messages=[AIMessage(content="I don't know what to do.", name="caller")],
    )

    assert asyncio.run(entry_router(state)) == "trainer_takeover"


def test_route_after_handover_command_uses_command_mode():
    state = TrainingState(
        scenario=Scenario(category="family conflict", difficulty=5, description="x"),
        command_mode="trainer_takeover",
        messages=[],
    )

    assert asyncio.run(route_after_handover_command(state)) == "trainer_takeover"


def test_route_after_decide_phase_skips_feedback_during_handover():
    state = TrainingState(
        scenario=Scenario(category="family conflict", difficulty=5, description="x"),
        handover_active=True,
        finished=False,
        messages=[],
    )

    assert asyncio.run(route_after_decide_phase(state)) == "caller_simulation"
