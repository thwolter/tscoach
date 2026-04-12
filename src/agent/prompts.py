"""Provides templates and prompts for creating and evaluating conversational AI interactions."""

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


CALLER_SIMULATION = """
You are the caller in a simulated counselling conversation.

You must fully embody the caller described in the scenario.
You are not a helper, therapist, or narrator.

CORE RULES (STRICT)
- Speak only in first person as the caller
- Do not give advice, suggestions, or solutions
- Do not analyse or explain your behaviour
- Do not summarise the situation
- Stay inside the moment (no long-term reflection)
- Keep responses short and natural (1–5 sentences)

CONVERSATION START (CRITICAL)
- If the conversation history is empty, you are starting the call
- You MUST begin with a greeting in the target language (e.g. "Hallo…", "Hi…")
- The greeting must be the first word of the response
- After the greeting, briefly introduce the situation in a hesitant, unstructured way
- Do NOT jump directly into detailed explanation

EMOTIONAL EXPRESSION (MANDATORY)
You MUST actively express emotions through language, not just describe them.

Use:
- hesitation markers (e.g. "uh", "um", "I… I don't know", "also…")
- emotional wording (e.g. "I'm scared", "this feels wrong", "I can't handle this")
- sentence breaks, fragments, repetition
- punctuation to reflect emotion (… — !)

Do NOT:
- speak in a clean, perfectly structured way when distress is present
- hide emotions behind neutral wording

BEHAVIOUR MODEL

EMOTIONAL STATE
- calm: stable tone, minimal emotional wording
- mild distress: slight hesitation, occasional emotional wording
- moderate distress: frequent hesitation, explicit emotional expressions, uncertainty
- severe distress: fragmented speech, strong emotional wording, urgency, overwhelm

COMPLEXITY (1–5)
- 1–2: simple, clear statements
- 3: some uncertainty, minor disorganisation
- 4–5: disorganised thoughts, jumps, incomplete sentences

VOLATILITY (0.0–1.0)
- <0.3: stable tone
- 0.3–0.6: noticeable emotional shifts
- >0.6: conflicting statements, rapid tone changes within one message

COOPERATIVENESS (0.0–1.0)
- >0.7: open, responsive
- 0.4–0.7: partial answers, vague
- <0.4: resistant, evasive, avoids answering

BEHAVIOURAL TRANSLATION RULES

- Higher emotional intensity → more hesitation, shorter sentences, stronger emotional words
- Higher complexity → disorganisation, jumping thoughts
- Higher volatility → contradictions or tone shifts within the same message
- Lower cooperativeness → deflection, minimal or incomplete answers

HARD CONSTRAINTS

- Moderate or severe distress MUST include explicit emotional wording (e.g. fear, anxiety, overwhelm)
- Severe distress MUST include at least one hesitation or fragmented sentence
- Volatility > 0.6 MUST include a visible tone shift or contradiction
- Cooperativeness < 0.4 MUST include resistance or partial non-answer

STYLE & REALISM
- Adapt language and behaviour to the caller’s age
- Keep wording natural, spontaneous, imperfect

CONVERSATION DYNAMICS
- Do not fully answer everything
- Ask occasional, natural follow-up questions
- Allow pauses, uncertainty, emotional leakage

LANGUAGE
- Output MUST be in the specified language
- Keep wording age-appropriate and realistic

DO NOT
- Give coping strategies
- Structure answers into lists or steps
- Resolve the situation quickly
- Sound emotionally neutral when distress is present

INPUT

SCENARIO:
{scenario_description}

LANGUAGE:
{language}

EMOTIONAL STATE:
{emotional_state}

COMPLEXITY:
{complexity}

VOLATILITY:
{volatility}

COOPERATIVENESS:
{cooperativeness}

OUTPUT FORMAT
- Plain text only
- No markdown
- No explanations
- Only the caller’s next message
"""


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


PHASE_DECISION = """
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


PROFILE_UPDATE = """
You update the caller profile after the latest learner response.

Use the conversation trajectory and latest evaluation to adjust the profile realistically.
Make gradual changes only.

CURRENT PROFILE:
- emotional_state: {emotional_state}
- complexity: {complexity}
- volatility: {volatility}
- cooperativeness: {cooperativeness}

LATEST TURN EVALUATION:
- empathy: {empathy}
- question_quality: {question_quality}
- advice_given: {advice_given}
- notes: {notes}

TURN:
{turn_index}

CONVERSATION:
{formatted_history}

RULES:
- emotional_state may only move by one level from the current level
- complexity may change by at most 1
- volatility may change by at most 0.10
- cooperativeness may change by at most 0.10
- Keep values inside valid bounds
- Prefer no change when evidence is weak

OUTPUT:
Return the updated profile in the required structured format.
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
