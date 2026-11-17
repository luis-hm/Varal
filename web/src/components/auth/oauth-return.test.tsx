import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { iniciarAutenticacao } from "@/lib/auth/isolamento";
import { GoogleReturn } from "./auth-form";

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); localStorage.clear(); document.cookie = "varal_owner=; Max-Age=0; Path=/"; window.history.replaceState(null, "", "/"); });

test("T11-J: cookie divergente rejeitado pelo ticket nunca é adotado", async () => {
  const tentativa = iniciarAutenticacao(true);
  const ticket = "00000000-0000-4000-8000-000000000001";
  document.cookie = "csrftoken=teste; Path=/";
  window.history.replaceState(null, "", `/entrar/retorno?tentativa=${tentativa}&ticket=${ticket}`);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 409 })));
  render(<QueryClientProvider client={new QueryClient()}><GoogleReturn /></QueryClientProvider>);
  await screen.findByText(/Não foi possível entrar com Google/);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  const [url, init] = vi.mocked(fetch).mock.calls[0];
  expect(url).toBe("/api/auth/google/tickets/consumir/");
  expect(JSON.parse(String(init?.body))).toEqual({ tentativa, ticket });
  expect(document.cookie).not.toContain("varal_owner=");
  expect(window.location.search).toBe("");
});

test("T11-J: retorno sem ticket não consulta nem adota a sessão corrente", async () => {
  const tentativa = iniciarAutenticacao(true);
  window.history.replaceState(null, "", `/entrar/retorno?tentativa=${tentativa}`);
  vi.stubGlobal("fetch", vi.fn());
  render(<QueryClientProvider client={new QueryClient()}><GoogleReturn /></QueryClientProvider>);
  await screen.findByText(/Não foi possível entrar com Google/);
  expect(fetch).not.toHaveBeenCalled();
  expect(document.cookie).not.toContain("varal_owner=");
});
