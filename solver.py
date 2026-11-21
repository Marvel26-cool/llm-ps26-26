"""LLM logic using the modern google-genai SDK + gemini-3.5-flash."""
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from verifier import verify_expression

load_dotenv()
_api_key = os.getenv("GEMINI_API_KEY")
if not _api_key:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

_client = genai.Client(api_key=_api_key)

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.5-flash"


class MathSolverError(Exception):
    """Raised when the LLM fails or returns an unusable response."""


PROMPT_TEMPLATE = """You are a patient, expert math tutor for school and college students.

Solve the given word problem carefully and show every step.

Return ONLY valid JSON (no markdown fences, no extra text) with this EXACT structure:
{{
  "steps": [
    {{"title": "Step 1: <short title>", "detail": "<clear explanation of what you did and why>"}}
  ],
  "final_answer": "<complete final answer with units, e.g. '8 apples' or '600 rupees'>",
  "verification_expression": "<single arithmetic expression using only numbers and + - * / ( ) that computes the numeric final answer, or null if not possible>"
}}

Rules:
- Steps must be logically ordered and understandable to a 10th-grade student.
- Use simple English.
- Do NOT skip any calculation.
- If the input is not a math word problem, return empty "steps", null "verification_expression", and a "final_answer" starting with "This doesn't look like a math word problem".

Word Problem:
{problem}
"""


def _call_model(model_name, prompt):
    response = _client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
            http_options=types.HttpOptions(timeout=30000),
        ),
    )
    return response.text


def solve_problem(problem):
    if not problem or not problem.strip():
        raise MathSolverError("Problem text is empty.")

    prompt = PROMPT_TEMPLATE.format(problem=problem.strip())

    raw = None
    last_err = None
    for model_name in (PRIMARY_MODEL, FALLBACK_MODEL):
        try:
            raw = _call_model(model_name, prompt)
            break
        except Exception as e:
            last_err = e
            msg = str(e)
            if (
                "429" in msg
                or "503" in msg
                or "RESOURCE_EXHAUSTED" in msg
                or "UNAVAILABLE" in msg
            ):
                continue
            raise MathSolverError(f"LLM request failed: {e}")

    if raw is None:
        raise MathSolverError(f"LLM request failed on both models: {last_err}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise MathSolverError("Model returned non-JSON output. Please try again.")

    if not isinstance(data, dict):
        raise MathSolverError("Model returned unexpected JSON.")

    steps = data.get("steps") or []
    final_answer = (data.get("final_answer") or "").strip()
    ver_expr = data.get("verification_expression")

    if not final_answer:
        raise MathSolverError("Model did not produce a final answer. Try rephrasing.")

    verified = verify_expression(ver_expr, final_answer) if ver_expr else None

    return {
        "steps": steps,
        "final_answer": final_answer,
        "verification_expression": ver_expr,
        "verified": verified,
    }