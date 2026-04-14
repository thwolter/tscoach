"""Graph of the agent."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph

from agent.nodes import (
    behaviour_analysis,
    caller_simulation,
    decide_phase,
    end_summary,
    entry_router,
    final_feedback,
    handover_command,
    onboarding,
    per_turn_feedback,
    route_after_decide_phase,
    route_after_end_summary,
    route_after_handover_command,
    route_after_onboarding,
    route_after_per_turn_feedback,
    scenario_setup,
    trainer_takeover,
    update_caller_profile,
)
from agent.nodes.onboarding import introduction
from agent.state import TrainingState

builder = StateGraph(TrainingState)

builder.add_node('onboarding', onboarding)
builder.add_node('scenario_setup', scenario_setup)
builder.add_node('handover_command', handover_command)
builder.add_node('trainer_takeover', trainer_takeover)
builder.add_node('caller_simulation', caller_simulation)
builder.add_node('behaviour_analysis', behaviour_analysis)
builder.add_node('update_caller_profile', update_caller_profile)
builder.add_node('decide_phase', decide_phase)
builder.add_node('per_turn_feedback', per_turn_feedback)
builder.add_node('end_summary', end_summary)
builder.add_node('final_feedback', final_feedback)
builder.add_node('introduction', introduction)


builder.add_conditional_edges(
    START,
    entry_router,
    {
        'onboarding': 'onboarding',
        'caller_simulation': 'caller_simulation',
        'behaviour_analysis': 'behaviour_analysis',
        'handover_command': 'handover_command',
        'trainer_takeover': 'trainer_takeover',
    },
)
builder.add_conditional_edges(
    'onboarding',
    route_after_onboarding,
    {
        'scenario_setup': 'scenario_setup',
        'end': END,
    },
)
builder.add_edge('scenario_setup', 'introduction')
builder.add_edge('introduction', 'caller_simulation')
builder.add_conditional_edges(
    'handover_command',
    route_after_handover_command,
    {
        'trainer_takeover': 'trainer_takeover',
        'behaviour_analysis': 'behaviour_analysis',
        'end': END,
    },
)
builder.add_edge('trainer_takeover', 'update_caller_profile')
builder.add_edge('caller_simulation', END)
builder.add_edge('behaviour_analysis', 'update_caller_profile')
builder.add_edge('update_caller_profile', 'decide_phase')
builder.add_conditional_edges(
    'decide_phase',
    route_after_decide_phase,
    {
        'per_turn_feedback': 'per_turn_feedback',
        'end_summary': 'end_summary',
        'caller_simulation': 'caller_simulation',
        'end': END,
    },
)
builder.add_conditional_edges(
    'per_turn_feedback',
    route_after_per_turn_feedback,
    {
        'end_summary': 'end_summary',
        'caller_simulation': 'caller_simulation',
    },
)
builder.add_conditional_edges(
    'end_summary',
    route_after_end_summary,
    {
        'final_feedback': 'final_feedback',
        'end': END,
    },
)
builder.add_edge('final_feedback', END)

memory = MemorySaver()
graph = builder.compile()
