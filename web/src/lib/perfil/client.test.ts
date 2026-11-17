import { afterEach, expect, test, vi } from "vitest";

const A = "00000000-0000-4000-8000-000000000001";
const B = "00000000-0000-4000-8000-000000000002";
afterEach(() => { vi.unstubAllGlobals(); vi.resetModules(); document.documentElement.removeAttribute("data-sessao-oculta"); });

test("download privado descarta resposta de identidade diferente antes de criar arquivo", async () => {
  const isolamento = await import("@/lib/auth/isolamento");
  isolamento.iniciarIdentidade(B);
  const create = vi.fn();
  vi.stubGlobal("URL", Object.assign(class extends URL {}, { createObjectURL: create }));
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response('{"segredo":"A"}', { status: 200, headers: { "X-Varal-Identidade": A } })));
  const { baixarExportacao } = await import("./client");
  await expect(baixarExportacao("job")).rejects.toBeInstanceOf(isolamento.SessaoAlterada);
  expect(create).not.toHaveBeenCalled();
});
