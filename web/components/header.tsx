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

  const mode = health == null ? "…" : health.provider === "fake" ? t.demo : health.model;

  return (
    <header className="sticky top-0 z-20 border-b border-line/80 bg-void/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
        <Link href="/" className="flex items-center gap-2.5">
          <Mark />
          <span className="text-sm font-semibold tracking-tight">ShopMind</span>
        </Link>
        <nav className="ml-auto flex items-center gap-1.5 text-sm">
          <span className="hidden sm:contents">
            <NavLink href="/" current={path === "/"} label={t.shop} />
          </span>
          <NavLink href="/evals" current={path === "/evals"} label={t.evals} />
          <span className="ml-1 hidden items-center gap-2 rounded-md border border-line bg-panel px-2.5 py-1 font-mono text-[11px] text-mist sm:inline-flex">
            <span
              className={`h-1.5 w-1.5 rounded-full ${health?.provider === "fake" ? "bg-signal" : "bg-ion"} ${health ? "node-live" : ""}`}
            />
            {mode}
          </span>
          <div className="ml-1 flex rounded-md border border-line p-0.5 font-mono text-[11px]">
            <LocaleButton active={locale === "pt"} onClick={() => setLocale("pt")} label="PT" />
            <LocaleButton active={locale === "en"} onClick={() => setLocale("en")} label="EN" />
          </div>
        </nav>
      </div>
    </header>
  );
}

function NavLink({ href, current, label }: { href: string; current: boolean; label: string }) {
  return (
    <Link
      href={href}
      aria-current={current ? "page" : undefined}
      className={`rounded-md px-2.5 py-1 text-xs ${current ? "bg-signal text-void" : "text-mist hover:text-snow"}`}
    >
      {label}
    </Link>
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
      className={`rounded px-2 py-1 ${active ? "bg-raise text-signal" : "text-mist"}`}
    >
      {label}
    </button>
  );
}

function Mark() {
  return (
    <svg viewBox="0 0 28 28" className="h-7 w-7" aria-hidden="true">
      <rect width="28" height="28" rx="7" fill="#10151e" stroke="#2a3548" />
      <circle cx="7" cy="14" r="1.6" fill="#3ef0c1" />
      <circle cx="14" cy="9" r="1.6" fill="#7eb0ff" />
      <circle cx="21" cy="16" r="1.6" fill="#3ef0c1" />
      <path d="M8.5 14h4l1.6-5 3.4 11 1.6-5h2" stroke="#f4f7fb" strokeWidth="1.2" fill="none" />
    </svg>
  );
}
