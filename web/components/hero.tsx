"use client";

import { text } from "@/lib/copy";
import type { Locale } from "@/lib/types";

export function Hero({ locale }: { locale: Locale }) {
  const t = text(locale);
  return (
    <section className="relative overflow-hidden rounded-2xl border border-line bg-panel/80 p-4 shadow-signal sm:p-7">
      <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-signal">{t.heroKicker}</p>
      <h1 className="mt-2 max-w-3xl text-[1.65rem] font-semibold leading-[1.05] tracking-tight sm:mt-3 sm:text-4xl">
        {t.heroTitle}
      </h1>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-mist sm:mt-4 sm:text-base">{t.heroLine}</p>
      <ul className="mt-5 flex flex-wrap gap-2 font-mono text-[11px] text-mist">
        <li className="rounded-md border border-line bg-void/60 px-2.5 py-1">01 intent</li>
        <li className="rounded-md border border-line bg-void/60 px-2.5 py-1">02 tools</li>
        <li className="rounded-md border border-line bg-void/60 px-2.5 py-1">03 cited reply</li>
      </ul>
    </section>
  );
}
