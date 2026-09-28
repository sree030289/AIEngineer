"""Lesson 2 — FastAPI: build an API where Pydantic models ARE the contract.

Start the server (auto-reloads when you save this file):
    uv run fastapi dev lessons/lesson2_fastapi.py

Then open:  http://127.0.0.1:8000/docs   <- interactive Swagger UI, generated for free

You already know this world from the other side (Postman, API tests).
Here you're BUILDING the API your tests would hit.
"""

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Ticket Service", version="0.1.0")


# ---------------------------------------------------------------------------
# 1. Pydantic models = request/response contracts
# ---------------------------------------------------------------------------
class TicketIn(BaseModel):
    """What the client SENDS (request body)."""

    category: Literal["bug", "feature", "question"]
    priority: int = Field(ge=1, le=5)
    summary: str = Field(min_length=5, max_length=200)


class TicketOut(TicketIn):
    """What the API RETURNS. Inherits every field from TicketIn, adds `id`."""

    id: int


# Fake database: a dict in memory (resets when the server restarts).
TICKETS: dict[int, TicketOut] = {}


# ---------------------------------------------------------------------------
# 2. Simplest endpoint: GET with no input
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}          # dicts are converted to JSON automatically


# ---------------------------------------------------------------------------
# 3. POST with a JSON body — FastAPI validates it with TicketIn
# ---------------------------------------------------------------------------
@app.post("/tickets", status_code=201)
def create_ticket(ticket: TicketIn) -> TicketOut:
    # By the time this line runs, `ticket` is GUARANTEED valid.
    # Bad input never reaches here: FastAPI returns 422 with the Pydantic errors.
    new_id = len(TICKETS) + 1
    saved = TicketOut(id=new_id, **ticket.model_dump())
    TICKETS[new_id] = saved
    return saved


# ---------------------------------------------------------------------------
# 4. Path parameter: /tickets/1  — the type hint `int` validates it too
# ---------------------------------------------------------------------------
@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int) -> TicketOut:
    if ticket_id not in TICKETS:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return TICKETS[ticket_id]


# ---------------------------------------------------------------------------
# 5. Query parameters: /tickets?category=bug&min_priority=2
# ---------------------------------------------------------------------------
@app.get("/tickets")
def list_tickets(
    category: Literal["bug", "feature", "question"] | None = None,
    min_priority: int = Query(default=1, ge=1, le=5),
) -> list[TicketOut]:
    results = TICKETS.values()
    if category:
        results = [t for t in results if t.category == category]
    return [t for t in results if t.priority >= min_priority]
