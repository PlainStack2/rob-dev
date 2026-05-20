from __future__ import annotations

from rob.throne.payloads import parse_throne_send_payload


def test_contribution_amount_is_treated_as_minor_units():
    payload = {
        "event_type": "contribution_purchased",
        "data": {
            "gifter_username": "briansadplobo",
            "item_name": "Birthday Presents",
            "amount": 1500,
            "currency": "EUR",
        },
    }

    parsed = parse_throne_send_payload(creator_id="creator-123", payload=payload)

    assert parsed.event_type == "contribution_purchased"
    assert parsed.amount_cents == 1500
    assert parsed.currency == "EUR"


def test_private_amounts_are_zeroed():
    payload = {
        "type": "gift_purchased",
        "data": {
            "itemName": "Secret Gift",
            "amount": 29.99,
            "currency": "USD",
            "isPrivate": True,
        },
    }

    parsed = parse_throne_send_payload(creator_id="creator-123", payload=payload)

    assert parsed.is_private is True
    assert parsed.amount_cents == 0
