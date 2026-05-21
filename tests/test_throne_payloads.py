from __future__ import annotations

from rob.throne.payloads import is_test_webhook_payload, parse_throne_send_payload


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



def test_explicit_test_payload_is_detected():
    payload = {"type": "webhook.test", "data": {"isTest": True}}
    parsed = parse_throne_send_payload(creator_id="creator-123", payload=payload)
    assert is_test_webhook_payload(payload, parsed) is True


def test_marie_test_fallback_is_detected():
    payload = {"type": "gift_purchased", "data": {"gifterUsername": "marie_123", "itemName": "Ring", "amount": 10}}
    parsed = parse_throne_send_payload(creator_id="creator-123", payload=payload)
    assert is_test_webhook_payload(payload, parsed, test_gifter_usernames={"marie_123"}) is True


def test_real_gift_payload_is_not_treated_as_test():
    payload = {"type": "gift_purchased", "data": {"gifterUsername": "real_sender", "itemName": "Shoes", "amount": 42.99}}
    parsed = parse_throne_send_payload(creator_id="creator-123", payload=payload)
    assert is_test_webhook_payload(payload, parsed, test_gifter_usernames={"marie_123"}) is False
