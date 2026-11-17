import { MutationObserver, QueryClient, onlineManager } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { LogoutButton } from "@/components/auth/logout-button";
import { desbloquearSessao, iniciarIdentidade } from "@/lib/auth/isolamento";
import { criarQueryClient, Providers } from "./providers";

const push = vi.hoisted(() => vi.fn());
vi.mock("@/lib/notificacoes/push", () => ({ desativarPush: push }));
const A = "00000000-0000-4000-8000-000000000001";
afterEach(() => {
  onlineManager.setOnline(true);
  desbloquearSessao();
  vi.unstubAllGlobals(); vi.clearAllMocks();
  document.cookie = "varal_owner=; Max-Age=0; Path=/";
  document.cookie = "varal_local_locked=; Max-Age=0; Path=/";
  document.documentElement.removeAttribute("data-sessao-oculta");
  localStorage.clear();
});

test("RNF10: configuração padrão do TanStack pausa e retoma uma mutação offline", async () => {
  onlineManager.setOnline(false);
  const client = new QueryClient(); client.mount();
  const enviar = vi.fn().mockResolvedValue("ok");
  const observer = new MutationObserver(client, { mutationFn: enviar });
  const resultado = observer.mutate(undefined);
  expect(observer.getCurrentResult().isPaused).toBe(true);
  expect(enviar).not.toHaveBeenCalled();
  onlineManager.setOnline(true);
  await expect(resultado).resolves.toBe("ok");
  expect(enviar).toHaveBeenCalledTimes(1);
  client.unmount();
});

test("RNF10: mutação offline falha imediatamente e não é repetida ao reconectar", async () => {
  onlineManager.setOnline(false);
  const client = criarQueryClient(); client.mount();
  const enviar = vi.fn().mockRejectedValue(new Error("offline"));
  const observer = new MutationObserver(client, { mutationFn: enviar });
  await expect(observer.mutate(undefined)).rejects.toThrow("offline");
  expect(observer.getCurrentResult().isPaused).toBe(false);
  expect(enviar).toHaveBeenCalledTimes(1);
  onlineManager.setOnline(true);
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(enviar).toHaveBeenCalledTimes(1);
  client.unmount();
});

test("RNF10: sair offline mascara antes da rede e inicia limpeza sem fila", async () => {
  onlineManager.setOnline(false);
  iniciarIdentidade(A);
  document.cookie = `varal_owner=${A}; Path=/`;
  push.mockImplementation(() => new Promise(() => {}));
  render(<Providers><LogoutButton /></Providers>);
  const botao = screen.getByRole("button", { name: "Sair da conta" });
  await waitFor(() => expect(botao.hasAttribute("disabled")).toBe(false));
  fireEvent.click(botao);
  expect(document.documentElement.hasAttribute("data-sessao-oculta")).toBe(true);
  expect(document.cookie).toContain("varal_local_locked=1");
  await waitFor(() => expect(push).toHaveBeenCalledWith(A));
  act(() => onlineManager.setOnline(true));
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(push).toHaveBeenCalledTimes(1);
});
