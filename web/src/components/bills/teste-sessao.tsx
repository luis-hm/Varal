// Test helper: renders inside the AppShell session and a fresh QueryClient.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { Sessao } from "@/components/layout/app-shell";
import type { Me } from "@/lib/auth/types";
import type { EspacoAtual } from "@/lib/espaco";

export const me = {
  id: "u1",
  email: "dev@varal.local",
  nome: "Dev Martins",
  espaco_pessoal: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const },
  grupos: [{ id: "g1", nome: "Família", papel: "admin" as const }],
};

export const json = (status: number, body?: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

export function renderComSessao(ui: ReactNode, espaco: EspacoAtual = { id: "g1", nome: "Família", tipo: "grupo", papel: "admin" }, user: Me = me) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <Sessao.Provider value={{ user, espaco, novaConta: () => {}, escolherEspaco: () => {} }}>{ui}</Sessao.Provider>
    </QueryClientProvider>,
  );
}
