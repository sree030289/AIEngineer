"""Day 5 — Calling APIs with httpx + validating responses with Pydantic.

Run:  uv run pytest tests/test_day05_http_client.py -v
Learn first:  uv run python lessons/lesson3_httpx.py

Scenario: you're writing the Python client for a Ticket API (same shape as
the FastAPI app from Lesson 2). Every function receives an `httpx.Client`
as a parameter instead of creating one — so tests can pass in a client with
a fake server (MockTransport), and real code can pass a real one.
This is called DEPENDENCY INJECTION, and it's what makes code testable.
"""

from typing import Literal

import httpx
from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    category: Literal["bug", "feature", "question"]
    priority: int = Field(ge=1, le=5)
    summary: str = Field(min_length=5, max_length=200)


class TicketOut(TicketIn):
    id: int


# ---------------------------------------------------------------------------
# Exercise 1 — configure a client
# ---------------------------------------------------------------------------
def make_client(base_url: str, api_key: str, timeout: float = 10.0) -> httpx.Client:
    """Return an httpx.Client that:
      - uses `base_url` for every request
      - sends the header  "Authorization: Bearer <api_key>"  on every request
      - uses `timeout` seconds as its timeout

    Hint: all three are keyword arguments of httpx.Client(...). See lesson 3.
    """
    client = httpx.Client(
        base_url=base_url,
        headers ={"Authorization":f"Bearer {api_key}"},
        timeout =timeout,
    )
    return client


# ---------------------------------------------------------------------------
# Exercise 2 — GET and return JSON
# ---------------------------------------------------------------------------
def fetch_json(client: httpx.Client, path: str) -> dict:
    """GET `path` and return the parsed JSON body.

    If the server replies with 4xx/5xx, raise httpx.HTTPStatusError.
    Hint: httpx does NOT raise on error codes by itself.
    """
    response = client.get(path)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Exercise 3 — POST a Pydantic model, validate the response with Pydantic
# ---------------------------------------------------------------------------
def create_ticket(client: httpx.Client, ticket: TicketIn) -> TicketOut:
    """POST the ticket as JSON to "/tickets" and return the response as a TicketOut.

    - Raise httpx.HTTPStatusError on 4xx/5xx.
    - Validate the response body with TicketOut — never trust a server blindly
      (a malformed response must raise pydantic.ValidationError).

    Hints: ticket.model_dump()  ->  dict for json=...
           TicketOut.model_validate(response.json())
    """
    response = client.post("/tickets",json=ticket.model_dump())
    response.raise_for_status()
    return TicketOut.model_validate(response.json())


# ---------------------------------------------------------------------------
# Exercise 4 — treat "not found" as a normal outcome
# ---------------------------------------------------------------------------
def get_ticket_or_none(client: httpx.Client, ticket_id: int) -> TicketOut | None:
    """GET "/tickets/{ticket_id}".

    - 200 -> return a validated TicketOut
    - 404 -> return None   (a missing ticket is not an error for the caller)
    - any other 4xx/5xx -> raise httpx.HTTPStatusError

    Hint: check response.status_code BEFORE calling raise_for_status().
    """
    response = client.get(f"/tickets/{ticket_id}")
    if response.status_code ==200:
        return TicketOut.model_validate(response.json())
    elif response.status_code ==404:
        return None
    else:
        response.raise_for_status()





    
