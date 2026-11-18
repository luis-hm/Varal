import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { SessaoGuard } from "./sessao-guard";
import { desbloquearSessao, sessaoBloqueada } from "@/lib/auth/isolamento";

const A = "00000000-0000-4000-8000-000000000001";
const B = "00000000-0000-4000-8000-000000000002";
const limparCookies = () => { for (const k of ["varal_owner", "varal_local_locked"]) document.cookie = `${k}=; Max-Age=0; Path=/`; };
afterEach(() => { vi.unstubAllGlobals(); desbloquearSessao(); limparCookies(); document.documentElement.removeAttribute("data-sessao-oculta"); Reflect.deleteProperty(document, "visibilityState"); });

const montar = () => {
  const client = new QueryClient();
  const r = render(<QueryClientProvider client={client}><div data-sessao-privada hidden><SessaoGuard usuario={A}><p>dados privados</p></SessaoGuard></div><p data-sessao-status><span data-sessao-texto /></p></QueryClientProvider>);
  return r.container.querySelector<HTMLElement>("[data-sessao-privada]")!;
};
const me = (status: number, id = A) => vi.fn().mockResolvedValue(new Response(JSON.stringify({ id }), { status }));
const voltarAba = () => {
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
  fireEvent(document, new Event("visibilitychange"));
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
  fireEvent(document, new Event("visibilitychange"));
};

test("COR-01: sem a marca local (navegador reaberto) a sessão válida aparece e a marca é gravada", () => {
  const privado = montar();
  expect(privado.hasAttribute("hidden")).toBe(false);
  expect(document.cookie).toContain(`varal_owner=${A}`);
});

test("COR-01: trocar de aba com sessão válida não esconde nem recarrega", async () => {
  vi.stubGlobal("fetch", me(200));
  const privado = montar();
  voltarAba();
  await waitFor(() => expect(fetch).toHaveBeenCalled());
  expect(privado.hasAttribute("hidden")).toBe(false);
  expect(sessaoBloqueada()).toBe(false);
});

test("COR-01: voltar offline mantém a tela do mesmo usuário", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  const privado = montar();
  voltarAba();
  await waitFor(() => expect(fetch).toHaveBeenCalled());
  expect(privado.hasAttribute("hidden")).toBe(false);
});

test("COR-01: sessão encerrada no servidor mascara com mensagem específica", async () => {
  vi.stubGlobal("fetch", me(401));
  const privado = montar();
  voltarAba();
  await waitFor(() => expect(privado.hasAttribute("hidden")).toBe(true));
  expect(document.querySelector("[data-sessao-texto]")?.textContent).toMatch(/sessão terminou/);
  expect(sessaoBloqueada()).toBe(true);
});

test("Q11-7: saída local ou outra conta em outra aba mascara de imediato", () => {
  const privado = montar();
  document.cookie = `varal_owner=${B}; Path=/`;
  fireEvent(window, new StorageEvent("storage", { key: "varal.auth.geracao.v1", newValue: "outra" }));
  expect(privado.hasAttribute("hidden")).toBe(true);
});

test("Q11-7: pagehide mascara; restauração do BFCache revalida antes de revelar", async () => {
  vi.stubGlobal("fetch", me(200));
  const privado = montar();
  fireEvent(window, new Event("pagehide"));
  expect(privado.hasAttribute("hidden")).toBe(true);
  const evento = new Event("pageshow"); Object.defineProperty(evento, "persisted", { value: true });
  fireEvent(window, evento);
  await waitFor(() => expect(privado.hasAttribute("hidden")).toBe(false));
});
