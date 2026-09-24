import { defineConfig, devices } from '@playwright/test'

// Full stack: isolated FastAPI (port 5001, fresh `pulso_e2e` database) + Vite dev server proxying /api.
export default defineConfig({
  testDir: 'e2e',
  fullyParallel: false,
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:5174', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] }, testIgnore: /mobile\.spec\.ts/ },
    { name: 'mobile', use: { ...devices['Pixel 7'] }, testMatch: /mobile\.spec\.ts/ },
  ],
  webServer: [
    { command: './e2e/start-api.sh', url: 'http://127.0.0.1:5001/api/health', reuseExistingServer: false, timeout: 120_000 },
    {
      command: 'npx vite --host 127.0.0.1 --port 5174 --strictPort',
      env: { PULSO_API: 'http://127.0.0.1:5001' },
      url: 'http://127.0.0.1:5174',
      reuseExistingServer: false,
    },
  ],
})
