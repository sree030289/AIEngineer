"""Lesson 2b — Testing a FastAPI app (your home turf!).

TestClient calls the app in-process — no server needed. Same idea as
Playwright's `request` fixture, but in Python.

    uv run pytest lessons/ -v
"""

import pytest
from fastapi.testclient import TestClient

from lessons.lesson2_fastapi import TICKETS, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    TICKETS.clear()          # each test starts with an empty "database"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_fetch_ticket():
    body = {"category": "bug", "priority": 2, "summary": "Login broken"}

    created = client.post("/tickets", json=body)
    assert created.status_code == 201
    assert created.json() == {**body, "id": 1}

    fetched = client.get("/tickets/1")
    assert fetched.json()["summary"] == "Login broken"


def test_invalid_body_returns_422_with_pydantic_errors():
    response = client.post("/tickets", json={"category": "outage", "priority": 9})

    assert response.status_code == 422
    failing_fields = {err["loc"][-1] for err in response.json()["detail"]}
    assert failing_fields == {"category", "priority", "summary"}


def test_unknown_ticket_returns_404():
    assert client.get("/tickets/999").status_code == 404


def test_path_param_type_is_validated():
    assert client.get("/tickets/abc").status_code == 422


def test_filter_by_category():
    client.post("/tickets", json={"category": "bug", "priority": 3, "summary": "Crash on save"})
    client.post("/tickets", json={"category": "feature", "priority": 1, "summary": "Dark mode"})

    bugs = client.get("/tickets", params={"category": "bug"}).json()
    assert [t["summary"] for t in bugs] == ["Crash on save"]
