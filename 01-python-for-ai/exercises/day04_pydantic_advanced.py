"""Day 4 — Pydantic advanced: custom validators, nested models, schemas, error feedback.

Run:  uv run pytest tests/test_day04_pydantic_advanced.py -v

Scenario: an LLM extracts invoice data from a PDF's text. You need to:
  - clean up fields it gets "almost right"         (field_validator)
  - enforce rules that span several fields          (model_validator)
  - describe the expected shape TO the LLM          (model_json_schema -> tool definition)
  - tell the LLM exactly what it got wrong, so it can retry   (ValidationError.errors())

Read first:  https://docs.pydantic.dev/latest/concepts/validators/
             https://docs.pydantic.dev/latest/concepts/json_schema/
"""

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


# ---------------------------------------------------------------------------
# Exercise 1 — nested model
# ---------------------------------------------------------------------------
class LineItem(BaseModel):
    """One row on the invoice. (Already done — read it, it's the pattern for Invoice.)"""

    description: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)

    @property
    def amount(self) -> float:
        return self.quantity * self.unit_price


class Invoice(BaseModel):
    """An invoice extracted by the LLM.

    Fields (already declared):
      - invoice_number: e.g. "INV-2026-0042"
      - currency:       3-letter code
      - items:          at least one LineItem   (a list of NESTED models)
      - total:          what the LLM says the total is
    """

    invoice_number: str
    currency: str
    items: list[LineItem] = Field(min_length=1)
    total: float

    # -----------------------------------------------------------------------
    # Exercise 2 — field_validator: clean up "almost right" values
    # -----------------------------------------------------------------------
    # TODO: add a @field_validator("currency") classmethod that:
    #   - strips whitespace and upper-cases it:   " usd " -> "USD"
    #   - raises ValueError if the result isn't exactly 3 letters  ("US", "US$", "EURO")
    #
    # Pattern:
    #   @field_validator("currency")
    #   @classmethod
    #   def normalise_currency(cls, value: str) -> str:
    #       ...
    #       return cleaned_value

    # TODO: add a @field_validator("invoice_number") that strips whitespace and
    #   raises ValueError unless it starts with "INV-".

    # -----------------------------------------------------------------------
    # Exercise 3 — model_validator: rules across several fields
    # -----------------------------------------------------------------------
    # LLMs are bad at arithmetic. Don't trust `total` blindly.
    # TODO: add a @model_validator(mode="after") method that raises ValueError
    #   if `total` differs from the sum of item amounts by more than 0.01.
    #   It must `return self`.
    #
    # Pattern:
    #   @model_validator(mode="after")
    #   def check_total(self) -> "Invoice":
    #       ...
    #       return self


# ---------------------------------------------------------------------------
# Exercise 4 — describe the shape to the LLM (tool definition)
# ---------------------------------------------------------------------------
def invoice_tool() -> dict:
    """Return a tool definition in the Anthropic Messages API format:

        {
            "name": "record_invoice",
            "description": "Record the invoice extracted from the document.",
            "input_schema": <JSON schema of Invoice>,
        }

    When you pass this to the API, the model is pushed to reply with JSON
    matching your schema. You'll use this for real on Days 11–14.

    Hint: Invoice.model_json_schema()
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 5 — turn validation errors into feedback for a retry
# ---------------------------------------------------------------------------
def error_feedback(error: ValidationError) -> str:
    """Build a message you'd send back to the LLM so it can fix its output.

    One line per error, in the format:
        "<location>: <message>"
    where <location> joins the error's "loc" parts with "." , e.g.
        "items.0.quantity: Input should be greater than 0"
        "currency: Value error, currency must be 3 letters"

    Lines joined with "\\n". Keep the order Pydantic reports them in.

    Hint: error.errors() returns a list of dicts with "loc" (a tuple — may
    contain ints, so convert with str()) and "msg" keys.
    """
    raise NotImplementedError
