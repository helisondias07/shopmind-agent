"""SQLAlchemy models for the fictional Lume & Co. store."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProductRow(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(40), primary_key=True)
    name_pt: Mapped[str] = mapped_column(String(120))
    name_en: Mapped[str] = mapped_column(String(120))
    description_pt: Mapped[str] = mapped_column(Text)
    description_en: Mapped[str] = mapped_column(Text)
    synonyms: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(40), index=True)
    price_cents: Mapped[int]
    stock: Mapped[int]
    weight_grams: Mapped[int]
    image_key: Mapped[str] = mapped_column(String(40))


class PolicyRow(Base):
    __tablename__ = "policies"

    slug: Mapped[str] = mapped_column(String(40), primary_key=True)
    topic: Mapped[str] = mapped_column(String(40))
    title_pt: Mapped[str] = mapped_column(String(160))
    title_en: Mapped[str] = mapped_column(String(160))
    body_pt: Mapped[str] = mapped_column(Text)
    body_en: Mapped[str] = mapped_column(Text)


class OrderRow(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_first_name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20))
    carrier: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tracking_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    total_cents: Mapped[int]
    note_pt: Mapped[str] = mapped_column(Text, default="")
    note_en: Mapped[str] = mapped_column(Text, default="")
    items: Mapped[list[OrderItemRow]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemRow(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    sku: Mapped[str] = mapped_column(String(40))
    qty: Mapped[int]
    unit_price_cents: Mapped[int]
    order: Mapped[OrderRow] = relationship(back_populates="items")
