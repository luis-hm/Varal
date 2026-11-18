import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { json, me, renderComSessao } from "@/components/bills/teste-sessao";
import { ContasSimples } from "./contas-simples";
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }) }));
afterEach(() => vi.unstubAllGlobals());

test("Q10-12: abertas incluem NULL e conta visível sem permissão, sem fingir que são pagáveis", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => json(200, { abertas_qtd: 2, pagas_mes_qtd: 1, itens: [
    { id: "a", descricao: "A definir", valor_centavos: null, vencimento: "2026-11-20", status: "aguardando", status_exibido: "aguardando", subgrupo: null, instrumento: null, documento_pdf: null, pode_pagar: false },
    { id: "b", descricao: "Outra conta", valor_centavos: 500, vencimento: "2027-01-01", status: "pendente", status_exibido: "pendente", subgrupo: null, instrumento: null, documento_pdf: null, pode_pagar: false },
  ] })));
  renderComSessao(<ContasSimples grupoId="g1" grupoNome="Família" nome="Dev" />);
  expect(await screen.findByText("Você tem 2 contas em aberto.")).toBeTruthy();
  expect(screen.getByText("Valor a definir")).toBeTruthy();
  expect(screen.getByText("Aguardando conferência")).toBeTruthy();
  expect(screen.getByRole("link", { name: "A definir" }).getAttribute("href")).toBe("/contas/a?origem=simples");
  expect(screen.getByText("Você pode consultar esta conta.")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Já paguei" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Copiar código" })).toBeNull();
  expect(screen.getByRole("button", { name: "Sair do grupo" })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /1 conta deste mês já paga/ }));
  expect(await screen.findByText("Contas deste mês já pagas")).toBeTruthy();
  expect(screen.getByRole("link", { name: "A definir" }).getAttribute("href")).toBe("/contas/a?origem=simples&pagas=1");
});

test("Q10-11: perda de acesso não mantém nome ou contas de grupo revogado", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => json(404)));
  renderComSessao(<ContasSimples grupoId="g1" grupoNome="Grupo privado" nome="Dev" />);
  expect(await screen.findByRole("alert")).toHaveProperty("textContent", "Este grupo não está mais disponível. Volte para Grupos.");
  expect(screen.queryByText("Grupo privado")).toBeNull();
  expect(screen.getByText("Grupo indisponível")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Sair do grupo" })).toBeNull();
});

test("RF07: pagador pode solicitar saída do grupo no modo simples", async () => {
  document.cookie = "csrftoken=t";
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => url === "/api/grupos/g1/sair/" && init?.method === "POST" ? new Response(null, { status: 204 }) : json(200, { abertas_qtd: 0, pagas_mes_qtd: 0, itens: [] }));
  vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<ContasSimples grupoId="g1" grupoNome="Família" nome="Dev" />, { id: "g1", nome: "Família", tipo: "grupo", papel: "pagador" }, { ...me, grupos: [{ id: "g1", nome: "Família", papel: "pagador" }] });
  fireEvent.click(await screen.findByRole("button", { name: "Sair do grupo" }));
  fireEvent.click(within(await screen.findByRole("dialog", { name: /Sair de Família/ })).getByRole("button", { name: "Sair" }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/grupos/g1/sair/", expect.objectContaining({ method: "POST" })));
});
