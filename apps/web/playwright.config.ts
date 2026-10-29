import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      // Deterministic test LLM + embedding providers (no network, no
      // keys). Tries Postgres via docker-compose; the spec itself skips
      // if /runs can't reach a DB (see apps/api/scripts/e2e_server.sh).
      command: "bash ../api/scripts/e2e_server.sh",
      url: "http://127.0.0.1:8000/healthz",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run build && npm run start -- -p 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
      timeout: 120_000,
      env: { NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000" },
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
