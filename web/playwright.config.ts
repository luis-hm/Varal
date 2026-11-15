import { defineConfig, devices } from "@playwright/test";

// `make e2e` (and CI) starts the real API/PostgreSQL before this browser suite.
export default defineConfig({
  testDir: "e2e",
  testIgnore: "production.spec.ts",
  globalSetup: "./e2e/global-setup.ts",
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 2,
  timeout: 45_000,
  reporter: [["list"], ["html", { open: "never" }]],
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure" },
  projects: [
    { name: "mobile", use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 } } },
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000/entrar",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
