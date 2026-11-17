import { defineConfig, devices } from "@playwright/test";
import lab from "./playwright.lab11.config";

// One real alternative engine; the CA is scoped to this process. Never ignore TLS errors.
export default defineConfig(lab, {
  testMatch: "identidade11.check.ts",
  preserveOutput: "always",
  use: {
    baseURL: process.env.LAB_BASE_URL,
    browserName: "webkit",
    channel: undefined,
    trace: "retain-on-failure",
    launchOptions: { env: { ...process.env, SSL_CERT_FILE: "/qa/ca.pem" } },
  },
  projects: [{ name: "webkit-mobile", use: { ...devices["Desktop Safari"], viewport: { width: 390, height: 844 } } }],
});
