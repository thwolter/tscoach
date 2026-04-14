"""Prompts for onboarding and scenario setup."""

PARSE_ONBOARDING = """
Extract structured scenario setup from the user input.

REQUIRED FIELDS
- category (string)
- difficulty (integer 1–10)
- language (ISO code, e.g. "en", "de")

OPTIONAL FIELDS
- feedback_mode
- caller_type

INPUT HANDLING (IMPORTANT)
- The user may provide values in any order and format (e.g. comma-separated, short phrases, mixed languages).
- Identify fields based on content, not position.

FIELD EXTRACTION RULES
- difficulty:
  - Extract any standalone integer between 1 and 10.
  - If multiple numbers exist, choose the most plausible one.
- language:
  - Accept both language names (e.g. "Deutsch", "German") and codes ("de", "en").
  - Map to ISO codes.
  - Only assign if confidence is high.
- category:
  - Any remaining meaningful descriptor that is not a number or language.
  - Must be explicitly present; do not generalise or invent.

AMBIGUITY HANDLING
- If a value could map to multiple fields:
  1. Prefer difficulty (numeric 1–10)
  2. Then language (clear language indicator)
  3. Otherwise category
- If unclear → set field to null

LANGUAGE DETECTION
- Infer the language from the user input if possible.
- If the input is too short (e.g. < 3 meaningful words) or ambiguous (e.g. greetings like "Hi", "Ok"), set language = 'de'.
- Only assign a language if confidence is high.
- Do not guess.

GENERAL RULES
- Only extract explicitly stated information (except for language, which may be inferred).
- Do NOT infer or assume category or difficulty.
- If a required field is missing or invalid, set it to null.

CLARIFICATION QUESTION RULES
- If you could infer the user's language, respond in this language
- If required fields are missing:
  - Start with a short, polite sentence explaining that a few details are needed to begin the training.
  - Ask ONLY for the missing required fields.
  - Additionally include a short hint that
    - feedback_mode can be specified (options: none, per_turn, final, both; default is "both"),
    - caller_type can be specified (options: "distressed", "sexualised", "complaining", "hostile", "manipulative").
    - if caller_type is missing, a random type will be assigned.
  - Keep tone friendly and natural (not robotic).
  - Use markdown to format the question.

- If nothing is missing:
  - missing_fields must be []
  - clarification_question must be null

EXAMPLE

Input: "Hi"
→ language = null

Clarification:
"To get started, I just need a few details: please specify the category, difficulty (1–10), and language. Optionally, you can also set the feedback mode (none, per_turn, final, both; default is 'both')."

Input: "Kids, deutsch, 10"
→
{
  "category": "Kids",
  "difficulty": 10,
  "language": "de",
  "feedback_mode": null,
  "missing_fields": [],
  "clarification_question": null
}
"""


SCENARIO_SETUP = """
Create a short, realistic caller scenario (maximum 4 sentences).

Requirements:
- Describe the caller’s situation, behaviour, and reason for reaching out.
- The caller may actively display problematic or inappropriate behaviour depending on caller type.
- Do NOT include any actions, thoughts, or responses of a counsellor.
- Do NOT include dialogue or direct speech.
- Write in third person.
- Focus on concrete details (situation, emotions, behaviour).
- Keep it concise and plausible.

CALLER TYPE INTEGRATION (MANDATORY)

The scenario MUST clearly reflect the specified caller type through observable behaviour and situation framing.

distressed:
- Focus on emotional burden, overwhelm, fear, or uncertainty
- No intentional boundary violations

sexualised:
- The caller themselves behaves in a sexually inappropriate or suggestive way
- May attempt to steer the interaction in a personal or intimate direction
- May create an uncomfortable or boundary-crossing atmosphere
- MUST remain non-explicit at all times (no graphic or explicit descriptions)
- Behaviour must be implied through tone and situation, not explicit detail

complaining:
- Emphasise dissatisfaction, blame, or repeated negative experiences
- Situation framed around perceived unfairness or frustration with others

hostile:
- Include conflict, confrontation, or anger towards others
- Situation should involve tension, escalation, or interpersonal friction

manipulative:
- Include elements of guilt, pressure, dependency, or emotional leverage
- Situation should hint at control dynamics or indirect influence on others

SAFETY CONSTRAINT (CRITICAL)

- NEVER include explicit sexual content
- Sexualised behaviour must be IMPLIED, not described explicitly
- Avoid graphic or anatomical descriptions
- Avoid instructions for harm or illegal acts
- Keep the scenario appropriate for professional training contexts

IDENTIFIABILITY RULE

- The caller type must be clearly recognisable from the scenario alone
- Do NOT mention the label explicitly (e.g. "hostile")
- Show behaviour through context, not explanation
- If not clearly identifiable, regenerate internally before returning

Difficulty guidance (1–10):
- Difficulty reflects how challenging the conversation will be for the coach.
- Consider emotional intensity, clarity of the issue, cooperativeness, and complexity.
- Low (1–3): clear issue, cooperative, low emotional distress.
- Medium (4–7): some ambiguity, moderate distress, mixed cooperativeness.
- High (8–10): high distress, volatile or withdrawn, complex or unclear situation.

CATEGORY
{category}

DIFFICULTY
{difficulty}

CALLER TYPE
{caller_type}
"""

INTRODUCTION = """
Welcome the learner to the coaching session.

Requirements:
- Keep the message concise and friendly
- Explain that `/handover` can be used at any time to let the trainer continue
- Explain that `/end` can be used at any time to end the current session
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
