"""Day 1 — References, mutability and copies.

Run:  uv run pytest tests/test_day01_mutability.py -v

Exercises 1 and 2 contain REAL BUGS. Fix them.
Exercises 3 and 4 are stubs. Implement them.
"""

# ---------------------------------------------------------------------------
# Exercise 1 — fix the bug
# ---------------------------------------------------------------------------
def add_tag(tag: str, tags: list[str]=None) -> list[str]:
    """Return a list of tags with `tag` appended.

    If `tags` is not given, start from an empty list.
    Calling add_tag("a") then add_tag("b") must return ["b"] the second time.

    BUG: this version leaks tags between calls. Why? Fix it.
    Hint: the idiomatic fix uses `None` as the default.
    """
    if tags is None:
        tags=[]
    tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# Exercise 2 — fix the bug
# ---------------------------------------------------------------------------
class Conversation:
    """Holds the messages of ONE conversation with an LLM.

    BUG: two different Conversation objects end up sharing messages.
    Fix it so each instance has its own list.
    """

    messages: list[str] = None

    def __init__(self, user_id: str):
        self.user_id = user_id
        if self.messages is None:
            self.messages = []

    def add(self, text: str) -> None:
        self.messages.append(text)


# ---------------------------------------------------------------------------
# Exercise 3 — implement
# ---------------------------------------------------------------------------
def with_item(items: list, item) -> list:
    """Return a NEW list equal to `items` + [item].

    The caller's `items` list must NOT be modified.
    """
    try:
        # new_item_list = items[:]
        # new_item_list.append(item)
        return items + [item]
    except:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 4 — implement
# ---------------------------------------------------------------------------
def override_config(base: dict, **overrides) -> dict:
    """Return a copy of `base` with top-level keys replaced by `overrides`.

    `base` is a nested config, e.g.
        {"model": "claude-sonnet-5", "params": {"temperature": 0.2, "stop": ["\\n"]}}

    Requirements:
      - `base` must be completely untouched afterwards — including nested
        dicts and lists — even if the caller later mutates the returned config.
      - override values replace the top-level key entirely.

    Hint: a shallow copy is not enough. Look at the `copy` module.
    """
    import copy
    try:
        new_base_dict = copy.deepcopy(base) #base.copy()
        for key,value in overrides.items():
            new_base_dict[key]=value
        return new_base_dict
    except:
        raise NotImplementedError
