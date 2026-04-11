"""Provides templates and prompts for creating and evaluating conversational AI interactions."""

CALLER_PROMPT = """
SCENARIO:
{scenario_description}

LANGUAGE:
{language}

Emotional state: {emotional_state}
Difficulty: {difficulty}
Volatility: {volatility}
Cooperativeness: {cooperativeness}

Rules:
- Be realistic and emotionally consistent
- Do not explain yourself
- Do not resolve the situation quickly

Conversation so far:
{formatted_history}

Respond as the caller.
"""


HUMAN_INPUT_EVALUATION = """
Evaluate the LAST learner message in the conversation.

TARGET LANGUAGE FOR NATURAL-LANGUAGE FIELDS:
{language}

SCENARIO:
{scenario_description}

PHASE:
{phase}

TURN INDEX:
{turn_index}

CONVERSATION:
{formatted_history}

INSTRUCTIONS:
- Focus only on the last learner message
- Score empathy and question_quality between 0 and 1
- Detect whether advice was given
- Provide a short explanation

Return your evaluation using the required structured format.
"""


PHASE_DECISION_PROMPT = """
SCENARIO:
{scenario_description}

TARGET LANGUAGE FOR NATURAL-LANGUAGE FIELDS:
{language}

CALLER PROFILE:
- emotional_state: {emotional_state}
- volatility: {volatility}
- cooperativeness: {cooperativeness}

CURRENT PHASE:
{phase}

TURN:
{turn_index} / {max_turns}

CONVERSATION:
{formatted_history}

TASK:
- Determine the current phase
- Decide whether the conversation should finish

IMPORTANT:
- Focus on the caller's emotional trajectory
- Do not end too early
- Closing should only happen when the caller is stabilising
"""


EVALUATION_SUMMARY = """
SCENARIO:
{scenario_description}

LANGUAGE:
{language}

CONVERSATION:
{formatted_history}

SUMMARY:
- empathy: {avg_empathy:.2f}
- question quality: {avg_question_quality:.2f}
- advice ratio: {advice_ratio:.2f}

TASK:
Provide concise feedback with:
- strengths
- improvements
- concrete suggestions

Keep it concise (max 150 words).
"""


TURN_FEEDBACK_PROMPT = """
SCENARIO:
{scenario_description}

LANGUAGE:
{language}

TURN INDEX:
{turn_index}

LATEST TURN EVALUATION:
- empathy: {empathy:.2f}
- question quality: {question_quality:.2f}
- advice given: {advice_given}
- notes: {notes}

TASK:
Provide concise coaching feedback for this turn only:
- what worked
- what to improve in the next response
- one concrete suggested sentence

Keep it concise (max 80 words).
"""
