// CA06: native allauth reauthentication over real HTTPS and captured local SMTP.
// The initial session is a backend-owned synthetic force_login fixture, not Google proof.
import { randomUUID } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import { expect, test } from "@playwright/test";

async function privateFile(file: string) {
  const info = await stat(file);
  if (!info.isFile() || (info.mode & 0o077) !== 0) throw new Error("Private fixture must be a 0600 file");
  return readFile(file, "utf8");
}

test("ca06: solicitar código não reautentica; confirmar código nativo autoriza exportação", async ({ page }) => {
  test.setTimeout(120_000);
  const meta = JSON.parse(await privateFile("/qa/ca06-meta.json")) as { email: string; owner: string };
  if (!/^ca06-code-[a-f0-9]{32}@example\.invalid$/.test(meta.email) || !/^[a-f0-9-]{36}$/i.test(meta.owner)) throw new Error("Invalid synthetic fixture metadata");
  const origin = process.env.LAB_BASE_URL;
  if (!origin || !/^https:\/\/varal\.local:\d+$/.test(origin)) throw new Error("Lab HTTPS origin required");
  const config = await page.request.get("/api/auth/browser/v1/config");
  expect(config.status()).toBe(200);
  const identidade = { "X-Varal-Identidade-Esperada": meta.owner };
  const sessao = await page.request.get("/api/auth/browser/v1/auth/session", { headers: identidade });
  expect(sessao.status()).toBe(200);
  expect((await sessao.json()).data.user.has_usable_password).toBe(false);
  const emails = await page.request.get("/api/auth/browser/v1/account/email", { headers: identidade });
  expect(emails.status()).toBe(200);
  const enderecos = (await emails.json()).data as { email: string; verified: boolean }[];
  expect(enderecos.some((e) => e.email === meta.email && e.verified)).toBe(true);
  async function tentarExportar() {
    const csrf = (await page.context().cookies()).find((c) => c.name === "csrftoken")?.value;
    if (!csrf) throw new Error("CSRF cookie missing");
    return page.request.post("/api/me/exportacoes/", {
      headers: { Origin: origin!, "X-CSRFToken": csrf, "X-Varal-Identidade-Esperada": meta.owner },
      data: { chave: randomUUID() },
    });
  }
  const antes = await tentarExportar();
  expect(antes.status()).toBe(401);
  expect((await antes.json()).code).toBe("reauth_required");
  await page.goto("/perfil");
  await page.getByRole("button", { name: "Preparar exportação" }).click();
  await expect(page.getByRole("heading", { name: "Confirme sua identidade" })).toBeVisible();
  await expect(page.getByText("Enviaremos um código para seu e-mail verificado.")).toBeVisible();
  const pedido = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/auth/browser/v1/auth/reauthenticate/code/request" && r.request().method() === "POST");
  await page.getByRole("button", { name: "Enviar código" }).click();
  expect((await pedido).status()).toBe(200);
  await expect(page.getByLabel("Código de confirmação")).toBeVisible();
  const semConfirmar = await tentarExportar();
  expect(semConfirmar.status()).toBe(401);
  expect((await semConfirmar.json()).code).toBe("reauth_required");
  // A host watcher supplies only the real SMTP code for this unique recipient, as a 0600 file.
  let codigo = "";
  await expect.poll(async () => {
    try { codigo = (await privateFile("/qa/ca06-code.txt")).trim(); return true; }
    catch { return false; }
  }, { timeout: 60_000, intervals: [500] }).toBe(true);
  if (!/^[BCDFGHJKLMNPQRSTVWXZ]{4}-[BCDFGHJKLMNPQRSTVWXZ]{4}$/.test(codigo)) throw new Error("Unexpected code format");
  await page.getByLabel("Código de confirmação").fill(codigo);
  const confirmado = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/auth/browser/v1/auth/reauthenticate/code/confirm" && r.request().method() === "POST");
  await page.getByRole("button", { name: "Confirmar identidade" }).click();
  expect((await confirmado).status()).toBe(200);
  await expect(page.getByText("Identidade confirmada. Continue a ação solicitada.")).toBeVisible();
  const criado = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/me/exportacoes/" && r.request().method() === "POST");
  await page.getByRole("button", { name: "Preparar exportação" }).click();
  expect((await criado).status()).toBe(202);
});
