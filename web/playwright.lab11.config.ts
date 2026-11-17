import { defineConfig, devices } from "@playwright/test";

// Explicit isolated production-like lab only. LAB_BASE_URL must be supplied by its operator;
// Node/browser must trust the laboratory CA rather than ignoring TLS errors.
const url = process.env.LAB_BASE_URL;
if (!url || new URL(url).protocol !== "https:") throw new Error("LAB_BASE_URL HTTPS is required for lab11");
export default defineConfig({
  testDir: "e2e", testMatch: "privacidade11.spec.ts", webServer: [], workers: 1,
  outputDir: process.env.LAB_QA_OUTPUT ? `${process.env.LAB_QA_OUTPUT}/test-results` : "test-results-lab11",
  timeout: 90_000, reporter: [["list"]],
  use: { baseURL: url, channel: "chromium", trace: "retain-on-failure" },
  projects: [
    { name: "small", use: { ...devices["Desktop Chrome"], viewport: { width: 360, height: 844 } } },
    { name: "mobile", use: { ...devices["Desktop Chrome"], viewport: { width: 390, height: 844 } } },
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  ],
});
