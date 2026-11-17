import path from "node:path";
import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  test: {
    environment: "jsdom",
    maxWorkers: 1,
    setupFiles: ["./vitest.setup.ts"],
    exclude: [...configDefaults.exclude, "e2e/**"], // Playwright specs
  },
});
