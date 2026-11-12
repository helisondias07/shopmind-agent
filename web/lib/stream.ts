import type { ChatResponse, HistoryItem, Locale, NodeTrace } from "./types";

export type StreamEvent =
  | { event: "node"; data: NodeTrace }
  | { event: "token"; data: { text: string } }
  | { event: "done"; data: ChatResponse };

type ChatBody = {
  message: string;
  session_id: string;
  locale: Locale | "auto";
  history: HistoryItem[];
};

export async function streamChat(
  body: ChatBody,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      accept: "text/event-stream",
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`chat ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const parsed = parseFrame(frame);
      if (parsed) onEvent(parsed);
    }
  }
}

function parseFrame(frame: string): StreamEvent | null {
  let eventName = "";
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!eventName || dataLines.length === 0) return null;
  const data = JSON.parse(dataLines.join("\n")) as StreamEvent["data"];
  if (eventName === "node") return { event: "node", data: data as NodeTrace };
  if (eventName === "token") return { event: "token", data: data as { text: string } };
  if (eventName === "done") return { event: "done", data: data as ChatResponse };
  return null;
}
