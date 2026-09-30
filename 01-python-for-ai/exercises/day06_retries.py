"""Day 6 — Retries with exponential backoff (production LLM calls need this).

Run:  uv run pytest tests/test_day06_retries.py -v

LLM APIs fail ALL THE TIME in normal operation: rate limits (429), overloaded
servers (529/503), timeouts. A production app retries the "temporary" failures
with increasing waits between attempts — and fails fast on "your fault" errors.

    attempt 1 ──► 503 ──wait 1s──► attempt 2 ──► 429 ──wait 2s──► attempt 3 ──► 200 ✅

Testability trick: `request_with_retry` takes a `sleep` function as a parameter.
Real code passes time.sleep; tests pass a fake that just records the waits,
so the test suite runs instantly instead of actually sleeping.
"""

import time
from collections.abc import Callable

import httpx

RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}


# ---------------------------------------------------------------------------
# Exercise 1 — decide what to do with a status code
# ---------------------------------------------------------------------------
def classify_status(status_code: int) -> str:
    """Return one of:
      "ok"     for 2xx
      "retry"  for codes in RETRYABLE_STATUS
      "fail"   for everything else (400, 401, 404, 422, ...)
    """
    if status_code in (200,201,204):
        return "ok"
    elif status_code in RETRYABLE_STATUS:
        return "retry"
    else:
        return "fail"



# ---------------------------------------------------------------------------
# Exercise 2 — how long to wait before the next attempt
# ---------------------------------------------------------------------------
def backoff_delay(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Exponential backoff: base * 2**attempt, but never more than `cap`.

    attempt is 0-based:  attempt 0 -> 1s, 1 -> 2s, 2 -> 4s, 3 -> 8s, ... capped at 30s.

    (Real systems also add random "jitter" so thousands of clients don't all
    retry at the same instant. We skip it here to keep tests deterministic.)
    """
    
    


# ---------------------------------------------------------------------------
# Exercise 3 — respect the server's Retry-After header
# ---------------------------------------------------------------------------
def retry_after_seconds(response: httpx.Response) -> float | None:
    """Return the Retry-After header as a float number of seconds, or None.

    Return None if the header is missing OR isn't a number
    (it can legally be an HTTP date — we don't handle that, just ignore it).

    Hint: response.headers.get("Retry-After"); float("abc") raises ValueError.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 4 — put it together
# ---------------------------------------------------------------------------
def request_with_retry(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    max_attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs,
) -> httpx.Response:
    """Send the request, retrying temporary failures. Return the successful response.

    For attempt in 0 .. max_attempts-1:
      1. Send:  client.request(method, url, **kwargs)
         - If it raises httpx.TransportError (timeout, connection failure):
             retry — unless this was the last attempt, then re-raise it.
      2. classify_status(response.status_code):
         - "ok"    -> return the response
         - "fail"  -> response.raise_for_status()  (no retry — it would fail again)
         - "retry" -> if last attempt: response.raise_for_status()
                      else wait, then loop
      3. How long to wait: retry_after_seconds(response) if the server gave one,
         otherwise backoff_delay(attempt). After a TransportError there is no
         response, so use backoff_delay(attempt).
         Call sleep(seconds) — never time.sleep directly (tests must stay fast).

    Tip: `raise` on its own inside an `except` block re-raises the caught error.
    """
    raise NotImplementedError
