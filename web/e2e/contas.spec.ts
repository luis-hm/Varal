// Etapa 04 (contas, núcleo): CA01, CA07–CA09, CA11–CA17, CA19–CA23, CA27–CA32; RF10–RF13, RN05–RN07,
// RN11–RN13, RN21, RN22, RN32 (ADR 0006/0007), D2, Q5, Q9, Q12, Q14, Q23, RNF08/RNF09/RNF11.
// API and PostgreSQL are real; every test creates its own users, groups and bills (no `dev` seed).
// Runs in both projects: mobile 390×844 and desktop 1440×900. Next 16 keeps visited routes mounted but
// hidden, hence the `visible` filters.
import path from "node:path";
import type { APIRequestContext, Locator, Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import {
  ORIGIN,
  api,
  criarGrupo,
  descartarContas,
  entrarNoGrupo,
  hoje,
  logar,
  me,
  mesAtual,
  novaConta,
  outraAba,
  semBadge,
  semRolagemEAlvos44,
  type Conta,
} from "./fixtures";

const SCREENS = path.join(__dirname, "__screens__");
const AVISO = "Quem paga também vê esta conta";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(semBadge);
  page.on("dialog", (d) => d.accept()); // window.confirm of cancel/leave/remove
});
test.afterEach(descartarContas);

const visivel = (page: Page | Locator, nome: string | RegExp) => page.getByRole("button", { name: nome }).filter({ visible: true });
const link = (page: Page | Locator, nome: string | RegExp) => page.getByRole("link", { name: nome }).filter({ visible: true });
const texto = (page: Page | Locator, t: string | RegExp) => page.getByText(t, typeof t === "string" ? { exact: true } : undefined).filter({ visible: true });
const desktop = (info: { project: { name: string } }) => info.project.name === "desktop";

type Nova = { id: string; descricao: string };
async function criarConta(dono: Conta, espaco: string, dados: Record<string, unknown> = {}): Promise<Nova> {
  const r = await api(dono.request, "POST", `/api/espacos/${espaco}/lancamentos/`, { descricao: "Luz", valor_centavos: 1000, vencimento: hoje(), ...dados });
  expect(r.status(), await r.text()).toBe(201);
  return r.json();
}

async function cancelar(dono: Conta, conta: Nova) {
  expect((await api(dono.request, "POST", `/api/lancamentos/${conta.id}/cancelar/`)).status()).toBe(200);
}

const json = async (request: APIRequestContext, url: string) => {
  const r = await request.get(url);
  expect(r.status(), url).toBe(200);
  return r.json();
};

/** Every aggregate a user can read about a space: lists, counts, filter options and the summary. */
const visao = (request: APIRequestContext, espaco: string) =>
  Promise.all(
    [
      `/api/espacos/${espaco}/lancamentos/`,
      `/api/espacos/${espaco}/lancamentos/?status=a_pagar`,
      `/api/espacos/${espaco}/lancamentos/?status=canceladas`,
      `/api/espacos/${espaco}/lancamentos/?pagador=nenhum`,
      `/api/espacos/${espaco}/resumo/`,
    ].map((u) => json(request, u)),
  );

async function casaDe(admin: Conta, grupo: string, nome = "Casa da praia"): Promise<string> {
  return (await json(admin.request, `/api/grupos/${grupo}/`)).casas.find((c: { nome: string }) => c.nome === nome).id;
}

/** Current space (decision 2): the `espaco` cookie the selector writes. */
const usarEspaco = (page: Page, id: string) => page.context().addCookies([{ name: "espaco", value: id, url: ORIGIN }]);

/** FAB "+" (< 1024px) or SideNav "Nova conta" (≥ 1024px): one visible per layout. */
const botaoNovaConta = (page: Page) => visivel(page, "Nova conta");
const hero = (page: Page) => page.getByRole("region", { name: `Total de ${mesAtual()}` }).filter({ visible: true });
const atencao = (page: Page) => page.getByRole("region", { name: "Precisa de atenção" }).filter({ visible: true });

test("ca01/ca16/ca17/ca31 rf10/rf13 rn11 q12/q23: nova conta pelo FAB ou pelo SideNav com o espaço atual; aparece no Início e em Contas", async ({ page, playwright }) => {
  const [admin, observador] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "observador", observador);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  const mes = mesAtual();

  await page.goto("/");
  await expect(hero(page)).toContainText("R$ 0,00");
  await expect(hero(page)).toContainText("0 contas");
  // Q07-7: no empty progress bar when there are no bills.
  await expect(hero(page).locator("[role=progressbar], [style*='--progress']")).toHaveCount(0);

  // CA31: the form opens with the current space marked; "Eu" pre-selected; observers cannot pay.
  const abrir = botaoNovaConta(page);
  await abrir.click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  await expect(form.getByRole("button", { name: grupo.nome })).toHaveAttribute("aria-pressed", "true");
  await expect(form.getByRole("button", { name: "Pessoal" })).toHaveAttribute("aria-pressed", "false");
  const quemPaga = form.getByRole("group", { name: "Quem paga" });
  await expect(quemPaga.getByRole("button", { name: "Eu" })).toHaveAttribute("aria-pressed", "true");
  await expect(quemPaga.getByRole("button", { name: observador.email })).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(form).toBeHidden();
  await expect(abrir).toBeFocused();

  await abrir.click();
  // RN11 on the client: no amount, no save.
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(form.getByText("Informe um valor maior que zero, como 287,43.")).toBeVisible();
  await form.getByLabel("Valor", { exact: true }).fill("287,43");
  await form.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await form.getByLabel("Descrição", { exact: true }).fill("Energia · Casa 3");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(form).toBeHidden();
  await expect(page).toHaveURL(new RegExp(`/contas/[\\da-f-]{36}\\?mes=${hoje().slice(0, 7)}$`));
  await expect(page.getByRole("heading", { level: 1, name: "Energia · Casa 3" })).toBeVisible();
  await expect(texto(page, /Você criou a conta/)).toBeVisible();

  // CA01: pendente, in the chosen space, with creator and one "criada" line.
  const id = new URL(page.url()).pathname.split("/").pop()!;
  const conta = await json(admin.request, `/api/lancamentos/${id}/`);
  expect(conta).toMatchObject({ status: "pendente", valor_centavos: 28743, vencimento: hoje(), espaco: { id: grupo.id }, criador: { sou_eu: true }, pagador: { sou_eu: true } });
  expect(conta.historico.map((h: { acao: string }) => h.acao)).toEqual(["criada"]);

  // CA16/CA17: hero with the month label; "Precisa de atenção" lists it; Contas shows it with the month total.
  await page.goto("/");
  await expect(hero(page)).toContainText("R$ 287,43");
  await expect(hero(page)).toContainText("1 conta");
  const progresso = hero(page).getByRole("progressbar", { name: `Contas pagas em ${mes}` });
  await expect(progresso).toHaveAttribute("aria-valuenow", "0");
  await expect(progresso).toHaveAttribute("aria-valuemax", "1");
  await expect(link(atencao(page), /Energia · Casa 3.*Vence em breve.*R\$ 287,43/)).toBeVisible();
  await page.goto("/contas");
  await expect(texto(page, new RegExp(`^Total de ${mes}: R\\$ 287,43`))).toBeVisible();
  await expect(link(page, /Energia · Casa 3/)).toBeVisible();
  await expect(visivel(page, /^Todas 1$/)).toHaveAttribute("aria-pressed", "true");
});

test("ca07/ca08/ca09/ca28 rn06/rn07: restrita com aviso de quem paga; admin não escolhido não a vê nem por total, contagem, Por casa ou HouseCard (404); pagador fora dos escolhidos vê", async ({ page, browser, playwright }, info) => {
  // Four users and three browser contexts exercise the full privacy flow, including cold routes.
  test.setTimeout(75_000);
  const [admin, membro, observador, pagador] = await Promise.all(Array.from({ length: 4 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin);
  for (const [papel, conta] of [["membro", membro], ["observador", observador], ["pagador", pagador]] as const) await entrarNoGrupo(admin, grupo.id, papel, conta);
  const casa = await casaDe(admin, grupo.id);
  await criarConta(admin, grupo.id, { descricao: "Água", valor_centavos: 5000, subgrupo: casa });
  const antes = await visao(admin.request, grupo.id);
  const mes = mesAtual();

  // CA28: the notice shows up before saving, only for "Só algumas pessoas" with someone else paying.
  await logar(page, membro);
  await usarEspaco(page, grupo.id);
  await page.goto("/contas");
  await botaoNovaConta(page).click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  const aviso = form.getByText(AVISO);
  const quemPaga = form.getByRole("group", { name: "Quem paga" });
  const quemVe = form.getByRole("group", { name: "Quem vê" });
  await expect(quemPaga.getByRole("button", { name: pagador.email })).toBeVisible();
  await quemPaga.getByRole("button", { name: pagador.email }).click();
  await expect(aviso).toHaveCount(0); // whole group sees it anyway
  await quemVe.getByRole("button", { name: "Só algumas pessoas" }).click();
  await expect(aviso).toBeVisible();
  await expect(form.locator("[aria-live=polite]")).toHaveText(AVISO);
  await quemPaga.getByRole("button", { name: "Eu" }).click();
  await expect(aviso).toHaveCount(0);
  await quemPaga.getByRole("button", { name: "Ninguém" }).click();
  await expect(aviso).toHaveCount(0);
  await quemPaga.getByRole("button", { name: pagador.email }).click();
  await expect(aviso).toBeVisible();
  await quemVe.getByRole("button", { name: "Todo o grupo" }).click();
  await expect(aviso).toHaveCount(0);
  await quemVe.getByRole("button", { name: "Só algumas pessoas" }).click();
  await expect(aviso).toBeVisible();
  // Chosen: the observer only (the admin is left out on purpose). Payer-by-role is never an option.
  const escolhidos = form.getByRole("group", { name: "Quem mais vê" });
  await expect(escolhidos.getByRole("button", { name: pagador.email })).toHaveCount(0);
  await escolhidos.getByRole("button", { name: observador.email }).click();
  await form.getByRole("group", { name: "Casa" }).getByRole("button", { name: "Casa da praia" }).click();
  await form.getByLabel("Valor", { exact: true }).fill("150,00");
  await form.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await form.getByLabel("Descrição", { exact: true }).fill("Presente surpresa");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(form).toBeHidden();
  await expect(page.getByRole("heading", { level: 1, name: "Presente surpresa" })).toBeVisible();
  // The effective audience includes the creator and payer as well as the chosen observer (Q04-38).
  const publico = page.getByRole("region", { name: "Informações" }).filter({ visible: true });
  await expect(publico).toContainText(observador.email);
  await expect(publico).toContainText(pagador.email);
  await expect(publico).toContainText(membro.email);
  await expect(publico).not.toContainText(admin.email);
  const id = new URL(page.url()).pathname.split("/").pop()!;

  // CA07: the admin who was not chosen sees exactly what they saw before, in the API and on screen.
  expect(await visao(admin.request, grupo.id)).toEqual(antes);
  expect((await admin.request.get(`/api/lancamentos/${id}/`)).status()).toBe(404);
  expect((await api(admin.request, "PATCH", `/api/lancamentos/${id}/`, { descricao: "X" })).status()).toBe(404);
  expect((await api(admin.request, "POST", `/api/lancamentos/${id}/cancelar/`)).status()).toBe(404);
  const abaAdmin = await outraAba(browser, page, admin);
  try {
    await usarEspaco(abaAdmin, grupo.id);
    await abaAdmin.goto("/");
    await expect(hero(abaAdmin)).toContainText("R$ 50,00");
    await expect(hero(abaAdmin)).toContainText("1 conta");
    await expect(link(atencao(abaAdmin), /Água/)).toBeVisible();
    await expect(texto(abaAdmin, /Presente surpresa/)).toHaveCount(0);
    if (desktop(info)) {
      const porCasa = abaAdmin.getByRole("region", { name: "Por casa" });
      await expect(porCasa).toContainText("R$ 50,00");
      await expect(porCasa).toContainText(`0 de 1 pagas em ${mes}`);
    }
    await abaAdmin.goto("/contas");
    await expect(visivel(abaAdmin, /^Todas 1$/)).toBeVisible();
    await expect(link(abaAdmin, /Água/)).toBeVisible();
    await expect(texto(abaAdmin, /Presente surpresa/)).toHaveCount(0);
    await abaAdmin.goto(`/contas/${id}`);
    await expect(abaAdmin.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toContainText("Conta não encontrada");
    await expect(texto(abaAdmin, /Presente surpresa/)).toHaveCount(0);
    await abaAdmin.goto(`/grupos/${grupo.id}`);
    await expect(visivel(abaAdmin, /Casa da praia/)).toContainText("R$ 50,00");
    await expect(visivel(abaAdmin, /Casa da praia/)).toContainText(`0 de 1 pagas em ${mes}`);
  } finally {
    await abaAdmin.context().close();
  }

  // CA08/CA09: the payer is outside the chosen people and still sees it (RN06), only it, read only (Q5).
  expect((await observador.request.get(`/api/lancamentos/${id}/`)).status()).toBe(200);
  const lista = await json(pagador.request, `/api/espacos/${grupo.id}/lancamentos/`);
  expect(lista.itens.map((c: Nova) => c.descricao)).toEqual(["Presente surpresa"]);
  expect(lista.total_centavos).toBe(15000);
  const abaPagador = await outraAba(browser, page, pagador);
  try {
    await abaPagador.goto(`/grupos/${grupo.id}/simples`);
    await expect(link(abaPagador, /Presente surpresa/)).toBeVisible();
    await expect(texto(abaPagador, /Água/)).toHaveCount(0);
    await link(abaPagador, /Presente surpresa/).click();
    await expect(abaPagador.getByRole("heading", { level: 1, name: "Presente surpresa" })).toBeVisible();
    await expect(visivel(abaPagador, "Editar conta")).toHaveCount(0);
  } finally {
    await abaPagador.context().close();
  }
});

test("ca12/ca13/ca14 rn22 d2: editar com histórico; cancelar tira do Início e da lista e mostra em Canceladas, riscada", async ({ page, playwright }) => {
  const dono = await novaConta(playwright);
  const pessoal = (await me(dono.request)).espaco_pessoal.id;
  const conta = await criarConta(dono, pessoal, { descricao: "Internet", valor_centavos: 9990 });
  await logar(page, dono);
  await page.goto(`/contas/${conta.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Internet" })).toBeVisible();

  await visivel(page, "Editar conta").click();
  const form = page.getByRole("dialog", { name: "Editar conta" });
  await expect(form.getByLabel("Valor", { exact: true })).toHaveValue("99,90");
  await form.getByLabel("Valor", { exact: true }).fill("120,00");
  await form.getByLabel("Descrição", { exact: true }).fill("Internet fibra");
  await form.getByRole("button", { name: "Salvar", exact: true }).click();
  await expect(form).toBeHidden();
  await expect(page.getByRole("heading", { level: 1, name: "Internet fibra" })).toBeVisible();
  // CA12: author, date and before → after of the changed fields only.
  const linha = page.getByRole("listitem").filter({ hasText: "Você editou" }).filter({ visible: true });
  await expect(linha).toContainText("descrição: Internet → Internet fibra");
  await expect(linha).toContainText("valor: R$ 99,90 → R$ 120,00");
  await expect(linha).not.toContainText("vencimento");
  const editada = (await json(dono.request, `/api/lancamentos/${conta.id}/`)).historico.at(-1);
  expect(editada).toMatchObject({ acao: "editada", sou_eu: true, dados: { descricao: ["Internet", "Internet fibra"], valor_centavos: [9990, 12000] } });
  expect(Object.keys(editada.dados).sort()).toEqual(["descricao", "valor_centavos"]);

  // CA13: cancel from the edit form (window.confirm accepted); stays in the database, no Editar any more.
  await visivel(page, "Editar conta").click();
  await form.getByRole("button", { name: "Cancelar conta" }).click();
  await expect(form).toBeHidden();
  const detalhe = page.getByRole("article", { name: "Detalhe da conta" }).filter({ visible: true });
  await expect(detalhe.getByText("Cancelada", { exact: true })).toBeVisible();
  await expect(texto(page, /Você cancelou a conta/)).toBeVisible();
  await expect(visivel(page, "Editar conta")).toHaveCount(0);
  expect((await api(dono.request, "POST", `/api/lancamentos/${conta.id}/cancelar/`)).status()).toBe(409);

  // CA14 / D2: out of Início, totals, "Todas"; only under "Canceladas", struck through and faded.
  await page.goto("/");
  await expect(hero(page)).toContainText("R$ 0,00");
  await expect(texto(page, /Internet fibra/)).toHaveCount(0);
  await page.goto("/contas");
  await expect(texto(page, `Nenhuma conta em ${mesAtual()}.`)).toBeVisible();
  await expect(visivel(page, /^Todas 0$/)).toBeVisible();
  await visivel(page, /^Canceladas 1$/).click();
  await expect(page).toHaveURL(/\/contas\?status=canceladas$/);
  const card = link(page, /Internet fibra/);
  await expect(card).toHaveAttribute("data-cancelled");
  await expect(card).toContainText("Cancelada");
  expect(await card.evaluate((el) => Number(getComputedStyle(el).opacity))).toBeLessThan(1);
  expect(await card.getByText("R$ 120,00").evaluate((el) => getComputedStyle(el).textDecorationLine)).toBe("line-through");
});

test("ca15 rf13 q14: filtros de status, casa e quem paga na URL; Voltar restaura; folha Filtros no mobile", async ({ page, playwright }, info) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const casa = await casaDe(admin, grupo.id);
  const membroId = (await me(membro.request)).id;
  await criarConta(admin, grupo.id, { descricao: "Luz da casa", subgrupo: casa, pagador: membroId });
  await criarConta(admin, grupo.id, { descricao: "Gás solto", pagador: null });
  await cancelar(admin, await criarConta(admin, grupo.id, { descricao: "Água cancelada" }));
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.goto("/contas");

  await expect(visivel(page, /^Todas 2$/)).toHaveAttribute("aria-pressed", "true");
  await expect(visivel(page, /^A pagar 2$/)).toBeVisible();
  await expect(visivel(page, /^Vencidas 0$/)).toBeVisible();
  await expect(visivel(page, /^Pagas 0$/)).toBeVisible();
  await expect(visivel(page, /^Canceladas 1$/)).toBeVisible();
  await visivel(page, /^A pagar/).click();
  await expect(page).toHaveURL(/\?status=a_pagar$/);
  await expect(visivel(page, /^A pagar/)).toHaveAttribute("aria-pressed", "true");

  // Casa and Quem paga: chip menus on desktop, the "Filtros" sheet on mobile (Q14).
  async function filtrar(grupoNome: "Casa" | "Quem paga", opcao: string) {
    if (desktop(info)) {
      await visivel(page, new RegExp(`^${grupoNome} `)).click();
      await page.getByRole("group", { name: grupoNome }).getByRole("button", { name: opcao }).click();
      return;
    }
    await visivel(page, "Filtros").click();
    const folha = page.getByRole("dialog", { name: "Filtros" });
    await folha.getByRole("group", { name: grupoNome }).getByRole("button", { name: opcao }).click();
    await expect(folha.getByRole("group", { name: grupoNome }).getByRole("button", { name: opcao })).toHaveAttribute("aria-pressed", "true");
    await folha.getByRole("button", { name: "Ver contas" }).click();
    await expect(folha).toBeHidden();
  }

  await filtrar("Casa", "Casa da praia");
  await expect(page).toHaveURL(new RegExp(`\\?status=a_pagar&casa=${casa}$`));
  await expect(link(page, /Luz da casa/)).toBeVisible();
  await expect(texto(page, /Gás solto/)).toHaveCount(0);

  await filtrar("Quem paga", "Sem pagador");
  await expect(page).toHaveURL(new RegExp(`casa=${casa}&pagador=nenhum$`));
  await expect(texto(page, "Nenhuma conta com esses filtros.")).toBeVisible();

  // Back restores each step.
  await page.goBack();
  await expect(page).toHaveURL(new RegExp(`\\?status=a_pagar&casa=${casa}$`));
  await expect(link(page, /Luz da casa/)).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\?status=a_pagar$/);
  await expect(link(page, /Luz da casa/)).toBeVisible();
  await expect(link(page, /Gás solto/)).toBeVisible();

  // A shared URL opens with its filters.
  await page.goto(`/contas?pagador=${membroId}`);
  await expect(link(page, /Luz da casa/)).toBeVisible();
  await expect(texto(page, /Gás solto/)).toHaveCount(0);
  await page.goto("/contas?status=canceladas");
  await expect(link(page, /Água cancelada/)).toBeVisible();
});

test("ca30: ≥ 1024px lista + painel slide-in com o card marcado; < 1024px a mesma rota mostra só o 07", async ({ page, playwright }, info) => {
  const dono = await novaConta(playwright);
  const conta = await criarConta(dono, (await me(dono.request)).espaco_pessoal.id, { descricao: "Condomínio" });
  await logar(page, dono);
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/contas");
  const lista = page.getByRole("heading", { level: 1, name: "Contas" });
  if (desktop(info)) await expect(texto(page, "Escolha uma conta para ver os detalhes.")).toBeVisible();
  await link(page, /Condomínio/).click();
  await expect(page).toHaveURL(`${ORIGIN}/contas/${conta.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Condomínio" })).toBeVisible();

  if (desktop(info)) {
    await expect(lista).toBeVisible();
    await expect(link(page, /Condomínio/)).toHaveAttribute("aria-current", "true");
    const painel = page.getByRole("complementary", { name: "Conta aberta" });
    const anim = await painel.evaluate((el) => {
      const s = getComputedStyle(el);
      return { nome: s.animationName, duracao: s.animationDuration };
    });
    expect(anim).toEqual({ nome: expect.stringMatching(/slide-in$/), duracao: "0.45s" });
    await page.getByRole("link", { name: "Fechar detalhe" }).click();
    await expect(page).toHaveURL(`${ORIGIN}/contas`);
    await expect(texto(page, "Escolha uma conta para ver os detalhes.")).toBeVisible();
  } else {
    await expect(lista).toBeHidden();
    await expect(page.getByRole("heading", { level: 1, name: "Conta", exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Voltar" }).filter({ visible: true }).click();
    await expect(page).toHaveURL(`${ORIGIN}/contas`);
    await expect(lista).toBeVisible();
  }
});

test("ca19/ca22/ca23 rn32 adr0007: saída barrada mostra a folha com as contas; escolher quem vê ou cancelar e sair", async ({ page, playwright }) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const presente = await criarConta(membro, grupo.id, { descricao: "Presente", visibilidade: "restrita", acesso: [], pagador: null });
  const viagem = await criarConta(membro, grupo.id, { descricao: "Viagem", visibilidade: "restrita", acesso: [], pagador: null });
  await logar(page, membro);
  await page.goto(`/grupos/${grupo.id}`);

  await visivel(page, "Sair do grupo").click();
  const folha = page.getByRole("dialog", { name: `Antes de sair de ${grupo.nome}` });
  await expect(folha).toContainText("escolha outra pessoa");
  await expect(folha.getByRole("link", { name: "Presente" })).toHaveAttribute("href", `/contas/${presente.id}`);
  await expect(folha.getByRole("link", { name: "Viagem" })).toBeVisible();
  const sair = folha.getByRole("button", { name: "Sair", exact: true });
  await expect(sair).toBeDisabled();

  await folha.getByRole("group", { name: "O que fazer com Presente" }).getByRole("button", { name: "Escolher quem vê" }).click();
  await expect(sair).toBeDisabled(); // nobody chosen yet
  // The admin has no name: a current member without a name shows by e-mail (decision 23).
  await folha.getByRole("group", { name: "Quem vê Presente" }).getByRole("button", { name: admin.email }).click();
  await expect(sair).toBeDisabled();
  await folha.getByRole("group", { name: "O que fazer com Viagem" }).getByRole("button", { name: "Cancelar conta" }).click();
  await expect(sair).toBeEnabled();
  await sair.click();
  await expect(page).toHaveURL(`${ORIGIN}/grupos`);
  expect((await me(membro.request)).grupos).toEqual([]);

  // Same transaction: the chosen admin now sees "Presente", with the reason in its history.
  const visto = await json(admin.request, `/api/lancamentos/${presente.id}/`);
  expect(visto.historico.at(-1)).toMatchObject({ acao: "editada", dados: { motivo: "saida_rn32" } });
  expect((await admin.request.get(`/api/lancamentos/${viagem.id}/`)).status()).toBe(404);
});

test("ca20/ca21/ca22 rn32/rn06: remoção pelo admin nunca é barrada e não mostra nenhuma mensagem nova", async ({ page, playwright }) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  await criarConta(admin, grupo.id, { descricao: "Água" });
  const segredo = await criarConta(membro, grupo.id, { descricao: "Segredo", visibilidade: "restrita", acesso: [], pagador: null });
  const antes = await visao(admin.request, grupo.id);
  await logar(page, admin);
  await page.goto(`/grupos/${grupo.id}`);

  await visivel(page, new RegExp(membro.email)).click();
  const gestao = page.getByRole("dialog", { name: membro.email });
  await gestao.getByRole("button", { name: "Remover do grupo" }).click();
  await expect(gestao).toBeHidden();
  await expect(visivel(page, new RegExp(membro.email))).toHaveCount(0);
  await expect(page.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toHaveCount(0);
  await expect(page.getByRole("dialog").filter({ visible: true })).toHaveCount(0);
  await expect(texto(page, /Segredo|cancelad/i)).toHaveCount(0);
  expect(await visao(admin.request, grupo.id)).toEqual(antes);
  expect((await admin.request.get(`/api/lancamentos/${segredo.id}/`)).status()).toBe(404);
});

test("ca11 rn13 q10: Configurações só para admin, janela de 1 a 7 dias muda o Precisa de atenção", async ({ page, browser, playwright }) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  await criarConta(admin, grupo.id, { descricao: "Escola", vencimento: hoje(5) });
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.goto("/");
  await expect(texto(page, "Nenhuma conta vencida ou vencendo nos próximos 3 dias.")).toBeVisible();

  await page.goto(`/grupos/${grupo.id}`);
  await visivel(page, "Configurações").click();
  const config = page.getByRole("dialog", { name: "Configurações" });
  const campo = config.getByLabel("Avisar quantos dias antes do vencimento");
  await expect(campo).toHaveValue("3");
  await campo.fill("8");
  await expect(config.getByText("Escolha de 1 a 7 dias.")).toBeVisible();
  await expect(config.getByRole("button", { name: "Salvar", exact: true })).toBeDisabled();
  await campo.fill("0");
  await expect(config.getByRole("button", { name: "Salvar", exact: true })).toBeDisabled();
  await campo.fill("5");
  await config.getByRole("button", { name: "Salvar", exact: true }).click();
  await expect(config).toBeHidden();
  expect((await json(admin.request, `/api/grupos/${grupo.id}/`)).janela_alerta_dias).toBe(5);

  await page.goto("/");
  await expect(link(atencao(page), /Escola.*Vence em breve/)).toBeVisible();

  // Other roles: no button and 403 in the API; the personal space keeps 3.
  const aba = await outraAba(browser, page, membro);
  try {
    await aba.goto(`/grupos/${grupo.id}`);
    await expect(aba.getByRole("heading", { level: 1, name: grupo.nome })).toBeVisible();
    await expect(visivel(aba, "Configurações")).toHaveCount(0);
  } finally {
    await aba.context().close();
  }
  expect((await api(membro.request, "PATCH", `/api/grupos/${grupo.id}/`, { janela_alerta_dias: 2 })).status()).toBe(403);
  expect((await json(admin.request, `/api/espacos/${(await me(admin.request)).espaco_pessoal.id}/resumo/`)).janela_alerta_dias).toBe(3);
});

test("ca27 q4/q5 rn07: seletor grava o cookie e troca Início e Contas; persiste ao recarregar; cookie alheio cai no pessoal; grupo de pagador abre /simples com as contas dele", async ({ page, playwright }, info) => {
  const [eu, outro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const meu = await me(eu.request);
  await criarConta(eu, meu.espaco_pessoal.id, { descricao: "Conta pessoal" });
  const familia = await criarGrupo(eu);
  await criarConta(eu, familia.id, { descricao: "Conta da família" });
  const pago = await criarGrupo(outro);
  await entrarNoGrupo(outro, pago.id, "pagador", eu);
  await criarConta(outro, pago.id, { descricao: "Minha parte", pagador: meu.id });
  await criarConta(outro, pago.id, { descricao: "Parte do outro" });
  const alheio = await criarGrupo(outro);
  await logar(page, eu);

  const trocar = async (nome: RegExp) => {
    await visivel(page, /Trocar de espaço/).click();
    await visivel(page, nome).click();
  };
  const cookie = async () => (await page.context().cookies()).find((c) => c.name === "espaco")?.value;

  await page.goto("/");
  await expect(link(atencao(page), /Conta pessoal/)).toBeVisible();
  await trocar(new RegExp(`${familia.nome}.*Grupo · Admin`));
  await expect(link(atencao(page), /Conta da família/)).toBeVisible();
  await expect(texto(page, /Conta pessoal/)).toHaveCount(0);
  expect(await cookie()).toBe(familia.id);
  await page.reload();
  await expect(link(atencao(page), /Conta da família/)).toBeVisible();
  await page.goto("/contas");
  await expect(link(page, /Conta da família/)).toBeVisible();
  await expect(texto(page, /Conta pessoal/)).toHaveCount(0);

  if (desktop(info)) {
    // From Contas the SideNav selector stays in Contas (decision 2).
    await trocar(/Espaço pessoal/);
    await expect(page).toHaveURL(`${ORIGIN}/contas`);
    await expect(link(page, /Conta pessoal/)).toBeVisible();
    expect(await cookie()).toBe(meu.espaco_pessoal.id);
  }

  // A cookie naming someone else's group (or anything unknown) falls back to the personal space.
  await usarEspaco(page, alheio.id);
  await page.goto("/");
  await expect(link(atencao(page), /Conta pessoal/)).toBeVisible();
  expect((await eu.request.get(`/api/espacos/${alheio.id}/resumo/`)).status()).toBe(404);

  // A payer group opens the simple mode with the payer's bills only, and is not stored.
  await trocar(new RegExp(`${pago.nome}.*Grupo · Pagador`));
  await expect(page).toHaveURL(`${ORIGIN}/grupos/${pago.id}/simples`);
  await expect(link(page, /Minha parte/)).toBeVisible();
  await expect(texto(page, /Parte do outro/)).toHaveCount(0);
  expect(await cookie()).toBe(alheio.id);
});

/** One group with bills in every displayed state: vencida (this and last month), vence, pendente, cancelada. */
async function grupoComContas(playwright: Parameters<typeof novaConta>[0]) {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin, ["Casa 3", "Apartamento centro"]);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const [casa3, apto] = await Promise.all([casaDe(admin, grupo.id, "Casa 3"), casaDe(admin, grupo.id, "Apartamento centro")]);
  const membroId = (await me(membro.request)).id;
  const adminId = (await me(admin.request)).id;
  const primeiro = `${hoje().slice(0, 7)}-01`;
  const anterior = new Date(Date.UTC(Number(primeiro.slice(0, 4)), Number(primeiro.slice(5, 7)) - 1, 0)).toISOString().slice(0, 10);
  const energia = await criarConta(admin, grupo.id, { descricao: "Energia · Casa 3", valor_centavos: 28743, vencimento: hoje(1), subgrupo: casa3, pagador: membroId });
  await criarConta(admin, grupo.id, { descricao: "Água · Cagece", valor_centavos: 8435, vencimento: hoje(), subgrupo: apto, pagador: adminId });
  await criarConta(admin, grupo.id, { descricao: "Condomínio", valor_centavos: 62000, vencimento: anterior, subgrupo: casa3, pagador: membroId });
  await criarConta(admin, grupo.id, { descricao: "Internet", valor_centavos: 11990, vencimento: hoje() === primeiro ? hoje() : primeiro });
  await criarConta(admin, grupo.id, { descricao: "Seguro", valor_centavos: 21040, vencimento: hoje(20), pagador: null });
  await cancelar(admin, await criarConta(admin, grupo.id, { descricao: "Gás", valor_centavos: 9500 }));
  return { admin, grupo, energia };
}

test("ca32 rnf08: 360px sem rolagem horizontal e alvos ≥ 44px em Início, Contas, Detalhe, formulário e Filtros", async ({ page, playwright }, info) => {
  test.skip(info.project.name !== "mobile", "360px is a phone layout; one project is enough");
  const { admin, grupo, energia } = await grupoComContas(playwright);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.setViewportSize({ width: 360, height: 800 });

  await page.goto("/");
  await expect(link(atencao(page), /Energia/)).toBeVisible();
  await semRolagemEAlvos44(page);
  await page.goto("/contas");
  await expect(link(page, /Energia/)).toBeVisible();
  await semRolagemEAlvos44(page);
  await visivel(page, "Filtros").click();
  await expect(page.getByRole("dialog", { name: "Filtros" })).toBeVisible();
  await semRolagemEAlvos44(page);
  await page.keyboard.press("Escape");
  await botaoNovaConta(page).click();
  await expect(page.getByRole("dialog", { name: "Nova conta" }).getByRole("group", { name: "Quem paga" })).toBeVisible();
  await page.getByRole("dialog", { name: "Nova conta" }).getByRole("button", { name: "Só algumas pessoas" }).click();
  await semRolagemEAlvos44(page);
  await page.keyboard.press("Escape");
  await page.goto(`/contas/${energia.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Energia · Casa 3" })).toBeVisible();
  await semRolagemEAlvos44(page);
  await visivel(page, "Editar conta").click();
  await expect(page.getByRole("dialog", { name: "Editar conta" })).toBeVisible();
  await semRolagemEAlvos44(page);
});

test("ca32 rnf09/rnf11: status com ícone e texto, valores em R$ e datas de Fortaleza; movimento reduzido desliga swing, count-up, rise, slide-in e badge-pulse", async ({ page, playwright }, info) => {
  const { admin, grupo, energia } = await grupoComContas(playwright);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  const nomes = () => page.evaluate(() => document.getAnimations().map((a) => (a as CSSAnimation).animationName ?? ""));

  // Control: without the preference the motion is there (the check can fail).
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto("/");
  await expect(link(atencao(page), /Condomínio/)).toBeVisible();
  await expect.poll(async () => (await nomes()).join(" ")).toMatch(/swing/);
  expect((await nomes()).join(" ")).toMatch(/badge-pulse/);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(link(atencao(page), /Condomínio/)).toBeVisible();
  // count-up off: the visible number is final at once.
  const total = (await json(admin.request, `/api/espacos/${grupo.id}/resumo/`)).total_centavos;
  const reais = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(total / 100).replace(/\s/g, " ");
  await expect(hero(page).locator("[aria-hidden=true]").first()).toHaveText(reais, { timeout: 1_000 });
  expect(await nomes()).toEqual([]);
  // RNF09: every status reads as text next to its icon; RNF11: last month's overdue bill shows its date.
  const vencida = link(atencao(page), /Condomínio/);
  await expect(vencida).toContainText("Vencida");
  await expect(vencida.locator("[data-status=vencida] svg")).toHaveCount(1);
  await expect(vencida).toContainText(/Venceu \d{2}\/\d{2}/);
  await expect(vencida).toContainText("R$ 620,00");

  await page.goto(`/contas/${energia.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Energia · Casa 3" })).toBeVisible();
  if (desktop(info)) await expect(page.getByRole("complementary", { name: "Conta aberta" })).toBeVisible();
  expect(await nomes()).toEqual([]);
});

test("ca29: screenshots de 02/D02, 03/D03 (com e sem painel), 07 e formulário (05/M01, parte manual) para comparar com o Doop", async ({ page, playwright }, info) => {
  const { admin, grupo, energia } = await grupoComContas(playwright);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.emulateMedia({ reducedMotion: "reduce" });
  const foto = async (arquivo: string, fullPage = true) => {
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(SCREENS, `${arquivo}-${info.project.name}.png`), fullPage, caret: "initial" });
  };

  await page.goto("/");
  await expect(link(atencao(page), /Energia/)).toBeVisible();
  await foto("inicio");

  await page.goto("/contas");
  await expect(link(page, /Energia/)).toBeVisible();
  await foto("contas");

  await page.goto(`/contas/${energia.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Energia · Casa 3" })).toBeVisible();
  // D03: the list loads after the bill (it is the list of the bill's space) and marks it.
  if (desktop(info)) await expect(link(page, /Energia/)).toHaveAttribute("aria-current", "true");
  await foto("conta-detalhe");

  // Decision 28: the stacked 07 has no TabBar (no FAB), so the form opens from Início.
  await page.goto("/");
  await expect(link(atencao(page), /Energia/)).toBeVisible();
  await botaoNovaConta(page).click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  await expect(form.getByRole("group", { name: "Quem paga" })).toBeVisible();
  await form.getByRole("button", { name: "Só algumas pessoas" }).click();
  await foto("conta-form", false);
});

// ---- Decisions 23, 27–30 (owner's answers to the stage 04 review). Decision 26 is covered by pytest
// (test_rn13_atencao_inclui_aguardando_na_janela): the API cannot create `aguardando` bills yet.

const tabBar = (page: Page) => page.getByRole("navigation", { name: "Navegação principal" });

test("dec28: abaixo de 1024px /contas/[id] não tem TabBar e tem TopBar com voltar; no desktop o D03 segue com lista, painel e fechar", async ({ page, playwright }, info) => {
  const { admin, grupo, energia } = await grupoComContas(playwright);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.goto("/contas");
  await link(page, /Energia/).click();
  await expect(page).toHaveURL(`${ORIGIN}/contas/${energia.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Energia · Casa 3" })).toBeVisible();

  if (!desktop(info)) {
    await expect(tabBar(page)).toHaveCount(0);
    await expect(botaoNovaConta(page)).toHaveCount(0);
    await expect(page.getByRole("heading", { level: 1, name: "Conta", exact: true })).toBeVisible();
    await link(page, "Voltar").click();
    await expect(page).toHaveURL(`${ORIGIN}/contas`);
    await expect(tabBar(page)).toBeVisible();
    await expect(link(page, /Energia/)).toBeVisible();
  } else {
    await expect(page.getByRole("complementary", { name: "Menu principal" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "Conta aberta" })).toBeVisible();
    await expect(link(page, /Energia/)).toHaveAttribute("aria-current", "true");
    await expect(link(page, "Voltar")).toHaveCount(0);
    await expect(botaoNovaConta(page)).toBeVisible();
    await link(page, "Fechar detalhe").click();
    await expect(page).toHaveURL(`${ORIGIN}/contas`);
    await expect(texto(page, "Escolha uma conta para ver os detalhes.")).toBeVisible();
  }
});

/** One line (height under 1.5 lines), actually cut (scrollWidth > clientWidth), whole value in `title`. */
async function cortadoEmUmaLinha(el: Locator, title: string | RegExp) {
  await expect(el).toHaveAttribute("title", title);
  const m = await el.evaluate((e) => {
    const cs = getComputedStyle(e);
    return { h: e.getBoundingClientRect().height, linha: parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.25, sw: e.scrollWidth, cw: e.clientWidth };
  });
  expect(m.h, "one line").toBeLessThan(m.linha * 1.5);
  expect(m.sw, "cut with an ellipsis").toBeGreaterThan(m.cw);
}

const semRolagemHorizontal = async (page: Page) =>
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);

test("dec29: e-mail longo sem nome fica em uma linha no BillCard, em Quem paga e na MemberRow, com title inteiro e sem rolagem em 360px", async ({ page, playwright }, info) => {
  const longo = `e2e-${crypto.randomUUID()}-nome-longo@varal.test`; // 62 characters
  const [admin, pagador] = await Promise.all([novaConta(playwright), novaConta(playwright, longo)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", pagador);
  const conta = await criarConta(admin, grupo.id, { descricao: "Luz", vencimento: hoje(1), pagador: (await me(pagador.request)).id });
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  if (!desktop(info)) await page.setViewportSize({ width: 360, height: 800 });
  const escapado = longo.replace(/[.-]/g, "\\$&");

  await page.goto("/contas");
  await cortadoEmUmaLinha(link(page, /Luz/).locator("[title$=' paga']"), new RegExp(`^Vence \\d{2}/\\d{2} · ${escapado} paga$`));
  await semRolagemHorizontal(page);

  await page.goto(`/contas/${conta.id}`);
  const info2 = page.getByRole("region", { name: "Informações" }).filter({ visible: true });
  await cortadoEmUmaLinha(info2.locator(`[title="${longo}"]`), longo);
  await semRolagemHorizontal(page);

  await page.goto(`/grupos/${grupo.id}`);
  const linha = visivel(page, new RegExp(escapado));
  await expect(linha).toHaveAccessibleName(new RegExp(escapado)); // the accessible name keeps the whole e-mail
  await cortadoEmUmaLinha(linha.locator(`[title="${longo}"]`), longo);
  await semRolagemHorizontal(page);
});

test("dec30: Nova conta abre com o espaço atual primeiro e selecionado: cada grupo a partir dele, Pessoal a partir do pessoal", async ({ page, playwright }) => {
  const eu = await novaConta(playwright);
  const primeiro = await criarGrupo(eu);
  const segundo = await criarGrupo(eu);
  await logar(page, eu);

  const confere = async (espaco: string, nome: string) => {
    await usarEspaco(page, espaco);
    await page.goto("/");
    await expect(hero(page)).toBeVisible();
    await botaoNovaConta(page).click();
    const onde = page.getByRole("dialog", { name: "Nova conta" }).getByRole("group", { name: /Onde fica/ });
    const chips = onde.getByRole("button");
    await expect(chips).toHaveCount(3);
    await expect(chips.first()).toHaveText(nome);
    await expect(chips.first()).toHaveAttribute("aria-pressed", "true");
    await expect(onde.locator("[aria-pressed=true]")).toHaveCount(1);
    await page.keyboard.press("Escape");
  };
  await confere(primeiro.id, primeiro.nome);
  await confere(segundo.id, segundo.nome);
  await confere((await me(eu.request)).espaco_pessoal.id, "Pessoal");
});

test("dec23 rn30: quem saiu do grupo aparece como Ex-membro em Criada por e o e-mail dele não aparece na página", async ({ page, playwright }, info) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const conta = await criarConta(membro, grupo.id, { descricao: "Internet", pagador: null });
  expect((await api(membro.request, "POST", `/api/grupos/${grupo.id}/sair/`)).status()).toBe(204);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);

  await page.goto(`/contas/${conta.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Internet" })).toBeVisible();
  const criadaPor = page.getByRole("region", { name: "Informações" }).filter({ visible: true }).locator("div", { hasText: "Criada por" });
  await expect(criadaPor).toContainText("Ex-membro");
  await expect(texto(page, /Ex-membro criou a conta/)).toBeVisible();
  if (desktop(info)) await expect(link(page, /Internet/)).toHaveAttribute("aria-current", "true"); // D03 list loaded too
  // Text, title, aria-label: nothing in the DOM carries the e-mail (or its local part).
  expect(await page.content()).not.toContain(membro.email.split("@")[0]);
});

test("dec27: no desktop o hero do Início tem a altura do conteúdo, sem vazio abaixo do valor e do varal", async ({ page, playwright }, info) => {
  test.skip(!desktop(info), "D02 hero (≥ 1024px)");
  const { admin, grupo } = await grupoComContas(playwright);
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(link(atencao(page), /Energia/)).toBeVisible();

  const caixa = async (l: Locator) => (await l.boundingBox())!;
  const h = await caixa(hero(page));
  const valor = await caixa(hero(page).locator("p", { has: page.locator("[aria-hidden=true]") }));
  const varal = await caixa(hero(page).getByRole("img", { name: /Precisa de atenção/ }));
  const tags = await hero(page).locator("[data-tom]").evaluateAll((els) => Math.max(...els.map((e) => e.getBoundingClientRect().bottom)));
  const fimHero = h.y + h.height;
  // Below the value there is less than one clothesline of room...
  expect(fimHero - (valor.y + valor.height)).toBeLessThan(varal.height);
  // ...and below the lowest content (value or tags) only the 28px padding (+ rounding).
  expect(fimHero - Math.max(valor.y + valor.height, tags)).toBeLessThanOrEqual(28 + 4);
});

test("dec38 rn06: Quem vê mostra cada pessoa efetiva da restrita sem cortar a lista nem duplicar quem paga", async ({ page, playwright }, info) => {
  const [admin, ...pessoas] = await Promise.all(Array.from({ length: 4 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin);
  for (const pessoa of pessoas) await entrarNoGrupo(admin, grupo.id, "membro", pessoa);
  const ids = await Promise.all(pessoas.map(async (pessoa) => (await me(pessoa.request)).id));
  const conta = await criarConta(admin, grupo.id, { descricao: "Lista completa de acesso", visibilidade: "restrita", acesso: ids, pagador: ids[0] });
  await logar(page, admin);
  await usarEspaco(page, grupo.id);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(`/contas/${conta.id}`);
  const linha = page.getByRole("region", { name: "Informações" }).filter({ visible: true }).locator("div", { has: page.getByText("Quem vê", { exact: true }) });
  for (const pessoa of [admin, ...pessoas]) {
    const nome = linha.locator(`[title="${pessoa.email}"]`);
    await expect(nome).toHaveCount(1);
    await expect(nome).toBeVisible();
    expect(await nome.evaluate((e) => getComputedStyle(e).whiteSpace)).toBe("nowrap");
  }
  // The audience is allowed to grow vertically; no person disappears beyond a clipped container.
  const alturas = await linha.locator("b").evaluate((e) => ({ visible: e.clientHeight, content: e.scrollHeight }));
  expect(alturas.content).toBeLessThanOrEqual(alturas.visible + 1);
  await semRolagemHorizontal(page);
  await page.screenshot({ path: path.join(SCREENS, `dec38-quem-ve-${info.project.name}.png`), fullPage: true });
});

test("dec39 rn01: grupos com prefixos iguais mostram nome completo ao escolher e salvam no espaço identificado", async ({ page, playwright }, info) => {
  const admin = await novaConta(playwright);
  const prefixo = "Família Martins – despesas da residência compartilhada com familiares durante as férias e os encontros de fim de ano – ";
  const grupos: { id: string; nome: string }[] = [];
  for (const sufixo of ["casa da praia", "apartamento da cidade"]) {
    const nome = prefixo + sufixo;
    const response = await api(admin.request, "POST", "/api/grupos/", { nome });
    expect(response.status(), await response.text()).toBe(201);
    grupos.push(await response.json());
  }
  await logar(page, admin);
  await usarEspaco(page, grupos[0].id);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const seletor = visivel(page, `Espaço: ${grupos[0].nome}. Trocar de espaço`);
  await seletor.click();
  const menu = page.locator(`[id="${await seletor.getAttribute("aria-controls")}"]`);
  for (const grupo of grupos) {
    const opcao = menu.getByRole("button", { name: new RegExp(grupo.nome) });
    await expect(opcao).toBeVisible();
    const nome = opcao.locator(`[title="${grupo.nome}"]`);
    expect(await nome.evaluate((e) => e.scrollHeight <= e.clientHeight + 1)).toBe(true);
  }
  await page.keyboard.press("Escape");
  await botaoNovaConta(page).click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  const onde = form.getByRole("group", { name: /Onde fica/ });
  const destino = onde.getByRole("button", { name: grupos[1].nome, exact: true });
  await destino.click();
  await expect(destino).toHaveAttribute("aria-pressed", "true");
  const nome = destino.locator(`[title="${grupos[1].nome}"]`);
  expect(await nome.evaluate((e) => e.scrollHeight <= e.clientHeight + 1)).toBe(true);
  await expect(form.getByRole("group", { name: "Quem paga" })).toBeVisible();
  await semRolagemHorizontal(page);
  await page.screenshot({ path: path.join(SCREENS, `dec39-espaco-identificado-${info.project.name}.png`), fullPage: true });
  await form.getByLabel("Valor", { exact: true }).fill("42,00");
  await form.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await form.getByLabel("Descrição", { exact: true }).fill("Conta no grupo identificado");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Conta no grupo identificado" })).toBeVisible();
  const id = new URL(page.url()).pathname.split("/").pop()!;
  expect((await json(admin.request, `/api/lancamentos/${id}/`)).espaco.id).toBe(grupos[1].id);
});
