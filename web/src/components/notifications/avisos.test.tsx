import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { json, renderComSessao } from "@/components/bills/teste-sessao";
import { AvisosPagina } from "./avisos";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));
afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks(); });

test("central marca todos no servidor e aviso P7 não navega para conta", async () => {
  document.cookie = "csrftoken=teste";
  vi.stubGlobal("matchMedia", () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  const fetchMock = vi.fn(async (input: string, init?: RequestInit) => {
    if (input === "/api/notificacoes/ler-todas/") return json(200, { nao_lidas: 0 });
    if (input === "/api/notificacoes/n1/ler/") return json(200, { lido_em: "2026-11-16T12:00:00Z" });
    if (input === "/api/notificacoes/") return json(200, { nao_lidas: 1, proximo: null, resultados: [{ id: "n1", titulo: "Conta cancelada", texto: "Ficou sem ninguém que pudesse vê-la.", tipo: "cancelada_rn32", criado_em: "2026-11-16T12:00:00Z", lido_em: null, destino: null }] });
    if (input === "/api/notificacoes/preferencias/") return json(200, { versao: 1, email: true, push: true });
    if (input === "/api/notificacoes/resumo/") return json(200, { nao_lidas: 1, recentes: [] });
    if (init?.method === "POST") return json(404);
    return json(404, { detail: "x" });
  });
  vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<AvisosPagina />);
  const aviso = await screen.findByRole("button", { name: /Conta cancelada.*Não lido/ }, { timeout: 4000 });
  fireEvent.click(aviso);
  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/notificacoes/n1/ler/", expect.objectContaining({ method: "POST" })));
  expect(push).not.toHaveBeenCalled();
  fireEvent.click(screen.getAllByRole("button", { name: "Marcar todos como lidos" })[0]);
  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/notificacoes/ler-todas/", expect.objectContaining({ method: "POST" })));
});

test("aviso revogado some imediatamente mesmo quando atualização posterior falha", async () => {
  document.cookie = "csrftoken=teste";
  vi.stubGlobal("matchMedia", () => ({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  let listas = 0;
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    if (input === "/api/notificacoes/n1/ler/") return json(404);
    if (input === "/api/notificacoes/") return ++listas === 1 ? json(200, { nao_lidas: 1, proximo: null, resultados: [{ id: "n1", titulo: "Aviso revogado", texto: "Conteúdo antigo", tipo: "vence_3", criado_em: "2026-11-16T12:00:00Z", lido_em: null, destino: "/contas/123" }] }) : json(500);
    if (input === "/api/notificacoes/preferencias/") return json(200, { versao: 1, email: true, push: true });
    if (input === "/api/notificacoes/resumo/") return json(200, { nao_lidas: 0, recentes: [] });
    return json(404);
  }));
  renderComSessao(<AvisosPagina />);
  fireEvent.click(await screen.findByRole("button", { name: /Aviso revogado/ }));
  await waitFor(() => expect(screen.queryByText("Conteúdo antigo")).toBeNull());
  expect(push).not.toHaveBeenCalled();
});

test("acesso direto desktop abre gaveta sobre Início e fechar retorna ao Início", async () => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  vi.stubGlobal("matchMedia", () => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    if (input === "/api/notificacoes/") return json(200, { nao_lidas: 0, proximo: null, resultados: [] });
    if (input === "/api/notificacoes/resumo/") return json(200, { nao_lidas: 0, recentes: [] });
    if (input === "/api/notificacoes/preferencias/") return json(200, { versao: 1, email: true, push: true });
    return json(404);
  }));
  const rendered = renderComSessao(<AvisosPagina />);
  expect(await screen.findByRole("dialog", { name: "Avisos" })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
  expect(push).toHaveBeenCalledWith("/");
  rendered.unmount();
  Reflect.deleteProperty(HTMLDialogElement.prototype, "showModal");
  Reflect.deleteProperty(HTMLDialogElement.prototype, "close");
});
