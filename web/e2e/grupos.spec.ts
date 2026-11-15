// Etapa 03 (espaços e grupos): CA01, CA04, CA05, CA09, CA11, CA12, CA14, CA15, CA17–CA20;
// RF04–RF07, RN01–RN05, RN07, RN21, RN24, RN31, RNF01, RNF02, RNF08, RNF09.
// API and PostgreSQL are real. Every test creates its own users and groups (no `dev` seed).
// Next 16 keeps visited routes mounted but hidden, hence the `visible` filters.
import path from "node:path";
import { randomUUID } from "node:crypto";
import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import {
  ORIGIN,
  TEST_PASSWORD,
  convidar,
  criarGrupo,
  descartarContas,
  entrarNoGrupo,
  logar,
  me,
  mesAtual,
  novaConta,
  outraAba,
  semBadge,
  semRolagemEAlvos44,
  uniqueEmail,
  api,
} from "./fixtures";

const SCREENS = path.join(__dirname, "__screens__");
const INVALIDO = "Este convite não vale mais. Peça um novo a quem convidou.";
const RN04 = /pelo menos um admin/;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(semBadge);
  page.on("dialog", (d) => d.accept()); // window.confirm of remove/leave/archive
});
test.afterEach(descartarContas);

const visivel = (page: Page, nome: string | RegExp) => page.getByRole("button", { name: nome }).filter({ visible: true });
const titulo = (page: Page, nome: string) => page.getByRole("heading", { level: 1, name: nome }).filter({ visible: true });
// Visible text only: Next keeps hidden copies of earlier routes (e.g. the /grupos card).
const texto = (page: Page, t: string) => page.getByText(t, { exact: true }).filter({ visible: true });
// "Convidar pessoa" (header, ≥1024px) or "+ Convidar" (Membros, <1024px): one visible per layout.
const botaoConvidar = (page: Page) => visivel(page, /Convidar/);

test("ca01/ca04/ca05/ca17 rf04/rf05/rf07 rn04/rn24/rn31: admin cria grupo e casa, convida; visitante cria conta com ?proximo e aceita; reuso é 410", async ({ page, context, browser, playwright }) => {
  const admin = await novaConta(playwright);
  await logar(page, admin);
  await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin: ORIGIN });
  const nome = `Família ${randomUUID().slice(0, 6)}`;

  // CA01 / CA17: /grupos lists and creates.
  await page.goto("/grupos");
  await expect(titulo(page, "Grupos")).toBeVisible();
  await expect(page.getByText("Você ainda não participa de nenhum grupo", { exact: false })).toBeVisible();
  await visivel(page, "Criar grupo").click();
  const criar = page.getByRole("dialog", { name: "Criar grupo" });
  await criar.getByLabel("Nome do grupo").fill(nome);
  await criar.getByLabel("Casa 1").fill("Casa da praia");
  await criar.getByRole("button", { name: "Criar grupo" }).click();
  await expect(page).toHaveURL(/\/grupos\/[\da-f-]{36}$/);
  const grupoId = page.url().split("/").pop()!;
  await expect(titulo(page, nome)).toBeVisible();
  await expect(texto(page, "1 membro · 1 casa · você é admin")).toBeVisible();
  // Etapa 04 (Q12): the HouseCard shows the month total and "N contas", no paid bar.
  await expect(texto(page, `0 contas em ${mesAtual()}`)).toHaveCount(1);
  expect((await me(admin.request)).grupos).toEqual([{ id: grupoId, nome, papel: "admin" }]);

  // RF07: + Nova casa.
  await visivel(page, "+ Nova casa").click();
  const casa = page.getByRole("dialog", { name: "Nova casa" });
  await casa.getByLabel("Nome da casa").fill("Apartamento centro");
  await casa.getByRole("button", { name: "Criar", exact: true }).click();
  await expect(casa).toBeHidden();
  await expect(visivel(page, /Apartamento centro/)).toBeVisible();
  await expect(texto(page, `0 contas em ${mesAtual()}`)).toHaveCount(2);

  // CA19: Pagador comes checked; the link is shortened on screen and whole in the copy.
  await botaoConvidar(page).click();
  const convite = page.getByRole("dialog", { name: "Convidar para o grupo" });
  await expect(convite.getByRole("radio", { name: /Pagador/ })).toBeChecked();
  const curto = convite.locator("b").filter({ hasText: /\/c\// });
  await expect(curto).toHaveText(/^localhost:3000\/c\/[\w-]{8}…[\w-]{4}$/);
  await expect(convite.getByText("Expira em 7 dias · vale para 1 pessoa")).toBeVisible();
  await convite.getByRole("button", { name: "Link do convite, copiar" }).click();
  await expect(convite.getByRole("status")).toHaveText("Link copiado.");
  const url = await page.evaluate(() => navigator.clipboard.readText());
  expect(url).toMatch(/^http:\/\/localhost:3000\/c\/[\w-]{43}$/);
  const token = url.split("/c/")[1];
  expect(await curto.textContent()).toBe(`localhost:3000/c/${token.slice(0, 8)}…${token.slice(-4)}`);
  await page.keyboard.press("Escape");
  await expect(convite).toBeHidden();
  // Copied, so closing keeps it: it shows as pending (admin only).
  await expect(page.getByRole("heading", { name: "Convites pendentes" })).toBeVisible();
  await expect(visivel(page, "Revogar convite de pagador")).toHaveCount(1);

  // CA04: visitor without a session opens the link, signs up with ?proximo and comes back to accept.
  const visitante = await outraAba(browser, page);
  try {
    await visitante.goto(`/c/${token}`);
    await expect(visitante.getByText("Convite para", { exact: true })).toBeVisible();
    await expect(titulo(visitante, nome)).toBeVisible();
    await expect(visitante.getByText("Pagador", { exact: true })).toBeVisible();
    await expect(visitante.getByText("Expira em 7 dias · vale para 1 pessoa")).toBeVisible();
    await visitante.getByRole("link", { name: "Criar conta", exact: true }).click();
    await expect(visitante).toHaveURL(`${ORIGIN}/criar-conta?proximo=${encodeURIComponent(`/c/${token}`)}`);
    const email = uniqueEmail();
    await visitante.getByLabel("E-mail", { exact: true }).filter({ visible: true }).fill(email);
    await visitante.getByLabel("Senha", { exact: true }).filter({ visible: true }).fill(TEST_PASSWORD);
    await visitante.getByRole("button", { name: "Criar conta", exact: true }).click();
    await expect(visitante).toHaveURL(`${ORIGIN}/c/${token}`);
    await visivel(visitante, "Aceitar convite").click();
    // RN07 / decision 6: the payer lands on the simple mode.
    await expect(visitante).toHaveURL(`${ORIGIN}/grupos/${grupoId}/simples`);
    await expect(titulo(visitante, nome)).toBeVisible();
    // Etapa 04 (Q5): the payer's own bills, read only.
    await expect(visitante.getByText(`Nenhuma conta para você pagar em ${mesAtual()}.`, { exact: true }).filter({ visible: true })).toBeVisible();
    const pagador = await me(visitante.context().request);
    expect(pagador.email).toBe(email);
    expect(pagador.grupos).toEqual([{ id: grupoId, nome, papel: "pagador" }]);
    // CA11: the payer typing the group URL is taken to /simples.
    await visitante.goto(`/grupos/${grupoId}`);
    await expect(visitante).toHaveURL(`${ORIGIN}/grupos/${grupoId}/simples`);
  } finally {
    await visitante.context().close();
  }

  // CA05 / RN24: the used link asks for a new invite, in the page and in the API (validity is checked
  // before membership, so the admin gets the same 410 as anyone; pytest covers an outsider too).
  await page.goto(`/c/${token}`);
  await expect(page.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toHaveText(INVALIDO);
  await expect(visivel(page, "Aceitar convite")).toHaveCount(0);
  const aceite = await api(admin.request, "POST", `/api/convites/${token}/aceitar/`);
  expect(aceite.status()).toBe(410);
  expect(await aceite.json()).toEqual({ detail: INVALIDO });

  // CA17: the list shows counts and role; the used invite left the pending list.
  await page.goto("/grupos");
  await expect(page.getByRole("link", { name: new RegExp(`${nome}.*2 membros · 2 casas · você é admin`) })).toBeVisible();
  await page.goto(`/grupos/${grupoId}`);
  await expect(texto(page, "2 membros · 2 casas · você é admin")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Convites pendentes" })).toHaveCount(0);
});

test("ca09/ca11/ca15/ca17 rn01/rn05/rn07 rnf01: admin com ações, membro e observador sem ações, pagador em /simples, não participante 404", async ({ page, browser, playwright }, info) => {
  const [admin, membro, observador, pagador, fora] = await Promise.all(Array.from({ length: 5 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin);
  for (const [papel, conta] of [["membro", membro], ["observador", observador], ["pagador", pagador]] as const) {
    await entrarNoGrupo(admin, grupo.id, papel, conta);
  }
  const url = `/grupos/${grupo.id}`;

  await logar(page, admin);
  await page.goto(url);
  await expect(titulo(page, grupo.nome)).toBeVisible();
  await expect(texto(page, "4 membros · 1 casa · você é admin")).toBeVisible();
  await expect(botaoConvidar(page)).toHaveCount(1);
  await expect(visivel(page, "+ Nova casa")).toBeVisible();
  await expect(visivel(page, new RegExp(`${observador.email}.*Observador`))).toBeVisible();
  await expect(visivel(page, /Casa da praia/)).toBeVisible();

  for (const [papel, conta] of [["membro", membro], ["observador", observador]] as const) {
    const aba = await outraAba(browser, page, conta);
    try {
      await aba.goto(url);
      await expect(titulo(aba, grupo.nome)).toBeVisible();
      await expect(texto(aba, `4 membros · 1 casa · você é ${papel}`)).toBeVisible();
      await expect(aba.getByText(admin.email, { exact: true })).toBeVisible();
      await expect(texto(aba, `0 contas em ${mesAtual()}`)).toBeVisible();
      // No management action: only "Sair do grupo" (Q3) besides the shell navigation.
      await expect(botaoConvidar(aba)).toHaveCount(0);
      await expect(visivel(aba, "+ Nova casa")).toHaveCount(0);
      await expect(aba.locator("main [aria-haspopup=dialog]:visible")).toHaveCount(0);
      await expect(aba.getByRole("heading", { name: "Convites pendentes" })).toHaveCount(0);
      expect(await aba.locator("main button:visible").allTextContents()).toEqual(["Sair do grupo"]);
      expect((await api(conta.request, "POST", `/api/grupos/${grupo.id}/convites/`, { papel: "admin" })).status()).toBe(403);
    } finally {
      await aba.context().close();
    }
  }

  const abaPagador = await outraAba(browser, page, pagador);
  try {
    await abaPagador.goto(url);
    await expect(abaPagador).toHaveURL(`${ORIGIN}${url}/simples`);
    await expect(visivel(abaPagador, "Sair do grupo")).toBeVisible();
    expect((await pagador.request.get(`/api/grupos/${grupo.id}/`)).status()).toBe(403);
    // CA17 (desktop): the space selector sends the payer to /simples (Etapa 04: options are buttons
    // that store the `espaco` cookie; a payer group is never stored).
    if (info.project.name === "desktop") {
      await abaPagador.goto("/grupos");
      await abaPagador.getByRole("button", { name: /Trocar de espaço/ }).click();
      await expect(abaPagador.getByRole("link", { name: "Criar grupo" })).toBeVisible();
      await abaPagador.keyboard.press("Escape");
      await expect(abaPagador.getByRole("link", { name: "Criar grupo" })).toBeHidden();
      await abaPagador.getByRole("button", { name: /Trocar de espaço/ }).click();
      await visivel(abaPagador, new RegExp(grupo.nome)).click();
      await expect(abaPagador).toHaveURL(`${ORIGIN}${url}/simples`);
      expect((await abaPagador.context().cookies()).find((c) => c.name === "espaco")).toBeUndefined();
    }
  } finally {
    await abaPagador.context().close();
  }

  // CA15 / RNF01: outsider gets 404 in the API and a page that reveals nothing.
  const abaFora = await outraAba(browser, page, fora);
  try {
    await abaFora.goto(url);
    await expect(abaFora.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toHaveText("Este grupo não existe ou você não participa dele.");
    await expect(abaFora.getByText(grupo.nome).filter({ visible: true })).toHaveCount(0);
    await abaFora.goto(`${url}/simples`);
    await expect(abaFora.getByText(grupo.nome).filter({ visible: true })).toHaveCount(0);
  } finally {
    await abaFora.context().close();
  }
  expect((await fora.request.get(`/api/grupos/${grupo.id}/`)).status()).toBe(404);
  expect((await me(fora.request)).grupos).toEqual([]);

  // CA17 (desktop): the admin's selector lists Pessoal and the group (full page).
  if (info.project.name === "desktop") {
    await page.getByRole("button", { name: /Trocar de espaço/ }).click();
    await expect(visivel(page, /Espaço pessoal/)).toBeVisible();
    await expect(visivel(page, new RegExp(`${grupo.nome}.*Grupo · Admin`))).toBeVisible();
  }
});

test("ca12/ca14 rf06 rn04/rn21: admin muda papel e remove; último admin não se rebaixa nem sai (409)", async ({ page, browser, playwright }) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const url = `/grupos/${grupo.id}`;
  await logar(page, admin);
  await page.goto(url);

  // Change role.
  await visivel(page, new RegExp(membro.email)).click();
  const gestao = page.getByRole("dialog", { name: membro.email });
  await expect(gestao.getByRole("radio", { name: /Membro/ })).toBeChecked();
  await gestao.getByRole("radio", { name: /Observador/ }).check();
  await gestao.getByRole("button", { name: "Salvar papel" }).click();
  await expect(gestao).toBeHidden();
  await expect(visivel(page, new RegExp(`${membro.email}.*Observador`))).toBeVisible();
  expect((await me(membro.request)).grupos[0].papel).toBe("observador");

  // RN04: the only admin cannot demote themselves (sheet) nor leave (page); the API says 409.
  await visivel(page, /\(você\)/).click();
  const eu = page.getByRole("dialog", { name: admin.email });
  await eu.getByRole("radio", { name: /Membro/ }).check();
  await eu.getByRole("button", { name: "Salvar papel" }).click();
  await expect(eu.getByRole("alert")).toHaveText(RN04);
  await eu.getByRole("button", { name: "Remover do grupo" }).click();
  await expect(eu.getByRole("alert")).toHaveText(RN04);
  await page.keyboard.press("Escape");
  await expect(eu).toBeHidden();
  await visivel(page, "Sair do grupo").click();
  await expect(page.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toHaveText(RN04);
  const sair = await api(admin.request, "POST", `/api/grupos/${grupo.id}/sair/`);
  expect(sair.status()).toBe(409);
  expect((await sair.json()).detail).toMatch(RN04);
  expect((await me(admin.request)).grupos[0].papel).toBe("admin");

  // Remove: the person loses access at once (RN21, CA14).
  const removido = await outraAba(browser, page, membro);
  try {
    await removido.goto(url);
    await expect(titulo(removido, grupo.nome)).toBeVisible();
    await page.reload();
    await visivel(page, new RegExp(membro.email)).click();
    await page.getByRole("dialog", { name: membro.email }).getByRole("button", { name: "Remover do grupo" }).click();
    await expect(visivel(page, new RegExp(membro.email))).toHaveCount(0);
    await expect(texto(page, "1 membro · 1 casa · você é admin")).toBeVisible();
    expect((await membro.request.get(`/api/grupos/${grupo.id}/`)).status()).toBe(404);
    expect((await me(membro.request)).grupos).toEqual([]);
    await removido.reload();
    await expect(removido.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toHaveText("Este grupo não existe ou você não participa dele.");
    await removido.goto("/grupos");
    await expect(removido.getByText(grupo.nome).filter({ visible: true })).toHaveCount(0);
  } finally {
    await removido.context().close();
  }
});

test("rnf02 ca04: ?proximo externo (//evil.example, https://evil.example) é descartado", async ({ page, playwright }) => {
  const conta = await novaConta(playwright);
  for (const proximo of ["//evil.example", "https://evil.example/c/x", "/\\evil.example"]) {
    await page.context().clearCookies();
    await page.goto(`/entrar?proximo=${encodeURIComponent(proximo)}`);
    // The link to signup only carries a validated local path.
    await expect(page.getByRole("link", { name: "Criar conta", exact: true })).toHaveAttribute("href", "/criar-conta");
    await page.getByLabel("E-mail", { exact: true }).filter({ visible: true }).fill(conta.email);
    await page.getByLabel("Senha", { exact: true }).filter({ visible: true }).fill(TEST_PASSWORD);
    await page.getByRole("button", { name: "Entrar", exact: true }).click();
    await expect(page).toHaveURL(`${ORIGIN}/`);
  }
  // Control: a local path is kept.
  await page.context().clearCookies();
  await page.goto(`/entrar?proximo=${encodeURIComponent("/grupos")}`);
  await expect(page.getByRole("link", { name: "Criar conta", exact: true })).toHaveAttribute("href", `/criar-conta?proximo=${encodeURIComponent("/grupos")}`);
  await page.getByLabel("E-mail", { exact: true }).filter({ visible: true }).fill(conta.email);
  await page.getByLabel("Senha", { exact: true }).filter({ visible: true }).fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL(`${ORIGIN}/grupos`);
});

test("ca19/ca20 rn31 rnf08/rnf09: folha/modal com foco preso, Esc, setas no RadioCard, shine 2× e fechar sem usar revoga", async ({ page, playwright }, info) => {
  const admin = await novaConta(playwright);
  const grupo = await criarGrupo(admin);
  await logar(page, admin);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto(`/grupos/${grupo.id}`);
  const abrir = botaoConvidar(page);
  await abrir.click();
  const convite = page.getByRole("dialog", { name: "Convidar para o grupo" });
  const link = convite.locator("[data-shine]");
  await expect(link).toHaveAttribute("data-shine", "on");

  const desktop = info.project.name === "desktop";
  const anim = await convite.evaluate((el) => getComputedStyle(el).animationName);
  expect(anim).toMatch(desktop ? /modal-pop$/ : /sheet-up$/);
  const shine = await link.evaluate((el) => {
    const s = getComputedStyle(el);
    return { nome: s.animationName, vezes: s.animationIterationCount, duracao: s.animationDuration, atraso: s.animationDelay };
  });
  expect(shine).toEqual({ nome: expect.stringMatching(/shine/), vezes: "2", duracao: "2.4s", atraso: desktop ? "0.6s" : "0.8s" });
  // Measure once sheet-up/modal-pop (the dialog's own animation) has settled.
  await convite.evaluate((el) => Promise.all(el.getAnimations().map((a) => a.finished)));
  const box = await convite.boundingBox();
  if (desktop) {
    expect(box).toMatchObject({ width: 560, height: 480 });
    expect(Math.round(box!.x + box!.width / 2)).toBe(720);
  } else {
    expect(box!.width).toBe(390);
    expect(Math.round(box!.y + box!.height)).toBe(844); // bottom sheet
  }

  // RadioCard is a native radio group: arrows move the choice and generate a new link.
  const primeiro = await link.locator("b").textContent();
  await convite.getByRole("radio", { name: /Pagador/ }).focus();
  await page.keyboard.press("ArrowDown");
  await expect(convite.getByRole("radio", { name: /Observador/ })).toBeChecked();
  await expect(link.locator("b")).toHaveText(/\/c\//);
  expect(await link.locator("b").textContent()).not.toBe(primeiro);

  // Focus never reaches the page behind (showModal makes it inert). Like every native modal dialog,
  // Chrome lets Tab pass through the browser UI (activeElement = body) before cycling back in.
  const lugares = new Set<string>();
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press("Tab");
    lugares.add(await convite.evaluate((el) => (el.contains(document.activeElement) ? "dialog" : document.activeElement?.tagName ?? "null")));
  }
  expect([...lugares].sort()).toEqual(["BODY", "dialog"]);
  await page.keyboard.press("Escape");
  await expect(convite).toBeHidden();
  await expect(abrir).toBeFocused();
  // Closed without copying or sharing: both generated links were revoked (ADR 0004).
  await expect.poll(async () => (await (await admin.request.get(`/api/grupos/${grupo.id}/convites/`)).json()).length).toBe(0);
  await expect(page.getByRole("heading", { name: "Convites pendentes" })).toHaveCount(0);

  // Reduced motion: no sheet/modal animation, no shine, no page entrance.
  await page.emulateMedia({ reducedMotion: "reduce" });
  await abrir.click();
  await expect(link).toHaveAttribute("data-shine", "on");
  expect(await convite.evaluate((el) => getComputedStyle(el).animationName)).toBe("none");
  expect(await link.evaluate((el) => getComputedStyle(el).animationName)).toBe("none");
  expect(await page.locator("main header").first().evaluate((el) => getComputedStyle(el).animationName)).toBe("none");
  // The × (desktop) or the grab bar (mobile) closes too.
  await convite.getByRole("button", { name: "Fechar" }).filter({ visible: true }).first().click();
  await expect(convite).toBeHidden();
});

test("ca20 rnf08/rnf09: 360px sem rolagem horizontal e alvos ≥ 44px em grupos, convite, gestão e aceite", async ({ page, browser, playwright }, info) => {
  test.skip(info.project.name !== "mobile", "360px is a phone layout; one project is enough");
  const admin = await novaConta(playwright);
  const grupo = await criarGrupo(admin, ["Casa da praia", "Apartamento centro"]);
  const url = await convidar(admin, grupo.id, "observador");
  await logar(page, admin);
  await page.setViewportSize({ width: 360, height: 800 });

  await page.goto("/grupos");
  await expect(page.getByRole("link", { name: new RegExp(grupo.nome) })).toBeVisible();
  await semRolagemEAlvos44(page);
  await visivel(page, "Criar grupo").click();
  await expect(page.getByRole("dialog", { name: "Criar grupo" })).toBeVisible();
  await semRolagemEAlvos44(page);

  await page.goto(`/grupos/${grupo.id}`);
  await expect(page.getByRole("heading", { name: "Convites pendentes" })).toBeVisible();
  await semRolagemEAlvos44(page);
  // Role is text, never colour alone (RNF09).
  await expect(visivel(page, new RegExp(`${admin.email}.*Admin`))).toBeVisible();
  await botaoConvidar(page).click();
  const convite = page.getByRole("dialog", { name: "Convidar para o grupo" });
  await expect(convite.getByRole("button", { name: "Link do convite, copiar" })).toBeEnabled();
  await semRolagemEAlvos44(page);
  await page.keyboard.press("Escape");
  await visivel(page, /\(você\)/).click();
  await expect(page.getByRole("dialog", { name: admin.email })).toBeVisible();
  await semRolagemEAlvos44(page);
  await page.keyboard.press("Escape");
  await visivel(page, /Casa da praia/).click();
  await expect(page.getByRole("dialog", { name: "Editar casa" })).toBeVisible();
  await semRolagemEAlvos44(page);

  const visitante = await outraAba(browser, page);
  try {
    await visitante.setViewportSize({ width: 360, height: 800 });
    await visitante.goto(new URL(url).pathname);
    await expect(titulo(visitante, grupo.nome)).toBeVisible();
    await semRolagemEAlvos44(visitante);
  } finally {
    await visitante.context().close();
  }
});

test("ca18/ca19: screenshots de 10/D04, 11/M05, /c/[token] e /grupos para comparar com o Doop", async ({ page, browser, playwright }, info) => {
  const [admin, ...outros] = await Promise.all(Array.from({ length: 4 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin, ["Casa da praia", "Apartamento centro"]);
  for (const [i, papel] of (["membro", "pagador", "observador"] as const).entries()) await entrarNoGrupo(admin, grupo.id, papel, outros[i]);
  await convidar(admin, grupo.id, "membro"); // one pending invite (CA18 addition)
  const url = await convidar(admin, grupo.id, "pagador");
  await logar(page, admin);
  await page.emulateMedia({ reducedMotion: "reduce" });
  const nome = info.project.name;
  const foto = (arquivo: string, p: Page = page, fullPage = true) =>
    p.screenshot({ path: path.join(SCREENS, `${arquivo}-${nome}.png`), fullPage, caret: "initial" });

  await page.goto("/grupos");
  await expect(page.getByRole("link", { name: new RegExp(grupo.nome) })).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await foto("grupos");

  await page.goto(`/grupos/${grupo.id}`);
  await expect(page.getByRole("heading", { name: "Convites pendentes" })).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await foto("grupo");

  await botaoConvidar(page).click();
  const convite = page.getByRole("dialog", { name: "Convidar para o grupo" });
  await expect(convite.getByRole("button", { name: "Link do convite, copiar" })).toBeEnabled();
  await foto("convite", page, false);
  await page.keyboard.press("Escape");

  const visitante = await outraAba(browser, page);
  try {
    await visitante.emulateMedia({ reducedMotion: "reduce" });
    await visitante.goto(new URL(url).pathname);
    await expect(titulo(visitante, grupo.nome)).toBeVisible();
    await visitante.evaluate(() => document.fonts.ready);
    await foto("convite-aceite", visitante);
  } finally {
    await visitante.context().close();
  }
});
