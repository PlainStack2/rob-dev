from __future__ import annotations


def dollars_to_cents(amount: float) -> int:
    return int(round(amount * 100))


def format_money_from_cents(amount_cents: int, currency: str = "USD") -> str:
    normalized_currency = (currency or "USD").upper()
    symbol = "$" if normalized_currency == "USD" else normalized_currency + " "
    return f"{symbol}{amount_cents / 100:.2f}"
