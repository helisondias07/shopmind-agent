"use client";

import { FormEvent, useEffect, useRef } from "react";
import { stepLabel, text } from "@/lib/copy";
import { formatMoney } from "@/lib/format";
import type { ChatMessage, Locale, NodeTrace, PublicProduct } from "@/lib/types";
import { ProductFigure } from "./figures";

export function Stage({ product, locale }: { product: PublicProduct | undefined; locale: Locale }) {
  if (!product) return <section className="stage" aria-hidden="true" />;
  const t = text(locale);
  const stockLine =
    product.stock <= 0
      ? t.outOfStock
      : locale === "pt"
        ? `${product.stock} un em estoque`
        : `${product.stock} in stock`;
  return (
    <section className="stage" aria-label={product.name}>
      <div className="stage-light" aria-hidden="true" />
      <div className="figure-wrap">
        <ProductFigure imageKey={product.image_key} label={product.name} />
      </div>
      <div className="hero-copy">
        <h1 data-testid="product-name">{product.name}</h1>
        <div className="ticket">
          <div className="eyelet" aria-hidden="true" />
          <div className="sku">{product.sku}</div>
          <div className="price">{formatMoney(product.price_cents, locale)}</div>
          <div className="stock">{stockLine}</div>
        </div>
      </div>
    </section>
  );
}

export function Desk({
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
  const pairs = pairMessages(messages);

  useEffect(() => {
    const node = scroller.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages]);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSend(draft);
  }

  return (
    <aside className="desk" aria-label={t.deskTitle}>
      <h2>{t.deskTitle}</h2>
      <div className="transcript" ref={scroller} aria-live="polite">
        {pairs.length === 0 ? (
          <div className="empty-desk">
            <p>{t.empty}</p>
            <div className="prompts">
              {t.suggestions.map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => onSend(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          pairs.map((pair) => <Turn key={pair.id} pair={pair} locale={locale} />)
        )}
      </div>
      <form className="composer" onSubmit={submit}>
        <label className="sr-only" htmlFor="chat-input">
          {t.placeholder}
        </label>
        <input
          id="chat-input"
          data-testid="chat-input"
          value={draft}
          placeholder={t.placeholder}
          onChange={(event) => onDraft(event.target.value)}
        />
        <button type="submit" data-testid="chat-send" disabled={busy || draft.trim().length === 0}>
          {t.send}
        </button>
      </form>
      {error ? <p className="desk-error">{t.deskError}</p> : null}
      <div className="handoff-row">
        <p>{t.handoffNote}</p>
        <button type="button" data-testid="handoff-call" onClick={() => onSend(t.handoffCall)}>
          {t.handoffButton}
        </button>
      </div>
    </aside>
  );
}

function Turn({
  pair,
  locale,
}: {
  pair: { id: string; question: string; answer: ChatMessage | undefined };
  locale: Locale;
}) {
  const t = text(locale);
  const answer = pair.answer;
  const response = answer?.response;
  const body = response ? stripSourceLine(answer.content) : (answer?.content ?? "");
  return (
    <article className="turn">
      <p className="question">
        <span className="who">{t.who}</span>
        {pair.question}
      </p>
      {answer ? (
        <div data-testid="assistant-reply">
          <p className="answer">{body || (answer.streaming ? "…" : "")}</p>
          {response && response.sources.length > 0 ? (
            <p className="source">
              {t.source}:{" "}
              {response.sources.map((source, index) => (
                <span key={source.id}>
                  {index > 0 ? ", " : null}
                  <span data-testid="source-chip">{source.title}</span>
                </span>
              ))}
            </p>
          ) : null}
          {response?.handoff ? (
            <div className="handoff-card" data-testid="handoff-banner">
              <p>{t.handoffArrived}</p>
              {response.protocol ? (
                <p className="protocol">
                  {t.protocol} {response.protocol}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export function Shelf({
  locale,
  products,
  onAsk,
}: {
  locale: Locale;
  products: PublicProduct[];
  onAsk: (product: PublicProduct) => void;
}) {
  const t = text(locale);
  if (products.length === 0) return null;
  return (
    <section className="shelf" aria-label={locale === "pt" ? "Outras peças" : "Other pieces"}>
      {products.map((product) => (
        <article key={product.sku} className="tag" data-testid="product-card">
          <div className="sku">{product.sku}</div>
          <h3>{product.name}</h3>
          <div className="tag-row">
            <span className="tag-price">{formatMoney(product.price_cents, locale)}</span>
            <span>{product.stock <= 0 ? t.outOfStock : `${product.stock} ${t.units}`}</span>
          </div>
          <button type="button" onClick={() => onAsk(product)}>
            {t.ask}
          </button>
        </article>
      ))}
    </section>
  );
}

export function Path({ locale, nodes, intent }: { locale: Locale; nodes: NodeTrace[]; intent: string }) {
  const t = text(locale);
  const steps = collapseSteps(nodes, locale);
  if (steps.length === 0) {
    return (
      <p className="path-empty">
        <span className="sr-only" data-testid="trace-intent">
          {intent}
        </span>
        {t.pathEmpty}
      </p>
    );
  }
  return (
    <ol className="path" aria-label={t.pathLabel}>
      <li className="sr-only" data-testid="trace-intent">
        {intent}
      </li>
      {steps.map((step, index) => (
          <li key={`${step.name}-${index}`}>
          {index > 0 ? <span className="rule" aria-hidden="true" /> : null}
          <span
            data-testid="trace-node"
            className={index === steps.length - 1 ? "is-on is-now" : "is-on"}
          >
            <b>{index + 1}</b>
            {step.label}
            <span className="sr-only">{step.name}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}

function collapseSteps(nodes: NodeTrace[], locale: Locale) {
  const steps: { name: string; label: string }[] = [];
  for (const node of nodes) {
    if (node.name === "guard_output" && steps.some((step) => step.name === "compose_answer")) {
      continue;
    }
    const label = stepLabel[node.name]?.[locale] ?? node.name;
    if (steps.at(-1)?.label === label) continue;
    steps.push({ name: node.name, label });
  }
  return steps;
}

function pairMessages(messages: ChatMessage[]) {
  const pairs: { id: string; question: string; answer: ChatMessage | undefined }[] = [];
  for (let index = 0; index < messages.length; index += 1) {
    const message = messages[index];
    if (message.role !== "user") continue;
    const next = messages[index + 1];
    pairs.push({
      id: message.id,
      question: message.content,
      answer: next?.role === "assistant" ? next : undefined,
    });
  }
  return pairs;
}

function stripSourceLine(reply: string) {
  return reply
    .split("\n")
    .filter((line) => !/^(fonte|source):/i.test(line.trim()))
    .join("\n")
    .trim();
}

export function questionFor(name: string, locale: Locale) {
  if (locale === "en") return `How much is the ${name}?`;
  return `Quanto custa ${name}?`;
}
