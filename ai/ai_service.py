"""
ai/ai_service.py
----------------
Real Gemini AI connection for AI Study Buddy.

Uses the official google-genai SDK (v2+).
Credentials are read from environment variables only — never hardcoded.

Usage:
    from ai.ai_service import generate_ai_response
    reply = generate_ai_response(user_prompt, conversation_history)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the project root (the directory that contains app.py and .env)
# regardless of the working directory Streamlit was launched from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _get_api_key() -> str:
    """
    Read GEMINI_API_KEY from the environment.
    Returns an empty string if not configured (caller handles the missing case).
    """
    return os.environ.get("GEMINI_API_KEY", "").strip()


def is_ai_available() -> bool:
    """Return True if the Gemini API key is present in the environment."""
    return bool(_get_api_key())


def generate_ai_response(
    user_prompt: str,
    conversation_history: list[dict] | None = None,
    system_instruction: str | None = None,
) -> str:
    """
    Send a prompt to the Gemini API and return the generated text.

    Args:
        user_prompt:          The student's question or message.
        conversation_history: Optional list of prior turns as
                              [{"role": "user"|"model", "text": "..."}].
                              Used to maintain context across a session.
        system_instruction:   Optional system-level instruction that shapes
                              the AI's behaviour. Defaults to the study
                              assistant persona defined in ai/prompts.py.

    Returns:
        The AI's reply as a plain string.

    Raises:
        EnvironmentError: If GEMINI_API_KEY is not configured.
        RuntimeError:     If the API call fails for any reason.
    """
    api_key = _get_api_key()
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example to .env and add your key from "
            "https://aistudio.google.com/app/apikey"
        )

    # Import here so the module loads cleanly even if google-genai is absent
    try:
        import google.genai as genai
        from google.genai import types
    except ImportError:
        raise RuntimeError(
            "google-genai is not installed. "
            "Run: pip install google-genai"
        )

    # Use the study-assistant persona by default
    if system_instruction is None:
        from ai.prompts import STUDY_ASSISTANT_SYSTEM_INSTRUCTION
        system_instruction = STUDY_ASSISTANT_SYSTEM_INSTRUCTION

    # Build the contents list from conversation history + new user message
    contents: list = []
    if conversation_history:
        for turn in conversation_history:
            role = turn.get("role", "user")
            text = turn.get("text", "")
            if text:
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=text)],
                    )
                )

    # Append the current user message
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_prompt)],
        )
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )

        # response.text is None when the model blocks the output (safety filter).
        # Surface this clearly instead of returning a silent empty string.
        if response.text is None:
            finish = ""
            try:
                finish = response.candidates[0].finish_reason.name
            except Exception:
                pass
            raise RuntimeError(
                f"The model returned no text "
                f"{'(finish_reason: ' + finish + ')' if finish else ''}. "
                "This usually means the response was blocked by a safety filter. "
                "Try rephrasing your question."
            )
        return response.text.strip()

    except RuntimeError:
        raise  # already formatted above
    except Exception as exc:
        # Surface a clean error message — never expose the raw key
        msg = str(exc)
        if "API_KEY" in msg.upper() or "INVALID_ARGUMENT" in msg:
            raise RuntimeError(
                "Invalid API key. Please check your GEMINI_API_KEY in .env."
            ) from exc
        if "QUOTA" in msg.upper() or "429" in msg:
            raise RuntimeError(
                "API quota exceeded. Please wait a moment and try again."
            ) from exc
        if "503" in msg or "UNAVAILABLE" in msg.upper():
            raise RuntimeError(
                "Gemini is temporarily overloaded (503). Please try again in a few seconds."
            ) from exc
        raise RuntimeError(f"AI service error: {msg}") from exc


# ── AI feature implementations ────────────────────────────────────────────────

def summarize_notes(notes_text: str) -> str:
    """
    Summarize study notes using Gemini.

    Args:
        notes_text: Raw text extracted from a PDF or pasted by the student.

    Returns:
        A structured bullet-point summary as a markdown string.
    """
    from ai.prompts import prompt_summarize_notes
    prompt = prompt_summarize_notes(notes_text)
    return generate_ai_response(user_prompt=prompt, system_instruction=" ")


def generate_mcqs(topic: str, notes_text: str, num_questions: int = 5) -> list[dict]:
    """
    Generate multiple-choice questions using Gemini.

    Args:
        topic:         Subject or topic name for the quiz.
        notes_text:    Study material to base the questions on.
        num_questions: How many MCQs to generate (1–20).

    Returns:
        A list of dicts, each with keys:
          - question (str)
          - options  (list[str])  — four labelled options, e.g. "A) ..."
          - answer   (str)        — correct letter, e.g. "A"
    """
    import re
    from ai.prompts import prompt_generate_mcqs

    prompt = prompt_generate_mcqs(topic, notes_text, num_questions)
    raw = generate_ai_response(user_prompt=prompt, system_instruction=" ")

    questions: list[dict] = []
    # Split on blank lines or "Q:" markers
    blocks = re.split(r"\n{2,}|\n(?=Q\d*[:.])", raw.strip())

    for block in blocks:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        if not lines:
            continue

        q_text = ""
        options: list[str] = []
        answer = ""

        for line in lines:
            if re.match(r"^Q\d*[:.]?\s*", line, re.IGNORECASE):
                q_text = re.sub(r"^Q\d*[:.]?\s*", "", line, flags=re.IGNORECASE).strip()
            elif re.match(r"^[A-D][.)]\s", line):
                options.append(line)
            elif re.match(r"^Answer\s*[:.]?\s*[A-D]", line, re.IGNORECASE):
                answer = re.search(r"[A-D]", line, re.IGNORECASE)
                answer = answer.group(0).upper() if answer else ""

        if q_text and len(options) >= 2:
            questions.append({"question": q_text, "options": options, "answer": answer})

    return questions


def generate_flashcards(notes_text: str, num_cards: int = 10) -> list[dict]:
    """
    Generate flashcard pairs using Gemini.

    Args:
        notes_text: Study material to extract flashcards from.
        num_cards:  How many front/back pairs to generate.

    Returns:
        A list of dicts, each with keys:
          - front (str) — term or question
          - back  (str) — definition or answer
    """
    import re
    from ai.prompts import prompt_generate_flashcards

    prompt = prompt_generate_flashcards(notes_text, num_cards)
    raw = generate_ai_response(user_prompt=prompt, system_instruction=" ")

    cards: list[dict] = []
    # Split on blank lines between cards
    blocks = re.split(r"\n{2,}", raw.strip())

    for block in blocks:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        front = back = ""
        for line in lines:
            if re.match(r"^FRONT\s*[:.]?\s*", line, re.IGNORECASE):
                front = re.sub(r"^FRONT\s*[:.]?\s*", "", line, flags=re.IGNORECASE).strip()
            elif re.match(r"^BACK\s*[:.]?\s*", line, re.IGNORECASE):
                back = re.sub(r"^BACK\s*[:.]?\s*", "", line, flags=re.IGNORECASE).strip()
        if front and back:
            cards.append({"front": front, "back": back})

    return cards


def analyze_weak_topics(quiz_results: list[dict]) -> str:
    """
    Analyze quiz results and return AI-powered study recommendations.

    Args:
        quiz_results: List of dicts, each with keys:
                      - topic     (str)
                      - score     (int)
                      - max_score (int)

    Returns:
        A markdown string with weak-topic analysis and study advice.
    """
    from ai.prompts import prompt_analyze_weak_topics

    # Format the results into readable text for the prompt
    lines = []
    for r in quiz_results:
        pct = round(r["score"] / r["max_score"] * 100) if r.get("max_score") else 0
        lines.append(f"- {r['topic']}: {r['score']}/{r['max_score']} ({pct}%)")

    results_text = "\n".join(lines) if lines else "No quiz results available yet."
    prompt = prompt_analyze_weak_topics(results_text)
    return generate_ai_response(user_prompt=prompt, system_instruction=" ")
