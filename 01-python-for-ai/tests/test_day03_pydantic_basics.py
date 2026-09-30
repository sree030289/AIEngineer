import pytest
from pydantic import ValidationError

from exercises.day03_pydantic_basics import (
    TicketClassification,
    extract_json,
    parse_classification,
    safe_parse,
)

VALID = '{"category": "bug", "priority": 2, "summary": "Login button does nothing"}'


# --- Exercise 1: the model ----------------------------------------------------
def test_valid_ticket():
    t = TicketClassification(category="bug", priority=2, summary="Login broken")
    assert t.category == "bug"
    assert t.priority == 2
    assert t.tags == []


def test_numeric_string_is_coerced_to_int():
    # LLMs often return "3" instead of 3 — Pydantic converts it for you.
    t = TicketClassification(category="feature", priority="3", summary="Add dark mode")
    assert t.priority == 3


@pytest.mark.parametrize("category", ["Bug", "incident", ""])
def test_unknown_category_rejected(category):
    with pytest.raises(ValidationError):
        TicketClassification(category=category, priority=1, summary="Something")


@pytest.mark.parametrize("priority", [0, 6, -1, "high"])
def test_priority_out_of_range_rejected(priority):
    with pytest.raises(ValidationError):
        TicketClassification(category="bug", priority=priority, summary="Something")


@pytest.mark.parametrize("summary", ["", "hi", "x" * 201])
def test_summary_length_enforced(summary):
    with pytest.raises(ValidationError):
        TicketClassification(category="bug", priority=1, summary=summary)


def test_missing_field_rejected():
    with pytest.raises(ValidationError):
        TicketClassification(category="bug", summary="No priority given")


def test_tags_default_not_shared():
    a = TicketClassification(category="bug", priority=1, summary="First one")
    b = TicketClassification(category="bug", priority=1, summary="Second one")
    a.tags.append("ui")
    assert b.tags == []


# # --- Exercise 2: extract_json -------------------------------------------------
def test_extract_plain_json():
    assert extract_json(VALID) == VALID


def test_extract_from_markdown_fence():
    assert extract_json(f"```json\n{VALID}\n```") == VALID


def test_extract_from_chatty_reply():
    raw = f"Sure! Here is the classification:\n{VALID}\nHope that helps."
    assert extract_json(raw) == VALID


def test_extract_keeps_nested_braces():
    raw = 'Result: {"a": {"b": 1}} done'
    assert extract_json(raw) == '{"a": {"b": 1}}'


@pytest.mark.parametrize("raw", ["", "I cannot classify this ticket.", "} backwards {"])
def test_extract_without_json_raises(raw):
    with pytest.raises(ValueError):
        extract_json(raw)


# --- Exercise 3: parse_classification ----------------------------------------
def test_parse_from_fenced_reply():
    t = parse_classification(f"```json\n{VALID}\n```")
    assert isinstance(t, TicketClassification)
    assert t.summary == "Login button does nothing"


def test_parse_invalid_data_raises_validation_error():
    with pytest.raises(ValidationError):
        parse_classification('{"category": "outage", "priority": 9, "summary": "x"}')


# --- Exercise 4: safe_parse ---------------------------------------------------
def test_safe_parse_valid():
    assert safe_parse(VALID).category == "bug"


@pytest.mark.parametrize(
    "raw",
    [
        "Sorry, I can't help with that.",                      # no JSON at all
        '{"category": "bug", "priority": 2, "summary": ',      # truncated JSON
        '{"category": "bug", "priority": 99, "summary": "Too high priority"}',
    ],
)
def test_safe_parse_returns_none_for_bad_replies(raw):
    assert safe_parse(raw) is None
