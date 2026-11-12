"use client";

import { text } from "@/lib/copy";
import { formatMoney, stockLabel } from "@/lib/format";
import type { Locale, PublicProduct } from "@/lib/types";
import { ProductMark, tintFor } from "./marks";

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
    <section aria-labelledby="store-title" data-testid="storefront">
      <p className="text-[11px] uppercase tracking-[0.2em] text-moss">{t.shopKicker}</p>
      <div className="mt-1 flex items-end justify-between gap-4">
        <h1 id="store-title" className="font-serif text-4xl tracking-tight sm:text-5xl">
          {t.storeName}
        </h1>
        <p className="max-w-[14rem] text-right text-sm text-ink/70">{t.storeLine}</p>
      </div>
      <p className="mt-4 max-w-xl text-sm leading-6 text-ink/80">{t.intro}</p>
      {error ? (
        <div className="mt-6 rounded-2xl border border-dashed border-ink/20 p-6">
          <p>{t.emptyProducts}</p>
          <button type="button" onClick={onRetry} className="mt-3 text-sm underline">
            {t.retry}
          </button>
        </div>
      ) : (
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {products.map((product, index) => (
            <li key={product.sku}>
              <article
                data-testid="product-card"
                className="flex h-full gap-3 rounded-2xl border border-ink/10 bg-white/40 p-3"
              >
                <div className={`grid h-20 w-20 shrink-0 place-items-center rounded-xl ${tintFor(product.category)}`}>
                  <ProductMark id={product.image_key} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-serif text-xs text-ink/40">{String(index + 1).padStart(2, "0")}</p>
                  <h2 data-testid="product-name" className="truncate font-serif text-xl leading-tight">
                    {product.name}
                  </h2>
                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-ink/70">{product.blurb}</p>
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <p className="text-sm">
                      <span className="font-medium">{formatMoney(product.price_cents, locale)}</span>
                      <span className="ml-2 text-xs text-ink/55">
                        {stockLabel(product.stock, t.inStock, t.outOfStock)}
                      </span>
                    </p>
                    <button
                      type="button"
                      onClick={() => onAsk(questionFor(product.name, locale))}
                      className="text-xs uppercase tracking-wider text-moss"
                    >
                      {t.ask}
                    </button>
                  </div>
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function questionFor(name: string, locale: Locale): string {
  if (locale === "en") return `How much is the ${name}?`;
  return `Quanto custa ${name}?`;
}
