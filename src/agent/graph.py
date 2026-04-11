"""Graph of the agent."""

from langgraph.constants import END, START
from langgraph.graph import StateGraph

from agent.nodes import (
    await_learner_input,
    behaviour_analysis,
    caller_simulation,
    decide_phase,
    final_feedback,
    per_turn_feedback,
    route_after_decide_phase,
    route_after_per_turn_feedback,
    scenario_setup,
)
from agent.state import TrainingInputState, TrainingState

builder = StateGraph(
    TrainingState, input_schema=TrainingInputState, output_schema=TrainingState
)

builder.add_node("scenario_setup", scenario_setup)
builder.add_node("caller_simulation", caller_simulation)
builder.add_node("learner_input", await_learner_input)
builder.add_node("behaviour_analysis", behaviour_analysis)
builder.add_node("decide_phase", decide_phase)
builder.add_node("per_turn_feedback", per_turn_feedback)
builder.add_node("final_feedback", final_feedback)


builder.add_edge(START, "scenario_setup")
builder.add_edge("scenario_setup", "caller_simulation")
builder.add_edge("caller_simulation", "learner_input")
builder.add_edge("learner_input", "behaviour_analysis")
builder.add_edge("behaviour_analysis", "decide_phase")
builder.add_conditional_edges(
    "decide_phase",
    route_after_decide_phase,
    {
        "per_turn_feedback": "per_turn_feedback",
        "final_feedback": "final_feedback",
        "continue": "caller_simulation",
        "end": END,
    },
)
builder.add_conditional_edges(
    "per_turn_feedback",
    route_after_per_turn_feedback,
    {
        "final_feedback": "final_feedback",
        "continue": "caller_simulation",
        "end": END,
    },
)
builder.add_edge("final_feedback", END)

graph = builder.compile()
