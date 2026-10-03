"""Shared test fixtures — YOUR WORK FOR DAY 10 IS IN THIS FILE.

A fixture is a function that PREPARES something a test needs (a clean object,
a fake server, a temp file). A test asks for it just by naming it as a parameter:

    def test_something(store):      # pytest sees "store", runs the fixture below,
        assert len(store) == 0      # and passes in whatever it returned

Rules:
  - decorate with @pytest.fixture
  - the name of the function = the name tests use
  - a fixture can ask for other fixtures the same way (parameters)
  - by default every TEST gets its own fresh copy (so tests can't affect each other)

The tests that use these live in  tests/test_day10_fixtures.py.
Replace each `raise NotImplementedError` with real code.
"""

import httpx
import pytest

from exercises.day10_ticket_store import Ticket, TicketStore


# ---------------------------------------------------------------------------
# Fixture 1
# ---------------------------------------------------------------------------
@pytest.fixture
def store():
    """Return a brand-new, empty TicketStore."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Fixture 2 — a fixture that uses another fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def loaded_store(store):
    """Take the `store` fixture (note it's a PARAMETER), add these 3 tickets, return it:

        Ticket(1, "bug",     "Login crash")
        Ticket(2, "feature", "Dark mode")
        Ticket(3, "bug",     "Upload fails")
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Fixture 3 — a fake server
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_api():
    """Return an httpx.Client whose "server" is a Python function (MockTransport):

        GET /tickets/1   -> 200 with JSON {"id": 1, "category": "bug", "summary": "Login crash"}
        anything else    -> 404

    Pattern:
        def handler(request: httpx.Request) -> httpx.Response: ...
        return httpx.Client(base_url="https://tickets.example.com",
                            transport=httpx.MockTransport(handler))
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Fixture 4 — temporary files with the built-in `tmp_path`
# ---------------------------------------------------------------------------
@pytest.fixture
def tickets_file(tmp_path, loaded_store):
    """Save `loaded_store` to a file called "tickets.json" inside `tmp_path` and
    return the file's path.

    `tmp_path` is a built-in pytest fixture: a fresh empty temporary folder
    (a pathlib.Path), deleted for you later. Use  tmp_path / "tickets.json".
    The store has a  .save(path)  method.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Fixture 5 — temporary environment variables with the built-in `monkeypatch`
# ---------------------------------------------------------------------------
@pytest.fixture
def api_key_env(monkeypatch):
    """Set the environment variable ANTHROPIC_API_KEY to "sk-test-123" for the
    duration of ONE test, and return that string.

    `monkeypatch` is a built-in fixture that changes things temporarily and puts
    them back afterwards, even if the test fails. Use  monkeypatch.setenv(name, value).
    """
    raise NotImplementedError
