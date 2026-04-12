"""Graph of the agent."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from agent.nodes import (
    behaviour_analysis,
    caller_simulation,
    decide_phase,
    entry_router,
    final_feedback,
    onboarding,
    per_turn_feedback,
    route_after_decide_phase,
    route_after_onboarding,
    route_after_per_turn_feedback,
    scenario_setup,
)
from agent.state import TrainingState

builder = StateGraph(TrainingState)

builder.add_node("onboarding", onboarding)
builder.add_node("scenario_setup", scenario_setup)
builder.add_node("caller_simulation", caller_simulation)
builder.add_node("behaviour_analysis", behaviour_analysis)
builder.add_node("decide_phase", decide_phase)
builder.add_node("per_turn_feedback", per_turn_feedback)
builder.add_node("final_feedback", final_feedback)


builder.add_conditional_edges(
    START,
    entry_router,
    {
        "onboarding": "onboarding",
        "caller_simulation": "caller_simulation",
        "behaviour_analysis": "behaviour_analysis",
    },
)
builder.add_conditional_edges(
    "onboarding",
    route_after_onboarding,
    {
        "scenario_setup": "scenario_setup",
        "onboarding": "onboarding",
    },
)
builder.add_edge("scenario_setup", "caller_simulation")
builder.add_edge("caller_simulation", END)
builder.add_edge("behaviour_analysis", "decide_phase")
builder.add_conditional_edges(
    "decide_phase",
    route_after_decide_phase,
    {
        "per_turn_feedback": "per_turn_feedback",
        "final_feedback": "final_feedback",
        "caller_simulation": "caller_simulation",
        "end": END,
    },
)
builder.add_conditional_edges(
    "per_turn_feedback",
    route_after_per_turn_feedback,
    {
        "final_feedback": "final_feedback",
        "caller_simulation": "caller_simulation",
        "end": END,
    },
)
builder.add_edge("final_feedback", END)

memory = MemorySaver()
graph = builder.compile()
