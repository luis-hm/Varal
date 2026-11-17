import { afterEach, expect, test, vi } from "vitest";

afterEach(() => { vi.unstubAllGlobals(); vi.resetModules(); localStorage.clear(); document.cookie = "varal_owner=; Max-Age=0; Path=/"; document.cookie = "varal_local_locked=; Max-Age=0; Path=/"; document.documentElement.removeAttribute("data-sessao-oculta"); });
const A = "00000000-0000-4000-8000-000000000001";
const B = "00000000-0000-4000-8000-000000000002";

test("T11-I: resultado A tardio não entra em cache da sessão B", async () => {
  const isolamento = await import("./isolamento");
  const { call } = await import("@/lib/grupos/client");
  isolamento.iniciarIdentidade(B);
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ segredo: "dado A" }), { status: 200, headers: { "X-Varal-Identidade": A, "Content-Type": "application/json" } }));
  vi.stubGlobal("fetch", fetchMock);
  await expect(call("notificacoes/resumo/")).rejects.toBeInstanceOf(isolamento.SessaoAlterada);
  expect(fetchMock.mock.calls[0][1].headers["X-Varal-Identidade-Esperada"]).toBe(B);
  expect(document.documentElement.hasAttribute("data-sessao-oculta")).toBe(true);
});

test("T11-I: autenticação atrasada não substitui a âncora da tentativa mais recente", async () => {
  const isolamento = await import("./isolamento");
  const anterior = isolamento.iniciarAutenticacao();
  const atual = isolamento.iniciarAutenticacao();
  isolamento.concluirAutenticacao(B, atual, () => {});
  expect(() => isolamento.concluirAutenticacao(A, anterior, () => {})).toThrow(isolamento.SessaoAlterada);
  expect(document.cookie).toContain(`varal_owner=${B}`);
});

test("T11-I: fechar sessão impede resultado privado em voo de ser aceito", async () => {
  const isolamento = await import("./isolamento");
  const { call } = await import("@/lib/grupos/client");
  isolamento.iniciarIdentidade(A);
  let responder!: (value: Response) => void;
  vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { responder = resolve; })));
  const pendente = call("notificacoes/resumo/");
  isolamento.bloquearSessao();
  responder(new Response("{}", { status: 200, headers: { "X-Varal-Identidade": A } }));
  await expect(pendente).rejects.toBeInstanceOf(isolamento.SessaoAlterada);
});

test("T11-C: 401 reauth autenticado é distinguido de sessão encerrada", async () => {
  const isolamento = await import("./isolamento");
  const { reautenticarSenha } = await import("./client");
  isolamento.iniciarIdentidade(A);
  document.cookie = "csrftoken=test; Path=/";
  const flows = [{ id: "reauthenticate" }];
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ status: 401, meta: { is_authenticated: true }, data: { flows } }), { status: 401, headers: { "X-Varal-Identidade": A } })).mockResolvedValueOnce(new Response(JSON.stringify({ status: 401, meta: { is_authenticated: false }, data: { flows: [] } }), { status: 401 })));
  await expect(reautenticarSenha({ password: "teste" })).rejects.toMatchObject({ status: 401, autenticada: true, flows });
  await expect(reautenticarSenha({ password: "teste" })).rejects.toMatchObject({ status: 401, autenticada: false });
});

test("T11-I: conclusão avisa aba observadora após início e limpa cache A antes de aceitar B", async () => {
  const { QueryClient } = await import("@tanstack/react-query");
  const isolamento = await import("./isolamento");
  const eventos: unknown[] = [];
  class Canal {
    postMessage(value: unknown) { observadorRemoto(value); }
    close() {}
  }
  vi.stubGlobal("BroadcastChannel", Canal);
  const cache = new QueryClient();
  cache.setQueryData(["contas"], { descricao: "privado A" });
  isolamento.iniciarIdentidade(A);
  document.cookie = `varal_owner=${A}; Path=/`;
  const geracao = isolamento.iniciarAutenticacao();
  const observadorRemoto = (value: unknown) => eventos.push(value);
  const storage = vi.spyOn(Storage.prototype, "setItem");
  const observado = vi.fn();
  window.addEventListener("varal-sessao-bloqueada", observado);
  isolamento.concluirAutenticacao(B, geracao, () => {
    expect(document.cookie).toContain(`varal_owner=${A}`);
    expect(isolamento.sessaoBloqueada()).toBe(true);
    cache.clear();
  });
  window.removeEventListener("varal-sessao-bloqueada", observado);
  expect(observado).toHaveBeenCalledTimes(1);
  expect(cache.getQueryData(["contas"])).toBeUndefined();
  expect(document.cookie).toContain(`varal_owner=${B}`);
  expect(isolamento.identidadeAtual()).toBe(B);
  expect(isolamento.sessaoBloqueada()).toBe(false);
  expect(storage).toHaveBeenCalledWith("varal.sessao.evento", expect.any(String));
  expect(eventos).toEqual(["autenticacao"]);
  storage.mockRestore();
});
