"use client";

import { useCallback, useEffect, useState } from "react";
import { text } from "@/lib/copy";
import { streamChat } from "@/lib/stream";
import type { ChatMessage, ChatResponse, NodeTrace, PublicProduct } from "@/lib/types";
import { ChatPanel } from "./chat-panel";
import { useLocale } from "./locale";
import { Storefront } from "./storefront";
import { TracePanel } from "./trace-panel";

const SESSION_KEY = "shopmind-session";

export function DemoApp() {
  const { locale } = useLocale();
  const t = text(locale);
  const [tab, setTab] = useState<"shop" | "chat" | "trace">("shop");
  const [products, setProducts] = useState<PublicProduct[]>([]);
  const [productError, setProductError] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatError, setChatError] = useState(false);
  const [liveNodes, setLiveNodes] = useState<NodeTrace[]>([]);
  const [last, setLast] = useState<ChatResponse | null>(null);
  const [sessionId, setSessionId] = useState("web");
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
      setTab("chat");
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

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-4 grid grid-cols-3 gap-2 lg:hidden">
        <TabButton active={tab === "shop"} onClick={() => setTab("shop")} label={t.shop} testId="tab-shop" />
        <TabButton active={tab === "chat"} onClick={() => setTab("chat")} label={t.chat} testId="tab-chat" />
        <TabButton active={tab === "trace"} onClick={() => setTab("trace")} label={t.trace} testId="tab-trace" />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
        <div className={tab === "shop" ? "block" : "hidden lg:block"}>
          <Storefront
            locale={locale}
            products={products}
            error={productError}
            onRetry={() => setReloadKey((value) => value + 1)}
            onAsk={(question) => void send(question)}
          />
        </div>
        <div className={tab === "chat" ? "block" : "hidden lg:block"}>
          <ChatPanel
            locale={locale}
            messages={messages}
            draft={draft}
            busy={busy}
            error={chatError}
            onDraft={setDraft}
            onSend={(value) => void send(value)}
          />
        </div>
      </div>
      <div className={`mt-6 ${tab === "trace" ? "block" : "hidden lg:block"}`}>
        <TracePanel locale={locale} nodes={liveNodes} response={last} streaming={busy} />
      </div>
      <p className="mt-8 text-center text-xs text-ink/45">{t.footer}</p>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  label,
  testId,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  testId: string;
}) {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full px-3 py-2 text-sm ${active ? "bg-ink text-cream" : "bg-white/50 text-ink/70"}`}
    >
      {label}
    </button>
  );
}
