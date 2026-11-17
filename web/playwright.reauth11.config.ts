import { defineConfig } from "@playwright/test";
import lab from "./playwright.lab11.config";

// Sensitive synthetic session and SMTP code must never enter traces, screenshots, or video.
export default defineConfig(lab, {
  testMatch: "reauth-code11.check.ts",
  projects: [{ name: "mobile", use: { ...lab.projects![1].use } }],
  use: { ...lab.use, storageState: "/qa/ca06-state.json", trace: "off", screenshot: "off", video: "off" },
});
