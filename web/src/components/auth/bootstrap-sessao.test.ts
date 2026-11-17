import { afterEach, expect, test } from "vitest";
import { bootstrap } from "./bootstrap-sessao";

afterEach(() => { document.documentElement.removeAttribute("data-sessao-oculta"); Reflect.deleteProperty(document, "visibilityState"); Reflect.deleteProperty(document, "currentScript"); document.cookie = "varal_owner=; Max-Age=0; Path=/"; });

test("Q11-7: bootstrap mascara uma aba oculta antes da hidratação", () => {
  const id = "00000000-0000-4000-8000-000000000001";
  const privado = document.createElement("div");
  privado.dataset.usuario = id;
  const script = document.createElement("script"); privado.append(script);
  document.body.append(privado);
  document.cookie = `varal_owner=${id}; Path=/`;
  Object.defineProperty(document, "currentScript", { configurable: true, value: script });
  Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
  new Function(bootstrap)();
  expect(privado.hidden).toBe(true);
  expect(document.documentElement.hasAttribute("data-sessao-oculta")).toBe(true);
  privado.hidden = false;
  document.documentElement.removeAttribute("data-sessao-oculta");
  document.dispatchEvent(new Event("visibilitychange"));
  expect(privado.hidden).toBe(true);
  expect(document.documentElement.hasAttribute("data-sessao-oculta")).toBe(true);
  privado.remove();
});
