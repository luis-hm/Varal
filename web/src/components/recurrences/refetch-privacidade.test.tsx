import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, expect, test, vi } from "vitest";
import { ContaFolha } from "@/components/bills/conta-folha";
import { json, me } from "@/components/bills/teste-sessao";
import { Sessao } from "@/components/layout/app-shell";
import type { ContaDetalhe, Recorrencia } from "@/lib/contas/client";
import { RecorrenciasFolha } from "./recorrencias-folha";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

const grupo = { id: "g1", nome: "Família", meu_papel: "admin", janela_alerta_dias: 3, casas: [], membros: [] };
const modelo: Recorrencia = { id: "r1", espaco_id: "g1", descricao: "Energia", dia_vencimento: 10, valor_tipo: "fixo", valor_centavos: 10000, subgrupo: null, pagador: null, visibilidade: "grupo", acesso: ["u4"], estado: "ativa", motivo_pausa: "", criado_em: "2026-11-01T12:00:00Z", pode_editar: true, pode_pausar: true, pode_retomar: false, pode_encerrar: true };
const conta: ContaDetalhe = { id: "l1", descricao: "Energia", valor_centavos: 10000, vencimento: "2026-11-10", status: "pendente", status_exibido: "pendente", dias_para_vencer: 1, espaco: { id: "g1", nome: "Família", tipo: "grupo" }, subgrupo: null, visibilidade: "grupo", acesso: [{ id: "u4", nome: "Pessoa" }], quem_ve: [], pagador: null, criador: { nome: "Dev", sou_eu: true }, criado_em: "2026-11-01T12:00:00Z", historico: [], pode_editar: true, instrumento: { tipo: "pix", codigo: null, chave_pix: "original@exemplo.com", beneficiario: null, data_emissao: null }, documento_pdf: null, pagamento_ativo: null, pagamentos: [], pode_pagar: true, pode_desfazer_pagamento: false, pode_anexar_comprovante: false, recorrente: true, recorrencia_id: "r1", competencia: "2026-11-01", pode_ver_recorrencia: true };

function montar(ui: React.ReactNode, client: QueryClient) {
  return render(<QueryClientProvider client={client}><Sessao.Provider value={{ user: me, espaco: { id: "g1", nome: "Família", tipo: "grupo", papel: "admin" }, novaConta: () => {}, escolherEspaco: () => {} }}>{ui}</Sessao.Provider></QueryClientProvider>);
}

test("b08-3: refetch de modelo não transforma ACL, dia e valor remotos em edição local", async () => {
  document.cookie = "csrftoken=t";
  const enviados: unknown[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === "PATCH") { enviados.push(JSON.parse(String(init.body))); return json(200, modelo); }
    if (url === "/api/recorrencias/r1/") return json(200, modelo);
    if (url === "/api/grupos/g1/") return json(200, grupo);
    if (url === "/api/espacos/g1/recorrencias/") return json(200, [modelo]);
    return json(404, {});
  }));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  montar(<RecorrenciasFolha open espacoId="g1" pessoal={false} inicial="r1" onClose={() => {}} />, client);
  await waitFor(() => expect((screen.getByLabelText("Descrição") as HTMLInputElement).value).toBe("Energia"));
  act(() => client.setQueryData(["recorrencias", "detalhe", "r1"], { ...modelo, dia_vencimento: 22, valor_centavos: 50000, visibilidade: "restrita", acesso: ["u3"] }));
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Energia editada" } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  await waitFor(() => expect(enviados).toHaveLength(1));
  expect(enviados[0]).toEqual({ descricao: "Energia editada" });
});

test("b08-3: refetch de conta não restaura ACL, valor, data ou instrumento antigos", async () => {
  document.cookie = "csrftoken=t";
  const enviados: unknown[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === "PATCH") { enviados.push(JSON.parse(String(init.body))); return json(200, conta); }
    if (url === "/api/boletos/ler/") return json(200, { instrumento: conta.instrumento, valor_centavos: null, vencimento: null, vencimentos_possiveis: [], avisos: [] });
    if (url === "/api/recorrencias/r1/") return json(200, modelo);
    if (url === "/api/grupos/g1/") return json(200, grupo);
    return json(404, {});
  }));
  let atualizar!: (nova: ContaDetalhe) => void;
  function Tela() { const [atual, setAtual] = useState(conta); atualizar = setAtual; return <ContaFolha conta={atual} open onClose={() => {}} />; }
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  montar(<Tela />, client);
  await screen.findByText(/Pix conferido/);
  act(() => atualizar({ ...conta, valor_centavos: 50000, vencimento: "2026-11-22", visibilidade: "restrita", acesso: [{ id: "u3", nome: "Outra pessoa" }], instrumento: { ...conta.instrumento!, chave_pix: "novo@exemplo.com" } }));
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: "Energia editada" } });
  fireEvent.click(await screen.findByRole("radio", { name: /Este mês e próximos/ }));
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  await waitFor(() => expect(enviados).toHaveLength(1));
  expect(enviados[0]).toEqual({ descricao: "Energia editada", escopo: "proximos" });
});
