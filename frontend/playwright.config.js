import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  testIgnore: ['hosted-smoke.spec.js'],
  timeout: 120000,
  expect: {
    timeout: 10000
  },
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry'
  },
  webServer: [
    {
      command:
        "bash -lc 'cd ../backend && source .venv/bin/activate && DATABASE_URL=sqlite:///./e2e_suite.db APP_SERVE_FRONTEND=false python -m uvicorn app.main:app --host 127.0.0.1 --port 8000'",
      url: 'http://127.0.0.1:8000/healthz',
      timeout: 120000,
      reuseExistingServer: true
    },
    {
      command: 'npm run dev',
      url: 'http://127.0.0.1:5173',
      timeout: 120000,
      reuseExistingServer: true
    }
  ]
});
