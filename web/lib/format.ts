import type { Locale } from "./types";

export function formatMoney(cents: number, locale: Locale): string {
  return new Intl.NumberFormat(locale === "pt" ? "pt-BR" : "en-US", {
    style: "currency",
    currency: "BRL",
  }).format(cents / 100);
}

export function stockLabel(stock: number, inStock: string, outOfStock: string): string {
  if (stock <= 0) return outOfStock;
  return `${stock} ${inStock}`;
}
