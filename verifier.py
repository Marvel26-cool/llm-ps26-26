"""Safely evaluate the LLM's arithmetic expression with sympy."""
import re
from sympy import sympify, SympifyError


def _extract_numbers(text):
    if not text:
        return []
    cleaned = str(text).replace(",", "")
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", cleaned)]


def verify_expression(expression, final_answer):
    if not expression or len(expression) > 200:
        return None
    try:
        value = float(sympify(expression, evaluate=True))
    except (SympifyError, TypeError, ValueError):
        return {
            "ok": False,
            "expression": expression,
            "reason": "Could not evaluate the expression.",
        }
    nums = _extract_numbers(final_answer)
    if not nums:
        return {
            "ok": False,
            "expression": expression,
            "reason": "No number found in the final answer to compare.",
        }
    if any(abs(value - n) < 1e-6 for n in nums):
        return {"ok": True, "expression": expression, "computed": value}
    return {
        "ok": False,
        "expression": expression,
        "computed": value,
        "reason": (
            f"Expression gives {value:g}, but final answer mentions {nums}."
        ),
    }