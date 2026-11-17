import { defineConfig } from "@playwright/test";
import lab from "./playwright.lab11.config";

// Chromium disables BFCache by default under Playwright. Remove only that flag;
// tests must record a real persisted pageshow, never dispatch a synthetic event.
export default defineConfig(lab, {
  testMatch: "identidade11.check.ts",
  preserveOutput: "always",
  use: { ...lab.use, launchOptions: { ignoreDefaultArgs: ["--disable-back-forward-cache"] } },
});
