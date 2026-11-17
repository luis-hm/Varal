import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AppShell } from "./app-shell";

const gate = vi.hoisted(() => {
  let liberar!: () => void;
  const pronto = new Promise<void>((resolve) => { liberar = resolve; });
  return { pronto, liberar, renderizada: vi.fn() };
});
const gateAvisos = vi.hoisted(() => {
  let liberar!: () => void;
  const pronto = new Promise<void>((resolve) => { liberar = resolve; });
  return { pronto, liberar, renderizada: vi.fn() };
});
vi.mock("next/navigation", () => ({ usePathname: () => "/", useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));
vi.mock("@/components/bills/conta-folha", async () => {
  await gate.pronto;
  const { Folha } = await import("@/components/ui/folha");
  return { ContaFolha: ({ open, onClose, returnFocusTo }: { open: boolean; onClose: () => void; returnFocusTo?: HTMLElement | null }) => {
    gate.renderizada(open);
    return <Folha open={open} title="Nova conta" onClose={onClose} returnFocusTo={returnFocusTo}><p>Formulário aberto</p></Folha>;
  } };
});
vi.mock("@/components/notifications/avisos", async () => {
  await gateAvisos.pronto;
  return { AvisosGaveta: () => { gateAvisos.renderizada(); return <p>Gaveta aberta</p>; } };
});

test("formulário carregado após fallback retorna foco ao FAB e não reabre após cancelamento", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ nao_lidas: 0, recentes: [] }), { status: 200 })));
  const user = { id: "u1", nome: "Ana", email: "ana@example.test", espaco_pessoal: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const }, grupos: [] };
  render(<QueryClientProvider client={new QueryClient()}><AppShell user={user} espaco={{ id: "p1", nome: "Pessoal", tipo: "pessoal" }}>Conteúdo</AppShell></QueryClientProvider>);
  const fab = screen.getAllByRole("button", { name: "Nova conta" })[1];
  fab.focus();
  fireEvent.click(fab);
  const dialog = await screen.findByRole("dialog", { name: "Nova conta" });
  expect(screen.getByRole("status").textContent).toContain("Carregando formulário");
  fireEvent(dialog, new Event("cancel", { bubbles: true, cancelable: true }));
  await waitFor(() => expect(screen.queryByRole("dialog", { name: "Nova conta" })).toBeNull());
  expect(document.activeElement).toBe(fab);
  fireEvent.click(fab);
  const fallback = await screen.findByRole("dialog", { name: "Nova conta" });
  fallback.querySelector<HTMLButtonElement>("button")!.focus();
  gate.liberar();
  await screen.findByText("Formulário aberto");
  expect(gate.renderizada).toHaveBeenCalledWith(true);
  const carregado = screen.getByRole("dialog", { name: "Nova conta" });
  carregado.querySelector<HTMLButtonElement>("button")!.focus();
  fireEvent(carregado, new Event("cancel", { bubbles: true, cancelable: true }));
  await waitFor(() => expect(document.activeElement).toBe(fab));
  expect(screen.queryByText("Formulário aberto")).toBeNull();
  vi.unstubAllGlobals();
});

test("gaveta em carregamento é cancelável e não reabre após retorno do chunk", async () => {
  vi.stubGlobal("matchMedia", () => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ nao_lidas: 0, recentes: [] }), { status: 200 })));
  const user = { id: "u1", nome: "Ana", email: "ana@example.test", espaco_pessoal: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const }, grupos: [] };
  render(<QueryClientProvider client={new QueryClient()}><AppShell user={user} espaco={{ id: "p1", nome: "Pessoal", tipo: "pessoal" }}>Conteúdo</AppShell></QueryClientProvider>);
  fireEvent.click(screen.getByRole("link", { name: "Avisos" }));
  const dialog = await screen.findByRole("dialog", { name: "Avisos" });
  expect(screen.getByRole("status").textContent).toContain("Carregando avisos");
  fireEvent(dialog, new Event("cancel", { bubbles: true, cancelable: true }));
  await waitFor(() => expect(screen.queryByRole("dialog", { name: "Avisos" })).toBeNull());
  await act(async () => { gateAvisos.liberar(); await gateAvisos.pronto; await new Promise((resolve) => setTimeout(resolve, 0)); });
  expect(gateAvisos.renderizada).not.toHaveBeenCalled();
  expect(screen.queryByText("Gaveta aberta")).toBeNull();
  vi.unstubAllGlobals();
});
