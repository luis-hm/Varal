import { expect, test } from "vitest";
import { proximoSeguro } from "@/lib/auth/proximo";
import { encurtarLink, expiraEm, iniciais } from "./papeis";

test("ca19/rn31: the invite link is shown shortened with the ellipsis in the middle", () => {
  const token = "9fKq2mXbAbCdEfGhIjKlMnOpQrStUvWxYz0123456R4dT";
  expect(encurtarLink(`https://varal.app/c/${token}`)).toBe("varal.app/c/9fKq2mXb…R4dT");
  expect(encurtarLink(`http://localhost:3000/c/${token}`)).toBe("localhost:3000/c/9fKq2mXb…R4dT");
  expect(encurtarLink(`https://varal.app/c/${token}`)).not.toContain(token);
});

test("expiraEm counts whole days left", () => {
  const agora = Date.parse("2026-11-14T12:00:00Z");
  expect(expiraEm("2026-11-21T12:00:00Z", agora)).toBe("Expira em 7 dias");
  expect(expiraEm("2026-11-15T11:00:00Z", agora)).toBe("Expira em 1 dia");
  expect(expiraEm("2026-11-14T11:00:00Z", agora)).toBe("Expira hoje");
});

test("iniciais from a name or an e-mail", () => {
  expect(iniciais("Família Martins")).toBe("FM");
  expect(iniciais("observador@varal.local")).toBe("OV");
});

test("ca04: proximo accepts only a local path", () => {
  expect(proximoSeguro("/c/abc_DEF-123")).toBe("/c/abc_DEF-123");
  expect(proximoSeguro("/grupos?x=1")).toBe("/grupos?x=1");
  for (const ruim of [null, "", "c/abc", "//evil.com", "/\\evil.com", "https://evil.com", "javascript:alert(1)", "/\t/evil.com", " /c/x"]) {
    expect(proximoSeguro(ruim), String(ruim)).toBeNull();
  }
});
