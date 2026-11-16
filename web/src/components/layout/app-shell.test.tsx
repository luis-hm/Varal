import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { AppShell } from "./app-shell";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

let pathname = "/";
vi.mock("next/navigation", () => ({ usePathname: () => pathname, useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

// SideNav and TabBar both link "Contas"; the TabBar is the second one (the SideNav is hidden by CSS below 1024px).
const tabBar = () => screen.getAllByRole("link", { name: "Contas" }).length === 2;

test("ajuste 28: the bill detail (07) is a stacked screen without TabBar; the list keeps it", () => {
  pathname = "/contas/abc";
  const client = new QueryClient();
  const { container, unmount } = render(<QueryClientProvider client={client}><AppShell>x</AppShell></QueryClientProvider>);
  expect(tabBar()).toBe(false);
  expect(container.querySelector("[data-empilhada]")).toBeTruthy(); // no bottom room kept for the TabBar
  unmount();
  pathname = "/contas";
  render(<QueryClientProvider client={client}><AppShell>x</AppShell></QueryClientProvider>);
  expect(tabBar()).toBe(true);
});

test("gaveta de avisos preserva contexto e voltar restaura foco", async () => {
  pathname = "/contas";
  window.history.replaceState(null, "", "/contas?mes=2026-11&status=pendente");
  vi.stubGlobal("matchMedia", () => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ nao_lidas: 0, recentes: [], resultados: [], proximo: null, email: true, push: true, versao: 1 }), { status: 200, headers: { "Content-Type": "application/json" } })));
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  const user = { id: "u1", nome: "Ana", email: "ana@varal.local", espaco_pessoal: { id: "p1", nome: "Pessoal", tipo: "pessoal" as const }, grupos: [] };
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const { fireEvent, waitFor } = await import("@testing-library/react");
  render(<QueryClientProvider client={client}><AppShell user={user} espaco={{ id: "p1", nome: "Pessoal", tipo: "pessoal" }}><div data-testid="contexto"><p>Contexto de contas</p><input aria-label="Filtro local" defaultValue="Energia" /></div></AppShell></QueryClientProvider>);
  const contexto = screen.getByTestId("contexto");
  contexto.scrollTop = 75;
  const opener = screen.getByRole("link", { name: "Avisos" });
  expect(opener.getAttribute("href")).toBe("/avisos");
  fireEvent.click(opener, { ctrlKey: true });
  expect(screen.queryByRole("dialog")).toBeNull();
  opener.focus();
  fireEvent.click(opener);
  expect(screen.getByText("Contexto de contas")).toBeTruthy();
  expect(window.location.search).toBe("?mes=2026-11&status=pendente");
  expect((screen.getByRole("textbox", { name: "Filtro local" }) as HTMLInputElement).value).toBe("Energia");
  expect(contexto.scrollTop).toBe(75);
  expect(screen.getByRole("dialog", { name: "Avisos" })).toBeTruthy();
  fireEvent.popState(window);
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(window.location.search).toBe("?mes=2026-11&status=pendente");
  expect(document.activeElement).toBe(opener);
  Reflect.deleteProperty(HTMLDialogElement.prototype, "showModal"); Reflect.deleteProperty(HTMLDialogElement.prototype, "close"); vi.unstubAllGlobals();
});
