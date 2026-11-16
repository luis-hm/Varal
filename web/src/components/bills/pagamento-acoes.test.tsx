import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import type { ContaDetalhe } from "@/lib/contas/client";
import { PagamentoAcoes } from "./pagamento-acoes";
import { json, renderComSessao } from "./teste-sessao";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
const conta: ContaDetalhe = {
  id: "l1", descricao: "Energia", valor_centavos: 10000, vencimento: "2026-11-20", status: "pendente", status_exibido: "pendente", dias_para_vencer: 4,
  espaco: { id: "p1", nome: "Pessoal", tipo: "pessoal" }, subgrupo: null, visibilidade: "grupo", acesso: [], quem_ve: [], pagador: null,
  criador: { nome: "Dev", sou_eu: true }, criado_em: "2026-11-01T12:00:00Z", historico: [], pode_editar: true,
  instrumento: null, documento_pdf: null, pagamento_ativo: null, pagamentos: [], pode_pagar: true, pode_desfazer_pagamento: false, pode_anexar_comprovante: false,
  recorrente: false, recorrencia_id: null, competencia: null, pode_ver_recorrencia: false, mensagem_solicitacao: null, pode_solicitar: false, solicitacao_ativa: null, versao_compartilhamento: null,
};

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

test("rn14/rn22: o submit repetido registra uma vez e não fecha durante gravação", async () => {
  document.cookie = "csrftoken=t";
  let responder!: (response: Response) => void;
  const fetchMock = vi.fn((url: string, init?: RequestInit) => {
    void url; void init;
    return new Promise<Response>((resolve) => { responder = resolve; });
  });
  vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<PagamentoAcoes conta={conta} />);
  fireEvent.click(screen.getByRole("button", { name: "Já paguei" }));
  const form = screen.getByLabelText("Data do pagamento").closest("form")!;
  fireEvent.submit(form);
  fireEvent.submit(form);
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  fireEvent(screen.getByRole("dialog", { name: "Marcar como paga" }), new Event("cancel", { bubbles: true, cancelable: true }));
  expect(screen.getByRole("dialog", { name: "Marcar como paga" })).toBeTruthy();
  expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toMatchObject({ valor_centavos_esperado: 10000 });
  responder(json(201, { ...conta, status: "paga", pode_pagar: false }));
  expect(await screen.findByText("Pagamento registrado.")).toBeTruthy();
});

test("rn16: autor autorizado vê desfazer e comprovante histórico, mesmo sem poder pagar", () => {
  const paga: ContaDetalhe = { ...conta, status: "confirmada", status_exibido: "confirmada", pode_pagar: false, pode_desfazer_pagamento: true,
    pagamento_ativo: { id: "p1", pago_em: "2026-11-16", valor_pago_centavos: 10000, criado_em: "2026-11-16T12:00:00Z", desfeito_em: null, marcado_por: "Dev", comprovante_id: "d1", derivado: false },
    pagamentos: [{ id: "p1", pago_em: "2026-11-16", valor_pago_centavos: 10000, criado_em: "2026-11-16T12:00:00Z", desfeito_em: null, marcado_por: "Dev", comprovante_id: "d1", derivado: false }],
  };
  renderComSessao(<PagamentoAcoes conta={paga} />);
  expect(screen.getByRole("button", { name: "Desfazer pagamento" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Abrir comprovante" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Já paguei" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Anexar comprovante" })).toBeNull();
});

test("q10-11: após pagar no modo simples a confirmação retorna ao contexto de contas", async () => {
  document.cookie = "csrftoken=t";
  const aoConcluir = vi.fn();
  vi.stubGlobal("fetch", vi.fn(async (_url: string, init?: RequestInit) => init?.method === "POST" ? json(201, { ...conta, status: "paga", pode_pagar: false }) : json(404, { detail: "x" })));
  renderComSessao(<PagamentoAcoes conta={conta} modoSimples aoConcluir={aoConcluir} />);
  fireEvent.click(screen.getByRole("button", { name: "Já paguei" }));
  fireEvent.submit(screen.getByLabelText("Data do pagamento").closest("form")!);
  const voltar = await screen.findByRole("button", { name: /Voltar às contas/ });
  fireEvent.click(voltar);
  expect(aoConcluir).toHaveBeenCalledOnce();
});

test("q10-5: marca derivada é identificada sem expor ator do outro espaço", () => {
  const pagamento = { id: "p1", pago_em: "2026-11-16", valor_pago_centavos: 10000, criado_em: "2026-11-16T12:00:00Z", desfeito_em: null, marcado_por: "Ex-membro", comprovante_id: null, derivado: true };
  renderComSessao(<PagamentoAcoes conta={{ ...conta, status: "paga", pagamento_ativo: pagamento, pagamentos: [pagamento], pode_pagar: false }} />);
  expect(screen.getByText(/Pagamento derivado de solicitação/)).toBeTruthy();
  expect(screen.queryByText(/Ex-membro/)).toBeNull();
});
