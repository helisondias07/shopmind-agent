"use client";

import { useCallback, useEffect, useState } from "react";
import { text } from "@/lib/copy";
import { streamChat } from "@/lib/stream";
import type { ChatMessage, ChatResponse, NodeTrace, PublicProduct } from "@/lib/types";
import { useLocale } from "./locale";
import { Desk, Path, Shelf, Stage, questionFor } from "./showroom";

const SESSION_KEY = "shopmind-session";

export function DemoApp() {
  const { locale } = useLocale();
  const t = text(locale);
  const [products, setProducts] = useState<PublicProduct[]>([]);
  const [productError, setProductError] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatError, setChatError] = useState(false);
  const [liveNodes, setLiveNodes] = useState<NodeTrace[]>([]);
  const [last, setLast] = useState<ChatResponse | null>(null);
  const [sessionId, setSessionId] = useState("web");
  const [featuredSku, setFeaturedSku] = useState("LUME-LAMP");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const existing = window.sessionStorage.getItem(SESSION_KEY);
    const next = existing ?? crypto.randomUUID();
    if (!existing) window.sessionStorage.setItem(SESSION_KEY, next);
    setSessionId(next);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setProductError(false);
    fetch(`/api/products?locale=${locale}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("products");
        return response.json() as Promise<{ products: PublicProduct[] }>;
      })
      .then((body) => {
        if (!controller.signal.aborted) setProducts(body.products);
      })
      .catch(() => {
        if (!controller.signal.aborted) setProductError(true);
      });
    return () => controller.abort();
  }, [locale, reloadKey]);

  const send = useCallback(
    async (value: string) => {
      const message = value.trim();
      if (!message || busy) return;
      const history = messages
        .filter((item) => item.content.trim().length > 0)
        .slice(-8)
        .map((item) => ({ role: item.role, content: item.content }));
      const userId = crypto.randomUUID();
      const assistantId = crypto.randomUUID();
      setMessages((current) => [
        ...current,
        { id: userId, role: "user", content: message },
        { id: assistantId, role: "assistant", content: "", streaming: true },
      ]);
      setDraft("");
      setBusy(true);
      setChatError(false);
      setLiveNodes([]);
      try {
        await streamChat(
          { message, session_id: sessionId, locale, history },
          (event) => {
            if (event.event === "node") {
              setLiveNodes((current) => [...current, event.data]);
            } else if (event.event === "token") {
              setMessages((current) =>
                current.map((item) =>
                  item.id === assistantId ? { ...item, content: item.content + event.data.text } : item,
                ),
              );
            } else if (event.event === "done") {
              const sku = event.data.products[0]?.sku;
              if (sku) setFeaturedSku(sku);
              setLast(event.data);
              setMessages((current) =>
                current.map((item) =>
                  item.id === assistantId
                    ? { ...item, content: event.data.reply, response: event.data, streaming: false }
                    : item,
                ),
              );
            }
          },
        );
      } catch {
        setChatError(true);
        setMessages((current) => current.filter((item) => item.id !== assistantId));
      } finally {
        setBusy(false);
      }
    },
    [busy, locale, messages, sessionId],
  );

  const featured = products.find((product) => product.sku === featuredSku) ?? products[0];
  const shelf = products.filter((product) => product.sku !== featured?.sku);

  return (
    <>
      {productError ? (
        <p className="catalog-error">
          {t.catalogError}
          <button type="button" onClick={() => setReloadKey((value) => value + 1)}>
            {t.retry}
          </button>
        </p>
      ) : null}
      <div className="stage-row">
        <Stage product={featured} locale={locale} />
        <Desk
          locale={locale}
          messages={messages}
          draft={draft}
          busy={busy}
          error={chatError}
          onDraft={setDraft}
          onSend={(value) => void send(value)}
        />
      </div>
      <Shelf
        locale={locale}
        products={shelf}
        onAsk={(product) => {
          setFeaturedSku(product.sku);
          void send(questionFor(product.name, locale));
        }}
      />
      <Path locale={locale} nodes={liveNodes.length > 0 ? liveNodes : (last?.nodes ?? [])} intent={last?.intent ?? ""} />
    </>
  );
}
