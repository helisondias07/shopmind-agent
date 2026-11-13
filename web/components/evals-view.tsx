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

  return (
    <section className="evals">
      <h1>{t.evalTitle}</h1>
      <p className="lead">{t.evalLead}</p>
      <div className="eval-score">
        <strong data-testid="eval-summary">
          {report ? `${report.passed}/${report.total} ${t.passed}` : loading ? t.running : "—"}
        </strong>
        <button type="button" onClick={() => setNonce((value) => value + 1)}>
          {loading ? t.running : t.runAgain}
        </button>
      </div>
      {error ? <p className="catalog-error">{t.deskError}</p> : null}
      <ul className="eval-list">
        {report?.results.map((item) => (
          <li key={item.id} data-testid="eval-case">
            <div className="eval-meta">
              <h2>{item.id}</h2>
              <span className={item.passed ? "passed" : "failed"}>{item.passed ? t.passed : t.failed}</span>
            </div>
            <p className="eval-reply">{item.reply}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
