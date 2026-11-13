"""Small text helpers shared by retrieval, guards, and the reply renderer."""

from __future__ import annotations

import re
import unicodedata

MONEY_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2})")
CARD_RE = re.compile(r"(?:\d[ -]*?){13,19}")
ORDER_RE = re.compile(r"\bLM-\d{3,6}\b", re.IGNORECASE)
CEP_RE = re.compile(r"\b(\d{5})-?(\d{3})\b")


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize(text: str) -> str:
    folded = strip_accents(text).lower()
    folded = re.sub(r"[^a-z0-9]+", " ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def format_money(cents: int, locale: str) -> str:
    sign = "-" if cents < 0 else ""
    whole, frac = divmod(abs(cents), 100)
    if locale == "en":
        return f"{sign}R$ {whole:,}.{frac:02d}"
    grouped = f"{whole:,}".replace(",", ".")
    return f"{sign}R$ {grouped},{frac:02d}"


def format_cep(digits: str) -> str:
    return f"{digits[:5]}-{digits[5:]}"


def money_to_cents(raw: str) -> int | None:
    token = raw.strip()
    if "," in token and "." in token:
        token = token.replace(".", "").replace(",", ".")
    elif "," in token:
        token = token.replace(",", ".")
    try:
        return int(round(float(token) * 100))
    except ValueError:
        return None


def extract_money_cents(text: str) -> list[int]:
    found: list[int] = []
    for match in MONEY_RE.finditer(text):
        cents = money_to_cents(match.group(1))
        if cents is not None:
            found.append(cents)
    return found


def find_order_id(text: str) -> str | None:
    match = ORDER_RE.search(text)
    return match.group(0).upper() if match else None


def find_cep(text: str) -> str | None:
    match = CEP_RE.search(text)
    if not match:
        return None
    return f"{match.group(1)}{match.group(2)}"


def redact_payment_cards(text: str) -> tuple[str, bool]:
    """Replace card-like digit runs. Order ids and CEPs are too short to match."""
    if not CARD_RE.search(text):
        return text, False
    return CARD_RE.sub("[redacted-card]", text), True


def first_sentence(text: str, limit: int = 180) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"
