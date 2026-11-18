import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { ContasPagina } from "./contas-pagina";
import { json, renderComSessao } from "./teste-sessao";

let busca = "";
const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }), useSearchParams: () => new URLSearchParams(busca) }));
afterEach(() => { vi.unstubAllGlobals(); busca = ""; push.mockClear(); });

const vazia = (opcoes = {}) => ({ mes: null as string | null, total_centavos: 0, valores_indefinidos_qtd: 0, itens: [], contagens: { todas: 0, a_pagar: 0, vencidas: 0, pagas: 0, canceladas: 0 }, opcoes: { casas: [], sem_categoria: false, pagadores: [], sem_pagador: false, ex_membro: false, ...opcoes } });
function montar(corpo = vazia()) {
  const urls: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string) => { urls.push(url); return json(200, corpo); }));
  // The session still points at a group (old cookie): Contas must start personal anyway (COR-05).
  renderComSessao(<ContasPagina />);
  return urls;
}

test("COR-02/05: Contas abre pessoal e sem mês obrigatório", async () => {
  const urls = montar();
  await screen.findByText("Nenhuma conta por aqui ainda.");
  expect(urls).toEqual(["/api/espacos/p1/lancamentos/?status=todas"]);
  expect(screen.getByText("Todos os meses")).toBeTruthy();
});

test("COR-05: ?espaco= escolhe o grupo e combina com mês e status", async () => {
  busca = "espaco=g1&mes=2026-12&status=a_pagar";
  const urls = montar({ ...vazia(), mes: "2026-12" });
  await screen.findByText("Nenhuma conta com esses filtros.");
  expect(urls[0]).toMatch(/^\/api\/espacos\/g1\/lancamentos\/\?/); expect(urls[0]).toContain("mes=2026-12"); expect(urls[0]).toContain("status=a_pagar");
});

test("COR-07: filtro ativo sem opções continua visível e removível no vazio", async () => {
  busca = "espaco=g1&casa=c1";
  montar();
  const tag = await screen.findByRole("button", { name: /Remover filtro Categoria: Indisponível/ });
  fireEvent.click(screen.getByRole("button", { name: "Limpar filtros" }));
  await waitFor(() => expect(push).toHaveBeenCalledWith("/contas?espaco=g1", { scroll: false }));
  fireEvent.click(tag);
  expect(push).toHaveBeenLastCalledWith("/contas?espaco=g1", { scroll: false });
});

test("COR-07: Sem categoria aparece como opção de filtro do grupo", async () => {
  busca = "espaco=g1";
  montar(vazia({ casas: [{ id: "c1", nome: "Luz", icone: "luz" }], sem_categoria: true }));
  await screen.findByText("Nenhuma conta por aqui ainda.");
  fireEvent.click(screen.getByRole("button", { name: /Categoria/ }));
  expect(screen.getByRole("button", { name: "Sem categoria" })).toBeTruthy();
});
