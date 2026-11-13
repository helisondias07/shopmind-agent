"""Load the fictional catalog, policies, and orders into SQLite."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from shopmind.db.models import Base, OrderItemRow, OrderRow, PolicyRow, ProductRow

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _read(name: str) -> list[dict]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def create_schema(engine) -> None:
    Base.metadata.create_all(engine)


def seed(session: Session) -> None:
    for row in _read("products.json"):
        current = session.get(ProductRow, row["sku"])
        if current is None:
            session.add(ProductRow(**row))
        else:
            for key, value in row.items():
                setattr(current, key, value)

    for row in _read("policies.json"):
        current = session.get(PolicyRow, row["slug"])
        if current is None:
            session.add(PolicyRow(**row))
        else:
            for key, value in row.items():
                setattr(current, key, value)

    for row in _read("orders.json"):
        items = row["items"]
        payload = {key: value for key, value in row.items() if key != "items"}
        current = session.scalar(select(OrderRow).where(OrderRow.public_id == row["public_id"]))
        if current is None:
            current = OrderRow(**payload)
            session.add(current)
            session.flush()
        else:
            for key, value in payload.items():
                setattr(current, key, value)
            current.items.clear()
        for item in items:
            current.items.append(
                OrderItemRow(
                    sku=item["sku"],
                    qty=item["qty"],
                    unit_price_cents=item["unit_price_cents"],
                )
            )
