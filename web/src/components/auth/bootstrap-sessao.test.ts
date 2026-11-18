import { afterEach, expect, test } from "vitest";
import { bootstrap } from "./bootstrap-sessao";

const id = "00000000-0000-4000-8000-000000000001";
afterEach(() => { document.documentElement.removeAttribute("data-sessao-oculta"); Reflect.deleteProperty(document, "currentScript"); for (const k of ["varal_owner", "varal_local_locked"]) document.cookie = `${k}=; Max-Age=0; Path=/`; });

function rodar() {
  const privado = document.createElement("div");
  privado.dataset.usuario = id;
  privado.hidden = true;
  const script = document.createElement("script"); privado.append(script);
  document.body.append(privado);
  Object.defineProperty(document, "currentScript", { configurable: true, value: script });
  new Function(bootstrap)();
  return privado;
}

test("COR-01: sem marca local revela; pagehide mascara", () => {
  const privado = rodar();
  expect(privado.hidden).toBe(false);
  window.dispatchEvent(new Event("pagehide"));
  expect(privado.hidden).toBe(true);
  privado.remove();
});

test("Q11-7: saída local ou outra conta mantém mascarado", () => {
  document.cookie = "varal_owner=outra; Path=/";
  const privado = rodar();
  expect(privado.hidden).toBe(true);
  expect(document.documentElement.hasAttribute("data-sessao-oculta")).toBe(true);
  privado.remove();
});
