"""Day 10 — pytest fixtures. THIS FILE IS COMPLETE — you don't edit it.

Your work is in  tests/conftest.py  (write 5 fixtures).
Run:  uv run pytest tests/test_day10_fixtures.py -v
See fixtures live first:  uv run pytest lessons/test_lesson7_fixtures_demo.py -v -s

This is just the "code under test": a tiny in-memory ticket store and an API helper.
Day 10 doesn't depend on any earlier day.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx


@dataclass
class Ticket:
    id: int
    category: str
    summary: str


class TicketStore:
    """Keeps tickets in memory, and can save/load them as a JSON file."""

    def __init__(self) -> None:
        self._tickets: dict[int, Ticket] = {}

    def add(self, ticket: Ticket) -> None:
        if ticket.id in self._tickets:
            raise ValueError(f"duplicate ticket id {ticket.id}")
        self._tickets[ticket.id] = ticket

    def get(self, ticket_id: int) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def by_category(self, category: str) -> list[Ticket]:
        return [t for t in self._tickets.values() if t.category == category]

    def __len__(self) -> int:
        return len(self._tickets)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps([asdict(t) for t in self._tickets.values()]))

    @classmethod
    def load(cls, path: Path) -> "TicketStore":
        store = cls()
        for row in json.loads(path.read_text()):
            store.add(Ticket(**row))
        return store


def fetch_ticket(client: httpx.Client, ticket_id: int) -> Ticket | None:
    """GET /tickets/<id>. Returns the ticket, or None if the server says 404."""
    response = client.get(f"/tickets/{ticket_id}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return Ticket(**response.json())
