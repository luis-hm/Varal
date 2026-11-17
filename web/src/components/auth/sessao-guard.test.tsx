import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { SessaoGuard } from "./sessao-guard";
import { desbloquearSessao } from "@/lib/auth/isolamento";

const A = "00000000-0000-4000-8000-000000000001";
afterEach(() => { vi.unstubAllGlobals(); desbloquearSessao(); document.documentElement.removeAttribute("data-sessao-oculta"); });

test("Q11-7: pagehide mascara imediatamente e restauração offline não revela a aba", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  const client = new QueryClient();
  const { container } = render(<QueryClientProvider client={client}><div data-sessao-privada><SessaoGuard usuario={A}><p>dados privados</p></SessaoGuard></div></QueryClientProvider>);
  const privado = container.querySelector("[data-sessao-privada]")!;
  fireEvent(window, new Event("pagehide"));
  expect(privado.hasAttribute("hidden")).toBe(true);
  expect(document.documentElement.hasAttribute("data-sessao-oculta")).toBe(true);
  const evento = new Event("pageshow"); Object.defineProperty(evento, "persisted", { value: true });
  fireEvent(window, evento);
  await waitFor(() => expect(fetch).toHaveBeenCalled());
  expect(privado.hasAttribute("hidden")).toBe(true);
});

test("Q11-7: mudança de autenticação em outra aba mascara conteúdo", () => {
  const client = new QueryClient();
  const { container } = render(<QueryClientProvider client={client}><div data-sessao-privada><SessaoGuard usuario={A}><p>dados privados</p></SessaoGuard></div></QueryClientProvider>);
  fireEvent(window, new StorageEvent("storage", { key: "varal.auth.geracao.v1", newValue: "outra" }));
  expect(container.querySelector("[data-sessao-privada]")?.hasAttribute("hidden")).toBe(true);
});

test("Q11-7: aba oculta mascara de imediato e voltar offline não revela dados", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  const client = new QueryClient();
  const { container } = render(<QueryClientProvider client={client}><div data-sessao-privada><SessaoGuard usuario={A}><p>dados privados</p></SessaoGuard></div></QueryClientProvider>);
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
  fireEvent(document, new Event("visibilitychange"));
  expect(container.querySelector("[data-sessao-privada]")?.hasAttribute("hidden")).toBe(true);
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
  fireEvent(document, new Event("visibilitychange"));
  await waitFor(() => expect(fetch).toHaveBeenCalled());
  expect(container.querySelector("[data-sessao-privada]")?.hasAttribute("hidden")).toBe(true);
  Reflect.deleteProperty(document, "visibilityState");
});

test("Q11-7: máscara anterior à hidratação é mantida ao montar sem rede", async () => {
  document.documentElement.setAttribute("data-sessao-oculta", "");
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  const client = new QueryClient();
  const { container } = render(<QueryClientProvider client={client}><div data-sessao-privada hidden><SessaoGuard usuario={A}><p>dados privados</p></SessaoGuard></div></QueryClientProvider>);
  await waitFor(() => expect(fetch).toHaveBeenCalled());
  expect(container.querySelector("[data-sessao-privada]")?.hasAttribute("hidden")).toBe(true);
});
