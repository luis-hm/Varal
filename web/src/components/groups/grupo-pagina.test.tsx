import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import type { GrupoDetalhe, Papel } from "@/lib/grupos/client";
import { GrupoPagina } from "./grupo-pagina";

const router = { replace: vi.fn(), push: vi.fn(), refresh: vi.fn() };
vi.mock("next/navigation", () => ({ useRouter: () => router }));

const TOKEN = "9fKq2mXbAbCdEfGhIjKlMnOpQrStUvWxYz0123456R4dT";
type Chamada = { method: string; url: string; body?: unknown };
let chamadas: Chamada[] = [];
let detalhe: { status: number; body?: unknown };
let conviteN = 0;

const grupo = (meu_papel: Papel): GrupoDetalhe => ({
  id: "g1",
  nome: "Família",
  meu_papel,
  membros: [
    { id: "m1", nome: "Dev", email: "dev@varal.local", papel: "admin", sou_eu: meu_papel === "admin" },
    { id: "m2", nome: "", email: "observador@varal.local", papel: "observador", sou_eu: meu_papel === "observador" },
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
  vi.unstubAllGlobals();
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
  expect(screen.getByText("Sem contas ainda")).toBeTruthy();
  // Stage-04+ content stays hidden (CA18).
  expect(screen.queryByText(/Contas que se repetem|Configurações|Gerenciar papéis|Paga \d+ contas/)).toBeNull();
});

test.each(["membro", "observador"] as const)("ca11: %s sees the page with no management action", async (papel) => {
  detalhe = { status: 200, body: grupo(papel) };
  renderPagina();
  await screen.findByRole("heading", { name: "Família" });
  expect(screen.queryByRole("button", { name: /Convidar|Nova casa|Admin|Observador|Casa 1/ })).toBeNull();
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
