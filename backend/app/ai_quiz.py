
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def generate_quiz(
    skill_name: str,
    difficulty: str = "Intermediate",
    topic: str = "",
    count: int = 5,
) -> list[dict]:
    """Generate multiple-choice questions using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from backend/.env")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Create exactly {count} original multiple-choice quiz questions.

Skill: {skill_name}
Topic: {topic or skill_name}
Difficulty: {difficulty}

Requirements:
- Each question must test knowledge of the requested skill.
- Provide exactly four distinct answer options.
- There must be exactly one correct answer.
- correct_index must be an integer from 0 to 3.
- Give a concise explanation of the correct answer.
- Do not repeat questions.

Return JSON in this exact format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Why this answer is correct"
    }}
  ]
}}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    try:
        data = json.loads(response.text or "")
        questions = data["questions"]

        if len(questions) != count:
            raise ValueError("Gemini returned an unexpected number of questions.")

        for question in questions:
            if not isinstance(question.get("question"), str):
                raise ValueError("Invalid question text.")

            options = question.get("options")
            answer = question.get("correct_index")

            if (
                not isinstance(options, list)
                or len(options) != 4
                or not all(isinstance(option, str) for option in options)
                or not isinstance(answer, int)
                or isinstance(answer, bool)
                or answer not in range(4)
            ):
                raise ValueError("Gemini returned invalid answer options.")

            if not isinstance(question.get("explanation"), str):
                raise ValueError("Invalid explanation.")

        return questions

    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("Gemini returned an invalid quiz response.") from exc
