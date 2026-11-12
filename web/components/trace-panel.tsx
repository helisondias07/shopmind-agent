"use client";

import { nodeLabel, text } from "@/lib/copy";
import type { ChatResponse, Locale, NodeTrace } from "@/lib/types";

export function TracePanel({
  locale,
  nodes,
  response,
  streaming,
}: {
  locale: Locale;
  nodes: NodeTrace[];
  response: ChatResponse | null;
  streaming: boolean;
}) {
  const t = text(locale);
  const shown = nodes.length > 0 ? nodes : (response?.nodes ?? []);
  const tokens = (response?.usage.prompt ?? 0) + (response?.usage.completion ?? 0);

  return (
    <section aria-labelledby="trace-title" className="rounded-[1.4rem] border border-ink/10 bg-white/45 p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-clay">{t.traceKicker}</p>
          <h2 id="trace-title" className="font-serif text-2xl">
            LangGraph
          </h2>
        </div>
        {response ? (
          <dl className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink/70">
            <div>
              <dt className="inline">{t.intent} </dt>
              <dd className="inline font-medium text-ink" data-testid="trace-intent">
                {response.intent}
              </dd>
            </div>
            <div>
              <dt className="inline">{t.confidence} </dt>
              <dd className="inline font-medium text-ink">{Math.round(response.confidence * 100)}%</dd>
            </div>
            <div>
              <dt className="inline">{t.latency} </dt>
              <dd className="inline font-medium text-ink">{Math.round(response.latency_ms)} ms</dd>
            </div>
            <div>
              <dt className="inline">{t.tokens} </dt>
              <dd className="inline font-medium text-ink">
                {tokens}
                {response.usage.estimated ? ` · ${t.estimated}` : ""}
              </dd>
            </div>
          </dl>
        ) : null}
      </div>
      {shown.length === 0 ? (
        <p className="mt-4 text-sm text-ink/60">{t.noTrace}</p>
      ) : (
        <ol className="mt-4 flex gap-2 overflow-x-auto pb-2">
          {shown.map((node, index) => (
            <li key={`${node.name}-${index}`} className="min-w-[8.5rem] shrink-0">
              <article
                data-testid="trace-node"
                className={`h-full rounded-xl border px-3 py-2 ${
                  streaming && index === shown.length - 1
                    ? "border-moss bg-moss text-cream"
                    : "border-ink/10 bg-paper"
                }`}
              >
                <p className="font-mono text-[11px]">{node.name}</p>
                <p className="mt-1 text-sm">{nodeLabel[node.name]?.[locale] ?? node.name}</p>
                <p className="mt-2 text-[11px] opacity-70">{node.latency_ms.toFixed(0)} ms</p>
                {node.tools.length > 0 ? (
                  <p className="mt-1 truncate font-mono text-[10px] opacity-80">{node.tools.join(" · ")}</p>
                ) : null}
              </article>
            </li>
          ))}
        </ol>
      )}
      {response && response.tools.length > 0 ? (
        <p className="mt-2 text-xs text-ink/60">
          {t.tools}: {response.tools.map((tool) => tool.tool).join(", ")}
          {response.guard_rewritten ? ` · ${t.rewritten}` : ""}
          {response.blocked ? ` · ${t.blocked}` : ""}
        </p>
      ) : null}
    </section>
  );
}
