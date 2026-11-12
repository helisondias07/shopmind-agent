export type Locale = "pt" | "en";

export type PublicProduct = {
  sku: string;
  name: string;
  price_cents: number;
  currency: string;
  stock: number;
  category: string;
  image_key: string;
  blurb: string;
  weight_grams: number;
};

export type Source = {
  id: string;
  title: string;
  snippet: string;
  kind: "catalog" | "policy" | "order" | "shipping";
};

export type NodeTrace = {
  name: string;
  latency_ms: number;
  detail: string;
  tools: string[];
};

export type ToolTrace = {
  tool: string;
  summary: string;
};

export type TokenUsage = {
  prompt: number;
  completion: number;
  estimated: boolean;
};

export type ChatResponse = {
  reply: string;
  session_id: string;
  intent: string;
  confidence: number;
  locale: Locale;
  handoff: boolean;
  handoff_reason: string | null;
  protocol: string | null;
  sources: Source[];
  products: PublicProduct[];
  recommendations: PublicProduct[];
  tools: ToolTrace[];
  nodes: NodeTrace[];
  usage: TokenUsage;
  latency_ms: number;
  provider: string;
  guard_rewritten: boolean;
  blocked: boolean;
  redacted_card: boolean;
};

export type HealthResponse = {
  status: string;
  version: string;
  provider: string;
  model: string;
  embeddings: string;
  vector_store: string;
  handoff_confidence: number;
};

export type EvalCaseResult = {
  id: string;
  passed: boolean;
  intent: string;
  handoff: boolean;
  errors: string[];
  reply: string;
};

export type EvalReport = {
  provider: string;
  total: number;
  passed: number;
  failed: number;
  results: EvalCaseResult[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
  streaming?: boolean;
};

export type HistoryItem = {
  role: "user" | "assistant";
  content: string;
};
