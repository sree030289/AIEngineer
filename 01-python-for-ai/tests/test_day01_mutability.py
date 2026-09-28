from exercises.day01_mutability import (
    Conversation,
    add_tag,
    override_config,
    with_item,
)


# --- Exercise 1: add_tag ----------------------------------------------------
def test_add_tag_calls_are_independent():
    assert add_tag("a") == ["a"]
    assert add_tag("b") == ["b"]


def test_add_tag_appends_to_given_list():
    assert add_tag("new", ["old"]) == ["old", "new"]


 # --- Exercise 2: Conversation -----------------------------------------------
def test_conversations_do_not_share_messages():
    alice = Conversation("alice")
    bob = Conversation("bob")
    alice.add("hi from alice")

    assert alice.messages == ["hi from alice"]
    assert bob.messages == []


def test_new_conversation_starts_empty():
    Conversation("x").add("leftover")
    assert Conversation("y").messages == []


# --- Exercise 3: with_item --------------------------------------------------
def test_with_item_returns_new_list():
    original = [1, 2]
    result = with_item(original, 3)

    assert result == [1, 2, 3]
    assert original == [1, 2]
    assert result is not original


# --- Exercise 4: override_config --------------------------------------------
def _base():
    return {
        "model": "claude-sonnet-5",
        "params": {"temperature": 0.2, "stop": ["\n"]},
    }


def test_override_replaces_top_level_key():
    result = override_config(_base(), model="claude-haiku-4-5")
    assert result["model"] == "claude-haiku-4-5"
    assert result["params"] == {"temperature": 0.2, "stop": ["\n"]}


def test_override_does_not_touch_base():
    base = _base()
    override_config(base, model="other")
    assert base == _base()


def test_mutating_result_does_not_leak_into_base():
    base = _base()
    result = override_config(base)

    result["params"]["temperature"] = 1.0
    result["params"]["stop"].append("END")

    assert base == _base()
