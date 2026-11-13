"use client";

import type { ReactNode } from "react";
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
    <section aria-labelledby="trace-title" className="rounded-2xl border border-line bg-panel/80 p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-signal">{t.traceKicker}</p>
          <h2 id="trace-title" className="text-lg font-semibold tracking-tight">
            LangGraph
          </h2>
        </div>
        {response ? (
          <dl className="flex flex-wrap gap-2 font-mono text-[11px]">
            <Stat label={t.intent}>
              <span data-testid="trace-intent">{response.intent}</span>
            </Stat>
            <Stat label={t.confidence}>{Math.round(response.confidence * 100)}%</Stat>
            <Stat label={t.latency}>{Math.round(response.latency_ms)} ms</Stat>
            <Stat label={t.tokens}>
              {tokens}
              {response.usage.estimated ? ` ${t.estimated}` : ""}
            </Stat>
          </dl>
        ) : null}
      </div>
      {shown.length === 0 ? (
        <p className="mt-4 text-sm text-mist">{t.noTrace}</p>
      ) : (
        <ol className="mt-5 flex flex-col gap-2 lg:flex-row lg:items-stretch lg:overflow-x-auto lg:pb-1">
          {shown.map((node, index) => {
            const live = streaming && index === shown.length - 1;
            return (
              <li key={`${node.name}-${index}`} className="node-in flex items-center gap-2">
                <article
                  data-testid="trace-node"
                  className={`w-full min-w-0 rounded-xl border px-3 py-2.5 lg:w-auto lg:min-w-[9.5rem] ${
                    live ? "node-live border-signal bg-signal/15" : "border-line bg-raise"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${live ? "bg-signal" : "bg-signal/80"}`} />
                    <span className="font-mono text-[10px] text-mist">{String(index + 1).padStart(2, "0")}</span>
                  </div>
                  <p className="mt-2 whitespace-nowrap font-mono text-[11px] text-snow">{node.name}</p>
                  <p className="mt-0.5 text-[11px] text-mist">{nodeLabel[node.name]?.[locale] ?? node.name}</p>
                  {node.tools.length > 0 ? (
                    <p className="mt-1 truncate font-mono text-[10px] text-ion">{node.tools[0]}</p>
                  ) : (
                    <p className="mt-1 font-mono text-[10px] text-mist">{node.latency_ms.toFixed(0)} ms</p>
                  )}
                </article>
                {index < shown.length - 1 ? (
                  <span aria-hidden="true" className="hidden h-px w-3 shrink-0 bg-signal/80 lg:block" />
                ) : null}
              </li>
            );
          })}
        </ol>
      )}
      {response && response.tools.length > 0 ? (
        <p className="mt-3 font-mono text-[11px] text-mist">
          {t.tools} {response.tools.map((tool) => tool.tool).join(" · ")}
          {response.guard_rewritten ? ` · ${t.rewritten}` : ""}
          {response.blocked ? ` · ${t.blocked}` : ""}
        </p>
      ) : null}
    </section>
  );
}

function Stat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-line bg-void/50 px-2 py-1 text-mist">
      <span className="mr-1 uppercase tracking-wider">{label}</span>
      <span className="text-snow">{children}</span>
    </div>
  );
}
