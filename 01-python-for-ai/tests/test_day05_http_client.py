import json

import httpx
import pytest
from pydantic import ValidationError

from exercises.day05_http_client import (
    TicketIn,
    TicketOut,
    create_ticket,
    fetch_json,
    get_ticket_or_none,
    make_client,
)

BASE = "https://tickets.example.com"
TICKET = {"id": 7, "category": "bug", "priority": 2, "summary": "Login broken"}


def client_for(handler) -> httpx.Client:
    """A client whose 'server' is the given Python function."""
    return httpx.Client(base_url=BASE, transport=httpx.MockTransport(handler))


# --- Exercise 1: make_client --------------------------------------------------
def test_make_client_configuration():
    client = make_client("https://api.example.com", "secret-123", timeout=5.0)

    assert client.base_url == "https://api.example.com"
    assert client.headers["Authorization"] == "Bearer secret-123"
    assert client.timeout.read == 5.0


def test_make_client_default_timeout():
    assert make_client("https://api.example.com", "k").timeout.read == 10.0


# --- Exercise 2: fetch_json ---------------------------------------------------
def test_fetch_json_returns_body():
    seen = []

    def server(request):
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"status": "ok"})

    assert fetch_json(client_for(server), "/health") == {"status": "ok"}
    assert seen == [("GET", "/health")]


@pytest.mark.parametrize("status", [400, 401, 404, 500, 503])
def test_fetch_json_raises_on_error_status(status):
    client = client_for(lambda request: httpx.Response(status, json={"error": "x"}))
    with pytest.raises(httpx.HTTPStatusError):
        fetch_json(client, "/health")


# --- Exercise 3: create_ticket ------------------------------------------------
def test_create_ticket_sends_json_and_returns_model():
    received = {}

    def server(request):
        received["method"] = request.method
        received["path"] = request.url.path
        received["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": 7, **received["body"]})

    ticket = TicketIn(category="bug", priority=2, summary="Login broken")
    result = create_ticket(client_for(server), ticket)

    assert received == {
        "method": "POST",
        "path": "/tickets",
        "body": {"category": "bug", "priority": 2, "summary": "Login broken"},
    }
    assert isinstance(result, TicketOut)
    assert result.id == 7


def test_create_ticket_raises_on_422():
    client = client_for(lambda request: httpx.Response(422, json={"detail": []}))
    ticket = TicketIn(category="bug", priority=2, summary="Login broken")
    with pytest.raises(httpx.HTTPStatusError):
        create_ticket(client, ticket)


def test_create_ticket_rejects_malformed_server_response():
    # Server "succeeds" but forgets the id — must not slip through.
    client = client_for(lambda request: httpx.Response(
        201, json={"category": "bug", "priority": 2, "summary": "Login broken"}))
    ticket = TicketIn(category="bug", priority=2, summary="Login broken")
    with pytest.raises(ValidationError):
        create_ticket(client, ticket)


# --- Exercise 4: get_ticket_or_none -------------------------------------------
def test_get_ticket_found():
    def server(request):
        assert request.url.path == "/tickets/7"
        return httpx.Response(200, json=TICKET)

    result = get_ticket_or_none(client_for(server), 7)
    assert result == TicketOut(**TICKET)


def test_get_ticket_404_returns_none():
    client = client_for(lambda request: httpx.Response(404, json={"detail": "Not found"}))
    assert get_ticket_or_none(client, 999) is None


@pytest.mark.parametrize("status", [401, 500])
def test_get_ticket_other_errors_raise(status):
    client = client_for(lambda request: httpx.Response(status))
    with pytest.raises(httpx.HTTPStatusError):
        get_ticket_or_none(client, 7)
