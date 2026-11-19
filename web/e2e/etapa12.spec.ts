// Etapa 12 (correções do teste inicial): CA01–CA06, CA08, CA10 in the browser.
// COR-01 sessão ao voltar à aba; COR-02/03/05 Contas pessoal, todos os meses, mês como filtro; COR-04 ícone da
// categoria; COR-06 destino da Nova conta; COR-07 Sem categoria; COR-10 permissões por categoria; COR-11 navegação
// Grupos → grupo → categoria → conta. API rules of COR-10 are covered by pytest (test_permissoes_categoria.py).
import path from "node:path";
import type { Locator, Page } from "@playwright/test";
import { expect } from "@playwright/test";
import { test } from "./rn31-isolation";
import { AUTH, ORIGIN, TEST_PASSWORD, api, criarGrupo, entrarNoGrupo, hoje, logar, me, novaConta, outraAba, uniqueEmail, type Conta } from "./fixtures";

const visivel = (page: Page | Locator, nome: string | RegExp) => page.getByRole("button", { name: nome }).filter({ visible: true });
const link = (page: Page | Locator, nome: string | RegExp) => page.getByRole("link", { name: nome }).filter({ visible: true });
const texto = (page: Page | Locator, t: string | RegExp) => page.getByText(t, typeof t === "string" ? { exact: true } : undefined).filter({ visible: true });
const desktop = (info: { project: { name: string } }) => info.project.name === "desktop";

async function criarConta(dono: Conta, espaco: string, dados: Record<string, unknown>) {
  const r = await api(dono.request, "POST", `/api/espacos/${espaco}/lancamentos/`, { valor_centavos: 1000, vencimento: hoje(), ...dados });
  expect(r.status(), await r.text()).toBe(201);
  return (await r.json()) as { id: string };
}
async function casaDe(admin: Conta, grupo: string, nome = "Casa da praia") {
  const r = await admin.request.get(`/api/grupos/${grupo}/`);
  return ((await r.json()) as { casas: { id: string; nome: string }[] }).casas.find((c) => c.nome === nome)!.id;
}
const mesDe = (data: string) => data.slice(0, 7);

test("ca01 cor01: voltar à aba mantém a sessão; sessão encerrada em outra aba mostra o aviso ao voltar", async ({ page, playwright }) => {
  const eu = await novaConta(playwright);
  await logar(page, eu);
  await page.goto("/contas");
  await expect(page.getByRole("heading", { level: 1, name: "Contas" })).toBeVisible();
  const voltarAba = () =>
    page.evaluate(() => {
      for (const estado of ["hidden", "visible"]) {
        Object.defineProperty(document, "visibilityState", { value: estado, configurable: true });
        document.dispatchEvent(new Event("visibilitychange"));
      }
    });

  await voltarAba();
  const aviso = texto(page, /Sua sessão terminou/);
  await expect(page.getByRole("heading", { level: 1, name: "Contas" })).toBeVisible();
  await expect(aviso).toHaveCount(0);
  await expect(texto(page, "Verificando sua sessão…")).toHaveCount(0);

  // Logout elsewhere (same session cookie): the next return to the tab hides private data.
  await api(page.request, "DELETE", `${AUTH}auth/session`);
  await voltarAba();
  await expect(aviso).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "Contas" })).toBeHidden();
});

test("ca02 ca04 cor02/03/05: Contas é pessoal e de todos os meses; ?espaco= mostra o grupo; mês e status combinam", async ({ page, playwright }) => {
  const eu = await novaConta(playwright);
  const pessoal = (await me(eu.request)).espaco_pessoal.id;
  const grupo = await criarGrupo(eu);
  // Three different months: 40 days apart can never share a month.
  await criarConta(eu, pessoal, { descricao: "Luz deste mês", vencimento: hoje() });
  await criarConta(eu, pessoal, { descricao: "Luz do próximo", vencimento: hoje(40) });
  await criarConta(eu, pessoal, { descricao: "Luz de depois", vencimento: hoje(80) });
  await criarConta(eu, grupo.id, { descricao: "Água da família" });
  await logar(page, eu);

  await page.goto("/contas");
  await expect(texto(page, /^Total de todos os meses: R\$ 30,00 · 3 contas · Pessoal$/)).toBeVisible();
  for (const nome of [/Luz deste mês/, /Luz do próximo/, /Luz de depois/]) await expect(link(page, nome)).toBeVisible();
  await expect(texto(page, /Água da família/)).toHaveCount(0);

  await page.goto(`/contas?espaco=${grupo.id}`);
  await expect(link(page, /Água da família/)).toBeVisible();
  await expect(texto(page, /Luz deste mês/)).toHaveCount(0);

  await page.goto(`/contas?mes=${mesDe(hoje(40))}&status=a_pagar`);
  await expect(link(page, /Luz do próximo/)).toBeVisible();
  await expect(texto(page, /Luz deste mês/)).toHaveCount(0);
  await expect(texto(page, /Luz de depois/)).toHaveCount(0);
  await link(page, "Todos os meses").click();
  await expect(page).toHaveURL(`${ORIGIN}/contas?status=a_pagar`);
  await expect(link(page, /Luz de depois/)).toBeVisible();
});

test("ca03 ca05 ca06 ca08 cor04/06/07/11: categoria com ícone; Grupos → grupo → categoria → conta e volta; Sem categoria; + já vem na categoria", async ({ page, playwright }, info) => {
  const admin = await novaConta(playwright);
  const grupo = await criarGrupo(admin);
  const casa = await casaDe(admin, grupo.id);
  const agua = await criarConta(admin, grupo.id, { descricao: "Água", subgrupo: casa });
  await criarConta(admin, grupo.id, { descricao: "Gás solto" });
  await logar(page, admin);

  await page.goto("/grupos");
  await link(page, new RegExp(grupo.nome)).click();
  await expect(page).toHaveURL(`${ORIGIN}/grupos/${grupo.id}`);

  // CA03: name and one of the 14 icons; the card shows the icon.
  await visivel(page, "+ Nova categoria").click();
  const folha = page.getByRole("dialog", { name: "Nova categoria" });
  await expect(folha.getByRole("radio")).toHaveCount(14);
  await folha.getByLabel("Nome da categoria").fill("Contas de luz");
  await folha.getByRole("radio", { name: "Luz" }).check();
  await folha.getByRole("button", { name: "Criar" }).click();
  await expect(folha).toBeHidden();
  await expect(link(page, /Contas de luz/).locator('svg[data-name="luz"]')).toBeVisible();

  // CA06: bills without category have their own card and screen.
  await link(page, /Sem categoria/).click();
  // The first visit compiles the route under `next dev`.
  await expect(page).toHaveURL(`${ORIGIN}/grupos/${grupo.id}/categorias/sem-categoria`, { timeout: 20_000 });
  await expect(link(page, /Gás solto/)).toBeVisible();
  await expect(texto(page, /^Água$/)).toHaveCount(0);
  await link(page, "Voltar ao grupo").click();

  // CA08: category → bill → back to the category.
  await link(page, /Casa da praia/).click();
  const categoria = `${ORIGIN}/grupos/${grupo.id}/categorias/${casa}`;
  await expect(page).toHaveURL(categoria);
  await expect(page.getByRole("heading", { level: 1, name: "Casa da praia" })).toBeVisible();
  await expect(texto(page, /Gás solto/)).toHaveCount(0);
  await link(page, /Água/).click();
  await expect(page).toHaveURL(`${categoria}/${agua.id}`);
  await expect(page.getByRole("heading", { level: 1, name: "Água" })).toBeVisible();
  await link(page, desktop(info) ? "Fechar detalhe" : "Voltar").click();
  await expect(page).toHaveURL(categoria);

  // CA05: "+" inside the category starts in this group and this category.
  await visivel(page, "Nova conta").click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  const onde = form.getByRole("group", { name: /Onde fica/ });
  await expect(onde.getByRole("button").first()).toHaveText(grupo.nome);
  await expect(onde.getByRole("button").first()).toHaveAttribute("aria-pressed", "true");
  await expect(form.getByRole("group", { name: "Categoria" }).getByRole("button", { name: "Casa da praia" })).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Escape");
  await link(page, "Voltar ao grupo").click();
  await expect(page).toHaveURL(`${ORIGIN}/grupos/${grupo.id}`);
});

test("ca10 cor10: admin tira o Ver de um membro na categoria; ele não vê a categoria nem a conta (404)", async ({ page, browser, playwright }) => {
  const [admin, membro] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  const casa = await casaDe(admin, grupo.id);
  const conta = await criarConta(admin, grupo.id, { descricao: "Água da praia", subgrupo: casa, pagador: null });
  expect((await membro.request.get(`/api/lancamentos/${conta.id}/`)).status()).toBe(200);
  await logar(page, admin);

  await page.goto(`/grupos/${grupo.id}`);
  await visivel(page, "Editar Casa da praia").click();
  await visivel(page.getByRole("dialog", { name: "Editar categoria" }), /^Quem pode fazer o quê/).click();
  const folha = page.getByRole("dialog", { name: "Quem pode fazer o quê" });
  await folha.getByRole("switch", { name: "Personalizar permissões desta categoria" }).check();
  const pessoa = folha.getByRole("group", { name: new RegExp(membro.email.replace(/[.-]/g, "\\$&")) });
  await expect(pessoa.getByRole("checkbox", { name: "Pagar" })).toBeChecked(); // role default
  await pessoa.getByRole("checkbox", { name: "Ver" }).uncheck();
  await expect(pessoa.getByRole("checkbox", { name: "Pagar" })).toBeDisabled();
  await folha.getByRole("button", { name: "Salvar" }).click();
  await expect(folha).toBeHidden();

  expect((await membro.request.get(`/api/lancamentos/${conta.id}/`)).status()).toBe(404);
  const aba = await outraAba(browser, page, membro);
  try {
    await aba.goto(`/grupos/${grupo.id}`);
    await expect(aba.getByRole("heading", { level: 1, name: grupo.nome })).toBeVisible();
    await expect(link(aba, /Casa da praia/)).toHaveCount(0);
    await aba.goto(`/contas?espaco=${grupo.id}`);
    await expect(texto(aba, "Nenhuma conta por aqui ainda.")).toBeVisible();
    await aba.goto(`/contas/${conta.id}`);
    await expect(aba.getByRole("alert").filter({ visible: true, hasText: /\S/ })).toContainText("Conta não encontrada");
  } finally {
    await aba.context().close();
  }
});

test("auditoria: a recorrência clicada no grupo abre direto nela", async ({ page, playwright }) => {
  const admin = await novaConta(playwright);
  const grupo = await criarGrupo(admin);
  for (const descricao of ["Internet fibra", "Condomínio"]) {
    const r = await api(admin.request, "POST", `/api/espacos/${grupo.id}/recorrencias/`, { chave_idempotencia: crypto.randomUUID(), descricao, dia_vencimento: 10, valor_tipo: "variavel", valor_centavos: null });
    expect(r.status(), await r.text()).toBe(201);
  }
  await logar(page, admin);
  await page.goto(`/grupos/${grupo.id}`);
  await visivel(page, /Condomínio/).click();
  const folha = page.getByRole("dialog", { name: "Conta que se repete" });
  await expect(folha.getByLabel("Descrição")).toHaveValue("Condomínio");
});

test("evidências da etapa 12: grupo, categoria, Contas, permissões, Perfil, Avisos e modo simples nas duas larguras", async ({ page, playwright }, info) => {
  test.setTimeout(90_000);
  const [admin, membro, pagador] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin, ["Casa da praia", "Internet"]);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  await entrarNoGrupo(admin, grupo.id, "pagador", pagador);
  const casa = await casaDe(admin, grupo.id);
  const pagadorId = (await me(pagador.request)).id;
  await criarConta(admin, grupo.id, { descricao: "Energia", valor_centavos: 28743, subgrupo: casa, pagador: pagadorId });
  await criarConta(admin, grupo.id, { descricao: "Água", valor_centavos: 8435, vencimento: hoje(10), subgrupo: casa });
  await criarConta(admin, grupo.id, { descricao: "Gás", valor_centavos: 9500, vencimento: hoje(40) });
  const pessoal = (await me(admin.request)).espaco_pessoal.id;
  await criarConta(admin, pessoal, { descricao: "Cartão", valor_centavos: 120000, vencimento: hoje(5) });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const dir = path.join(__dirname, "../../docs/etapas/12-correcoes-teste/evidencias");
  const foto = async (nome: string) => {
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(dir, `${nome}-${info.project.name}.jpg`), type: "jpeg", quality: 70, fullPage: true });
  };

  await logar(page, admin);
  await page.goto(`/grupos/${grupo.id}`);
  await expect(link(page, /Casa da praia/)).toContainText("R$ 371,78");
  // Owner's request (18/11): no recurrence, no section; "Ver todas as contas" sits above the categories.
  await expect(page.getByRole("heading", { name: "Contas que se repetem" })).toHaveCount(0);
  expect((await link(page, /Ver todas as contas do grupo/).boundingBox())!.y).toBeLessThan((await page.getByRole("heading", { name: "Categorias" }).boundingBox())!.y);
  await foto("grupo");
  await visivel(page, "Editar Casa da praia").click();
  await visivel(page.getByRole("dialog", { name: "Editar categoria" }), /^Quem pode fazer o quê/).click();
  const folha = page.getByRole("dialog", { name: "Quem pode fazer o quê" });
  await folha.getByRole("switch").check();
  await expect(folha.getByRole("checkbox", { name: "Ver" }).first()).toBeVisible();
  await foto("permissoes");
  await page.keyboard.press("Escape");
  await page.goto(`/grupos/${grupo.id}/categorias/${casa}`);
  await expect(link(page, /Energia/)).toBeVisible();
  await foto("categoria");
  await page.goto("/contas");
  await expect(link(page, /Cartão/)).toBeVisible();
  await foto("contas-pessoal");
  await page.goto(`/contas?espaco=${grupo.id}`);
  await expect(link(page, /Gás/)).toBeVisible();
  await foto("contas-grupo");
  await page.goto("/perfil");
  await expect(page.getByRole("heading", { name: "Seus dados" })).toBeVisible();
  await foto("perfil");
  if (!desktop(info)) {
    await page.goto("/avisos");
    await expect(page.getByRole("heading", { level: 1, name: "Avisos" })).toBeVisible();
    await expect(texto(page, "Carregando avisos…")).toHaveCount(0);
    await foto("avisos");
  }
  await logar(page, pagador);
  await page.goto(`/grupos/${grupo.id}/simples`);
  await expect(link(page, /Energia/)).toBeVisible();
  await foto("simples");
});

test("q12-2: nome opcional no cadastro, mostrado e editável no Perfil", async ({ page }, info) => {
  await page.context().clearCookies();
  await page.goto("/criar-conta");
  await page.getByLabel("Nome (opcional)").fill("Ana Martins");
  await page.getByLabel("E-mail", { exact: true }).fill(uniqueEmail());
  await page.getByLabel("Senha", { exact: true }).fill(TEST_PASSWORD);
  const cadastro = page.waitForResponse((r) => new URL(r.url()).pathname === `${AUTH}auth/signup` && r.request().method() === "POST");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  expect((await cadastro).status()).toBe(200);
  await expect(page).toHaveURL(`${ORIGIN}/`, { timeout: 20_000 }); // first visit compiles "/" in next dev
  expect((await me(page.request)).nome).toBe("Ana Martins");

  await page.goto("/perfil");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Ana Martins");
  await visivel(page, "Editar nome").click();
  await page.getByLabel("Nome", { exact: true }).fill("Ana M. Souza");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(__dirname, "../../docs/etapas/12-correcoes-teste/evidencias", `perfil-nome-${info.project.name}.jpg`), type: "jpeg", quality: 70, fullPage: true });
  await visivel(page, "Salvar nome").click();
  await expect(texto(page, "Nome salvo.")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Ana M. Souza");
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Ana M. Souza");
});
