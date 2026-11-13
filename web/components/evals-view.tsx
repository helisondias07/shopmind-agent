"use client";

import { useCallback, useEffect, useState } from "react";
import { text } from "@/lib/copy";
import type { EvalReport } from "@/lib/types";
import { useLocale } from "./locale";

export function EvalsView() {
  const { locale } = useLocale();
  const t = text(locale);
  const [report, setReport] = useState<EvalReport | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  const load = useCallback(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(false);
    fetch("/api/evals", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("evals");
        return response.json() as Promise<EvalReport>;
      })
      .then((body) => {
        if (!controller.signal.aborted) setReport(body);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  useEffect(() => load(), [load, nonce]);

  const ratio = report && report.total > 0 ? report.passed / report.total : 0;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-signal">{t.evals}</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">{t.evalTitle}</h1>
      <p className="mt-3 max-w-xl text-sm leading-6 text-mist">{t.evalLine}</p>
      <div className="mt-6 flex items-center gap-4">
        <div
          className="grid h-20 w-20 place-items-center rounded-full"
          style={{ background: `conic-gradient(#3ef0c1 ${ratio * 360}deg, #182131 0deg)` }}
          aria-hidden="true"
        >
          <span className="grid h-14 w-14 place-items-center rounded-full bg-void font-mono text-lg text-snow">
            {report ? report.passed : "–"}
          </span>
        </div>
        <div>
          <p className="font-mono text-sm text-mist" data-testid="eval-summary">
            {report ? `${report.passed}/${report.total} ${t.passed}` : loading ? t.running : "—"}
          </p>
          <button type="button" onClick={() => setNonce((value) => value + 1)} className="mt-2 text-sm text-signal">
            {loading ? t.running : t.runAgain}
          </button>
        </div>
      </div>
      {error ? <p className="mt-6 text-sm text-flare">{t.error}</p> : null}
      <ul className="mt-8 divide-y divide-line rounded-2xl border border-line bg-panel/70">
        {report?.results.map((item) => (
          <li key={item.id} className="px-4 py-4" data-testid="eval-case">
            <div className="flex items-baseline justify-between gap-3">
              <h2 className="font-mono text-sm">{item.id}</h2>
              <span className={item.passed ? "font-mono text-xs text-signal" : "font-mono text-xs text-flare"}>
                {item.passed ? t.passed : t.failed}
              </span>
            </div>
            <p className="mt-1 font-mono text-[10px] uppercase tracking-wider text-mist">
              {item.intent}
              {item.handoff ? " · handoff" : ""}
            </p>
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-snow/80">{item.reply}</p>
            {item.errors.length > 0 ? <p className="mt-2 text-xs text-flare">{item.errors.join(" · ")}</p> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
