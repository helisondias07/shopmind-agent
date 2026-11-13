"use client";

import { text } from "@/lib/copy";
import { formatMoney } from "@/lib/format";
import type { Locale, PublicProduct } from "@/lib/types";

export function Storefront({
  locale,
  products,
  error,
  onRetry,
  onAsk,
}: {
  locale: Locale;
  products: PublicProduct[];
  error: boolean;
  onRetry: () => void;
  onAsk: (question: string) => void;
}) {
  const t = text(locale);
  return (
    <section
      aria-labelledby="store-title"
      data-testid="storefront"
      className="flex flex-col overflow-hidden rounded-2xl border border-line bg-panel/70 lg:h-[24rem]"
    >
      <div className="flex items-end justify-between gap-3 border-b border-line px-4 py-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-ion">{t.shopKicker}</p>
          <h2 id="store-title" className="text-lg font-semibold tracking-tight">
            {t.storeName}
          </h2>
        </div>
        <p className="max-w-[12rem] text-right font-mono text-[10px] uppercase tracking-wider text-mist">{t.storeLine}</p>
      </div>
      {error ? (
        <div className="p-5">
          <p className="text-sm text-mist">{t.emptyProducts}</p>
          <button type="button" onClick={onRetry} className="mt-3 text-sm text-signal">
            {t.retry}
          </button>
        </div>
      ) : (
        <ul className="min-h-0 flex-1 divide-y divide-line overflow-auto">
          {products.map((product) => (
            <li key={product.sku}>
              <article data-testid="product-card" className="grid grid-cols-[1fr_auto] items-center gap-3 px-4 py-3">
                <div className="min-w-0">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-mist">{product.sku}</p>
                  <h3 data-testid="product-name" className="truncate text-sm font-medium">
                    {product.name}
                  </h3>
                  <StockMeter stock={product.stock} label={product.stock <= 0 ? t.outOfStock : `${product.stock} ${t.inStock}`} />
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm text-snow">{formatMoney(product.price_cents, locale)}</p>
                  <button
                    type="button"
                    onClick={() => onAsk(questionFor(product.name, locale))}
                    className="mt-1 font-mono text-[10px] uppercase tracking-wider text-signal"
                  >
                    {t.ask}
                  </button>
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function StockMeter({ stock, label }: { stock: number; label: string }) {
  const width = `${Math.max(stock <= 0 ? 4 : 8, Math.min(100, (stock / 40) * 100))}%`;
  return (
    <div className="mt-2 flex items-center gap-2">
      <div className="h-1 w-24 overflow-hidden rounded-full bg-raise">
        <div className={`h-full ${stock <= 0 ? "bg-flare" : "bg-signal"}`} style={{ width }} />
      </div>
      <span className="font-mono text-[10px] text-mist">{label}</span>
    </div>
  );
}

export function questionFor(name: string, locale: Locale): string {
  if (locale === "en") return `How much is the ${name}?`;
  return `Quanto custa ${name}?`;
}
