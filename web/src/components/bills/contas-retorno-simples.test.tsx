import { screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { ContasPagina } from "./contas-pagina";
import { json, me, renderComSessao } from "./teste-sessao";

let busca = "";
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }), useSearchParams: () => new URLSearchParams(busca) }));
afterEach(() => { vi.unstubAllGlobals(); busca = ""; });
const detalhe = { id: "a", descricao: "Energia", valor_centavos: 500, vencimento: "2026-11-20", status: "pendente", status_exibido: "pendente", dias_para_vencer: 4, espaco: { id: "g1", nome: "Família", tipo: "grupo" }, subgrupo: null, visibilidade: "restrita", acesso: [], quem_ve: [], pagador: null, criador: { nome: "Dev", sou_eu: true }, criado_em: "2026-11-01T12:00:00Z", historico: [], pode_editar: false, instrumento: null, documento_pdf: null, pagamento_ativo: null, pagamentos: [], pode_pagar: false, pode_desfazer_pagamento: false, pode_anexar_comprovante: false, recorrente: false, recorrencia_id: null, competencia: null, pode_ver_recorrencia: false, mensagem_solicitacao: null, pode_solicitar: false, solicitacao_ativa: null, versao_compartilhamento: null };
function montar(autorizado = true) {
  vi.stubGlobal("fetch", vi.fn(async (url: string) => url === "/api/lancamentos/a/" ? json(200, detalhe) : json(200, { mes: "2026-11", total_centavos: 0, valores_indefinidos_qtd: 0, itens: [], contagens: { todas: 0, a_pagar: 0, vencidas: 0, pagas: 0, canceladas: 0 }, opcoes: { casas: [], pagadores: [], sem_pagador: false, ex_membro: false } })));
  renderComSessao(<ContasPagina contaId="a" />, { id: "g1", nome: "Família", tipo: "grupo", papel: "pagador" }, { ...me, grupos: autorizado ? [{ id: "g1", nome: "Família", papel: "pagador" }] : [] });
}

test("Q10: detalhe volta às pagas do grupo autorizado, sem aceitar URL externa", async () => {
  busca = "origem=simples&pagas=1&voltar=https%3A%2F%2Fexterno.exemplo";
  montar();
  expect((await screen.findByRole("link", { name: "Fechar detalhe" })).getAttribute("href")).toBe("/grupos/g1/simples?pagas=1");
  expect(screen.queryByRole("button", { name: "Editar conta" })).toBeNull();
});

test("Q10: sem vínculo elegível o retorno não aponta para o modo simples do grupo", async () => {
  busca = "origem=simples&pagas=1";
  montar(false);
  expect((await screen.findByRole("link", { name: "Fechar detalhe" })).getAttribute("href")).toBe("/grupos");
});

test("Q04: detalhe comum preserva filtros existentes ao voltar", async () => {
  busca = "mes=2026-11&status=pagas&casa=c1";
  montar();
  expect((await screen.findByRole("link", { name: "Fechar detalhe" })).getAttribute("href")).toBe("/contas?mes=2026-11&status=pagas&casa=c1");
});
