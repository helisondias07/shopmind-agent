"""Order lookup against the SQLite mock of the store's order API."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shopmind.db.database import Database
from shopmind.db.models import OrderRow, ProductRow
from shopmind.schemas import OrderItemView, OrderView


class OrderService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get(self, public_id: str) -> OrderView | None:
        normalized = public_id.strip().upper()
        with self.database.session() as session:
            row = session.scalar(
                select(OrderRow)
                .where(OrderRow.public_id == normalized)
                .options(selectinload(OrderRow.items))
            )
            if row is None:
                return None
            items: list[OrderItemView] = []
            for item in row.items:
                product = session.get(ProductRow, item.sku)
                items.append(
                    OrderItemView(
                        sku=item.sku,
                        name_pt=product.name_pt if product else item.sku,
                        name_en=product.name_en if product else item.sku,
                        qty=item.qty,
                        unit_price_cents=item.unit_price_cents,
                    )
                )
            return OrderView(
                public_id=row.public_id,
                customer_first_name=row.customer_first_name,
                status=row.status,  # type: ignore[arg-type]
                carrier=row.carrier,
                tracking_code=row.tracking_code,
                total_cents=row.total_cents,
                items=items,
                note_pt=row.note_pt,
                note_en=row.note_en,
            )
