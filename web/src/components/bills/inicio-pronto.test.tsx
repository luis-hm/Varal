import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sessao } from "@/components/layout/app-shell";
import { Inicio } from "./inicio";

const dados = vi.hoisted(() => ({ avisos: false }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));
vi.mock("@/lib/contas/hooks", () => ({ useResumo: () => ({ data: { mes: "2026-11", total_centavos: 120000, valores_indefinidos_qtd: 1, qtd: 1, pagas_qtd: 0, vencidas_qtd: 0, vence_qtd: 0, janela_alerta_dias: 3, atencao: [], por_casa: [] } }) }));
vi.mock("@/lib/notificacoes/hooks", () => ({ useAvisosResumo: () => ({ data: dados.avisos ? { nao_lidas: 0, recentes: [] } : undefined, isError: false }), useLeituraAvisos: () => ({ um: { isPending: false }, todos: {} }) }));
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); dados.avisos = false; });

test("RNF05: anima valor por 1,2 s e só marca pronto após valor final e avisos", () => {
  let proximo = 0;
  const quadros = new Map<number, FrameRequestCallback>();
  vi.stubGlobal("requestAnimationFrame", (fn: FrameRequestCallback) => { const id = ++proximo; quadros.set(id, fn); return id; });
  vi.stubGlobal("cancelAnimationFrame", (id: number) => { quadros.delete(id); });
  vi.stubGlobal("matchMedia", () => ({ matches: false }));
  const mark = vi.spyOn(performance, "mark").mockImplementation(() => ({} as PerformanceMark));
  const usuario = { id: "u1", nome: "Ana", email: "ana@example.test", espaco_pessoal: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const }, grupos: [] };
  const sessao = { user: usuario, espaco: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const }, novaConta: () => {}, escolherEspaco: () => {}, abrirAvisos: () => {} };
  const client = new QueryClient();
  const tree = () => <QueryClientProvider client={client}><Sessao.Provider value={sessao}><Inicio /></Sessao.Provider></QueryClientProvider>;
  const view = render(tree());
  function quadro(tempo: number) { const atual = [...quadros.values()]; quadros.clear(); act(() => atual.forEach((fn) => fn(tempo))); }
  expect(screen.getByText("1 valor a definir")).toBeTruthy();
  quadro(0);
  quadro(600);
  expect(mark).not.toHaveBeenCalled();
  quadro(1200);
  expect(screen.getAllByText("R$ 1.200,00").length).toBeGreaterThan(0);
  expect(mark).not.toHaveBeenCalled();
  dados.avisos = true;
  view.rerender(tree());
  quadro(1216); quadro(1232);
  expect(mark).toHaveBeenCalledOnce();
  expect(mark).toHaveBeenCalledWith("inicio_pronto");
});
