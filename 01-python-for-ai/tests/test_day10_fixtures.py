"""These tests are COMPLETE. They fail until you write the fixtures in tests/conftest.py.

Notice that no test creates its own data: each one just asks for a fixture by name.
"""

import os

import pytest

from exercises.day10_ticket_store import Ticket, TicketStore, fetch_ticket


# --- Fixture 1: store ---------------------------------------------------------
def test_store_starts_empty(store):
    assert isinstance(store, TicketStore)
    assert len(store) == 0


def test_store_can_be_modified(store):
    store.add(Ticket(1, "bug", "Something broke"))
    assert len(store) == 1


def test_each_test_gets_a_fresh_store(store):
    # The previous test added a ticket. If your fixture shared one object between
    # tests (e.g. a module-level variable), this would see it. (Day 1 again!)
    assert len(store) == 0


# --- Fixture 2: loaded_store --------------------------------------------------
def test_loaded_store_has_three_tickets(loaded_store):
    assert len(loaded_store) == 3
    assert loaded_store.get(2).summary == "Dark mode"


def test_loaded_store_is_built_on_the_store_fixture(store, loaded_store):
    # Inside ONE test, asking for the same fixture twice gives the SAME object.
    assert loaded_store is store


@pytest.mark.parametrize("category, expected_count", [("bug", 2), ("feature", 1), ("question", 0)])
def test_by_category(loaded_store, category, expected_count):
    assert len(loaded_store.by_category(category)) == expected_count


def test_duplicate_id_rejected(loaded_store):
    with pytest.raises(ValueError):
        loaded_store.add(Ticket(1, "bug", "Same id again"))


# --- Fixture 3: fake_api ------------------------------------------------------
def test_fetch_existing_ticket(fake_api):
    assert fetch_ticket(fake_api, 1) == Ticket(1, "bug", "Login crash")


def test_fetch_missing_ticket_returns_none(fake_api):
    assert fetch_ticket(fake_api, 99) is None


# --- Fixture 4: tickets_file --------------------------------------------------
def test_tickets_file_exists_in_temp_folder(tickets_file, tmp_path):
    assert tickets_file.exists()
    assert tickets_file.name == "tickets.json"
    assert tickets_file.parent == tmp_path


def test_tickets_file_round_trips(tickets_file):
    reloaded = TicketStore.load(tickets_file)
    assert len(reloaded) == 3
    assert reloaded.get(3) == Ticket(3, "bug", "Upload fails")


# --- Fixture 5: api_key_env ---------------------------------------------------
def test_api_key_env_sets_the_variable(api_key_env):
    assert api_key_env == "sk-test-123"
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-test-123"
