"""Prompts for onboarding and scenario setup."""

PARSE_ONBOARDING = """
EExtract structured scenario setup from the user input.

REQUIRED FIELDS
- category
- difficulty (integer 1–10)
- language

OPTIONAL FIELDS
- feedback_mode

LANGUAGE DETECTION
- Infer the language from the user input if possible.
- If the input is too short (e.g. < 3 meaningful words) or ambiguous (e.g. greetings like "Hi", "Ok"), set language = null.
- Only assign a language if confidence is high.
- Do not guess.

GENERAL RULES
- Only extract explicitly stated information (except for language, which may be inferred).
- Do NOT infer or assume category or difficulty.
- If a required field is missing or invalid, set it to null.

CLARIFICATION QUESTION RULES
- If required fields are missing:
  - Start with a short, polite sentence explaining that a few details are needed to begin the training.
  - Ask ONLY for the missing required fields.
  - Additionally include a short hint that feedback_mode can be specified (options: none, per_turn, final, both; default is "both").
  - Keep tone friendly and natural (not robotic).
  - Prefer a single concise sentence (max. two if needed).

- If nothing is missing:
  - missing_fields must be []
  - clarification_question must be null

EXAMPLE

Input: "Hi"
→ language = null

Clarification:
"To get started, I just need a few details: please specify the category, difficulty (1–10), and language. Optionally, you can also set the feedback mode (none, per_turn, final, both; default is 'both')."
"""


SCENARIO_SETUP = """
Create a short, realistic caller scenario (maximum 4 sentences).

Requirements:
- Describe only the caller’s situation, context, and reason for reaching out.
- Do NOT include any actions, thoughts, or responses of a counsellor.
- Do NOT include dialogue or direct speech.
- Write in third person.
- Focus on concrete details (situation, emotions, background).
- Keep it concise and plausible.

Difficulty guidance (1–10):
- Difficulty reflects how challenging the conversation will be for the coach.
- Consider factors such as emotional intensity, clarity of the issue, cooperativeness, and complexity.
- Low (1–3): clear issue, cooperative, low emotional distress.
- Medium (4–7): some ambiguity, moderate distress, mixed cooperativeness.
- High (8–10): high distress, volatile or withdrawn, complex or unclear situation.

CATEGORY
{category}

DIFFICULTY
{difficulty}
"""

INTRODUCTION = """
Welcome the learner to the coaching session.

Requirements:
- Keep the message concise and friendly
- Explain that `/handover` can be used at any time to let the trainer continue
- Mention the category and difficulty of the scenario
- Mention, how and when you provide feedback
- End by inviting the learner to begin

CATEGORY
{category}

DIFFICULTY
{difficulty}

FEEDBACK MODE
{feedback_mode}
"""
