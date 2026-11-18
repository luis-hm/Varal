import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

// Run only after `next build` + `next start` and the API are ready on their usual ports.
// Never start `next dev`: that would make an HTTP-404 regression pass in the wrong mode.
// Spread, not defineConfig(base, ...): that merge appends webServer arrays and kept `npm run dev`.
export default defineConfig({ ...base, testMatch: "production.spec.ts", testIgnore: [], webServer: undefined });
