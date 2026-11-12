"""A small, explicit shipping table. The quote is the only price the agent may cite."""

from __future__ import annotations

from dataclasses import dataclass

from shopmind.schemas import ShippingQuote
from shopmind.textutil import format_cep

FREE_SHIPPING_CENTS = 29900


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    code: str
    label_pt: str
    label_en: str
    price_cents: int
    eta_business_days: int


REGIONS: tuple[Region, ...] = (
    Region(1000, 19999, "sp", "São Paulo", "São Paulo", 1490, 2),
    Region(20000, 28999, "rj", "Rio de Janeiro", "Rio de Janeiro", 2190, 3),
    Region(29000, 29999, "es", "Espírito Santo", "Espírito Santo", 2390, 4),
    Region(30000, 39999, "mg", "Minas Gerais", "Minas Gerais", 1990, 3),
    Region(40000, 48999, "ba", "Bahia", "Bahia", 2790, 6),
    Region(70000, 76799, "df", "Distrito Federal", "Federal District", 2290, 4),
    Region(80000, 87999, "sul", "Sul", "South", 2490, 5),
)

DEFAULT_REGION = Region(0, 99999, "other", "demais regiões", "other regions", 3490, 8)


class ShippingService:
    threshold_cents = FREE_SHIPPING_CENTS

    def quote(self, postal_code: str, subtotal_cents: int) -> ShippingQuote | None:
        digits = "".join(char for char in postal_code if char.isdigit())
        if len(digits) != 8:
            return None
        prefix = int(digits[:5])
        region = DEFAULT_REGION
        for candidate in REGIONS:
            if candidate.start <= prefix <= candidate.end:
                region = candidate
                break
        free = subtotal_cents >= self.threshold_cents and subtotal_cents > 0
        return ShippingQuote(
            postal_code=format_cep(digits),
            subtotal_cents=subtotal_cents,
            price_cents=0 if free else region.price_cents,
            eta_business_days=region.eta_business_days,
            free_shipping=free,
            region=region.code,
            region_pt=region.label_pt,
            region_en=region.label_en,
            threshold_cents=self.threshold_cents,
        )
