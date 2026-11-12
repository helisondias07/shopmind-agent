"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { text } from "@/lib/copy";
import type { HealthResponse } from "@/lib/types";
import { useLocale } from "./locale";

export function Header() {
  const { locale, setLocale } = useLocale();
  const t = text(locale);
  const path = usePathname();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((response) => (response.ok ? response.json() : null))
      .then((body: HealthResponse | null) => {
        if (!controller.signal.aborted) setHealth(body);
      })
      .catch(() => {
        if (!controller.signal.aborted) setHealth(null);
      });
    return () => controller.abort();
  }, []);
  const mode =
    health == null ? "…" : health.provider === "fake" ? t.demo : health.model;

  return (
    <header className="border-b border-ink/10">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-4">
        <Link href="/" className="group flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-moss text-cream">
            <LampIcon />
          </span>
          <span>
            <span className="block font-serif text-xl leading-none tracking-tight">ShopMind</span>
            <span className="text-[11px] uppercase tracking-[0.18em] text-ink/60">{t.storeName}</span>
          </span>
        </Link>
        <nav className="ml-auto flex items-center gap-2 text-sm">
          <Link
            href="/"
            className={`rounded-full px-3 py-1 ${path === "/" ? "bg-ink text-cream" : "text-ink/70"}`}
            aria-current={path === "/" ? "page" : undefined}
          >
            {t.storeName}
          </Link>
          <Link
            href="/evals"
            className={`rounded-full px-3 py-1 ${path === "/evals" ? "bg-ink text-cream" : "text-ink/70"}`}
            aria-current={path === "/evals" ? "page" : undefined}
          >
            {t.evals}
          </Link>
          <span className="hidden items-center gap-2 rounded-full border border-ink/15 px-3 py-1 text-xs text-ink/70 sm:inline-flex">
            <span className={`h-1.5 w-1.5 rounded-full ${health?.provider === "fake" ? "bg-clay" : "bg-moss"}`} />
            {mode}
          </span>
          <div className="flex rounded-full border border-ink/15 p-0.5 text-xs">
            <LocaleButton active={locale === "pt"} onClick={() => setLocale("pt")} label="PT" />
            <LocaleButton active={locale === "en"} onClick={() => setLocale("en")} label="EN" />
          </div>
        </nav>
      </div>
    </header>
  );
}

function LocaleButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      data-testid={`locale-${label.toLowerCase()}`}
      className={`rounded-full px-2.5 py-1 ${active ? "bg-moss text-cream" : "text-ink/60"}`}
    >
      {label}
    </button>
  );
}

function LampIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
      <path d="M12 3v5M7 8h10M8.5 8c.4 5 1.4 8 3.5 8s3.1-3 3.5-8" stroke="currentColor" strokeWidth="1.4" fill="none" />
    </svg>
  );
}
