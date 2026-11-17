// Etapa 07: usuários e arquivos sintéticos; API, worker e Silo reais, nas duas resoluções.
import path from "node:path";
import { readFile } from "node:fs/promises";
import { expect, type APIRequestContext } from "@playwright/test";
import { test } from "./rn31-isolation";
import { ORIGIN, api, criarGrupo, csrf, descartarContas, entrarNoGrupo, hoje, logar, me, mesAtual, novaConta, semBadge, type Conta } from "./fixtures";

const SCREENS = path.join(__dirname, "__screens__");
const FOTO = path.join(__dirname, "fixtures", "comprovante-sintetico.png");
const PDF = path.join(__dirname, "fixtures", "manual-sintetico.pdf");

test.beforeEach(async ({ page }) => { await page.addInitScript(semBadge); page.on("dialog", (d) => d.accept()); });
test.afterEach(descartarContas);

async function criar(dono: Conta, espaco: string, extra: Record<string, unknown> = {}) {
  const resposta = await api(dono.request, "POST", `/api/espacos/${espaco}/lancamentos/`, { descricao: "Conta de teste", valor_centavos: 12345, vencimento: hoje(), ...extra });
  expect(resposta.status(), await resposta.text()).toBe(201);
  return resposta.json();
}
async function detalhe(request: APIRequestContext, id: string) {
  const resposta = await request.get(`/api/lancamentos/${id}/`);
  expect(resposta.status()).toBe(200);
  return resposta.json();
}
async function marcar(pessoa: Conta, id: string, extra: Record<string, unknown> = {}) {
  return api(pessoa.request, "POST", `/api/lancamentos/${id}/pagamentos/`, { pago_em: hoje(), valor_centavos_esperado: 12345, ...extra });
}
async function upload(pessoa: Conta, contaId: string, arquivo: string, pagamentoId?: string) {
  const resposta = await pessoa.request.post(`/api/lancamentos/${contaId}/comprovantes/`, {
    headers: { Origin: ORIGIN, "X-CSRFToken": await csrf(pessoa.request) },
    multipart: { arquivo: { name: path.basename(arquivo), mimeType: arquivo.endsWith(".png") ? "image/png" : "application/pdf", buffer: await readFile(arquivo) }, ...(pagamentoId ? { pagamento_id: pagamentoId } : {}) },
  });
  expect(resposta.status(), await resposta.text()).toBe(202);
  const { id } = await resposta.json();
  await expect.poll(async () => (await (await pessoa.request.get(`/api/comprovantes/${id}/`)).json()).estado, { timeout: 40_000 }).toBe("valido");
  return id as string;
}

test("rf15/rn14/rn16: marca integral, progresso de mês, desfaz e mantém histórico", async ({ page, playwright }, info) => {
  test.setTimeout(90_000);
  const eu = await novaConta(playwright);
  const espaco = (await me(eu.request)).espaco_pessoal.id;
  const conta = await criar(eu, espaco, { descricao: "Conta para registrar" });
  await logar(page, eu);
  await page.goto(`/contas/${conta.id}`);
  await page.getByRole("button", { name: "Já paguei" }).filter({ visible: true }).click();
  const folha = page.getByRole("dialog", { name: "Marcar como paga" });
  await expect(folha.getByLabel("Data do pagamento")).toHaveValue(hoje());
  await expect(folha.getByLabel("Data do pagamento")).toHaveAttribute("max", hoje());
  await page.screenshot({ path: path.join(SCREENS, `pagamento-folha-${info.project.name}.png`), fullPage: true, animations: "disabled" });
  await folha.getByRole("button", { name: "Confirmar pagamento" }).click();
  const sucesso = page.getByRole("dialog", { name: "Pagamento registrado." });
  await expect(sucesso).toBeVisible();
  if (info.project.name === "desktop") {
    await expect.poll(async () => {
      const box = await sucesso.boundingBox();
      return box && [Math.round(box.x), Math.round(box.y), Math.round(box.width), Math.round(box.height)];
    }).toEqual([480, 190, 480, 520]);
    await page.setViewportSize({ width: 1440, height: 500 });
    await expect.poll(async () => Math.round((await sucesso.boundingBox())?.height ?? 0)).toBe(468);
    await sucesso.getByRole("button", { name: "Anexar comprovante" }).scrollIntoViewIfNeeded();
    await expect(sucesso.getByRole("button", { name: "Anexar comprovante" })).toBeInViewport();
    await page.setViewportSize({ width: 1440, height: 900 });
  }
  await page.screenshot({ path: path.join(SCREENS, `pagamento-sucesso-${info.project.name}.png`), fullPage: true, animations: "disabled" });
  const paga = await detalhe(eu.request, conta.id);
  expect(paga.status).toBe("paga");
  expect(paga.pagamento_ativo).toMatchObject({ pago_em: hoje(), valor_pago_centavos: 12345 });
  const pagamentoId = paga.pagamento_ativo.id;
  await sucesso.getByRole("button", { name: "Anexar comprovante" }).click();
  const anexo = page.getByRole("dialog", { name: "Anexar comprovante" });
  await anexo.locator('input[type="file"]').nth(1).setInputFiles(FOTO);
  await expect(anexo.getByText(/arquivo original e seus metadados/)).toBeVisible();
  await anexo.getByRole("button", { name: "Anexar comprovante", exact: true }).click();
  await expect(anexo).toBeHidden({ timeout: 40_000 });
  await expect.poll(async () => (await detalhe(eu.request, conta.id)).status, { timeout: 40_000 }).toBe("confirmada");
  await page.goto("/");
  const progressoPago = page.getByRole("progressbar", { name: `Contas pagas em ${mesAtual()}` });
  await expect(progressoPago).toHaveAttribute("aria-valuenow", "1");
  await expect(progressoPago).toHaveAttribute("aria-valuemax", "1");
  await page.goto(`/contas/${conta.id}`);
  await page.getByRole("button", { name: "Desfazer pagamento" }).filter({ visible: true }).click();
  await expect.poll(async () => (await detalhe(eu.request, conta.id)).status).toBe("pendente");
  const reaberta = await detalhe(eu.request, conta.id);
  expect(reaberta.status).toBe("pendente");
  expect(reaberta.pagamento_ativo).toBeNull();
  expect(reaberta.pagamentos).toEqual(expect.arrayContaining([expect.objectContaining({ id: pagamentoId, desfeito_em: expect.any(String) })]));
  await expect(page.getByRole("button", { name: "Abrir comprovante" }).filter({ visible: true })).toBeVisible();
  await page.goto("/");
  const barra = page.getByRole("progressbar", { name: `Contas pagas em ${mesAtual()}` });
  await expect(barra).toHaveAttribute("aria-valuenow", "0");
  await expect(barra).toHaveAttribute("aria-valuemax", "1");
});

test("rf16/rn15/rn16: anexo posterior confirma e permanece histórico privado após desfazer", async ({ playwright }) => {
  test.setTimeout(90_000);
  const [admin, membro, observador, estranho] = await Promise.all(Array.from({ length: 4 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  await entrarNoGrupo(admin, grupo.id, "observador", observador);
  const conta = await criar(admin, grupo.id);
  const marcada = await marcar(membro, conta.id);
  expect(marcada.status()).toBe(201);
  const pagamentoId = (await marcada.json()).pagamento_ativo.id;
  const docId = await upload(membro, conta.id, FOTO, pagamentoId);
  const anexada = await api(membro.request, "POST", `/api/lancamentos/${conta.id}/pagamentos/${pagamentoId}/comprovante/`, { comprovante_id: docId });
  expect(anexada.status()).toBe(200);
  expect((await anexada.json()).status).toBe("confirmada");
  const rota = `/api/comprovantes/${docId}/arquivo/`;
  expect((await estranho.request.get(rota)).status()).toBe(404);
  const assinatura = await observador.request.get(rota);
  expect(assinatura.status()).toBe(200);
  const publico = await playwright.request.newContext();
  try {
    const { url } = await assinatura.json();
    expect(new URL(url).searchParams.get("X-Amz-Expires")).toBe("60");
    const arquivo = await publico.get(url);
    expect(arquivo.status()).toBe(200);
    expect(arquivo.headers()["content-type"]).toContain("image/png");
    expect(await arquivo.body()).toEqual(await readFile(FOTO));
    const semAssinatura = new URL(url); semAssinatura.search = "";
    expect((await publico.get(semAssinatura.toString())).status()).toBe(403);
  } finally { await publico.dispose(); }
  const desfaz = await api(membro.request, "POST", `/api/lancamentos/${conta.id}/pagamentos/${pagamentoId}/desfazer/`);
  expect(desfaz.status()).toBe(200);
  const depois = await detalhe(observador.request, conta.id);
  expect(depois.status).toBe("pendente");
  expect(depois.pagamentos).toEqual(expect.arrayContaining([expect.objectContaining({ id: pagamentoId, comprovante_id: docId, desfeito_em: expect.any(String) })]));
  expect((await observador.request.get(rota)).status()).toBe(200);
  expect((await estranho.request.get(rota)).status()).toBe(404);
});

test("rn05/rn06/rn14: permissão atual, data futura e valor divergente não alteram a conta", async ({ playwright }) => {
  const [admin, membro, pagador] = await Promise.all(Array.from({ length: 3 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  await entrarNoGrupo(admin, grupo.id, "membro", pagador);
  const atribuida = (await me(membro.request)).id;
  const escolhido = (await me(pagador.request)).id;
  const conta = await criar(admin, grupo.id, { pagador: atribuida, visibilidade: "restrita", acesso: [escolhido] });
  const grupoInicial = await (await admin.request.get(`/api/grupos/${grupo.id}/`)).json();
  const vinculoPagador = grupoInicial.membros.find((p: { email?: string }) => p.email === pagador.email);
  expect((await api(admin.request, "PATCH", `/api/grupos/${grupo.id}/membros/${vinculoPagador.id}/`, { papel: "pagador" })).status()).toBe(200);
  expect((await marcar(pagador, conta.id)).status()).toBe(403);
  expect((await marcar(membro, conta.id, { pago_em: hoje(1) })).status()).toBe(400);
  expect((await marcar(membro, conta.id, { valor_centavos_esperado: 12344 })).status()).toBe(409);
  expect((await detalhe(membro.request, conta.id)).status).toBe("pendente");
  const marcada = await marcar(membro, conta.id);
  expect(marcada.status()).toBe(201);
  const pagamentoId = (await marcada.json()).pagamento_ativo.id;
  expect((await api(admin.request, "PATCH", `/api/lancamentos/${conta.id}/`, { valor_centavos: 99999 })).status()).toBe(409);
  const dadosGrupo = await (await admin.request.get(`/api/grupos/${grupo.id}/`)).json();
  const vinculo = dadosGrupo.membros.find((p: { email?: string }) => p.email === membro.email);
  expect((await api(admin.request, "PATCH", `/api/grupos/${grupo.id}/membros/${vinculo.id}/`, { papel: "observador" })).status()).toBe(200);
  expect((await marcar(membro, conta.id)).status()).toBe(403);
  expect((await api(membro.request, "POST", `/api/lancamentos/${conta.id}/pagamentos/${pagamentoId}/desfazer/`)).status()).toBe(200);
});


test("rf16/rn15: PDF validado na marca inicial confirma somente após vínculo", async ({ playwright }) => {
  test.setTimeout(90_000);
  const eu = await novaConta(playwright);
  const espaco = (await me(eu.request)).espaco_pessoal.id;
  const conta = await criar(eu, espaco);
  const docId = await upload(eu, conta.id, PDF);
  expect((await detalhe(eu.request, conta.id)).status).toBe("pendente");
  const response = await marcar(eu, conta.id, { comprovante_id: docId });
  expect(response.status()).toBe(201);
  const confirmada = await response.json();
  expect(confirmada.status).toBe("confirmada");
  expect(confirmada.pagamento_ativo.comprovante_id).toBe(docId);
  const link = await eu.request.get(`/api/comprovantes/${docId}/arquivo/`);
  expect(link.status()).toBe(200);
  const cliente = await playwright.request.newContext();
  try {
    const { url } = await link.json();
    const arquivo = await cliente.get(url);
    expect(arquivo.headers()["content-type"]).toContain("application/pdf");
    expect(await arquivo.body()).toEqual(await readFile(PDF));
  } finally { await cliente.dispose(); }
});

test("q04-37/rf13: um filtro Ex-membro agrupa pagadores históricos e separa Sem pagador", async ({ playwright }) => {
  test.setTimeout(90_000);
  const [admin, primeiro, segundo] = await Promise.all(Array.from({ length: 3 }, () => novaConta(playwright)));
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", primeiro);
  await entrarNoGrupo(admin, grupo.id, "membro", segundo);
  const um = await criar(admin, grupo.id, { descricao: "Primeiro ex-membro", pagador: (await me(primeiro.request)).id });
  const dois = await criar(admin, grupo.id, { descricao: "Segundo ex-membro", pagador: (await me(segundo.request)).id });
  const sem = await criar(admin, grupo.id, { descricao: "Sem pagador", pagador: null });
  expect((await marcar(admin, um.id)).status()).toBe(201);
  expect((await marcar(admin, dois.id)).status()).toBe(201);
  expect((await api(primeiro.request, "POST", `/api/grupos/${grupo.id}/sair/`)).status()).toBe(204);
  expect((await api(segundo.request, "POST", `/api/grupos/${grupo.id}/sair/`)).status()).toBe(204);
  const base = `/api/espacos/${grupo.id}/lancamentos/`;
  const lista = await (await admin.request.get(base)).json();
  expect(lista.opcoes).toMatchObject({ ex_membro: true, sem_pagador: true });
  const ex = await (await admin.request.get(`${base}?pagador=ex_membro`)).json();
  expect(ex.itens.map((c: { id: string }) => c.id).sort()).toEqual([um.id, dois.id].sort());
  const nenhum = await (await admin.request.get(`${base}?pagador=nenhum`)).json();
  expect(nenhum.itens.map((c: { id: string }) => c.id)).toEqual([sem.id]);
});
