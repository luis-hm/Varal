import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import type { GrupoDetalhe, Papel } from "@/lib/grupos/client";
import { GrupoPagina } from "./grupo-pagina";
import houseStyles from "./house-card.module.css";

const router = { replace: vi.fn(), push: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const TOKEN = "9fKq2mXbAbCdEfGhIjKlMnOpQrStUvWxYz0123456R4dT";
type Chamada = { method: string; url: string; body?: unknown };
let chamadas: Chamada[] = [];
let detalhe: { status: number; body?: unknown };
let conviteN = 0;
let sair: (body: { resolucoes?: unknown[] }) => Response = () => json(204);

const grupo = (meu_papel: Papel): GrupoDetalhe => ({
  id: "g1",
  nome: "Família",
  meu_papel,
  janela_alerta_dias: 3,
  membros: [
    { id: "m1", usuario: "u1", nome: "Dev", email: "dev@varal.local", papel: "admin", sou_eu: meu_papel === "admin", contas_atribuidas_qtd: 2 },
    { id: "m2", usuario: "u2", nome: "", email: "observador@varal.local", papel: "observador", sou_eu: meu_papel === "observador", contas_atribuidas_qtd: 0 },
  ],
  casas: [{ id: "c1", nome: "Casa 1" }],
});

const json = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

beforeEach(() => {
  chamadas = [];
  conviteN = 0;
  document.cookie = "csrftoken=t";
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    chamadas.push({ method, url: input, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    if (input === "/api/grupos/g1/" && method === "GET") return json(detalhe.status, detalhe.body);
    if (input === "/api/grupos/g1/convites/" && method === "GET") return json(200, []);
    if (input === "/api/espacos/g1/resumo/")
      return json(200, { mes: "2026-11", total_centavos: 0, qtd: 4, pagas_qtd: 3, vencidas_qtd: 0, vence_qtd: 0, janela_alerta_dias: 3, atencao: [], por_casa: [{ id: "c1", nome: "Casa 1", total_centavos: 147960, qtd: 4, pagas_qtd: 3 }] });
    if (input === "/api/grupos/g1/" && method === "PATCH") return json(200, { ...grupo("admin"), ...JSON.parse(String(init!.body)) });
    if (input === "/api/grupos/g1/sair/") return sair(JSON.parse(String(init?.body ?? "{}")));
    if (input === "/api/grupos/g1/convites/" && method === "POST") {
      conviteN += 1;
      const papel = (JSON.parse(String(init!.body)) as { papel: Papel }).papel;
      return json(201, { id: `cv${conviteN}`, url: `http://localhost:3000/c/${TOKEN}${conviteN}`, expira_em: "2026-11-21T12:00:00Z", papel });
    }
    if (method === "DELETE") return json(204);
    return json(404, { detail: "x" });
  }));
});

afterEach(() => {
  sair = () => json(204);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

function renderPagina() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return render(<GrupoPagina id="g1" />, { wrapper });
}

test("ca11/ca18: admin sees the whole page with management actions; name falls back to e-mail", async () => {
  detalhe = { status: 200, body: grupo("admin") };
  renderPagina();
  expect(await screen.findByRole("heading", { name: "Família" })).toBeTruthy();
  expect(screen.getByText(/2 membros · 1 casa · você é admin/)).toBeTruthy();
  expect(screen.getByRole("button", { name: "Convidar pessoa" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "+ Nova casa" })).toBeTruthy();
  expect(screen.getByRole("button", { name: /Dev \(você\).*Admin/ })).toBeTruthy();
  expect(screen.getByRole("button", { name: /observador@varal\.local.*Observador/ })).toBeTruthy();
  // Q07-7: progress counts visible paid accounts in the due month.
  expect(await screen.findByText("R$ 1.479,60")).toBeTruthy();
  expect(screen.getByText("3 de 4 pagas em novembro")).toBeTruthy();
  expect(screen.getAllByRole("button", { name: "Configurações" }).length).toBeGreaterThan(0);
  // Later stages stay hidden.
  expect(screen.queryByText(/Contas que se repetem|Gerenciar papéis/)).toBeNull();
});

test("q07-7: a house without visible bills shows zero without a progress bar", async () => {
  detalhe = { status: 200, body: grupo("admin") };
  vi.stubGlobal("fetch", vi.fn(async (input: string) => input === "/api/grupos/g1/" ? json(200, detalhe.body) : input === "/api/espacos/g1/resumo/" ? json(200, { mes: "2026-11", total_centavos: 0, qtd: 0, pagas_qtd: 0, vencidas_qtd: 0, vence_qtd: 0, janela_alerta_dias: 3, atencao: [], por_casa: [] }) : json(200, [])));
  renderPagina();
  const legenda = await screen.findByText("0 contas em novembro");
  expect(legenda.parentElement?.querySelector(`.${houseStyles.bar}`)).toBeNull();
});

test.each(["membro", "observador"] as const)("ca11: %s sees the page with no management action", async (papel) => {
  detalhe = { status: 200, body: grupo(papel) };
  renderPagina();
  await screen.findByRole("heading", { name: "Família" });
  expect(screen.queryByRole("button", { name: /Convidar|Nova casa|Admin|Observador|Casa 1|Configurações/ })).toBeNull();
  expect(screen.getByRole("button", { name: "Sair do grupo" })).toBeTruthy(); // Q3: leaving is about yourself
  expect(chamadas.some((c) => c.url.includes("convites"))).toBe(false);
});

test("ca11: the payer (403) is sent to the simple mode", async () => {
  detalhe = { status: 403, body: { detail: "Seu papel não permite esta ação." } };
  renderPagina();
  await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/grupos/g1/simples"));
});

test("ca14/ca15: a group you are not in shows a neutral message", async () => {
  detalhe = { status: 404, body: { detail: "Not found." } };
  renderPagina();
  expect((await screen.findByRole("alert")).textContent).toBe("Este grupo não existe ou você não participa dele.");
});

test("ca19/rn31: invite starts as Pagador, shows the short link, copies the full one, revokes unused links", async () => {
  detalhe = { status: 200, body: grupo("admin") };
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
  renderPagina();
  fireEvent.click(await screen.findByRole("button", { name: "Convidar pessoa" }));
  expect(screen.getByRole("radio", { name: /Pagador/ })).toHaveProperty("checked", true);
  expect(await screen.findByText("localhost:3000/c/9fKq2mXb…4dT1")).toBeTruthy();
  expect(chamadas.find((c) => c.method === "POST")?.body).toEqual({ papel: "pagador" });
  expect(document.body.textContent).not.toContain(TOKEN);
  expect(screen.getByText("Expira em 7 dias · vale para 1 pessoa")).toBeTruthy();

  // Switching role revokes the unused link and creates a new one.
  fireEvent.click(screen.getByRole("radio", { name: /Observador/ }));
  await screen.findByText("localhost:3000/c/9fKq2mXb…4dT2");
  expect(chamadas.filter((c) => c.method === "DELETE").map((c) => c.url)).toEqual(["/api/grupos/g1/convites/cv1/"]);

  // Copy uses the full URL; a used link is not revoked on close.
  await act(async () => fireEvent.click(screen.getByRole("button", { name: "Link do convite, copiar" })));
  expect(writeText).toHaveBeenCalledWith(`http://localhost:3000/c/${TOKEN}2`);
  fireEvent.click(screen.getAllByRole("button", { name: "Fechar" })[0]);
  expect(chamadas.filter((c) => c.method === "DELETE")).toHaveLength(1);
  for (const store of [localStorage, sessionStorage]) expect(JSON.stringify({ ...store })).not.toContain(TOKEN);

  // Opening again and closing without using it revokes that link.
  fireEvent.click(screen.getByRole("button", { name: "Convidar pessoa" }));
  await screen.findByText("localhost:3000/c/9fKq2mXb…4dT3");
  fireEvent.click(screen.getAllByRole("button", { name: "Fechar" })[0]);
  await waitFor(() => expect(chamadas.filter((c) => c.method === "DELETE").map((c) => c.url)).toContain("/api/grupos/g1/convites/cv3/"));
});

test("q10/rn13: admin sets the alert window from 1 to 7 days", async () => {
  detalhe = { status: 200, body: grupo("admin") };
  renderPagina();
  fireEvent.click((await screen.findAllByRole("button", { name: "Configurações" }))[0]);
  const campo = screen.getByLabelText("Avisar quantos dias antes do vencimento");
  fireEvent.change(campo, { target: { value: "9" } });
  expect(screen.getByText("Escolha de 1 a 7 dias.")).toBeTruthy();
  fireEvent.change(campo, { target: { value: "5" } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  await waitFor(() => expect(chamadas.find((c) => c.method === "PATCH")?.body).toEqual({ janela_alerta_dias: 5 }));
});

test("ca22/rn32: a blocked exit lists the bills, each resolved before Sair resends with resolucoes", async () => {
  detalhe = { status: 200, body: grupo("membro") };
  sair = (body) =>
    body.resolucoes
      ? json(204)
      : json(409, {
          code: "conta_restrita_orfa",
          detail: "Você é a única pessoa que vê 2 contas restritas. Escolha quem vê cada uma ou cancele antes de sair.",
          contas: [{ id: "l1", descricao: "Remédio da vó" }, { id: "l2", descricao: "Presente" }],
          pessoas: [{ id: "u9", nome: "Ana" }],
        });
  vi.spyOn(window, "confirm").mockReturnValue(true);
  renderPagina();
  fireEvent.click(await screen.findByRole("button", { name: "Sair do grupo" }));
  expect(await screen.findByText(/Escolha quem vê cada uma/)).toBeTruthy();
  expect(screen.getByRole("link", { name: "Remédio da vó" }).getAttribute("href")).toBe("/contas/l1");
  const sairBtn = screen.getByRole("button", { name: "Sair" });
  expect(sairBtn).toHaveProperty("disabled", true);

  const l1 = screen.getByRole("group", { name: "O que fazer com Remédio da vó" });
  fireEvent.click(within(l1).getByRole("button", { name: "Escolher quem vê" }));
  fireEvent.click(within(screen.getByRole("group", { name: "Quem vê Remédio da vó" })).getByRole("button", { name: "Ana" }));
  fireEvent.click(within(screen.getByRole("group", { name: "O que fazer com Presente" })).getByRole("button", { name: "Cancelar conta" }));
  expect(sairBtn).toHaveProperty("disabled", false);
  fireEvent.click(sairBtn);
  await waitFor(() => expect(router.replace).toHaveBeenCalledWith("/grupos"));
  expect(chamadas.filter((c) => c.url === "/api/grupos/g1/sair/").map((c) => c.body)).toEqual([
    undefined,
    { resolucoes: [{ lancamento: "l1", acao: "acesso", usuarios: ["u9"] }, { lancamento: "l2", acao: "cancelar" }] },
  ]);
});
