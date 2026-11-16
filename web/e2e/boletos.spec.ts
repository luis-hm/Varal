// Etapa05 RF08/RF09/RF14, RN01/RN08–RN11/RN22. One real account per scenario, both viewports.
import path from "node:path";
import { expect, test } from "@playwright/test";
import { ORIGIN, api, descartarContas, hoje, logar, novaConta, semBadge } from "./fixtures";

// Synthetic bank vector shared with the independently generated parser fixtures: factor1000, R$123,45.
const BANCO = "00191234546789012345767890123457710000000012345";
// Official BCB dynamic BR Code vector. The server parses its location without fetching it.
const PIX = "00020101021226700014br.gov.bcb.pix2548pix.example.com/8b3da2f39a4140d1a91abd93113bd4415204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***630464E4";
const SCREENS = path.join(__dirname, "__screens__");

test.beforeEach(async ({ page }) => page.addInitScript(semBadge));
test.afterEach(descartarContas);

test("rf08/rn09/rf14: corrige código inválido, escolhe data legada, salva boleto e copia os dígitos completos", async ({ page, playwright, context }, info) => {
  test.setTimeout(60_000);
  const eu = await novaConta(playwright);
  await logar(page, eu);
  await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin: ORIGIN });
  await page.goto("/");
  await page.getByRole("button", { name: "Nova conta" }).filter({ visible: true }).click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  await form.getByRole("button", { name: "Colar código", exact: true }).click();
  const entrada = form.getByRole("textbox", { name: "Linha digitável ou Pix copia e cola" });
  // CA13: the full permitted input remains usable with keyboard and does not widen the page.
  await entrada.fill("0".repeat(4096));
  await entrada.focus();
  await page.keyboard.press("Tab");
  const ler = form.getByRole("button", { name: "Ler código" });
  await expect(ler).toBeFocused();
  for (const controle of [entrada, ler]) {
    const caixa = await controle.boundingBox();
    expect(caixa).not.toBeNull();
    expect(caixa!.width).toBeGreaterThanOrEqual(44);
    expect(caixa!.height).toBeGreaterThanOrEqual(44);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await entrada.fill("123.4 inválido");
  await form.getByRole("button", { name: "Ler código" }).click();
  await expect(entrada).toHaveAttribute("aria-invalid", "true");
  await expect(entrada).toHaveValue("123.4 inválido");
  const formatado = `${BANCO.slice(0, 5)}.${BANCO.slice(5, 10)} ${BANCO.slice(10)}`;
  await entrada.fill(formatado);
  await form.getByRole("button", { name: "Ler código" }).click();
  await expect(form.getByText("Boleto bancário conferido. Confira os dados antes de salvar.")).toBeVisible();
  await expect(form.getByLabel("Valor", { exact: true })).toHaveValue("123,45");
  await expect(form.getByLabel("Valor", { exact: true })).toHaveAttribute("readonly", "");
  const vencimento = form.getByRole("combobox", { name: "Vencimento" });
  await expect(vencimento).toHaveValue("2025-02-22");
  await vencimento.selectOption("2000-07-03");
  await form.getByLabel("Descrição").fill("Boleto do ciclo anterior");
  await page.screenshot({ path: path.join(SCREENS, `boleto-conferencia-${info.project.name}.png`), fullPage: true });
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Boleto do ciclo anterior" })).toBeVisible();
  const id = new URL(page.url()).pathname.split("/").pop()!;
  const saved = await api(eu.request, "GET", `/api/lancamentos/${id}/`);
  expect(await saved.json()).toMatchObject({ valor_centavos: 12345, vencimento: "2000-07-03", instrumento: { tipo: "boleto_bancario", codigo: BANCO } });
  await page.getByRole("button", { name: "Copiar código", exact: true }).click();
  await expect(page.getByText("Código copiado.")).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(BANCO);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await page.screenshot({ path: path.join(SCREENS, `boleto-detalhe-${info.project.name}.png`), fullPage: true });
});

test("rf09/rf14/rn22: chave normalizada tem cópia alternativa; trocar por Pix dinâmico pede valor/data sem consultar URL", async ({ page, playwright }, info) => {
  test.setTimeout(60_000);
  const eu = await novaConta(playwright);
  await logar(page, eu);
  await page.addInitScript(() => Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async () => { throw new Error("denied"); } } }));
  const externas: string[] = [];
  page.on("request", (request) => { if (request.url().includes("pix.example.com")) externas.push(request.url()); });
  await page.goto("/");
  await page.getByRole("button", { name: "Nova conta" }).filter({ visible: true }).click();
  const form = page.getByRole("dialog", { name: "Nova conta" });
  await form.getByRole("button", { name: "Chave Pix", exact: true }).click();
  await form.getByLabel("Chave Pix", { exact: true }).fill("CONTAS@VARAL.TEST");
  await form.getByRole("button", { name: "Conferir chave" }).click();
  await expect(form.getByText("Pix conferido. Confira os dados antes de salvar.")).toBeVisible();
  await form.getByLabel("Valor", { exact: true }).fill("42,00");
  await form.getByLabel("Vencimento", { exact: true }).fill(hoje());
  await form.getByLabel("Descrição").fill("Pix para o aluguel");
  await form.getByRole("button", { name: "Salvar conta" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Pix para o aluguel" })).toBeVisible();
  await page.getByRole("button", { name: "Copiar chave Pix" }).click();
  const fallbackChave = page.getByRole("textbox", { name: "Chave Pix para copiar manualmente" });
  await expect(fallbackChave).toHaveValue("contas@varal.test");
  await expect(fallbackChave).toBeFocused();

  await page.getByRole("button", { name: "Editar conta" }).filter({ visible: true }).click();
  const editar = page.getByRole("dialog", { name: "Editar conta" });
  await editar.getByRole("button", { name: "Colar código", exact: true }).click();
  await editar.getByRole("textbox", { name: "Linha digitável ou Pix copia e cola" }).fill(PIX);
  await editar.getByRole("button", { name: "Ler código" }).click();
  await expect(editar.getByText("Pix conferido. Confira os dados antes de salvar.")).toBeVisible();
  await expect(editar.getByLabel("Valor", { exact: true })).toHaveValue("");
  await expect(editar.getByLabel("Vencimento", { exact: true })).toHaveValue("");
  await expect(editar.getByLabel("Beneficiário", { exact: true })).toHaveValue("Fulano de Tal");
  await editar.getByLabel("Valor", { exact: true }).fill("50,00");
  await editar.getByLabel("Vencimento", { exact: true }).fill(hoje(1));
  await editar.getByRole("button", { name: "Salvar", exact: true }).click();
  await expect(editar).toBeHidden();
  await expect(page.getByRole("region", { name: "Pix copia e cola" })).toContainText(PIX);
  await page.getByRole("button", { name: "Copiar código", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Código para copiar manualmente" })).toHaveValue(PIX);
  expect(externas).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  await page.screenshot({ path: path.join(SCREENS, `pix-dinamico-detalhe-${info.project.name}.png`), fullPage: true });
});
