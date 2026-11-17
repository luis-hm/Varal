// LAB-only CA11: real identity transitions; no simulated private HTTP responses.
import { writeFile } from "node:fs/promises";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { TEST_PASSWORD, api, descartarContas, hoje, logar, me, novaConta } from "./fixtures";

test.afterEach(descartarContas);

async function entrada(page: Page, email: string) {
  await page.goto("/entrar");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).not.toHaveURL(/\/entrar/);
}

test("rnf10: falha offline não mantém escrita pendente nem reenvia ao reconectar", async ({ page, playwright }) => {
  test.setTimeout(120_000);
  const usuario = await novaConta(playwright);
  const espaco = (await me(usuario.request)).espaco_pessoal.id;
  const descricao = `Offline sem reenvio ${crypto.randomUUID()}`;
  const rota = `/api/espacos/${espaco}/lancamentos/`;
  const requisicoes: string[] = [];
  const falhas: string[] = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === rota) requisicoes.push(request.url());
  });
  page.on("requestfailed", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === rota) falhas.push(request.url());
  });
  await logar(page, usuario);
  await page.goto("/");
  await page.getByRole("button", { name: "Nova conta" }).filter({ visible: true }).click();
  const folha = page.getByRole("dialog", { name: "Nova conta" });
  await folha.getByLabel("Valor", { exact: true }).fill("12,34");
  await folha.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await folha.getByLabel("Descrição", { exact: true }).fill(descricao);
  await page.context().setOffline(true);
  try {
    await folha.getByRole("button", { name: "Salvar conta" }).click();
    await expect(folha.getByRole("alert")).toBeVisible();
    await expect(folha.getByRole("button", { name: "Salvar conta" })).toBeEnabled();
    await expect.poll(() => falhas.length).toBe(1);
    expect(requisicoes).toHaveLength(1);
  } finally {
    await page.context().setOffline(false);
  }
  // Observe a bounded reconnection window without another click; the API client has its own connection.
  await page.waitForTimeout(3_000);
  expect(requisicoes).toHaveLength(1);
  const lista = await api(usuario.request, "GET", rota);
  expect(lista.status()).toBe(200);
  const dados = await lista.json() as { itens: { descricao: string }[] };
  expect(dados.itens.some((item) => item.descricao === descricao)).toBe(false);
});

test("ca11: logout offline em uma aba isola A; B lê e grava sua própria conta", async ({ page, playwright }) => {
  test.setTimeout(120_000);
  const a = await novaConta(playwright);
  const b = await novaConta(playwright);
  const espacoA = (await me(a.request)).espaco_pessoal.id;
  const espacoB = (await me(b.request)).espaco_pessoal.id;
  for (const [usuario, espaco, descricao] of [[a, espacoA, "Conta privada de A"], [b, espacoB, "Conta privada de B"]] as const) {
    const resposta = await api(usuario.request, "POST", `/api/espacos/${espaco}/lancamentos/`, { descricao, valor_centavos: 1200, vencimento: hoje() });
    expect(resposta.status()).toBe(201);
  }
  await logar(page, a);
  await page.goto("/contas");
  await expect(page.getByText("Conta privada de A", { exact: true }).filter({ visible: true }).first()).toBeVisible();
  const antiga = await page.context().newPage();
  await antiga.goto("/contas");
  await expect(antiga.getByText("Conta privada de A", { exact: true }).filter({ visible: true }).first()).toBeVisible();
  await page.bringToFront();
  await page.goto("/perfil");
  await page.context().setOffline(true);
  try {
    await page.getByRole("button", { name: "Sair da conta" }).click();
    await expect.poll(async () => (await page.context().cookies()).find((c) => c.name === "varal_owner")?.value).toBe("bloqueada");
    await antiga.bringToFront();
    await expect(antiga.getByText("Conta privada de A", { exact: true }).filter({ visible: true })).toHaveCount(0);
  } finally { await page.context().setOffline(false); }
  await page.bringToFront();
  await entrada(page, b.email);
  await page.goto("/contas");
  await expect(page.getByText("Conta privada de B", { exact: true }).filter({ visible: true }).first()).toBeVisible();
  await expect(page.getByText("Conta privada de A", { exact: true }).filter({ visible: true })).toHaveCount(0);
  await page.goto("/");
  await page.getByRole("button", { name: "Nova conta" }).filter({ visible: true }).click();
  const folha = page.getByRole("dialog", { name: "Nova conta" });
  await folha.getByLabel("Valor", { exact: true }).fill("12,34");
  await folha.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await folha.getByLabel("Descrição", { exact: true }).fill("Nova conta própria de B");
  await folha.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { name: "Nova conta própria de B" }).filter({ visible: true }).first()).toBeVisible();
  await antiga.bringToFront();
  await expect(antiga.getByText("Conta privada de A", { exact: true }).filter({ visible: true })).toHaveCount(0);
});

test("ca11: BFCache real mantém dados antigos ocultos desde pageshow", async ({ page, playwright }, info) => {
  test.setTimeout(120_000);
  const a = await novaConta(playwright);
  const b = await novaConta(playwright);
  await page.addInitScript(() => {
    window.addEventListener("pageshow", (event) => {
      if (!event.persisted) return;
      const root = document.querySelector<HTMLElement>("[data-sessao-privada]");
      sessionStorage.setItem("qa11.bfcache.first", JSON.stringify({ persisted: event.persisted, visible: !!root?.checkVisibility() }));
    });
  });
  await logar(page, a);
  await page.goto("/perfil");
  await expect(page.getByRole("heading", { name: "Perfil" })).toBeVisible();
  await page.goto("/entrar");
  const outra = await page.context().newPage();
  await entrada(outra, b.email);
  await page.bringToFront();
  await page.goBack({ waitUntil: "domcontentloaded" });
  const prova = await page.evaluate(() => sessionStorage.getItem("qa11.bfcache.first"));
  if (!prova) {
    const detalhes = await page.evaluate(() => {
      const nav = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming & { notRestoredReasons?: unknown };
      return nav?.notRestoredReasons ?? null;
    });
    const dados = JSON.stringify({ persisted: false, detalhes });
    await info.attach("bfcache-not-restored.json", { body: dados, contentType: "application/json" });
    if (process.env.LAB_QA_OUTPUT) await writeFile(path.join(process.env.LAB_QA_OUTPUT, `bfcache-not-restored-${info.project.name}.json`), dados, { mode: 0o600, flag: "wx" });
    test.skip(true, "Chromium não restaurou BFCache; razões anexadas quando disponíveis");
  }
  const medida = JSON.parse(prova!);
  expect(medida).toEqual({ persisted: true, visible: false });
  await expect(page.getByText(a.email, { exact: true }).filter({ visible: true })).toHaveCount(0);
});

test("ca11: BFCache real após revogação de A no servidor sem mudar cookies do navegador", async ({ page, browser, playwright }, info) => {
  test.setTimeout(120_000);
  const a = await novaConta(playwright);
  const dono = (await me(a.request)).id;
  const espaco = (await me(a.request)).espaco_pessoal.id;
  expect((await api(a.request, "POST", `/api/espacos/${espaco}/lancamentos/`, { descricao: "Privada A BFCache", valor_centavos: 1200, vencimento: hoje() })).status()).toBe(201);
  await page.addInitScript(() => {
    window.addEventListener("pageshow", (event) => {
      if (!event.persisted) return;
      const root = document.querySelector<HTMLElement>("[data-sessao-privada]");
      sessionStorage.setItem("qa11.bfcache.revoked", JSON.stringify({ persisted: true, visible: !!root?.checkVisibility() }));
    });
  });
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Page.enable");
  const razoes: string[] = [];
  cdp.on("Page.backForwardCacheNotUsed", (event) => {
    for (const item of event.notRestoredExplanations ?? []) razoes.push(item.reason);
  });
  const navegador = await browser.newBrowserCDPSession();
  let flags: string[] = [];
  try {
    const args = await navegador.send("Browser.getBrowserCommandLine");
    flags = args.arguments.filter((arg) => /back-forward-cache|BackForwardCache/i.test(arg));
  } catch { flags = ["Browser.getBrowserCommandLine indisponível"]; }
  await navegador.detach();
  await logar(page, a);
  await page.goto("/contas");
  await expect(page.getByText("Privada A BFCache", { exact: true }).filter({ visible: true }).first()).toBeVisible();
  const estado = await page.context().storageState();
  const csrf = estado.cookies.find((cookie) => cookie.name === "csrftoken")?.value;
  if (!csrf) throw new Error("CSRF missing before isolated logout");
  const cliente = await playwright.request.newContext({ baseURL: process.env.LAB_BASE_URL, storageState: estado });
  try {
    await page.goto("/entrar");
    const saida = await cliente.delete("/api/auth/browser/v1/auth/session", { headers: { Origin: process.env.LAB_BASE_URL!, "X-CSRFToken": csrf, "X-Varal-Identidade-Esperada": dono } });
    expect(saida.status()).toBe(401); // allauth's successful logout is unauthenticated state
    expect((await cliente.get("/api/me/")).status()).toBe(401);
    await page.goBack({ waitUntil: "domcontentloaded" });
    const prova = await page.evaluate(() => sessionStorage.getItem("qa11.bfcache.revoked"));
    const dados = { persisted: !!prova, medida: prova ? JSON.parse(prova) : null, razoes, flags };
    if (process.env.LAB_QA_OUTPUT) await writeFile(path.join(process.env.LAB_QA_OUTPUT, `bfcache-revoked-${info.project.name}.json`), JSON.stringify(dados), { mode: 0o600, flag: "wx" });
    if (!prova) test.skip(true, "Chromium não restaurou BFCache; evento CDP e flags registrados");
    expect(dados.medida).toEqual({ persisted: true, visible: false });
    await expect(page.getByText("Privada A BFCache", { exact: true }).filter({ visible: true })).toHaveCount(0);
  } finally { await cliente.dispose(); await cdp.detach(); }
});
