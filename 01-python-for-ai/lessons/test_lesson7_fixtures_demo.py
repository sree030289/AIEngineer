"""Lesson 7 — pytest fixtures, shown live.

Run:  uv run pytest lessons/test_lesson7_fixtures_demo.py -v -s
(-s lets the print() lines show, so you can watch the ORDER things happen in.)

If you've used Playwright fixtures (page, request, context), this is the same idea.
"""

import pytest


# ---------------------------------------------------------------------------
# 1. A fixture = a function that prepares something. Tests ask for it BY NAME.
# ---------------------------------------------------------------------------
@pytest.fixture
def basket():
    print("\n   [fixture] making a new empty basket")
    return []


def test_add_apple(basket):
    print("   [test]    test_add_apple starts")
    basket.append("apple")
    assert basket == ["apple"]


def test_basket_is_fresh_again(basket):
    print("   [test]    test_basket_is_fresh_again starts")
    assert basket == []             # the apple from the previous test is NOT here


# ---------------------------------------------------------------------------
# 2. Setup AND cleanup: `yield` splits the fixture in two halves.
# ---------------------------------------------------------------------------
@pytest.fixture
def database():
    print("\n   [setup]   connecting to the database")
    connection = {"rows": []}
    yield connection                # <- the test runs HERE, with `connection`
    print("   [cleanup] closing the database  (runs even if the test FAILS)")


def test_insert_row(database):
    print("   [test]    inserting a row")
    database["rows"].append("row 1")
    assert len(database["rows"]) == 1


# ---------------------------------------------------------------------------
# 3. A fixture can use another fixture.
# ---------------------------------------------------------------------------
@pytest.fixture
def full_basket(basket):            # <- asks for `basket`
    basket.extend(["apple", "banana"])
    return basket


def test_full_basket(full_basket):
    assert full_basket == ["apple", "banana"]


# ---------------------------------------------------------------------------
# 4. Built-in fixtures: tmp_path (temporary folder) and monkeypatch (temporary changes).
# ---------------------------------------------------------------------------
def test_tmp_path_gives_a_fresh_folder(tmp_path):
    file = tmp_path / "notes.txt"
    file.write_text("hello")
    print(f"\n   [tmp_path] this test's private folder: {tmp_path.name}")
    assert file.read_text() == "hello"


def test_monkeypatch_changes_are_undone(monkeypatch):
    import os

    monkeypatch.setenv("DEMO_FIXTURE_VAR", "temporary")
    assert os.environ["DEMO_FIXTURE_VAR"] == "temporary"


def test_the_variable_is_gone_again():
    import os

    assert "DEMO_FIXTURE_VAR" not in os.environ


# ---------------------------------------------------------------------------
# 5. Where do shared fixtures live? In a file named exactly  conftest.py.
#    Every test file in that folder can use them without importing anything.
#    (Your Day 10 fixtures go in tests/conftest.py.)
# ---------------------------------------------------------------------------
