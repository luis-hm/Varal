import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { mesAtual } from "@/lib/contas/formato";
import type { Conta, ContaDetalhe } from "@/lib/contas/client";
import { ContaCard } from "./bill-card";
import { ContaFolha } from "./conta-folha";
import { json, renderComSessao } from "./teste-sessao";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

test("q08-1: valor desconhecido continua legível em conta cancelada", () => {
  const conta: Conta = { id: "l1", descricao: "Água", valor_centavos: null, vencimento: `${mesAtual()}-14`, status: "cancelada", status_exibido: "cancelada", dias_para_vencer: 0, espaco: { id: "p1", nome: "Pessoal", tipo: "pessoal" }, subgrupo: null, pagador: null, visibilidade: "grupo", criado_em: "2026-11-01T12:00:00Z" };
  renderComSessao(<ContaCard conta={conta} href="/contas/l1" />);
  expect(screen.getByText("Valor a definir")).toBeTruthy();
  expect(screen.queryByText("R$ 0,00")).toBeNull();
});

test("q08-9: primeira conta e modelo são enviados juntos, retry preserva chave", async () => {
  document.cookie = "csrftoken=t";
  const corpos: Record<string, unknown>[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    if (url === "/api/espacos/p1/recorrencias/" && init?.method === "POST") {
      corpos.push(JSON.parse(String(init.body)));
      if (corpos.length === 1) throw new Error("rede indisponível");
      return json(201, { recorrencia: { id: "r1" }, ocorrencia: { id: "l1", vencimento: `${mesAtual()}-14` } });
    }
    return json(404, { detail: "Não encontrado" });
  }));
  renderComSessao(<ContaFolha open onClose={() => {}} />, { id: "p1", nome: "Pessoal", tipo: "pessoal" });
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Energia" } });
  fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "123,45" } });
  fireEvent.change(screen.getByLabelText("Vencimento"), { target: { value: `${mesAtual()}-14` } });
  fireEvent.click(screen.getByLabelText(/Repetir todo mês/));
  fireEvent.click(screen.getByRole("radio", { name: /Valor muda/ }));
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  await screen.findByText("rede indisponível");
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  await waitFor(() => expect(corpos).toHaveLength(2));
  expect(corpos[0]).toEqual(corpos[1]);
  expect(corpos[0]).toMatchObject({ valor_tipo: "variavel", valor_centavos: null, dia_vencimento: 14, ocorrencia_inicial: { valor_centavos: 12345, vencimento: `${mesAtual()}-14` } });
});

test("q08-9: vencimento de outro mês conserva campos e não cria recorrência", async () => {
  const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<ContaFolha open onClose={() => {}} />, { id: "p1", nome: "Pessoal", tipo: "pessoal" });
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Conta antiga" } });
  fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "42,00" } });
  fireEvent.change(screen.getByLabelText("Vencimento"), { target: { value: "2020-01-14" } });
  fireEvent.click(screen.getByLabelText(/Repetir todo mês/));
  fireEvent.click(screen.getByRole("button", { name: "Salvar conta" }));
  expect(screen.getByRole("alert").textContent).toContain("vencimento da primeira conta precisa ser deste mês");
  expect((screen.getByLabelText("Valor") as HTMLInputElement).value).toBe("42,00");
  expect(fetchMock).not.toHaveBeenCalled();
});

test("q08-3/q08-4: confirmar aguardando envia apenas alterações e escopo escolhido", async () => {
  document.cookie = "csrftoken=t";
  const conta: ContaDetalhe = { id: "l1", descricao: "Água", valor_centavos: null, vencimento: `${mesAtual()}-14`, status: "aguardando", status_exibido: "aguardando", dias_para_vencer: 2, espaco: { id: "p1", nome: "Pessoal", tipo: "pessoal" }, subgrupo: null, visibilidade: "grupo", acesso: [], quem_ve: [], pagador: null, criador: { nome: "Dev", sou_eu: true }, criado_em: "2026-11-01T12:00:00Z", historico: [], pode_editar: true, instrumento: null, documento_pdf: null, pagamento_ativo: null, pagamentos: [], pode_pagar: false, pode_desfazer_pagamento: false, pode_anexar_comprovante: false, recorrente: true, recorrencia_id: "r1", competencia: `${mesAtual()}-01`, pode_ver_recorrencia: true, mensagem_solicitacao: null, pode_solicitar: false, solicitacao_ativa: null, versao_compartilhamento: null };
  const chamadas: unknown[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => { if (init?.method === "PATCH") { chamadas.push(JSON.parse(String(init.body))); return json(200, conta); } if (url === "/api/recorrencias/r1/") return json(200, { id: "r1", pode_editar: true }); return json(404, {}); }));
  renderComSessao(<ContaFolha conta={conta} open onClose={() => {}} />, { id: "p1", nome: "Pessoal", tipo: "pessoal" });
  fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "42,00" } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  expect(screen.getByText("Confirme a chegada para alterar o valor.")).toBeTruthy();
  expect(chamadas).toHaveLength(0);
  fireEvent.click(screen.getByLabelText("Confirmar valor e vencimento desta conta"));
  fireEvent.click(await screen.findByRole("radio", { name: /Este mês e próximos/ }));
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  await waitFor(() => expect(chamadas).toHaveLength(1));
  expect(chamadas[0]).toEqual({ valor_centavos: 4200, escopo: "proximos", confirmar_chegada: true });
});

test("q08-9: gravação bloqueia reenvio e resposta atrasada não navega após desmontar", async () => {
  document.cookie = "csrftoken=t"; push.mockClear();
  let resolver!: (value: Response) => void;
  const chamadas = vi.fn(() => new Promise<Response>((resolve) => { resolver = resolve; }));
  vi.stubGlobal("fetch", chamadas);
  const tela = renderComSessao(<ContaFolha open onClose={() => {}} />, { id: "p1", nome: "Pessoal", tipo: "pessoal" });
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Energia" } });
  fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "12,00" } });
  fireEvent.change(screen.getByLabelText("Vencimento"), { target: { value: `${mesAtual()}-14` } });
  fireEvent.click(screen.getByLabelText(/Repetir todo mês/));
  const form = document.getElementById("conta-form")!;
  fireEvent.submit(form); fireEvent.submit(form);
  await waitFor(() => expect(chamadas).toHaveBeenCalledTimes(1));
  expect((screen.getByRole("button", { name: "Salvando…" }) as HTMLButtonElement).disabled).toBe(true);
  tela.unmount();
  await act(async () => resolver(json(201, { recorrencia: { id: "r1" }, ocorrencia: { id: "l1", vencimento: `${mesAtual()}-14` } })));
  expect(push).not.toHaveBeenCalled();
});
