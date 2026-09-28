"""Day 3 — Pydantic basics: turning messy LLM text into typed, validated data.

Run:  uv run pytest tests/test_day03_pydantic_basics.py -v

Scenario: you ask an LLM to classify a support ticket and reply in JSON.
LLMs are NOT reliable JSON producers — they wrap output in ```json fences,
add chatty sentences, return "3" instead of 3, or invent categories.
Your job: parse and validate so the rest of the app only ever sees clean data.

Read first:  https://docs.pydantic.dev/latest/concepts/models/
             https://docs.pydantic.dev/latest/concepts/fields/
"""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError


# ---------------------------------------------------------------------------
# Exercise 1 — define the model
# ---------------------------------------------------------------------------
class TicketClassification(BaseModel):
    """What the LLM must return for each ticket.

    TODO: declare these fields (type hints + Field(...) constraints):
      - category:  only "bug", "feature" or "question"          (hint: Literal)
      - priority:  int from 1 to 5 inclusive                    (hint: Field(ge=..., le=...))
      - summary:   str, 5 to 200 characters                     (hint: min_length / max_length)
      - tags:      list of str, defaults to an empty list

    Note: unlike a plain class or dataclass, `tags: list[str] = []` is SAFE in
    Pydantic — it copies the default for each instance. (Day 1 bug can't happen.)
    """


# ---------------------------------------------------------------------------
# Exercise 2 — strip the noise around the JSON
# ---------------------------------------------------------------------------
def extract_json(raw: str) -> str:
    """Return just the JSON object text from an LLM reply.

    LLM replies look like any of these:
        '{"category": "bug", ...}'
        '```json\\n{"category": "bug", ...}\\n```'
        'Sure! Here is the classification:\\n{"category": "bug", ...}\\nHope that helps.'

    Return the substring from the FIRST "{" to the LAST "}" (inclusive).
    Raise ValueError if there is no "{...}" in the text.

    Hint: str.find() / str.rfind() return -1 when not found.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 3 — parse + validate
# ---------------------------------------------------------------------------
def parse_classification(raw: str) -> TicketClassification:
    """Extract the JSON from `raw` and return a validated TicketClassification.

    Let pydantic.ValidationError propagate if the data is invalid.
    Hint: TicketClassification.model_validate_json(...)
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 4 — never crash the app
# ---------------------------------------------------------------------------
def safe_parse(raw: str) -> TicketClassification | None:
    """Like parse_classification, but return None if the reply is unusable
    (no JSON found, or JSON fails validation).

    Catch ONLY the specific exceptions you expect — no bare `except:`
    (remember the Day 1 review!).
    """
    raise NotImplementedError
