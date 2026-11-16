import { fireEvent, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { afterEach, expect, test, vi } from "vitest";
import type { ContaDetalhe } from "@/lib/contas/client";
import { guardarTentativa, tentativaPendente } from "@/lib/solicitacoes/marcador";
import { json, renderComSessao } from "./teste-sessao";
import { SolicitacaoAcoes } from "./solicitacao-acoes";
import { ContaDetalhe as TelaConta } from "./conta-detalhe";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));

const conta: ContaDetalhe = { id: "l1", descricao: "Energia", valor_centavos: 10000, vencimento: "2026-11-20", status: "pendente", status_exibido: "pendente", dias_para_vencer: 4, espaco: { id: "p1", nome: "Pessoal", tipo: "pessoal" }, subgrupo: null, visibilidade: "grupo", acesso: [], quem_ve: [], pagador: null, criador: { nome: "Dev", sou_eu: true }, criado_em: "2026-11-01T12:00:00Z", historico: [], pode_editar: true, instrumento: null, documento_pdf: null, pagamento_ativo: null, pagamentos: [], pode_pagar: true, pode_desfazer_pagamento: false, pode_anexar_comprovante: false, recorrente: false, recorrencia_id: null, competencia: null, pode_ver_recorrencia: false, mensagem_solicitacao: null, pode_solicitar: true, solicitacao_ativa: null, versao_compartilhamento: "hash-antigo" };
afterEach(() => { localStorage.clear(); vi.unstubAllGlobals(); });

test("detalhe preserva uma solicitação aberta e um pagamento após refetch da conta", async () => {
  const erros = vi.spyOn(console, "error").mockImplementation(() => {});
  vi.stubGlobal("fetch", vi.fn(async () => json(200, [{ id: "g1", nome: "Família", pagadores: [{ id: "u2", nome: "Ana" }] }])));
  function Tela() {
    const [atual, setAtual] = useState(conta);
    return <><button onClick={() => setAtual({ ...atual })}>Refetch detalhe</button><TelaConta conta={atual} voltar="/contas" /></>;
  }
  try {
    renderComSessao(<Tela />);
    fireEvent.click(screen.getByRole("button", { name: "Pedir para alguém pagar" }));
    expect(await screen.findByRole("dialog", { name: "Pedir para alguém pagar" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Refetch detalhe" }));
    expect(screen.getAllByRole("button", { name: "Pedir para alguém pagar" })).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Já paguei" })).toHaveLength(1);
    expect(screen.getByRole("dialog", { name: "Pedir para alguém pagar" })).toBeTruthy();
    expect(erros.mock.calls.some((args) => args.join(" ").includes("same key"))).toBe(false);
  } finally { erros.mockRestore(); }
});

test("Q10-13: refetch de valor e hash não confirma conteúdo diferente da base exibida", async () => {
  const fetchMock = vi.fn(async (url: string) => url.endsWith("/opcoes/") ? json(200, [{ id: "g1", nome: "Família", pagadores: [{ id: "u2", nome: "Ana" }] }]) : json(500));
  vi.stubGlobal("fetch", fetchMock);
  function Tela() {
    const [atual, setAtual] = useState(conta);
    return <><button onClick={() => setAtual({ ...conta, valor_centavos: 20000, versao_compartilhamento: "hash-novo" })}>Refetch</button><SolicitacaoAcoes conta={atual} /></>;
  }
  renderComSessao(<Tela />);
  fireEvent.click(screen.getByRole("button", { name: "Pedir para alguém pagar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ana" }));
  const confirmacao = screen.getByRole("checkbox", { name: /Confirmo o compartilhamento/ }) as HTMLInputElement;
  fireEvent.click(confirmacao);
  fireEvent.click(screen.getByRole("button", { name: "Refetch" }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar pedido" }));
  expect((await screen.findByRole("alert")).textContent).toContain("A cobrança mudou");
  expect(confirmacao.checked).toBe(false);
  expect(fetchMock.mock.calls.every(([url]) => url.endsWith("/opcoes/"))).toBe(true);
});

test("T10-E: 404 de tentativa não permite nova chave antes de tombstone", async () => {
  document.cookie = "csrftoken=t";
  const nonce = "5f2d5844-0e98-4d49-a5ca-9682730e1842";
  guardarTentativa("u1", "l1", nonce);
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => init?.method === "DELETE" ? new Response(null, { status: 204 }) : url.includes("/nonce/") ? json(404) : json(200, []));
  vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<SolicitacaoAcoes conta={conta} />);
  fireEvent.click(await screen.findByRole("button", { name: "Ver pedido" }));
  fireEvent.click(await screen.findByRole("button", { name: "Encerrar tentativa" }));
  await waitFor(() => expect(tentativaPendente("u1", "l1")).toBeNull());
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining(`/nonce/${nonce}/`), expect.objectContaining({ method: "DELETE" }));
  expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
});

test("Q10-13: falha ao revalidar opções oculta elegíveis antigos e bloqueia envio", async () => {
  let consultas = 0;
  vi.stubGlobal("fetch", vi.fn(async () => ++consultas === 1 ? json(200, [{ id: "g1", nome: "Família", pagadores: [{ id: "u2", nome: "Ana" }] }]) : json(403)));
  function Tela() {
    const cache = useQueryClient();
    return <><button onClick={() => cache.invalidateQueries({ queryKey: ["solicitacoes", "opcoes"] })}>Revalidar</button><SolicitacaoAcoes conta={conta} /></>;
  }
  renderComSessao(<Tela />);
  fireEvent.click(screen.getByRole("button", { name: "Pedir para alguém pagar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ana" }));
  fireEvent.click(screen.getByRole("checkbox", { name: /Confirmo/ }));
  fireEvent.click(screen.getByRole("button", { name: "Revalidar" }));
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Ana" })).toBeNull();
  expect((screen.getByRole("button", { name: "Enviar pedido" }) as HTMLButtonElement).disabled).toBe(true);
});

test("B10-final1: troca de único grupo não redireciona confirmação anterior", async () => {
  document.cookie = "csrftoken=t";
  let consultas = 0;
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith("/opcoes/")) {
      consultas++;
      return json(200, [{ id: consultas === 1 ? "g1" : "g2", nome: consultas === 1 ? "Grupo A" : "Grupo B", pagadores: [{ id: "u2", nome: "Ana" }] }]);
    }
    if (init?.method === "POST") {
      const body = JSON.parse(String(init.body));
      return json(202, { id: "s1", nonce: body.nonce, estado: "preparando", copia_id: null, pode_cancelar: true });
    }
    return json(404);
  });
  vi.stubGlobal("fetch", fetchMock);
  function Tela() {
    const cache = useQueryClient();
    return <><button onClick={() => cache.invalidateQueries({ queryKey: ["solicitacoes", "opcoes"] })}>Revalidar</button><SolicitacaoAcoes conta={conta} /></>;
  }
  renderComSessao(<Tela />);
  fireEvent.click(screen.getByRole("button", { name: "Pedir para alguém pagar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ana" }));
  const confirmacao = screen.getByRole("checkbox", { name: /Confirmo/ }) as HTMLInputElement;
  fireEvent.click(confirmacao);
  expect(confirmacao.checked).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Revalidar" }));
  const grupo = await screen.findByRole("combobox", { name: "Grupo" });
  await waitFor(() => expect(confirmacao.checked).toBe(false));
  expect((screen.getByRole("button", { name: "Enviar pedido" }) as HTMLButtonElement).disabled).toBe(true);
  expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  fireEvent.change(grupo, { target: { value: "g2" } });
  fireEvent.click(screen.getByRole("button", { name: "Ana" }));
  expect(confirmacao.checked).toBe(false);
  fireEvent.click(confirmacao);
  fireEvent.click(screen.getByRole("button", { name: "Enviar pedido" }));
  await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(true));
  const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST")!;
  expect(JSON.parse(String(post[1]?.body)).grupo_id).toBe("g2");
});

test("Q10-14: reserva 202 mantém nonce e informa preparação sem prometer sucesso", async () => {
  document.cookie = "csrftoken=t";
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith("/opcoes/")) return json(200, [{ id: "g1", nome: "Família", pagadores: [{ id: "u2", nome: "Ana" }] }]);
    if (init?.method === "POST") {
      const body = JSON.parse(String(init.body));
      return json(202, { id: "s1", nonce: body.nonce, estado: "preparando", copia_id: null, pode_cancelar: true });
    }
    return json(404);
  });
  vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<SolicitacaoAcoes conta={conta} />);
  fireEvent.click(screen.getByRole("button", { name: "Pedir para alguém pagar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ana" }));
  fireEvent.click(screen.getByRole("checkbox", { name: /Confirmo/ }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar pedido" }));
  expect(await screen.findByText("Preparando pedido…")).toBeTruthy();
  expect(screen.getByText(/Você pode fechar esta janela/)).toBeTruthy();
  expect(screen.queryByText("Pedido criado.")).toBeNull();
  const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST")!;
  const payload = JSON.parse(String(post[1]?.body));
  expect(payload.versao_compartilhamento).toBe("hash-antigo");
  expect(payload.confirmar_compartilhamento).toBe(true);
  expect(tentativaPendente("u1", "l1")).toBe(payload.nonce);
});

test("Q10-14: fechar durante POST incerto preserva nonce para reconciliar ao reabrir", async () => {
  document.cookie = "csrftoken=t";
  let resolver!: (value: Response) => void;
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith("/opcoes/")) return json(200, [{ id: "g1", nome: "Família", pagadores: [{ id: "u2", nome: "Ana" }] }]);
    if (init?.method === "POST") return new Promise<Response>((resolve) => { resolver = resolve; });
    return json(404);
  });
  vi.stubGlobal("fetch", fetchMock);
  renderComSessao(<SolicitacaoAcoes conta={conta} />);
  fireEvent.click(screen.getByRole("button", { name: "Pedir para alguém pagar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ana" }));
  fireEvent.click(screen.getByRole("checkbox", { name: /Confirmo/ }));
  fireEvent.click(screen.getByRole("button", { name: "Enviar pedido" }));
  await waitFor(() => expect(tentativaPendente("u1", "l1")).toBeTruthy());
  const nonce = tentativaPendente("u1", "l1")!;
  fireEvent.click(screen.getByRole("button", { name: "Voltar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Ver pedido" }));
  expect(await screen.findByRole("button", { name: "Encerrar tentativa" })).toBeTruthy();
  expect(tentativaPendente("u1", "l1")).toBe(nonce);
  resolver(json(202, { id: "s1", nonce, estado: "preparando", copia_id: null, pode_cancelar: true }));
});
