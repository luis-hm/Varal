// Etapa 11 (RN30): exportar, excluir e sessão; usuários e dados sintéticos. Roda na suíte normal desde a ADR 0018.
import { test, expect, type Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { ORIGIN, TEST_PASSWORD, api, criarGrupo, descartarContas, entrarNoGrupo, estadoAutenticado, hoje, logar, me, novaConta, semRolagemEAlvos44 } from "./fixtures";

test.afterEach(descartarContas);
// The `next dev` badge is not part of the app and is smaller than 44px.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => addEventListener("DOMContentLoaded", () => {
    const style = document.createElement("style");
    style.textContent = "nextjs-portal { display: none !important; }";
    document.head.append(style);
  }));
});

async function acaoComReauth(page: Page, label: string, endpoint: string) {
  const enviar = async () => {
    const resposta = page.waitForResponse((r) => new URL(r.url()).pathname === endpoint && r.request().method() === "POST");
    await page.getByRole("button", { name: label }).click();
    return resposta;
  };
  let resposta = await enviar();
  if (resposta.status() === 401) {
    await expect(page.getByRole("heading", { name: "Confirme sua identidade" })).toBeVisible();
    await page.getByLabel("Senha", { exact: true }).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Confirmar identidade" }).click();
    await expect(page.getByText("Identidade confirmada. Continue a ação solicitada.")).toBeVisible();
    resposta = await enviar();
  }
  return resposta;
}

test("ca06: credencial errada mostra erro e não cria hint de identidade", async ({ page, playwright }) => {
  const conta = await novaConta(playwright);
  await page.goto("/entrar");
  await page.getByLabel("E-mail").fill(conta.email);
  await page.getByLabel("Senha").fill("senha-sintetica-incorreta");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("alert").first()).toBeVisible();
  expect((await page.context().cookies()).some((cookie) => cookie.name === "varal_owner")).toBe(false);
  await expect(page).toHaveURL(/\/entrar/);
});

test("ca11: sessão legada sem hint não revela SSR e exige entrada real", async ({ browser, playwright }) => {
  const conta = await novaConta(playwright);
  const contexto = await browser.newContext({ storageState: await conta.request.storageState(), baseURL: ORIGIN });
  try {
    const page = await contexto.newPage();
    const resposta = await contexto.request.get("/perfil", { maxRedirects: 0 });
    expect([200, 307, 308]).toContain(resposta.status());
    expect(await resposta.text()).not.toContain(conta.email);
    await page.goto("/perfil");
    await expect(page).toHaveURL(/\/entrar/);
    await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
    expect((await contexto.cookies()).some((cookie) => cookie.name === "varal_owner")).toBe(false);
  } finally { await contexto.close(); }
});

test("ca05: exclusão de último admin retorna conflito sem destruir conta ou grupo", async ({ page, playwright }) => {
  const conta = await novaConta(playwright);
  const grupo = await criarGrupo(conta);
  await logar(page, conta);
  await page.goto("/perfil");
  await expect(page.getByRole("heading", { name: "Perfil" })).toBeVisible();
  expect((await acaoComReauth(page, "Preparar exclusão", "/api/me/exclusao/intencoes/")).status()).toBe(201);
  await page.getByRole("checkbox", { name: "Quero excluir minha conta" }).check();
  const resposta = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/me/" && r.request().method() === "DELETE");
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  expect((await resposta).status()).toBe(409);
  await expect(page.getByRole("alert").filter({ hasText: "Não foi possível concluir agora" })).toBeVisible();
  expect((await me(conta.request)).grupos.some((g) => g.id === grupo.id)).toBe(true);
  expect((await conta.request.get(`/api/grupos/${grupo.id}/`)).status()).toBe(200);
});

test("ca06/ca07: exclusão elegível preserva conta do grupo e revoga sessão", async ({ page, playwright }) => {
  const admin = await novaConta(playwright);
  const dono = await novaConta(playwright);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", dono);
  const criado = await api(dono.request, "POST", `/api/espacos/${grupo.id}/lancamentos/`, {
    descricao: "Conta sintética preservada", valor_centavos: 2400, vencimento: hoje(),
    pagador: (await me(admin.request)).id,
  });
  expect(criado.status()).toBe(201);
  const conta = await criado.json();
  await logar(page, dono);
  await page.goto("/perfil");
  expect((await acaoComReauth(page, "Preparar exclusão", "/api/me/exclusao/intencoes/")).status()).toBe(201);
  await page.getByRole("checkbox", { name: "Quero excluir minha conta" }).check();
  const resposta = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/me/" && r.request().method() === "DELETE");
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  expect((await resposta).status()).toBe(204);
  await expect(page).toHaveURL(/\/entrar/);
  expect((await dono.request.get("/api/me/")).status()).toBe(401);
  const detalhe = await admin.request.get(`/api/lancamentos/${conta.id}/`);
  expect(detalhe.status()).toBe(200);
  const preservada = await detalhe.json();
  expect(preservada.descricao).toBe("Conta sintética preservada");
  expect(preservada.criador.nome).toBe("Ex-membro");
  expect(JSON.stringify(preservada)).not.toContain(dono.email);
});

test("ca05/rn32: restrita órfã impede exclusão sem revelar conta ao admin", async ({ page, playwright }) => {
  const admin = await novaConta(playwright);
  const dono = await novaConta(playwright);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", dono);
  const uid = (await me(dono.request)).id;
  const nome = "Restrita sintética protegida";
  const criado = await api(dono.request, "POST", `/api/espacos/${grupo.id}/lancamentos/`, {
    descricao: nome, valor_centavos: 2400, vencimento: hoje(), pagador: uid,
    visibilidade: "restrita", acesso: [],
  });
  expect(criado.status()).toBe(201);
  const conta = await criado.json();
  expect((await admin.request.get(`/api/lancamentos/${conta.id}/`)).status()).toBe(404);
  await logar(page, dono);
  await page.goto("/perfil");
  expect((await acaoComReauth(page, "Preparar exclusão", "/api/me/exclusao/intencoes/")).status()).toBe(201);
  await page.getByRole("checkbox", { name: "Quero excluir minha conta" }).check();
  const resposta = page.waitForResponse((r) => new URL(r.url()).pathname === "/api/me/" && r.request().method() === "DELETE");
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  const conflito = await resposta;
  expect(conflito.status()).toBe(409);
  expect(await conflito.text()).not.toContain(nome);
  expect(await conflito.text()).not.toContain(conta.id);
  expect((await dono.request.get("/api/me/")).status()).toBe(200);
  expect((await dono.request.get(`/api/lancamentos/${conta.id}/`)).status()).toBe(200);
  expect((await admin.request.get(`/api/lancamentos/${conta.id}/`)).status()).toBe(404);
});

test("ca10/ca11/ca12: perfil responsivo e service worker sem cache privado", async ({ page, playwright }, info) => {
  const conta = await novaConta(playwright);
  await logar(page, conta);
  await page.emulateMedia({ reducedMotion: "reduce" });
  // Inject before navigation through Playwright, without changing the application's CSP.
  await page.addInitScript({ path: require.resolve("axe-core/axe.min.js") });
  await page.goto("/perfil");
  await expect(page.getByRole("heading", { name: "Perfil" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Seus dados" }).locator("..").getByText(conta.email, { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Exportar meus dados" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Excluir minha conta" })).toBeVisible();
  await semRolagemEAlvos44(page);
  const preparar = page.getByRole("button", { name: "Preparar exportação" });
  for (let i = 0; i < 50 && !(await preparar.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
  await expect(preparar).toBeFocused();
  const foco = await preparar.evaluate((el) => {
    const css = getComputedStyle(el);
    return { visivel: el.matches(":focus-visible"), outline: css.outlineStyle, sombra: css.boxShadow };
  });
  expect(foco.visivel && (foco.outline !== "none" || foco.sombra !== "none")).toBe(true);
  const screenshots = process.env.LAB_QA_OUTPUT ?? "e2e/__screens__";
  await mkdir(screenshots, { recursive: true });
  await page.screenshot({ path: path.join(screenshots, `perfil11-${info.project.name}.png`), animations: "disabled", fullPage: true });
  // axe-core is already present in the locked dependency tree; no extra network install.
  const diagnostico = await page.evaluate(async (prototipar) => {
    type Helper = { data: (value: unknown) => void };
    type Evaluate = (this: Helper, node: Element, options: unknown, vnode: unknown) => boolean | undefined;
    const axe = (window as unknown as { axe: {
      run: (context?: Element, options?: unknown) => Promise<{ violations: { id: string; impact: string | null; nodes: { target: string[]; failureSummary?: string; any: { id: string; data: unknown }[] }[] }[] }>;
      _audit: { checks: Record<string, { evaluate: Evaluate }> };
      commons: { text: { visibleVirtual: (node: unknown, sr: boolean, noRecursing: boolean, options: unknown) => string; accessibleText: (node: Element) => string } };
    } }).axe;
    const check = axe._audit.checks["label-content-name-mismatch"];
    const original = check.evaluate;
    check.evaluate = function (node, options, vnode) {
      const resultado = original.call(this, node, options, vnode);
      if (resultado === false) this.data({ visible: axe.commons.text.visibleVirtual(vnode, false, false, { ...(options as object), ignoreIconLigature: true }), accessible: axe.commons.text.accessibleText(node), innerText: (node as HTMLElement).innerText, textContent: node.textContent });
      return resultado;
    };
    try {
      const inicial = (await axe.run()).violations;
      const violacoes = inicial.map(({ id, impact, nodes }) => ({ id, impact, nodes: nodes.map(({ target, failureSummary, any }) => ({ target, failureSummary, checks: any.map(({ id, data }) => ({ id, data })) })) }));
      let prototipo: unknown = null;
      const alvo = inicial.find((v) => v.id === "label-content-name-mismatch")?.nodes[0]?.target;
      const botao = prototipar && alvo?.length === 1 ? document.querySelector(alvo[0]) : null;
      const avatar = botao?.children[0], texto = botao?.children[1], nome = texto?.children[0], detalhe = texto?.children[1];
      if (botao && avatar && texto && nome && detalhe) {
        const antes = Array.from(botao.children).map((el) => el.getBoundingClientRect().toJSON());
        const espaco1 = document.createTextNode(" "), espaco2 = document.createTextNode(" ");
        botao.insertBefore(espaco1, texto); texto.insertBefore(espaco2, detalhe);
        try {
          const depois = Array.from(botao.children).map((el) => el.getBoundingClientRect().toJSON());
          const resultado = await axe.run(botao, { runOnly: { type: "rule", values: ["label-content-name-mismatch"] } });
          prototipo = { antes, depois, violacoes: resultado.violations.map((v) => v.id) };
        } finally { espaco1.remove(); espaco2.remove(); }
      }
      return { violacoes, prototipo };
    } finally { check.evaluate = original; }
  }, process.env.LAB_AXE_DIAG === "1");
  if (diagnostico.prototipo) await info.attach("axe-prototipo.json", { body: JSON.stringify(diagnostico.prototipo), contentType: "application/json" });
  expect(diagnostico.violacoes).toEqual([]);
  const manifesto = await page.locator('link[rel="manifest"]').getAttribute("href");
  expect(manifesto).toBeTruthy();
  const manifest = await (await page.request.get(manifesto!)).json();
  expect(manifest.start_url).toBeTruthy();
  expect(manifest.icons.length).toBeGreaterThan(0);
  await page.evaluate(() => navigator.serviceWorker.ready);
  const estado = await page.evaluate(async () => ({
    registrations: (await navigator.serviceWorker.getRegistrations()).length,
    urls: (await Promise.all((await caches.keys()).map(async (key) => (await (await caches.open(key)).keys()).map((request) => {
      const url = new URL(request.url);
      return url.origin === location.origin ? url.pathname + url.search : request.url;
    })))).flat(),
  }));
  expect(estado.registrations).toBe(1);
  expect(estado.urls.sort()).toEqual(["/icons/varal-192-v1.png", "/icons/varal-512-v1.png", "/offline-v1.html"].sort());
  // A registered SW and manifest are not evidence of browser installation or push delivery.
  expect((await estadoAutenticado(conta.request)).cookies.some((c) => c.name === "varal_owner")).toBe(true);
});

test("ca01/ca02: exportação própria pronta baixa JSON sem credenciais; alheio recebe 404", async ({ page, playwright }) => {
  const dono = await novaConta(playwright);
  const outro = await novaConta(playwright);
  await logar(page, dono);
  await page.goto("/perfil");
  const resposta = await acaoComReauth(page, "Preparar exportação", "/api/me/exportacoes/");
  expect(resposta.status()).toBe(202);
  const job = await resposta.json();
  expect(job.id).toBeTruthy();
  expect((await outro.request.get(`/api/me/exportacoes/${job.id}/`)).status()).toBe(404);
  await expect(page.getByText(/Exportação pronta/)).toBeVisible({ timeout: 60_000 });
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Baixar exportação" }).click();
  const download = await downloadPromise;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream) chunks.push(Buffer.from(chunk));
  const documento = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  expect(documento.schema_version).toBe(1);
  expect(documento.perfil.email).toBe(dono.email);
  for (const campo of ["password", "sessionid", "csrftoken", "access_token", "refresh_token"]) {
    expect(JSON.stringify(documento)).not.toContain(campo);
  }
});

test("ca11/t11-i: resposta de login A tardia após B não revela A", async ({ browser, playwright }) => {
  test.setTimeout(120_000);
  const a = await novaConta(playwright);
  const b = await novaConta(playwright);
  const contexto = await browser.newContext({ baseURL: ORIGIN });
  let liberar!: () => void;
  let capturado!: () => void;
  let entregue!: () => void;
  const pendente = new Promise<void>((resolve) => { liberar = resolve; });
  const chegou = new Promise<void>((resolve) => { capturado = resolve; });
  const entregueA = new Promise<void>((resolve) => { entregue = resolve; });
  let clienteA: Awaited<ReturnType<typeof playwright.request.newContext>> | undefined;
  try {
    const [abaA, abaB] = await Promise.all([contexto.newPage(), contexto.newPage()]);
    await Promise.all([abaA.goto("/entrar"), abaB.goto("/entrar")]);
    await expect(abaA.getByRole("button", { name: "Entrar", exact: true })).toBeEnabled();
    clienteA = await playwright.request.newContext({ baseURL: ORIGIN, storageState: await contexto.storageState() });
    await contexto.route("**/api/auth/browser/v1/auth/login", async (route) => {
      const body = route.request().postDataJSON() as { email?: string } | null;
      if (route.request().method() !== "POST" || body?.email !== a.email) return route.continue();
      // route.fetch shares the browser jar. Use the anonymous pre-A snapshot in a separate jar.
      const headers = { ...route.request().headers() };
      delete headers.cookie;
      delete headers.host;
      delete headers["content-length"];
      const resposta = await clienteA!.post(route.request().url(), { headers, data: route.request().postDataBuffer() ?? undefined });
      expect(resposta.status()).toBe(200);
      expect(resposta.headersArray().some((h) => h.name.toLowerCase() === "set-cookie" && h.value.includes("sessionid="))).toBe(true);
      capturado();
      await pendente;
      await route.fulfill({ response: resposta });
      entregue();
    });
    await abaA.getByLabel("E-mail").fill(a.email);
    await abaA.getByLabel("Senha").fill(TEST_PASSWORD);
    await abaA.getByRole("button", { name: "Entrar", exact: true }).click();
    await chegou;
    await abaB.getByLabel("E-mail").fill(b.email);
    await abaB.getByLabel("Senha").fill(TEST_PASSWORD);
    await abaB.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(abaB).not.toHaveURL(/\/entrar/);
    await abaB.goto("/perfil");
    await expect(abaB.getByRole("heading", { name: "Seus dados" }).locator("..").getByText(b.email, { exact: true })).toBeVisible();
    const identidadeA = await clienteA.get("/api/me/");
    expect(identidadeA.status()).toBe(200);
    expect((await identidadeA.json()).id).toBe((await me(a.request)).id);
    expect((await (await abaB.request.get("/api/me/")).json()).id).toBe((await me(b.request)).id);
    liberar();
    await entregueA;
    // A late cookie may force reauthentication; neither SSR nor a restored page may show A to B.
    const html = await contexto.request.get("/perfil", { maxRedirects: 0 });
    expect([200, 307, 308]).toContain(html.status());
    expect(await html.text()).not.toContain(a.email);
    await abaB.reload();
    await expect(abaB.getByText(a.email, { exact: true })).toHaveCount(0);
    await expect(abaA.getByText(b.email, { exact: true })).toHaveCount(0);
  } finally {
    liberar();
    await contexto.close();
    await clienteA?.dispose();
  }
});
