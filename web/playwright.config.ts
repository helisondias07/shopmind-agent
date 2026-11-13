import { defineConfig, devices } from "@playwright/test";

const apiOrigin = process.env.SHOPMIND_API_ORIGIN ?? "http://127.0.0.1:8000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "sh -c 'if [ -x ../.venv/bin/python ]; then exec ../.venv/bin/python -m uvicorn index:app --host 127.0.0.1 --port 8000; else exec python3 -m uvicorn index:app --host 127.0.0.1 --port 8000; fi'",
      cwd: "../api",
      url: `${apiOrigin}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        ...process.env,
        LLM_PROVIDER: "fake",
        EMBEDDINGS: "hash",
        VECTOR_STORE: "memory",
        CHECKPOINT_BACKEND: "memory",
        DATABASE_URL: "sqlite://",
        SHOPMIND_STREAM_PACE_MS: "0",
      },
    },
    {
      command: "npm run dev -- --port 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        SHOPMIND_API_ORIGIN: apiOrigin,
      },
    },
  ],
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 5"] } },
  ],
});
