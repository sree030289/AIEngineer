import pytest
from pydantic import ValidationError

from exercises.day04_pydantic_advanced import Invoice, LineItem, error_feedback, invoice_tool


def _invoice(**overrides) -> dict:
    data = {
        "invoice_number": "INV-2026-0042",
        "currency": "USD",
        "items": [
            {"description": "API credits", "quantity": 2, "unit_price": 10.0},
            {"description": "Support plan", "quantity": 1, "unit_price": 5.5},
        ],
        "total": 25.5,
    }
    data.update(overrides)
    return data


# --- Exercise 1: nested models -----------------------------------------------
def test_valid_invoice_builds_nested_models():
    inv = Invoice.model_validate(_invoice())
    assert isinstance(inv.items[0], LineItem)
    assert inv.items[0].amount == 20.0


def test_invalid_nested_item_rejected():
    items = [{"description": "Credits", "quantity": 0, "unit_price": 10}]
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(items=items, total=0))


def test_empty_items_rejected():
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(items=[], total=0))


# --- Exercise 2: field validators --------------------------------------------
@pytest.mark.parametrize("raw, expected", [("usd", "USD"), (" eur ", "EUR"), ("Gbp", "GBP")])
def test_currency_normalised(raw, expected):
    assert Invoice.model_validate(_invoice(currency=raw)).currency == expected


@pytest.mark.parametrize("raw", ["US", "US$", "EURO", "", "1234"])
def test_bad_currency_rejected(raw):
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(currency=raw))


def test_invoice_number_stripped():
    inv = Invoice.model_validate(_invoice(invoice_number="  INV-7  "))
    assert inv.invoice_number == "INV-7"


@pytest.mark.parametrize("raw", ["2026-0042", "inv-7", "Invoice 7"])
def test_invoice_number_must_start_with_inv(raw):
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(invoice_number=raw))


# --- Exercise 3: model validator ---------------------------------------------
def test_wrong_total_rejected():
    with pytest.raises(ValidationError) as exc:
        Invoice.model_validate(_invoice(total=30.0))
    assert "total" in str(exc.value).lower()


def test_total_within_rounding_tolerance_accepted():
    Invoice.model_validate(_invoice(total=25.505))


# --- Exercise 4: tool definition ---------------------------------------------
def test_invoice_tool_shape():
    tool = invoice_tool()
    assert tool["name"] == "record_invoice"
    assert tool["description"]
    schema = tool["input_schema"]
    assert schema["type"] == "object"
    assert set(schema["required"]) == {"invoice_number", "currency", "items", "total"}
    assert "items" in schema["properties"]


# --- Exercise 5: error feedback ----------------------------------------------
def test_error_feedback_lists_every_problem_with_location():
    bad = _invoice(
        currency="dollars",
        items=[{"description": "Credits", "quantity": 0, "unit_price": 10}],
    )
    with pytest.raises(ValidationError) as exc:
        Invoice.model_validate(bad)

    lines = error_feedback(exc.value).split("\n")

    assert len(lines) == 2
    assert lines[0].startswith("currency: ")
    assert lines[1] == "items.0.quantity: Input should be greater than 0"
