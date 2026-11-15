import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, expect, test, vi } from "vitest";
import { AceiteConvite } from "./aceite-convite";

const json = (status: number, body: unknown) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const anonimo = { status: 401, meta: { is_authenticated: false }, data: { flows: [] } };

function renderAceite(convite: Response, sessao: unknown) {
  vi.stubGlobal("fetch", vi.fn(async (url: string) => (url.startsWith("/api/convites/") ? convite.clone() : json(401, sessao))));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return render(<AceiteConvite token="tok_EN-123" />, { wrapper });
}

afterEach(() => vi.unstubAllGlobals());

test("ca04: without a session the invite offers login or signup and comes back to /c/<token>", async () => {
  renderAceite(json(200, { grupo_nome: "Família", papel: "observador", expira_em: new Date(Date.now() + 6.5 * 86_400_000).toISOString() }), anonimo);
  expect(await screen.findByRole("heading", { name: "Família" })).toBeTruthy();
  expect(screen.getByText("Só acompanha, sem alterar nada")).toBeTruthy();
  expect((await screen.findByRole("link", { name: "Entrar" })).getAttribute("href")).toBe("/entrar?proximo=%2Fc%2Ftok_EN-123");
  expect(screen.getByRole("link", { name: "Criar conta" }).getAttribute("href")).toBe("/criar-conta?proximo=%2Fc%2Ftok_EN-123");
  expect(screen.queryByRole("button", { name: "Aceitar convite" })).toBeNull();
});

test("ca05: an invalid invite (410) asks for a new one", async () => {
  renderAceite(json(410, { detail: "qualquer" }), anonimo);
  expect((await screen.findByRole("alert")).textContent).toBe("Este convite não vale mais. Peça um novo a quem convidou.");
});
