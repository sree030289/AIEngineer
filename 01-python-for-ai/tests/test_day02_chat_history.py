import pytest

from exercises.day02_chat_history import ChatHistory, Message


# --- Message ------------------------------------------------------------------
def test_valid_message():
    msg = Message("user", "hello")
    assert (msg.role, msg.content) == ("user", "hello")


@pytest.mark.parametrize("role", ["system", "bot", "USER", ""])
def test_invalid_role_rejected(role):
    with pytest.raises(ValueError):
        Message(role, "hello")


@pytest.mark.parametrize("content", ["", "   ", "\n\t"])
def test_blank_content_rejected(content):
    with pytest.raises(ValueError):
        Message("user", content)


# --- ChatHistory: state isolation -------------------------------------------
def test_histories_do_not_share_messages():
    a = ChatHistory(system="You are A")
    b = ChatHistory(system="You are B")
    a.add_user("hi")

    assert len(a.messages) == 1
    assert b.messages == []


# --- ChatHistory: turn order ------------------------------------------------
def test_alternating_turns():
    h = ChatHistory(system="s")
    h.add_user("q1")
    h.add_assistant("a1")
    h.add_user("q2")
    assert [m.role for m in h.messages] == ["user", "assistant", "user"]


def test_two_user_messages_in_a_row_rejected():
    h = ChatHistory(system="s")
    h.add_user("q1")
    with pytest.raises(ValueError):
        h.add_user("q2")


def test_assistant_cannot_speak_first():
    with pytest.raises(ValueError):
        ChatHistory(system="s").add_assistant("hello")


def test_two_assistant_messages_in_a_row_rejected():
    h = ChatHistory(system="s")
    h.add_user("q1")
    h.add_assistant("a1")
    with pytest.raises(ValueError):
        h.add_assistant("a2")


# --- ChatHistory: trim ------------------------------------------------------
def _history_with(n_pairs: int) -> ChatHistory:
    h = ChatHistory(system="s")
    for i in range(n_pairs):
        h.add_user(f"q{i}")
        h.add_assistant(f"a{i}")
    return h


def test_trim_keeps_most_recent():
    h = _history_with(3)  # q0 a0 q1 a1 q2 a2
    h.trim(4)
    assert [m.content for m in h.messages] == ["q1", "a1", "q2", "a2"]


def test_trim_never_starts_with_assistant():
    h = _history_with(3)
    h.trim(3)  # naive slice would be: a1 q2 a2
    assert h.messages[0].role == "user"
    assert [m.content for m in h.messages] == ["q2", "a2"]


def test_trim_larger_than_history_is_noop():
    h = _history_with(1)
    h.trim(10)
    assert len(h.messages) == 2


# --- ChatHistory: payload ---------------------------------------------------
def test_to_api_payload_shape():
    h = ChatHistory(system="Be concise")
    h.add_user("hi")
    h.add_assistant("hello")

    assert h.to_api_payload() == {
        "system": "Be concise",
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    }


def test_mutating_payload_does_not_change_history():
    h = ChatHistory(system="s")
    h.add_user("hi")

    payload = h.to_api_payload()
    payload["messages"].append({"role": "assistant", "content": "injected"})
    payload["messages"][0]["content"] = "tampered"

    assert len(h.messages) == 1
    assert h.messages[0].content == "hi"
