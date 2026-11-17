// Etapa 10: usuários/arquivos sintéticos; API, PostgreSQL, worker e Silo reais.
import path from "node:path";
import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import { expect, type Locator, type Page } from "@playwright/test";
import { test } from "./rn31-isolation";
import type { components } from "../src/types/api";
import { ORIGIN, api, criarGrupo, csrf, descartarContas, entrarNoGrupo, estadoAutenticado, hoje, logar, me, novaConta, semBadge, semRolagemEAlvos44, type Conta } from "./fixtures";

type Entrada = components["schemas"]["Entrada"];
const FIXTURES = path.join(__dirname, "fixtures");
const SCREENS = path.join(__dirname, "__screens__");
test.beforeEach(async ({ page }) => { await page.addInitScript(semBadge); page.on("dialog", (d) => d.accept()); });
test.afterEach(descartarContas);

async function origem(pessoa: Conta, descricao: string, pdf = false) {
  const espaco = (await me(pessoa.request)).espaco_pessoal.id;
  let documento: string | undefined;
  if (pdf) {
    const upload = await pessoa.request.post(`/api/espacos/${espaco}/boletos/pdf/`, {
      headers: { Origin: ORIGIN, "X-CSRFToken": await csrf(pessoa.request) },
      multipart: { arquivo: { name: "manual-sintetico.pdf", mimeType: "application/pdf", buffer: await readFile(path.join(FIXTURES, "manual-sintetico.pdf")) } },
    });
    expect(upload.status(), await upload.text()).toBe(202);
    documento = (await upload.json()).id;
    await expect.poll(async () => (await (await pessoa.request.get(`/api/boletos/pdfs/${documento}/`)).json()).estado, { timeout: 40_000 }).toBe("conferencia_manual");
  }
  const resposta = await api(pessoa.request, "POST", `/api/espacos/${espaco}/lancamentos/`, {
    descricao, valor_centavos: 4200, vencimento: hoje(), instrumento: { chave_pix: "contas@varal.test" }, ...(documento ? { documento_pdf: documento } : {}),
  });
  expect(resposta.status(), await resposta.text()).toBe(201);
  return resposta.json();
}
async function detalhes(pessoa: Conta, id: string) {
  const r = await pessoa.request.get(`/api/lancamentos/${id}/`);
  expect(r.status()).toBe(200);
  return r.json();
}
async function abrirPedido(page: Page) {
  await page.getByRole("button", { name: "Pedir para alguém pagar" }).filter({ visible: true }).click();
  return page.getByRole("dialog", { name: "Pedir para alguém pagar" });
}
async function alvosDaFolha(page: Page, folha: Locator) {
  await folha.evaluate((el) => Promise.all(el.getAnimations({ subtree: true }).filter((a) => a.effect?.getComputedTiming().endTime !== Infinity).map((a) => a.finished.catch(() => undefined))));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  const pequenos = await folha.locator("a, button, input:not([type=hidden]), select, textarea").evaluateAll((els) => els.filter((el) => el.checkVisibility()).filter((el) => {
    const r = el.getBoundingClientRect();
    if (r.width >= 44 && r.height >= 44) return false;
    if (el instanceof HTMLInputElement && (el.type === "checkbox" || el.type === "radio" || el.type === "file")) {
      return !Array.from(el.labels ?? []).some((label) => { const box = label.getBoundingClientRect(); return label.checkVisibility() && box.width >= 44 && box.height >= 44; });
    }
    return true;
  }).map((el) => { const r = el.getBoundingClientRect(); return `${Math.round(r.width)}×${Math.round(r.height)} ${el.outerHTML.slice(0, 80)}`; }));
  expect(pequenos).toEqual([]);
}
async function aguardarAtiva(pessoa: Conta, id: string, nonce: string) {
  const url = `/api/lancamentos/${id}/solicitacoes/nonce/${nonce}/`;
  await expect.poll(async () => {
    const r = await pessoa.request.get(url);
    return r.ok() ? (await r.json()).estado : r.status();
  }, { timeout: 60_000 }).toBe("ativa");
  return (await pessoa.request.get(url)).json();
}
async function reservar(dono: Conta, original: { id: string; versao_compartilhamento: string }, grupo: string, pagador: string) {
  const corpo: Entrada = { nonce: randomUUID(), grupo_id: grupo, pagador_id: pagador, mensagem: "Mensagem sintética", confirmar_compartilhamento: true, versao_compartilhamento: original.versao_compartilhamento };
  const resposta = await api(dono.request, "POST", `/api/lancamentos/${original.id}/solicitacoes/`, corpo);
  expect(resposta.status(), await resposta.text()).toBe(202);
  return { corpo, reserva: await resposta.json() };
}

test("rn20: pedido com PDF, pagamento no modo simples e undo preservam fronteiras", async ({ page, browser, playwright }, info) => {
  test.setTimeout(120_000);
  const [dono, pagador, estranho] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(dono);
  await criarGrupo(dono);
  await entrarNoGrupo(dono, grupo.id, "pagador", pagador);
  const pessoa = await me(pagador.request);
  const original = await origem(dono, "Conta pessoal sintética", true);
  await logar(page, dono);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(`/contas/${original.id}`);
  const folha = await abrirPedido(page);
  await expect(folha.getByLabel("Grupo")).toHaveValue("");
  await folha.getByLabel("Grupo").selectOption(grupo.id);
  const opcoes = await (await dono.request.get(`/api/lancamentos/${original.id}/solicitacoes/opcoes/`)).json();
  const escolha = opcoes.find((g: { id: string }) => g.id === grupo.id).pagadores.find((p: { id: string }) => p.id === pessoa.id);
  expect(escolha.nome).toBe(pagador.email);
  const chip = folha.getByRole("button", { name: escolha.nome, exact: true });
  await expect(chip.locator("[title]")).toHaveAttribute("title", escolha.nome);
  expect(await chip.evaluate((el) => {
    const rect = el.getBoundingClientRect();
    const container = el.closest("fieldset")!.getBoundingClientRect();
    return rect.left >= container.left && rect.right <= container.right && rect.right <= innerWidth;
  })).toBe(true);
  await chip.click();
  await folha.getByLabel("Mensagem (opcional)").fill("Pagar esta cópia sintética");
  await expect(folha.getByText(/PDF inteiro, com todas as páginas e metadados/)).toBeVisible();
  await folha.getByRole("checkbox", { name: /Confirmo o compartilhamento/ }).check();
  await alvosDaFolha(page, folha);
  await folha.getByRole("heading", { name: "Pedir para alguém pagar" }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(SCREENS, `pedido-topo-${info.project.name}.png`), animations: "disabled" });
  await folha.getByRole("button", { name: "Enviar pedido" }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(SCREENS, `pedido-fundo-${info.project.name}.png`), animations: "disabled" });
  const envio = page.waitForResponse((r) => r.request().method() === "POST" && new URL(r.url()).pathname === `/api/lancamentos/${original.id}/solicitacoes/`);
  await folha.getByRole("button", { name: "Enviar pedido" }).click();
  const resposta = await envio;
  expect(resposta.status(), await resposta.text()).toBe(202);
  const reserva = await resposta.json();
  const ativa = await aguardarAtiva(dono, original.id, reserva.nonce);
  expect(ativa.copia_id).toBeTruthy();
  await expect(folha.getByText("Pedido criado.")).toBeVisible({ timeout: 30_000 });
  await folha.getByRole("button", { name: info.project.name === "mobile" ? "Voltar" : "Fechar" }).filter({ visible: true }).first().click();
  await expect(folha).toBeHidden();
  await semRolagemEAlvos44(page);
  const copia = await detalhes(pagador, ativa.copia_id);
  expect(copia).toMatchObject({ descricao: "Conta pessoal sintética", mensagem_solicitacao: "Pagar esta cópia sintética", visibilidade: "restrita", recorrente: false });
  expect(JSON.stringify(copia)).not.toContain(original.id);
  expect((await estranho.request.get(`/api/lancamentos/${ativa.copia_id}/`)).status()).toBe(404);
  expect((await pagador.request.get(`/api/lancamentos/${original.id}/`)).status()).toBe(404);
  const arquivo = await pagador.request.get(`/api/lancamentos/${ativa.copia_id}/pdf/`);
  expect(arquivo.status()).toBe(200);
  const cliente = await playwright.request.newContext();
  try {
    const { url } = await arquivo.json();
    expect(await (await cliente.get(url)).body()).toEqual(await readFile(path.join(FIXTURES, "manual-sintetico.pdf")));
    const anonimo = new URL(url); anonimo.search = "";
    expect((await cliente.get(anonimo.toString())).status()).toBe(403);
  } finally { await cliente.dispose(); }
  const contexto = await browser.newContext({ baseURL: ORIGIN, viewport: page.viewportSize(), storageState: await estadoAutenticado(pagador.request), permissions: ["clipboard-read", "clipboard-write"] });
  await contexto.addInitScript(semBadge);
  const simples = await contexto.newPage();
  try {
    await simples.goto(`/grupos/${grupo.id}/simples`);
    const card = simples.locator("article").filter({ hasText: "Conta pessoal sintética" });
    await expect(card).toBeVisible();
    await semRolagemEAlvos44(simples);
    await expect(card.getByRole("button", { name: "Baixar boleto em PDF" })).toBeVisible();
    const respostaPdf = contexto.waitForEvent("response", (r) => new URL(r.url()).port === "9000" && new URL(r.url()).pathname.endsWith(".pdf"));
    const novaAba = contexto.waitForEvent("page");
    await card.getByRole("button", { name: "Baixar boleto em PDF" }).click();
    const [abaPdf, pdfReal] = await Promise.all([novaAba, respostaPdf]);
    expect(pdfReal.status()).toBe(200);
    expect(pdfReal.headers()["content-type"]).toContain("application/pdf");
    await abaPdf.close();
    await card.getByRole("button", { name: "Copiar chave Pix" }).click();
    expect(await simples.evaluate(() => navigator.clipboard.readText())).toBe("contas@varal.test");
    const copiar = await card.getByRole("button", { name: "Copiar chave Pix" }).boundingBox();
    const marcar = await card.getByRole("button", { name: "Já paguei" }).boundingBox();
    expect(copiar && marcar && (copiar.x + copiar.width <= marcar.x || copiar.y + copiar.height <= marcar.y || marcar.x + marcar.width <= copiar.x || marcar.y + marcar.height <= copiar.y)).toBe(true);
    await simples.screenshot({ path: path.join(SCREENS, `modo-simples-${info.project.name}.png`), animations: "disabled" });
    await card.getByRole("button", { name: "Já paguei" }).click();
    const pagar = simples.getByRole("dialog", { name: "Marcar como paga" });
    await pagar.locator('input[type="file"]').nth(1).setInputFiles(path.join(FIXTURES, "comprovante-sintetico.png"));
    await pagar.getByRole("button", { name: "Confirmar pagamento" }).click();
    const sucesso = simples.getByRole("dialog", { name: "Pagamento registrado." });
    await expect(sucesso).toBeVisible({ timeout: 45_000 });
    await sucesso.getByRole("button", { name: info.project.name === "mobile" ? "Voltar às contas" : "Fechar" }).click();
    await expect(simples).toHaveURL(new RegExp(`/grupos/${grupo.id}/simples`));
    await simples.getByRole("button", { name: /1 conta deste mês já paga/ }).click();
    await simples.getByRole("link", { name: "Conta pessoal sintética" }).click();
    await expect(simples).toHaveURL(/origem=simples.*pagas=1/);
    await simples.getByRole("link", { name: info.project.name === "mobile" ? "Voltar" : "Fechar detalhe" }).click();
    await expect(simples).toHaveURL(new RegExp(`/grupos/${grupo.id}/simples\\?pagas=1`));
    await expect(simples.getByRole("button", { name: "Voltar às contas em aberto" })).toBeVisible();
    await expect(simples.getByRole("link", { name: "Conta pessoal sintética" })).toBeVisible();
    const pessoal = await detalhes(dono, original.id);
    const grupoPago = await detalhes(pagador, ativa.copia_id);
    expect(pessoal.status).toBe("paga");
    expect(pessoal.pagamento_ativo).toMatchObject({ derivado: true, comprovante_id: null, valor_pago_centavos: 4200, pago_em: hoje() });
    expect(grupoPago.status).toBe("confirmada");
    expect(grupoPago.pagamento_ativo.comprovante_id).toBeTruthy();
    expect((await api(pagador.request, "POST", `/api/lancamentos/${ativa.copia_id}/pagamentos/${grupoPago.pagamento_ativo.id}/desfazer/`)).status()).toBe(200);
    expect((await detalhes(dono, original.id)).status).toBe("pendente");
    expect((await detalhes(pagador, ativa.copia_id)).status).toBe("pendente");
  } finally {
    try { await contexto.close(); } catch (erro) {
      if (test.info().status === test.info().expectedStatus) throw erro;
    }
  }
});

test("t10-e: resposta perdida recupera mesmo nonce após fechar e recarregar", async ({ page, playwright }, info) => {
  test.setTimeout(90_000);
  const [dono, pagador] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(dono);
  await entrarNoGrupo(dono, grupo.id, "pagador", pagador);
  const original = await origem(dono, "Pedido com resposta perdida");
  const opcoes = await (await dono.request.get(`/api/lancamentos/${original.id}/solicitacoes/opcoes/`)).json();
  const usuario = await me(pagador.request);
  const nome = opcoes[0].pagadores.find((p: { id: string }) => p.id === usuario.id).nome;
  expect(nome).toBe(pagador.email);
  let nonce = "";
  let envios = 0;
  await page.route(`**/api/lancamentos/${original.id}/solicitacoes/`, async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    envios++;
    nonce = (route.request().postDataJSON() as Entrada).nonce;
    await route.fetch(); // The real server processes the command; only its response is lost.
    await route.abort("failed");
  });
  await logar(page, dono);
  await page.goto(`/contas/${original.id}`);
  let folha = await abrirPedido(page);
  await folha.getByRole("button", { name: nome, exact: true }).click();
  await folha.getByRole("checkbox", { name: /Confirmo o compartilhamento/ }).check();
  await folha.getByRole("button", { name: "Enviar pedido" }).click();
  await expect.poll(() => nonce).not.toBe("");
  const ativa = await aguardarAtiva(dono, original.id, nonce);
  expect(ativa.copia_id).toBeTruthy();
  await folha.getByRole("button", { name: info.project.name === "mobile" ? "Voltar" : "Fechar" }).filter({ visible: true }).first().click();
  await page.reload();
  await page.getByRole("button", { name: "Ver pedido" }).filter({ visible: true }).click();
  folha = page.getByRole("dialog", { name: "Pedir para alguém pagar" });
  await expect(folha.getByText("Pedido criado.")).toBeVisible({ timeout: 30_000 });
  expect(envios).toBe(1);
  expect((await (await dono.request.get(`/api/lancamentos/${original.id}/solicitacoes/nonce/${nonce}/`)).json()).id).toBe(ativa.id);
});

test("t10-e: tombstone anterior ao POST e revisão antiga recusam criação", async ({ playwright }) => {
  const [dono, pagador] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(dono);
  await entrarNoGrupo(dono, grupo.id, "pagador", pagador);
  const original = await origem(dono, "Pedido cancelado antes da reserva");
  const usuario = await me(pagador.request);
  const corpo: Entrada = { nonce: randomUUID(), grupo_id: grupo.id, pagador_id: usuario.id, mensagem: "", confirmar_compartilhamento: true, versao_compartilhamento: original.versao_compartilhamento };
  const base = `/api/lancamentos/${original.id}/solicitacoes/`;
  expect((await api(dono.request, "DELETE", `${base}nonce/${corpo.nonce}/`)).status()).toBe(204);
  expect((await api(dono.request, "POST", base, corpo)).status()).toBe(409);
  const alterada = await api(dono.request, "PATCH", `/api/lancamentos/${original.id}/`, { descricao: "Cobrança revisada" });
  expect(alterada.status()).toBe(200);
  expect((await api(dono.request, "POST", base, { ...corpo, nonce: randomUUID() })).status()).toBe(409);
  expect((await detalhes(dono, original.id)).solicitacao_ativa).toBeNull();
});

test("rn20: pagamento manual ou cancelamento da origem encerram cópia aberta", async ({ playwright }) => {
  const [dono, pagador] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(dono);
  await entrarNoGrupo(dono, grupo.id, "pagador", pagador);
  const uid = (await me(pagador.request)).id;
  const a = await origem(dono, "Original com pagamento manual");
  const { corpo: envioA } = await reservar(dono, a, grupo.id, uid);
  const ativaA = await aguardarAtiva(dono, a.id, envioA.nonce);
  const paga = await api(dono.request, "POST", `/api/lancamentos/${a.id}/pagamentos/`, { pago_em: hoje(), valor_centavos_esperado: 4200 });
  expect(paga.status()).toBe(201);
  const marca = (await paga.json()).pagamento_ativo.id;
  expect((await detalhes(pagador, ativaA.copia_id)).status).toBe("cancelada");
  expect((await api(dono.request, "POST", `/api/lancamentos/${a.id}/pagamentos/${marca}/desfazer/`)).status()).toBe(200);
  expect((await detalhes(pagador, ativaA.copia_id)).status).toBe("cancelada");
  const b = await origem(dono, "Original cancelada");
  const { corpo: envioB } = await reservar(dono, b, grupo.id, uid);
  const ativaB = await aguardarAtiva(dono, b.id, envioB.nonce);
  expect((await api(dono.request, "POST", `/api/lancamentos/${b.id}/cancelar/`)).status()).toBe(200);
  expect((await detalhes(pagador, ativaB.copia_id)).status).toBe("cancelada");
});

test("cu11: modo simples reúne meses e mostra acesso sem poder pagar", async ({ page, playwright }, info) => {
  const [admin, pagador, outraPessoa] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", pagador);
  await entrarNoGrupo(admin, grupo.id, "membro", outraPessoa);
  const uid = (await me(pagador.request)).id;
  const outro = (await me(outraPessoa.request)).id;
  const proximo = new Date(`${hoje().slice(0, 7)}-01T12:00:00Z`);
  proximo.setUTCMonth(proximo.getUTCMonth() + 1);
  const criar = async (body: Record<string, unknown>) => {
    const r = await api(admin.request, "POST", `/api/espacos/${grupo.id}/lancamentos/`, { valor_centavos: 1000, vencimento: hoje(), ...body });
    expect(r.status(), await r.text()).toBe(201);
    return r.json();
  };
  await criar({ descricao: "Conta deste mês", pagador: uid });
  await criar({ descricao: "Conta do próximo mês", vencimento: proximo.toISOString().slice(0, 10), pagador: uid });
  await criar({ descricao: "Conta alheia visível", pagador: outro, visibilidade: "restrita", acesso: [uid] });
  const modelo = await api(admin.request, "POST", `/api/espacos/${grupo.id}/recorrencias/`, { chave_idempotencia: randomUUID(), descricao: "Valor desconhecido", dia_vencimento: 15, valor_tipo: "variavel", valor_centavos: null, pagador: uid });
  expect(modelo.status(), await modelo.text()).toBe(201);
  const grupoDados = await (await admin.request.get(`/api/grupos/${grupo.id}/`)).json();
  const vinculo = grupoDados.membros.find((m: { usuario: string }) => m.usuario === uid);
  expect((await api(admin.request, "PATCH", `/api/grupos/${grupo.id}/membros/${vinculo.id}/`, { papel: "pagador" })).status()).toBe(200);
  const lista = await (await pagador.request.get(`/api/espacos/${grupo.id}/lancamentos/simples/`)).json();
  expect(lista.abertas_qtd).toBe(4);
  const ordenadas = [...lista.itens].sort((a, b) => a.vencimento.localeCompare(b.vencimento) || a.id.localeCompare(b.id));
  expect(lista.itens.map((c: { id: string }) => c.id)).toEqual(ordenadas.map((c: { id: string }) => c.id));
  await logar(page, pagador);
  await page.goto(`/grupos/${grupo.id}/simples`);
  await expect(page.getByRole("heading", { name: "Você tem 4 contas em aberto." })).toBeVisible();
  const alheia = page.locator("article").filter({ hasText: "Conta alheia visível" });
  await expect(alheia.getByRole("button", { name: "Já paguei" })).toHaveCount(0);
  const desconhecida = page.locator("article").filter({ hasText: "Valor desconhecido" });
  await expect(desconhecida.getByText("Valor a definir")).toBeVisible();
  await expect(desconhecida.getByText("Aguardando conferência")).toBeVisible();
  await expect(desconhecida.getByRole("button", { name: "Já paguei" })).toHaveCount(0);
  await expect(page.locator("article").filter({ hasText: "Conta do próximo mês" })).toBeVisible();
  await page.screenshot({ path: path.join(SCREENS, `modo-simples-lista-${info.project.name}.png`), animations: "disabled" });
});

test("rn16/rn32: dono sem acesso ao grupo não desfaz marca derivada", async ({ playwright }) => {
  const [dono, pagador] = await Promise.all([novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(dono);
  await entrarNoGrupo(dono, grupo.id, "admin", pagador);
  const original = await origem(dono, "Derivada sem acesso ao grupo");
  const { corpo } = await reservar(dono, original, grupo.id, (await me(pagador.request)).id);
  const ativa = await aguardarAtiva(dono, original.id, corpo.nonce);
  expect((await api(dono.request, "POST", `/api/grupos/${grupo.id}/sair/`)).status()).toBe(204);
  const paga = await api(pagador.request, "POST", `/api/lancamentos/${ativa.copia_id}/pagamentos/`, { pago_em: hoje(), valor_centavos_esperado: 4200 });
  expect(paga.status(), await paga.text()).toBe(201);
  const local = (await paga.json()).pagamento_ativo.id;
  const pessoal = await detalhes(dono, original.id);
  expect(pessoal.pagamento_ativo.derivado).toBe(true);
  expect((await api(dono.request, "POST", `/api/lancamentos/${original.id}/pagamentos/${pessoal.pagamento_ativo.id}/desfazer/`)).status()).toBe(409);
  expect((await detalhes(dono, original.id)).status).toBe("paga");
  expect((await api(pagador.request, "POST", `/api/lancamentos/${ativa.copia_id}/pagamentos/${local}/desfazer/`)).status()).toBe(200);
  expect((await detalhes(dono, original.id)).status).toBe("pendente");
});
