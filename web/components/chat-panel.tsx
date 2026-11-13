"use client";

import { FormEvent, useEffect, useRef } from "react";
import { text } from "@/lib/copy";
import { formatMoney } from "@/lib/format";
import type { ChatMessage, Locale, PublicProduct, Source } from "@/lib/types";

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
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = scroller.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages]);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSend(draft);
  }

  return (
    <section
      aria-labelledby="chat-title"
      className="flex h-[28rem] flex-col overflow-hidden rounded-2xl border border-line bg-panel/90 lg:h-[24rem]"
    >
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-signal">{t.chatKicker}</p>
          <h2 id="chat-title" className="text-lg font-semibold tracking-tight">
            ShopMind
          </h2>
        </div>
        <span className="font-mono text-[10px] uppercase tracking-wider text-mist">{busy ? t.live : "idle"}</span>
      </div>
      <div ref={scroller} className="flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite">
        {messages.length === 0 ? (
          <div>
            <p className="max-w-sm text-sm leading-6 text-mist">{t.intro}</p>
            <div className="mt-4 flex flex-col gap-2">
              {t.suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => onSend(suggestion)}
                  className="rounded-lg border border-line bg-void/40 px-3 py-2 text-left font-mono text-[12px] text-snow hover:border-signal/50"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : null}
        {messages.map((message) =>
          message.role === "user" ? (
            <p key={message.id} className="ml-8 rounded-lg border border-ion/30 bg-ion/10 px-3 py-2 text-sm leading-6">
              {message.content}
            </p>
          ) : (
            <AssistantBubble key={message.id} message={message} locale={locale} />
          ),
        )}
        {error ? <p className="text-sm text-flare">{t.error}</p> : null}
      </div>
      <form onSubmit={submit} className="border-t border-line p-3">
        <label htmlFor="chat-input" className="sr-only">
          {t.placeholder}
        </label>
        <div className="flex items-end gap-2 rounded-xl border border-line bg-void/70 p-2">
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
            className="max-h-28 flex-1 resize-none bg-transparent px-2 py-1 text-sm text-snow outline-none placeholder:text-mist/70"
          />
          <button
            type="submit"
            data-testid="chat-send"
            disabled={busy || draft.trim().length === 0}
            className="rounded-lg bg-signal px-3 py-2 text-sm font-semibold text-void disabled:opacity-40"
          >
            {busy ? "…" : t.send}
          </button>
        </div>
      </form>
    </section>
  );
}

function AssistantBubble({ message, locale }: { message: ChatMessage; locale: Locale }) {
  const t = text(locale);
  const response = message.response;
  const streaming = Boolean(message.streaming);
  return (
    <div className="mr-2 border-l-2 border-signal pl-3" data-testid="assistant-reply">
      <p className={`whitespace-pre-wrap text-sm leading-6 ${streaming ? "caret" : ""}`}>
        {message.content || (streaming ? t.thinking : "")}
      </p>
      {response?.handoff ? (
        <div
          data-testid="handoff-banner"
          className="mt-3 rounded-xl border border-flare/50 bg-flare/10 px-3 py-3"
        >
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-flare">{t.handoff}</p>
          {response.protocol ? (
            <p className="mt-1 font-mono text-sm text-snow">
              {t.protocol} {response.protocol}
            </p>
          ) : null}
        </div>
      ) : null}
      {response && response.products.length > 0 ? (
        <MiniCards products={response.products} locale={locale} />
      ) : null}
      {response && response.recommendations.length > 0 ? (
        <div className="mt-3">
          <p className="mb-2 font-mono text-[10px] uppercase tracking-[0.16em] text-mist">{t.recommendations}</p>
          <MiniCards products={response.recommendations} locale={locale} />
        </div>
      ) : null}
      {response && response.sources.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
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
    <ul className="mt-3 grid gap-2">
      {products.map((product) => (
        <li key={product.sku} className="flex items-center justify-between gap-3 rounded-lg border border-line bg-void/50 px-3 py-2">
          <span className="min-w-0">
            <span className="block truncate text-sm">{product.name}</span>
            <span className="font-mono text-[10px] text-mist">{product.sku}</span>
          </span>
          <span className="shrink-0 text-right font-mono text-xs">
            <span className="block text-signal">{formatMoney(product.price_cents, locale)}</span>
            <span className="text-mist">{product.stock}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

function SourceChip({ source }: { source: Source }) {
  return (
    <details className="rounded-md border border-line bg-void/40 px-2.5 py-1 text-xs text-mist">
      <summary data-testid="source-chip" className="cursor-pointer font-mono text-[11px] text-ion">
        {source.id}
      </summary>
      <p className="mt-2 max-w-xs pb-1 leading-5 text-snow/80">{source.snippet}</p>
    </details>
  );
}
