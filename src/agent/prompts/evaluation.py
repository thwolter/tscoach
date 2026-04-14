"""Prompts for per-turn and final evaluation."""

LEARNER_EVALUATION = """
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


TRAINING_WRAP_UP = """
SCENARIO:
{scenario_description}

LANGUAGE:
{language}

CURRENT PHASE:
{phase}

CONVERSATION:
{formatted_history}

TASK:
Write a short closing wrap-up of the conversation and development.

FORMAT:
- Start with **Wrap-up:**
- Mention key progress from the beginning to the end in 2-3 short sentences
- End with a polite closing sentence

Keep it concise (max 90 words).
"""


EVALUATION_SUMMARY = """
SCENARIO:
{scenario_description}

LANGUAGE:
{language}

SUMMARY:
- empathy: {avg_empathy:.2f}
- question quality: {avg_question_quality:.2f}
- advice ratio: {advice_ratio:.2f}
- overall score: {overall_score:.2f}
- performance band: {performance_band}

TASK:
Provide concise end-of-training feedback with:
- strengths
- improvements
- concrete suggestions
- a short closing wrap-up to end the training nicely

FORMAT:
- Start with **Summary:** (1 short sentence)
- Then "Result:" (1 short sentence based on score and performance band - without mentioning score and the band)
- Then 1-2 short bullet points with concrete next-step suggestions

Keep it concise (max 120 words).
"""


TURN_FEEDBACK = """
You are a trainer for telephone counselling.

SCENARIO:
{scenario_description}

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

Start with **Feedback** and keep it concise (max 80 words).
"""
