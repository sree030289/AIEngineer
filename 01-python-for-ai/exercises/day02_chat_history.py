"""Day 2 — Class vs instance attributes and @dataclass.

Run:  uv run pytest tests/test_day02_chat_history.py -v

You'll build the chat-history object every LLM app needs. The API shape
mirrors Anthropic's Messages API: a separate `system` string plus a list of
{"role": ..., "content": ...} messages alternating user/assistant.

Read first:  https://docs.python.org/3/library/dataclasses.html
             (especially `field(default_factory=...)` and `__post_init__`)
"""

from dataclasses import dataclass, field

VALID_ROLES = {"user", "assistant"}


@dataclass
class Message:
    """A single chat message.

    TODO: implement `__post_init__` so that:
      - a role not in VALID_ROLES raises ValueError
      - empty or whitespace-only content raises ValueError
    """

    role: str
    content: str

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError
        if self.content  == "" or self.content.isspace():
            raise ValueError


@dataclass
class ChatHistory:
    """Conversation state sent to the LLM on every turn.

    TODO: add a `messages` field that defaults to an empty list —
    each ChatHistory must get its OWN list (remember Day 1!).
    """

    system: str
    # default_factory=list calls list() for EACH new ChatHistory,
    # so every instance gets its own fresh [] (the Day 1 bug can't happen).
    messages: list[Message] = field(default_factory=list)

    def add_user(self, content: str) -> None:
        """Append a user message.

        Raise ValueError if the previous message is also from the user
        (the API requires user/assistant turns to alternate).
        """
        # `self.messages` is falsy when empty, so this only checks the last
        # message if there is one. [-1] = last item.
        if self.messages and self.messages[-1].role == "user":
            raise ValueError("two user messages in a row")
        # Message() runs __post_init__, so blank content is rejected here too.
        self.messages.append(Message("user", content))

    def add_assistant(self, content: str) -> None:
        """Append an assistant message.

        Raise ValueError if there is no message yet, or the previous
        message is also from the assistant.
        """
        if not self.messages:
            raise ValueError("assistant cannot speak first")
        if self.messages[-1].role == "assistant":
            raise ValueError("two assistant messages in a row")
        self.messages.append(Message("assistant", content))

    def trim(self, max_messages: int) -> None:
        """Keep only the most recent `max_messages` messages (context window limit).

        After trimming, the history must still START with a user message —
        drop a leading assistant message if needed.
        """
        # [-n:] = "last n items". If n > len, you just get the whole list.
        self.messages = self.messages[-max_messages:]
        # Turns alternate, so at most ONE leading assistant message can appear.
        if self.messages and self.messages[0].role == "assistant":
            self.messages = self.messages[1:]

    def to_api_payload(self) -> dict:
        """Return {"system": str, "messages": [{"role": ..., "content": ...}, ...]}.

        The caller may mutate the returned payload; that must NOT change
        this ChatHistory.
        """
        # The comprehension builds brand-new dicts and a brand-new list,
        # so the caller can't reach our Message objects through the payload.
        return {
            "system": self.system,
            "messages": [{"role": m.role, "content": m.content} for m in self.messages],
        }
