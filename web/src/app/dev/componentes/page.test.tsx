import { afterEach, expect, test, vi } from "vitest";
import ComponentesPage from "./page";

// The server session is exercised by E2E; this unit checks the early environment gate.
vi.mock("@/components/auth/protected-shell", () => ({ ProtectedShell: () => null }));

afterEach(() => vi.unstubAllEnvs());

test("ca16: the showcase is a 404 in production", () => {
  vi.stubEnv("NODE_ENV", "production");
  expect(() => ComponentesPage()).toThrow(expect.objectContaining({ digest: expect.stringContaining("404") }));
});

test("the showcase renders outside production", () => {
  vi.stubEnv("NODE_ENV", "development");
  expect(ComponentesPage()).toBeTruthy();
});
