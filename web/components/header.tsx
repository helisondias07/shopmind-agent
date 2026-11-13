"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { text } from "@/lib/copy";
import { useLocale } from "./locale";

export function Header() {
  const { locale, setLocale } = useLocale();
  const t = text(locale);
  const path = usePathname();

  return (
    <header className="topbar">
      <Link href="/" className="wordmark">
        Lume
      </Link>
      <div className="topbar-side">
        <p className="demo-note">{t.demoNote}</p>
        <Link href="/evals" className="quiet-link" aria-current={path === "/evals" ? "page" : undefined}>
          {t.evals}
        </Link>
        <div className="langs">
          <button
            type="button"
            data-testid="locale-pt"
            aria-current={locale === "pt" ? "true" : undefined}
            onClick={() => setLocale("pt")}
          >
            PT
          </button>
          <button
            type="button"
            data-testid="locale-en"
            aria-current={locale === "en" ? "true" : undefined}
            onClick={() => setLocale("en")}
          >
            EN
          </button>
        </div>
      </div>
    </header>
  );
}
