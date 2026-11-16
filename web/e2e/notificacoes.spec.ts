// Etapa 09: eventos reais de pagamento e remoção; API, worker e banco reais.
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";
import type { components } from "../src/types/api";
import { api, criarGrupo, descartarContas, entrarNoGrupo, hoje, logar, me, novaConta, outraAba, semBadge, semRolagemEAlvos44, type Conta } from "./fixtures";

type Lista = components["schemas"]["ListaNotificacoes"];
const SCREENS = path.join(__dirname, "__screens__");
test.beforeEach(async ({ page }) => { await page.addInitScript(semBadge); });
test.afterEach(descartarContas);

async function lista(pessoa: Conta, query = ""): Promise<Lista> {
  const r = await pessoa.request.get(`/api/notificacoes/${query}`);
  expect(r.status()).toBe(200);
  return r.json();
}
async function gerarPagamento(criador: Conta, pagador: Conta, grupo: string, descricao: string) {
  const uid = (await me(pagador.request)).id;
  const conta = await api(criador.request, "POST", `/api/espacos/${grupo}/lancamentos/`, { descricao, valor_centavos: 12345, vencimento: hoje(), pagador: uid });
  expect(conta.status(), await conta.text()).toBe(201);
  const criada = await conta.json();
  const marca = await api(pagador.request, "POST", `/api/lancamentos/${criada.id}/pagamentos/`, { pago_em: hoje(), valor_centavos_esperado: 12345 });
  expect(marca.status(), await marca.text()).toBe(201);
  return { conta: criada, pagamento: (await marca.json()).pagamento_ativo };
}
async function abrirAvisos(page: Page, projeto: string) {
  await page.getByRole("link", { name: /Avisos/ }).filter({ visible: true }).first().click();
  if (projeto === "desktop") {
    const gaveta = page.getByRole("dialog", { name: "Avisos" });
    await expect(gaveta).toBeVisible();
    return gaveta;
  }
  await expect(page).toHaveURL(/\/avisos(?:\?|$)/);
  return page.locator("main");
}

test("ca03/ca07/ca11: pagamento real, central e revogação após desfazer", async ({ page, browser, playwright }, info) => {
  test.setTimeout(120_000);
  const [admin, membro, estranho] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const { conta, pagamento } = await gerarPagamento(admin, membro, grupo.id, "Pagamento sintético QA09");
  await expect.poll(async () => (await lista(admin)).resultados.some((n) => n.tipo === "pagamento" && n.destino === `/contas/${conta.id}`), { timeout: 60_000 }).toBe(true);
  const aviso = (await lista(admin)).resultados.find((n) => n.tipo === "pagamento" && n.destino === `/contas/${conta.id}`)!;
  expect((await lista(estranho)).resultados).toHaveLength(0);
  await logar(page, admin);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  if (info.project.name === "desktop") {
    await expect(page.locator('main header a[href="/avisos"][aria-label^="Avisos"]:visible')).toHaveAttribute("aria-label", "Avisos, 1 não lidos");
    await expect(page.getByRole("region", { name: "Avisos recentes" }).getByText("Pagamento sintético QA09")).toBeVisible();
  } else {
    await expect(page.getByRole("link", { name: /Avisos, 1 não lidos/ }).filter({ visible: true })).toBeVisible();
  }
  await page.screenshot({ path: path.join(SCREENS, `avisos-inicio-${info.project.name}.png`), animations: "disabled" });
  if (info.project.name === "desktop") await page.goto("/contas?status=pagas");
  const urlOriginal = page.url();
  const central = await abrirAvisos(page, info.project.name);
  if (info.project.name === "desktop") expect(page.url()).toBe(urlOriginal);
  const linha = central.getByRole("button", { name: /Pagamento sintético QA09.*Não lido/ });
  await expect(linha).toBeVisible();
  await page.screenshot({ path: path.join(SCREENS, `avisos-pagamento-${info.project.name}.png`), animations: "disabled" });
  await semRolagemEAlvos44(page);
  if (info.project.name === "desktop") {
    await page.keyboard.press("Escape");
    await expect(central).toBeHidden();
    expect(page.url()).toBe(urlOriginal);
    const linkAvisos = page.getByRole("link", { name: /Avisos/ }).filter({ visible: true }).first();
    await expect(linkAvisos).toBeFocused();
    const popupPromise = page.context().waitForEvent("page", { timeout: 10_000 });
    await linkAvisos.click({ modifiers: ["Control"] });
    const popup = await popupPromise;
    try {
      await expect(popup).toHaveURL(/\/avisos(?:\?|$)/);
      await expect(popup.getByRole("dialog", { name: "Avisos" })).toBeVisible();
    } finally { await popup.close(); }
    await page.goForward();
    await expect(central).toBeVisible();
    expect(page.url()).toBe(urlOriginal);
  }
  await central.getByRole("button", { name: "Marcar todos como lidos" }).filter({ visible: true }).click();
  await expect.poll(async () => (await lista(admin)).nao_lidas).toBe(0);
  expect((await lista(admin)).resultados.find((n) => n.id === aviso.id)?.lido_em).not.toBeNull();
  const desfeita = await api(membro.request, "POST", `/api/lancamentos/${conta.id}/pagamentos/${pagamento.id}/desfazer/`);
  expect(desfeita.status()).toBe(200);
  expect((await lista(admin)).resultados.some((n) => n.id === aviso.id)).toBe(false);
  expect((await api(admin.request, "POST", `/api/notificacoes/${aviso.id}/ler/`)).status()).toBe(404);
  const outra = await outraAba(browser, page, estranho);
  try { await outra.goto("/avisos"); await expect(outra.getByText("Você ainda não tem avisos.")).toBeVisible(); }
  finally { await outra.context().close(); }
});

test("ca04/ca05: remoção produz RN21 para admin e P7 privado sem link", async ({ page, playwright }, info) => {
  test.setTimeout(120_000);
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const uid = (await me(membro.request)).id;
  const aberta = await api(admin.request, "POST", `/api/espacos/${grupo.id}/lancamentos/`, { descricao: "Sem pagador QA09", valor_centavos: 1000, vencimento: hoje(), pagador: uid });
  expect(aberta.status()).toBe(201);
  const restrita = await api(membro.request, "POST", `/api/espacos/${grupo.id}/lancamentos/`, { descricao: "Privada P7 sintética", valor_centavos: 1000, vencimento: hoje(), visibilidade: "restrita" });
  expect(restrita.status()).toBe(201);
  const contaPrivada = await restrita.json();
  const detalhes = await (await admin.request.get(`/api/grupos/${grupo.id}/`)).json();
  const vinculo = detalhes.membros.find((p: { usuario: string }) => p.usuario === uid);
  const remover = await api(admin.request, "DELETE", `/api/grupos/${grupo.id}/membros/${vinculo.id}/`);
  expect(remover.status()).toBe(204);
  await expect.poll(async () => (await lista(membro)).resultados.some((n) => n.tipo === "cancelada_rn32"), { timeout: 60_000 }).toBe(true);
  await expect.poll(async () => (await lista(admin)).resultados.some((n) => n.tipo === "pagador_removido"), { timeout: 60_000 }).toBe(true);
  const p7 = (await lista(membro)).resultados.find((n) => n.tipo === "cancelada_rn32")!;
  expect(p7.texto).toContain("Privada P7 sintética");
  expect(p7.destino).toBeNull();
  expect((await membro.request.get(`/api/lancamentos/${contaPrivada.id}/`)).status()).toBe(404);
  expect((await lista(admin)).resultados.some((n) => n.id === p7.id || n.texto.includes("Privada P7 sintética"))).toBe(false);
  await logar(page, membro);
  await page.goto("/avisos");
  const central = info.project.name === "desktop" ? page.getByRole("dialog", { name: "Avisos" }) : page.locator("main");
  const aviso = central.getByRole("button", { name: /Privada P7 sintética/ });
  await expect(aviso).toBeVisible();
  await page.screenshot({ path: path.join(SCREENS, `avisos-p7-${info.project.name}.png`), animations: "disabled" });
  await aviso.click();
  await expect.poll(async () => (await lista(membro)).nao_lidas).toBe(0);
  expect(new URL(page.url()).pathname).toBe("/avisos");
});

test("q09-9: marcar todas alcança avisos fora da página e conserva timestamps", async ({ page, playwright }, info) => {
  test.setTimeout(180_000);
  const [admin, membro, estranho] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  for (let i = 0; i < 21; i++) await gerarPagamento(admin, membro, grupo.id, `Lote sintético ${i + 1}`);
  await expect.poll(async () => (await lista(admin)).nao_lidas, { timeout: 75_000 }).toBe(21);
  const primeira = await lista(admin);
  expect(primeira.resultados).toHaveLength(20);
  expect(primeira.proximo).toBeTruthy();
  expect((await lista(estranho)).nao_lidas).toBe(0);
  await logar(page, admin);
  await page.goto("/avisos");
  await expect(page.getByRole("button", { name: "Carregar mais" })).toBeVisible();
  await page.getByRole("button", { name: "Marcar todos como lidos" }).filter({ visible: true }).click();
  await expect.poll(async () => (await lista(admin)).nao_lidas).toBe(0);
  const todos = await lista(admin, "?limite=50");
  expect(todos.resultados).toHaveLength(21);
  expect(todos.resultados.every((n) => n.lido_em !== null)).toBe(true);
  const tempos = new Map(todos.resultados.map((n) => [n.id, n.lido_em]));
  expect((await api(admin.request, "POST", "/api/notificacoes/ler-todas/")).status()).toBe(200);
  expect((await lista(admin, "?limite=50")).resultados.every((n) => n.lido_em === tempos.get(n.id))).toBe(true);
  expect((await lista(estranho)).resultados).toHaveLength(0);
  await page.screenshot({ path: path.join(SCREENS, `avisos-lote-${info.project.name}.png`), animations: "disabled" });
});

test("ca10/ca12: preferências e troca de sessão não mostram avisos anteriores", async ({ page, context, playwright }, info) => {
  test.setTimeout(120_000);
  const [criador, membro, outro] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(criador);
  await entrarNoGrupo(criador, grupo.id, "membro", membro);
  await gerarPagamento(criador, membro, grupo.id, "Aviso privado da primeira sessão");
  await expect.poll(async () => (await lista(criador)).nao_lidas, { timeout: 60_000 }).toBe(1);
  await context.grantPermissions([]);
  await logar(page, criador);
  await page.goto("/avisos");
  const central = info.project.name === "desktop" ? page.getByRole("dialog", { name: "Avisos" }) : page.locator("main");
  await expect(central.getByRole("button", { name: /Aviso privado da primeira sessão/ })).toBeVisible();
  await central.getByText("Preferências de notificações", { exact: true }).click();
  const email = central.getByRole("checkbox", { name: "E-mail" });
  const push = central.getByRole("checkbox", { name: "Push" });
  await expect(email).toBeChecked();
  await expect(push).toBeChecked();
  await email.click();
  await expect.poll(async () => (await (await criador.request.get("/api/notificacoes/preferencias/")).json()).email).toBe(false);
  await expect(email).not.toBeChecked();
  const config = await (await criador.request.get("/api/notificacoes/push/configuracao/")).json();
  if (!config.habilitado) await expect(page.getByText("Notificações indisponíveis no momento.")).toBeVisible();
  expect(await page.evaluate(() => Notification.permission)).toBe("denied");
  await page.screenshot({ path: path.join(SCREENS, `avisos-preferencias-${info.project.name}.png`), animations: "disabled" });
  await page.goto("/perfil");
  await page.getByRole("button", { name: "Sair da conta", exact: true }).click();
  await expect(page).toHaveURL(/\/entrar/);
  await logar(page, outro);
  await page.goto("/avisos");
  await expect(page.getByText("Você ainda não tem avisos.")).toBeVisible();
  await expect(page.getByText("Aviso privado da primeira sessão")).toHaveCount(0);
  expect((await lista(outro)).nao_lidas).toBe(0);
});
