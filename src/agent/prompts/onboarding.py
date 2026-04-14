"""Prompts for onboarding and scenario setup."""

PARSE_ONBOARDING = """
Extract structured scenario setup from the user input.

REQUIRED FIELDS
- category
- difficulty

OPTIONAL FIELDS
- language
- feedback_mode

RULES
- Do NOT infer or guess values apart from the language
- Infer language from the user input if not stated explicitly
- Only extract explicitly stated information
- If required fields are missing or invalid, set them to null

OUTPUT
Return all fields.

- missing_fields must contain missing or invalid required fields
- clarification_question must ask ONLY for missing required fields
- If nothing is missing, missing_fields must be empty and clarification_question null
- If you cannot identify the language, set it as missing_fields
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
