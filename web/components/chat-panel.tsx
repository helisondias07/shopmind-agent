"use client";

import { FormEvent } from "react";
import { text } from "@/lib/copy";
import { formatMoney } from "@/lib/format";
import type { ChatMessage, Locale, PublicProduct, Source } from "@/lib/types";
import { ProductMark, tintFor } from "./marks";

export function ChatPanel({
  locale,
  messages,
  draft,
  busy,
  error,
  onDraft,
  onSend,
}: {
  locale: Locale;
  messages: ChatMessage[];
  draft: string;
  busy: boolean;
  error: boolean;
  onDraft: (value: string) => void;
  onSend: (value: string) => void;
}) {
  const t = text(locale);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSend(draft);
  }

  return (
    <section
      aria-labelledby="chat-title"
      className="flex min-h-[32rem] flex-col overflow-hidden rounded-[1.4rem] bg-chat text-cream shadow-panel lg:min-h-0 lg:h-[calc(100vh-15rem)]"
    >
      <div className="flex items-baseline justify-between px-5 pt-5">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-cream/50">{t.chatKicker}</p>
          <h2 id="chat-title" className="font-serif text-3xl">
            ShopMind
          </h2>
        </div>
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4" aria-live="polite">
        {messages.length === 0 ? (
          <div>
            <p className="max-w-sm text-sm leading-6 text-cream/75">{t.intro}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {t.suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => onSend(suggestion)}
                  className="rounded-full border border-cream/15 px-3 py-1.5 text-left text-xs text-cream/85 hover:border-cream/40"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : null}
        {messages.map((message) =>
          message.role === "user" ? (
            <p key={message.id} className="ml-8 rounded-2xl bg-moss px-4 py-3 text-sm leading-6">
              {message.content}
            </p>
          ) : (
            <AssistantBubble key={message.id} message={message} locale={locale} />
          ),
        )}
        {error ? <p className="text-sm text-clay">{t.error}</p> : null}
      </div>
      <form onSubmit={submit} className="border-t border-cream/10 p-3">
        <label htmlFor="chat-input" className="sr-only">
          {t.placeholder}
        </label>
        <div className="flex items-end gap-2 rounded-2xl bg-chat-raise p-2">
          <textarea
            id="chat-input"
            data-testid="chat-input"
            rows={2}
            value={draft}
            placeholder={t.placeholder}
            onChange={(event) => onDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                onSend(draft);
              }
            }}
            className="max-h-28 flex-1 resize-none bg-transparent px-2 py-1 text-sm outline-none placeholder:text-cream/35"
          />
          <button
            type="submit"
            data-testid="chat-send"
            disabled={busy || draft.trim().length === 0}
            className="rounded-full bg-cream px-4 py-2 text-sm text-ink disabled:opacity-40"
          >
            {busy ? t.thinking : t.send}
          </button>
        </div>
      </form>
    </section>
  );
}

function AssistantBubble({ message, locale }: { message: ChatMessage; locale: Locale }) {
  const t = text(locale);
  const response = message.response;
  return (
    <div className="mr-4 space-y-3" data-testid="assistant-reply">
      <p className="whitespace-pre-wrap text-sm leading-6 text-cream/90">
        {message.content || (message.streaming ? t.thinking : "")}
      </p>
      {response?.handoff ? (
        <p
          data-testid="handoff-banner"
          className="rounded-xl border border-clay/50 bg-clay/15 px-3 py-2 text-xs"
        >
          {t.handoff}
          {response.protocol ? ` · ${t.protocol} ${response.protocol}` : ""}
        </p>
      ) : null}
      {response && response.products.length > 0 ? (
        <MiniCards products={response.products} locale={locale} />
      ) : null}
      {response && response.recommendations.length > 0 ? (
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-[0.16em] text-cream/45">{t.recommendations}</p>
          <MiniCards products={response.recommendations} locale={locale} />
        </div>
      ) : null}
      {response && response.sources.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {response.sources.map((source) => (
            <SourceChip key={source.id} source={source} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function MiniCards({ products, locale }: { products: PublicProduct[]; locale: Locale }) {
  return (
    <ul className="grid gap-2">
      {products.map((product) => (
        <li key={product.sku} className="flex items-center gap-3 rounded-xl bg-chat-raise px-2 py-2">
          <span className={`grid h-10 w-10 place-items-center rounded-lg text-moss ${tintFor(product.category)}`}>
            <ProductMark id={product.image_key} className="h-8 w-8" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm">{product.name}</span>
            <span className="text-xs text-cream/55">
              {formatMoney(product.price_cents, locale)} · {product.stock}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

function SourceChip({ source }: { source: Source }) {
  return (
    <details className="rounded-full border border-cream/15 px-3 py-1 text-xs text-cream/75">
      <summary data-testid="source-chip" className="cursor-pointer list-none">
        {source.title}
      </summary>
      <p className="mt-2 max-w-xs pb-1 leading-5">{source.snippet}</p>
    </details>
  );
}
