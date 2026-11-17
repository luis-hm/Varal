import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { expect, test, vi } from "vitest";

test("Q11-7: worker armazena apenas assets públicos explícitos e nunca intercepta API financeira", async () => {
  type Evento = { request?: unknown; respondWith?: (p: Promise<unknown>) => void; waitUntil?: (p: Promise<unknown>) => void };
  const handlers = new Map<string, (event: Evento) => void>();
  const addAll = vi.fn().mockResolvedValue(undefined);
  const cache = { addAll, match: vi.fn().mockResolvedValue(new Response("offline")) };
  const caches = { open: vi.fn().mockResolvedValue(cache), keys: vi.fn().mockResolvedValue([]), delete: vi.fn() };
  const self = { location: { origin: "https://varal.test" }, addEventListener: (name: string, handler: (event: Evento) => void) => handlers.set(name, handler) };
  runInNewContext(readFileSync("public/sw-notificacoes.js", "utf8"), { self, caches, URL, Response, Promise, fetch: vi.fn().mockRejectedValue(new Error("offline")) });
  let install!: Promise<unknown>;
  handlers.get("install")!({ waitUntil: (promise) => { install = promise; } });
  await install;
  expect(addAll.mock.calls[0][0]).toEqual(["/offline-v1.html", "/icons/varal-192-v1.png", "/icons/varal-512-v1.png"]);
  const respond = vi.fn();
  for (const path of ["/api/espacos/abc/resumo/", "/api/auth/browser/v1/auth/session", "/api/lancamentos/abc/pdf/", "/_next/data/private.json"]) {
    handlers.get("fetch")!({ request: { method: "GET", mode: "cors", url: `https://varal.test${path}` }, respondWith: respond });
  }
  expect(respond).not.toHaveBeenCalled();
  expect(handlers.has("push")).toBe(true);
  expect(handlers.has("notificationclick")).toBe(true);
});
