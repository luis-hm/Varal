import { afterEach, expect, test } from "vitest";
import { guardarTentativa, removerTentativa, tentativaPendente } from "./marcador";
afterEach(() => localStorage.clear());
test("T10-E: tentativas concorrentes não sobrescrevem nonce e remoção não apaga outro usuário", () => {
  guardarTentativa("u1", "a", "nonce-a");
  guardarTentativa("u1", "a", "nonce-b");
  guardarTentativa("u2", "a", "nonce-c");
  expect(tentativaPendente("u1", "a")).toBe("nonce-a");
  removerTentativa("u1", "a", "nonce-a");
  expect(tentativaPendente("u1", "a")).toBe("nonce-b");
  expect(tentativaPendente("u2", "a")).toBe("nonce-c");
  expect(Array.from({ length: localStorage.length }, (_, i) => localStorage.getItem(localStorage.key(i)!))).toEqual(["1", "1"]);
});
