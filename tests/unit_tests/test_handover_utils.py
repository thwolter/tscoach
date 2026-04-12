import asyncio

from langchain_core.messages import AIMessage, HumanMessage

from agent.schemas import Scenario
from agent.state import TrainingState
from agent.utils import format_conversation_history, parse_handover_command


def test_parse_handover_command():
    assert parse_handover_command("/handover") == "request"
    assert parse_handover_command("/handover trainer") == "request"
    assert parse_handover_command("/handover confirm") == "confirm"
    assert parse_handover_command("/handover cancel") == "cancel"
    assert parse_handover_command("hello there") is None


def test_format_conversation_history_ignores_commands_and_includes_trainer():
    state = TrainingState(
        scenario=Scenario(category="work stress", difficulty=4, description="x"),
        messages=[
            AIMessage(content="Hi", name="caller"),
            HumanMessage(content="/handover trainer"),
            AIMessage(content="Can you tell me more about that?", name="trainer"),
            AIMessage(content="I feel overwhelmed.", name="caller"),
        ],
    )

    history = asyncio.run(format_conversation_history(state))

    assert "/handover trainer" not in history
    assert "Learner: Can you tell me more about that?" in history
    assert "Caller: I feel overwhelmed." in history
