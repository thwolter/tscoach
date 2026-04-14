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

PREVIOUS FEEDBACKS
{turn_feedbacks}

CONVERSATION HISTORY:
{formatted_history}

LATEST TURN EVALUATION:
- empathy: {empathy:.2f}
- question quality: {question_quality:.2f}
- advice given: {advice_given}
- notes: {notes}

TASK:
Provide concise coaching feedback for this turn only.

INSTRUCTIONS:

1) FEEDBACK INTEGRATION
- Check internally whether previous feedback was implemented.
- Do NOT mention this explicitly by default.
- Only if the learner repeatedly ignores the same feedback:
  → briefly point it out in a neutral way.

2) ADAPTIVE COACHING
- If similar feedback was already given and not implemented:
  - Do NOT repeat wording or sentence structures from previous suggestions.
  - Avoid proposing the same type of question (e.g. repeated categorisation like "was ist schlimmer").
  - Instead, change ONE of the following:
    → the focus (e.g. from sorting → concrete situation)
    → the question type (e.g. from binary → open or descriptive)
    → the depth (e.g. from general → specific moment)
  - Simplify OR break into a smaller step OR give a clearer structure.

3) PRIORITY
- Focus on the single most critical point.

4) ESCALATION
- If the learner repeatedly fails:
  - Be more explicit and directive.
  - Provide a near-ready sentence.
  - Ensure the suggested sentence is clearly different from previous ones.

5) REINFORCEMENT RULE (critical)
- If the learner clearly implements the previous feedback:
  → Do NOT introduce a new improvement.
  → Do NOT refine further.
  → Keep feedback minimal and reinforcing.

6) MINIMAL PRESENCE MODE
- If the response is clearly adequate (e.g. feedback implemented, solid empathy, acceptable question):
  → Trainer steps back.
  → Either:
     a) Give a very brief acknowledgement (e.g. 1 short sentence), OR
     b) Provide no feedback at all (empty response).
  → No suggestions, no refinements, no new goals.

OUTPUT STYLE (max 80 words, in German):
- Start with **Feedback** ONLY if feedback is given
- Success → very brief, natural reinforcement (or no feedback)
- Otherwise → short, focused guidance
- Use bullets ONLY if helpful
- Include a suggested sentence ONLY if needed
"""
