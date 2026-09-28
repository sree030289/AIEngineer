"""Lesson 1 — Pydantic in 7 steps.

Run it and read the output next to the code:
    uv run python lessons/lesson1_pydantic.py
"""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator


def step(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


# ---------------------------------------------------------------------------
step("STEP 1 — A model is a class that describes the shape of your data")
# ---------------------------------------------------------------------------
# Like a dataclass: fields are declared with type hints.
class User(BaseModel):
    name: str
    age: int


u = User(name="Sree", age=30)
print(u)             # name='Sree' age=30
print(u.name)        # attribute access, like any object


# ---------------------------------------------------------------------------
step("STEP 2 — Unlike a dataclass, Pydantic CHECKS the types at runtime")
# ---------------------------------------------------------------------------
try:
    User(name="Sree", age="thirty")
except ValidationError as e:
    print(e)
# A dataclass would have happily stored "thirty". Pydantic refuses.


# ---------------------------------------------------------------------------
step("STEP 3 — It converts values when it's safe to do so")
# ---------------------------------------------------------------------------
u = User(name="Sree", age="30")    # string "30" -> int 30
print(u.age, type(u.age))          # 30 <class 'int'>
# This is why it's great for LLM output: models often return "30" instead of 30.


# ---------------------------------------------------------------------------
step("STEP 4 — Constraints with Field() and fixed choices with Literal")
# ---------------------------------------------------------------------------
class Ticket(BaseModel):
    category: Literal["bug", "feature", "question"]   # only these 3 strings
    priority: int = Field(ge=1, le=5)                 # 1 <= priority <= 5
    summary: str = Field(min_length=5)                # at least 5 chars
    tags: list[str] = []                              # optional, default []


print(Ticket(category="bug", priority=2, summary="Login broken"))

try:
    Ticket(category="outage", priority=9, summary="hi")
except ValidationError as e:
    print(f"\n{e.error_count()} errors found at once:")
    print(e)


# ---------------------------------------------------------------------------
step("STEP 5 — JSON in, JSON out (the part you'll use with LLMs and APIs)")
# ---------------------------------------------------------------------------
raw_json = '{"category": "feature", "priority": "3", "summary": "Add dark mode"}'

ticket = Ticket.model_validate_json(raw_json)   # JSON string -> validated object
print("parsed:     ", ticket)
print("as dict:    ", ticket.model_dump())       # object -> dict
print("as JSON:    ", ticket.model_dump_json())  # object -> JSON string

data = {"category": "question", "priority": 1, "summary": "How do I reset my password?"}
print("from dict:  ", Ticket.model_validate(data))  # dict -> validated object


# ---------------------------------------------------------------------------
step("STEP 6 — Nested models: a model can contain other models")
# ---------------------------------------------------------------------------
class Address(BaseModel):
    city: str
    country: str


class Customer(BaseModel):
    name: str
    address: Address                 # one nested model
    tickets: list[Ticket] = []       # a list of nested models


c = Customer.model_validate({
    "name": "Acme",
    "address": {"city": "Hyderabad", "country": "IN"},
    "tickets": [{"category": "bug", "priority": 1, "summary": "Checkout fails"}],
})
print(c.address.city)            # Hyderabad  (plain dicts became objects)
print(c.tickets[0].priority)     # 1

try:
    Customer.model_validate({"name": "Acme", "address": {"city": "Pune"},
                             "tickets": [{"category": "bug", "priority": 0, "summary": "Crash!"}]})
except ValidationError as e:
    print("\nErrors point to the exact nested location:")
    for err in e.errors():
        print("  ", err["loc"], "->", err["msg"])


# ---------------------------------------------------------------------------
step("STEP 7 — Custom rules with @field_validator")
# ---------------------------------------------------------------------------
class Order(BaseModel):
    currency: str

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str) -> str:
        value = value.strip().upper()          # clean it up...
        if len(value) != 3:
            raise ValueError("must be a 3-letter code")   # ...or reject it
        return value                           # whatever you return is stored


print(Order(currency="  usd "))    # currency='USD'
try:
    Order(currency="dollars")
except ValidationError as e:
    print(e.errors()[0]["msg"])    # Value error, must be a 3-letter code


# ---------------------------------------------------------------------------
step("BONUS — The model can describe itself as a JSON Schema")
# ---------------------------------------------------------------------------
import json  # noqa: E402

print(json.dumps(Ticket.model_json_schema(), indent=2))
# FastAPI uses this to build Swagger docs. LLM APIs use it to define tools.
