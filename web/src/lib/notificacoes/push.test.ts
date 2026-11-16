import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { ativarPush, desativarPush, estadoPush } from "./push";
import { inscreverPush, revogarInstalacao } from "./client";

vi.mock("./client", () => ({ inscreverPush: vi.fn(), revogarInstalacao: vi.fn() }));
const unsubscribe = vi.fn().mockResolvedValue(true);
const subscription = { endpoint: "https://push.example.test/a", unsubscribe, toJSON: () => ({ endpoint: "https://push.example.test/a", keys: { p256dh: "public", auth: "secret" } }) };
const pushManager = { getSubscription: vi.fn().mockResolvedValue(subscription), subscribe: vi.fn() };
const registration = { pushManager };
const requestPermission = vi.fn().mockResolvedValue("granted");
beforeEach(() => {
  localStorage.clear(); vi.clearAllMocks();
  vi.stubGlobal("isSecureContext", true);
  vi.stubGlobal("PushManager", function PushManager() {});
  vi.stubGlobal("Notification", { requestPermission });
  vi.stubGlobal("navigator", { serviceWorker: { register: vi.fn().mockResolvedValue(registration), getRegistration: vi.fn().mockResolvedValue(registration) } });
  vi.mocked(inscreverPush).mockResolvedValue({ ativo: true, id: "server-id" });
  vi.mocked(revogarInstalacao).mockResolvedValue(null);
});
afterEach(() => { vi.unstubAllGlobals(); });

test("ativação é explícita e desligar revoga o mesmo ciclo e inscrição local", async () => {
  expect(requestPermission).not.toHaveBeenCalled();
  await ativarPush("usuario-1", { habilitado: true, chave_publica: "AQ" });
  const payload = vi.mocked(inscreverPush).mock.calls[0][0];
  expect(requestPermission).toHaveBeenCalledOnce();
  expect(estadoPush("usuario-1")).toBe(true);
  expect(estadoPush("usuario-2")).toBe(false);
  await desativarPush();
  expect(revogarInstalacao).toHaveBeenCalledWith(payload.instalacao);
  expect(unsubscribe).toHaveBeenCalled();
  expect(estadoPush("usuario-1")).toBe(false);
});

test("permissão negada não cadastra inscrição", async () => {
  requestPermission.mockResolvedValueOnce("denied");
  await expect(ativarPush("usuario-1", { habilitado: true, chave_publica: "AQ" })).rejects.toThrow("não concedida");
  expect(inscreverPush).not.toHaveBeenCalled();
  await desativarPush();
});

test("logout durante ativação revoga o UUID e impede reativação tardia", async () => {
  let liberar!: (value: string) => void;
  requestPermission.mockReturnValueOnce(new Promise((resolve) => { liberar = resolve; }));
  const pendente = ativarPush("usuario-1", { habilitado: true, chave_publica: "AQ" });
  await desativarPush();
  liberar("granted");
  await expect(pendente).rejects.toThrow("interrompida");
  expect(revogarInstalacao).toHaveBeenCalledOnce();
  expect(inscreverPush).not.toHaveBeenCalled();
  expect(estadoPush("usuario-1")).toBe(false);
});

test("resposta tardia do registro após logout não restaura inscrição", async () => {
  let liberar!: (value: { ativo: boolean; id: string }) => void;
  vi.mocked(inscreverPush).mockReturnValueOnce(new Promise((resolve) => { liberar = resolve; }));
  const pendente = ativarPush("usuario-1", { habilitado: true, chave_publica: "AQ" });
  await vi.waitFor(() => expect(inscreverPush).toHaveBeenCalledOnce());
  const id = vi.mocked(inscreverPush).mock.calls[0][0].instalacao;
  await desativarPush();
  liberar({ ativo: true, id: "server-id" });
  await expect(pendente).rejects.toThrow("interrompida");
  expect(revogarInstalacao).toHaveBeenCalledWith(id);
  expect(estadoPush("usuario-1")).toBe(false);
});
