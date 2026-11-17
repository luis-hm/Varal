// Etapa 06: API, Celery, PostgreSQL e Silo reais; PDFs sintéticos sem dados privados.
import path from "node:path";
import { readFile } from "node:fs/promises";
import { expect, type Locator, type Page } from "@playwright/test";
import { test } from "./rn31-isolation";
import { ORIGIN, api, criarGrupo, descartarContas, entrarNoGrupo, hoje, logar, novaConta, semBadge } from "./fixtures";

const FIXTURES = path.join(__dirname, "fixtures");
const SCREENS = path.join(__dirname, "__screens__");
const BANCO = "00191234546789012345767890123457710000000012345";
const OUTRO = "00191234546789012345767890123457210010000012345";

test.beforeEach(async ({ page }) => { await page.addInitScript(semBadge); });
test.afterEach(descartarContas);

async function abrir(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Nova conta" }).filter({ visible: true }).click();
  return page.getByRole("dialog", { name: "Nova conta" });
}

async function enviar(page: Page, form: Locator, nome: string) {
  const resposta = page.waitForResponse((r) => r.request().method() === "POST" && /\/boletos\/pdf\/$/.test(new URL(r.url()).pathname));
  await form.locator('input[type="file"]').setInputFiles(path.join(FIXTURES, nome));
  const recebido = await resposta;
  expect(recebido.status()).toBe(202);
  return (await recebido.json() as { id: string }).id;
}

async function abrirPdfReal(page: Page, botao: Locator) {
  // Chromium headless may keep the PDF viewer page at about:blank even after the PDF response.
  const resposta = page.context().waitForEvent("response", (r) => new URL(r.url()).port === "9000" && new URL(r.url()).pathname.endsWith(".pdf"));
  const abertura = page.waitForEvent("popup");
  await botao.click();
  const [popup, arquivo] = await Promise.all([abertura, resposta]);
  expect(arquivo.status()).toBe(200);
  expect(arquivo.headers()["content-type"]).toContain("application/pdf");
  expect(arquivo.headers()["content-disposition"]).toContain("inline");
  await popup.close();
}

test("rf23/rn26/rn27/rn29: PDF real é lido, código prevalece, vincula e download assinado funciona", async ({ page, playwright }, info) => {
  test.setTimeout(90_000);
  const eu = await novaConta(playwright);
  await logar(page, eu);
  const form = await abrir(page);
  const alvo = form.getByText("Enviar PDF do boleto", { exact: true }).locator("..");
  const dimensoes = await alvo.boundingBox();
  expect(dimensoes).not.toBeNull();
  expect(dimensoes!.width).toBeGreaterThanOrEqual(44);
  expect(dimensoes!.height).toBeGreaterThanOrEqual(44);
  await form.getByRole("button", { name: "Pessoal" }).focus();
  await page.keyboard.press("Tab");
  await expect(form.locator('input[type="file"]')).toBeFocused();
  await expect(alvo).toHaveCSS("outline-style", "solid");
  const id = await enviar(page, form, "boleto-sintetico.pdf");
  await expect(form.getByText("Boleto bancário conferido. Confira os dados antes de salvar.")).toBeVisible({ timeout: 40_000 });
  await expect(form.getByLabel("Valor", { exact: true })).toHaveValue("123,45");
  await expect(form.getByText(/Valor do texto diverge/)).toBeVisible();
  await expect(form.getByText(/Vencimento do texto diverge/)).toBeVisible();
  await expect(form.getByLabel("Emissão", { exact: true })).toHaveValue("2025-02-01");
  await expect(form.getByLabel("Beneficiário", { exact: true })).toHaveValue("Empresa Exemplo");
  const trocar = form.getByText("Trocar", { exact: true });
  const tamanhoTrocar = await trocar.boundingBox();
  expect(tamanhoTrocar).not.toBeNull();
  expect(tamanhoTrocar!.width).toBeGreaterThanOrEqual(44);
  expect(tamanhoTrocar!.height).toBeGreaterThanOrEqual(44);
  await form.getByRole("button", { name: "Pessoal" }).focus();
  await page.keyboard.press("Tab");
  await expect(form.locator('input[type="file"]')).toBeFocused();
  await expect(trocar).toHaveCSS("outline-style", "solid");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  const abrirPdf = form.getByRole("button", { name: "Abrir PDF em outra aba" });
  await expect(abrirPdf).toBeVisible();
  await form.getByRole("button", { name: "Carregar prévia" }).click();
  const previa = form.locator('iframe[title="Prévia do PDF"]');
  await expect(previa).toHaveAttribute("src", /X-Amz-Signature=/);
  await previa.screenshot({ path: path.join(SCREENS, `pdf-previa-${info.project.name}.png`) });
  await abrirPdfReal(page, abrirPdf);
  await page.screenshot({ path: path.join(SCREENS, `pdf-conferencia-${info.project.name}.png`), fullPage: true });
  await form.getByLabel("Descrição").fill("Boleto PDF sintético");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Boleto PDF sintético" })).toBeVisible();
  const contaId = new URL(page.url()).pathname.split("/").pop()!;
  const conta = await (await eu.request.get(`/api/lancamentos/${contaId}/`)).json();
  expect(conta.instrumento.codigo).toBe(BANCO);
  expect(conta.valor_centavos).toBe(12345);
  expect(conta.documento_pdf.id).toBe(id);
  const informacoes = page.getByRole("region", { name: "Informações" }).filter({ visible: true });
  await expect(informacoes).toContainText("01/02");
  const assinatura = await eu.request.get(`/api/lancamentos/${contaId}/pdf/`);
  expect(assinatura.status()).toBe(200);
  const { url } = await assinatura.json();
  const objeto = await playwright.request.newContext();
  try {
    const download = await objeto.get(url);
    expect(download.status()).toBe(200);
    expect(download.headers()["content-type"]).toContain("application/pdf");
    expect(await download.body()).toEqual(await readFile(path.join(FIXTURES, "boleto-sintetico.pdf")));
    const semAssinatura = new URL(url); semAssinatura.search = "";
    expect((await objeto.get(semAssinatura.toString())).status()).toBe(403);
  } finally { await objeto.dispose(); }
  await expect(page.getByRole("button", { name: "Baixar PDF" })).toBeVisible();
  await abrirPdfReal(page, page.getByRole("button", { name: "Baixar PDF" }));
  await page.screenshot({ path: path.join(SCREENS, `pdf-detalhe-${info.project.name}.png`), fullPage: true });
});

test("rn28/rn29: PDF sem código aceita conferência manual e conserva o arquivo", async ({ page, playwright }, info) => {
  test.setTimeout(90_000);
  const eu = await novaConta(playwright);
  await logar(page, eu);
  const form = await abrir(page);
  await enviar(page, form, "manual-sintetico.pdf");
  await expect(form.getByLabel("Beneficiário", { exact: true })).toHaveValue("Exemplo Manual", { timeout: 40_000 });
  await form.getByLabel("Valor", { exact: true }).fill("42,00");
  await form.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await form.getByLabel("Descrição").fill("PDF manual sintético");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "PDF manual sintético" })).toBeVisible();
  const id = new URL(page.url()).pathname.split("/").pop()!;
  const conta = await (await eu.request.get(`/api/lancamentos/${id}/`)).json();
  expect(conta.instrumento).toMatchObject({ tipo: "manual", codigo: null, beneficiario: "Exemplo Manual" });
  expect(conta.documento_pdf.nome).toBe("manual-sintetico.pdf");
  await page.screenshot({ path: path.join(SCREENS, `pdf-manual-${info.project.name}.png`), fullPage: true });
});

test("rn06/rn27: múltiplos exigem escolha, arquivo inteiro é compartilhado e uploader removido perde acesso", async ({ page, playwright }, info) => {
  test.setTimeout(120_000);
  const [admin, membro, estranho] = await Promise.all([novaConta(playwright), novaConta(playwright), novaConta(playwright)]);
  const grupo = await criarGrupo(admin);
  await entrarNoGrupo(admin, grupo.id, "membro", membro);
  await logar(page, membro);
  await page.context().addCookies([{ name: "espaco", value: grupo.id, url: ORIGIN }]);
  const form = await abrir(page);
  const docId = await enviar(page, form, "multiplos-sintetico.pdf");
  const escolha = form.getByRole("group", { name: "Escolha a linha do boleto" });
  await expect(escolha.getByRole("button", { name: BANCO })).toBeVisible({ timeout: 40_000 });
  await expect(form.getByText(/O arquivo inteiro ficará disponível/)).toBeVisible();
  expect((await estranho.request.get(`/api/boletos/pdfs/${docId}/`)).status()).toBe(404);
  expect((await admin.request.get(`/api/boletos/pdfs/${docId}/arquivo/`)).status()).toBe(404);
  await form.getByLabel("Valor", { exact: true }).fill("42,00");
  await form.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await form.getByLabel("Descrição").fill("PDF com múltiplos códigos");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(escolha.getByRole("alert")).toHaveText("Escolha uma das linhas encontradas no PDF.");
  await escolha.getByRole("button", { name: OUTRO }).click();
  await expect(form.getByText("Boleto bancário conferido. Confira os dados antes de salvar.")).toBeVisible();
  await page.screenshot({ path: path.join(SCREENS, `pdf-multiplos-${info.project.name}.png`), fullPage: true });
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "PDF com múltiplos códigos" })).toBeVisible();
  const contaId = new URL(page.url()).pathname.split("/").pop()!;
  expect((await (await membro.request.get(`/api/lancamentos/${contaId}/`)).json()).instrumento.codigo).toBe(OUTRO);
  expect((await admin.request.get(`/api/boletos/pdfs/${docId}/arquivo/`)).status()).toBe(200);
  const dadosGrupo = await (await admin.request.get(`/api/grupos/${grupo.id}/`)).json();
  const vinculo = dadosGrupo.membros.find((p: { email?: string }) => p.email === membro.email);
  expect(vinculo).toBeTruthy();
  expect((await api(admin.request, "DELETE", `/api/grupos/${grupo.id}/membros/${vinculo.id}/`)).status()).toBe(204);
  for (const rota of [`/api/boletos/pdfs/${docId}/`, `/api/boletos/pdfs/${docId}/arquivo/`, `/api/lancamentos/${contaId}/pdf/`]) {
    expect((await membro.request.get(rota)).status(), rota).toBe(404);
    expect((await estranho.request.get(rota)).status(), rota).toBe(404);
  }
  expect((await admin.request.get(`/api/lancamentos/${contaId}/pdf/`)).status()).toBe(200);
});
