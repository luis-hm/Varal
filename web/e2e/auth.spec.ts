// Etapa 02: RF01–RF03, RN03, RNF01/02/08/09. API and PostgreSQL are real.
import path from "node:path";
import { expect, test } from "@playwright/test";
import { AUTH, ORIGIN, TEST_PASSWORD, createAccount, me, uniqueEmail } from "./fixtures";

const SCREENS = path.join(__dirname, "__screens__");

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => addEventListener("DOMContentLoaded", () => {
    const style = document.createElement("style");
    style.textContent = "nextjs-portal { display: none !important; }";
    document.head.append(style);
  }));
});

test("rf01/rf02 rn03 ca01/ca03/ca09/ca10/ca11: cadastro, sessão persistente, isolamento, saída e nova entrada", async ({ page, context, playwright, request }) => {
  // Raw SSR must not accept edits that controlled inputs could discard at hydration.
  const serverResponse = await request.get("/entrar");
  expect(serverResponse.status()).toBe(200);
  const serverControls = await page.evaluate((html) => {
    const doc = new DOMParser().parseFromString(html, "text/html");
    const form = doc.querySelector<HTMLFormElement>('form[aria-label="Entrar"]');
    const inputs = [...(form?.querySelectorAll<HTMLInputElement>('input:not([type="hidden"])') ?? [])];
    const submit = form?.querySelector<HTMLButtonElement>('button[type="submit"]');
    return { count: inputs.length, inputsDisabled: inputs.every((input) => input.disabled), submitDisabled: submit?.disabled };
  }, await serverResponse.text());
  expect(serverControls).toEqual({ count: 2, inputsDisabled: true, submitDisabled: true });
  await page.goto("/entrar");
  await expect(page.getByLabel("E-mail", { exact: true })).toBeEnabled();
  await expect(page.getByLabel("Senha", { exact: true })).toBeEnabled();
  await expect(page.getByRole("button", { name: "Entrar", exact: true })).toBeEnabled();

  const email = uniqueEmail();
  await page.goto("/criar-conta");
  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page).toHaveURL(`${ORIGIN}/`);
  await expect(page.getByRole("heading", { name: "Início", exact: true })).toBeVisible();

  const first = await me(context.request);
  expect(first.email).toBe(email);
  expect(first.espaco_pessoal).toMatchObject({ tipo: "pessoal", nome: "Pessoal" });
  expect(first.espaco_pessoal.id).toMatch(/^[\da-f-]{36}$/);
  expect(Object.keys(first).sort()).toEqual(["email", "espaco_pessoal", "id", "nome"]);
  const session = (await context.cookies()).find((cookie) => cookie.name === "sessionid");
  expect(session).toMatchObject({ httpOnly: true, sameSite: "Lax" });
  expect(await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }))).toEqual({ local: {}, session: {} });

  await page.reload();
  await expect(page.getByRole("heading", { name: "Início", exact: true })).toBeVisible();
  expect((await me(context.request)).espaco_pessoal.id).toBe(first.espaco_pessoal.id);

  const other = await playwright.request.newContext({ baseURL: ORIGIN });
  try {
    const otherEmail = await createAccount(other);
    const second = await me(other);
    expect(second.email).toBe(otherEmail);
    expect(second.id).not.toBe(first.id);
    expect(second.espaco_pessoal.id).not.toBe(first.espaco_pessoal.id);
    expect(JSON.stringify(first)).not.toContain(otherEmail);
    expect(JSON.stringify(second)).not.toContain(email);
  } finally {
    await other.dispose();
  }

  // Keep a protected page in history to exercise Back after the session is gone.
  await page.goto("/contas");
  await page.goto("/perfil");
  await page.getByRole("button", { name: "Sair da conta", exact: true }).click();
  await expect(page).toHaveURL(`${ORIGIN}/entrar`);
  expect((await context.request.get("/api/me/")).status()).toBe(403);
  await page.goBack();
  await expect(page).toHaveURL(`${ORIGIN}/entrar`);
  await expect(page.getByRole("heading", { name: "Contas", exact: true })).not.toBeVisible();

  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByLabel("Senha", { exact: true }).fill("Senha-errada!83");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("region", { name: "Acesso à conta" }).filter({ visible: true }).getByRole("alert")).toBeVisible();
  expect((await context.request.get("/api/me/")).status()).toBe(403);
  await page.getByLabel("Senha", { exact: true }).fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page).toHaveURL(`${ORIGIN}/`);
  expect((await me(context.request)).espaco_pessoal.id).toBe(first.espaco_pessoal.id);
});

test("rnf02 ca11: proxy bloqueia cadastro sem CSRF e visitante não acessa páginas protegidas", async ({ page, request }) => {
  const response = await request.post(`${AUTH}auth/signup`, {
    data: { email: uniqueEmail(), password: TEST_PASSWORD },
  });
  expect(response.status()).toBe(403);
  for (const route of ["/perfil", "/dev/componentes"]) {
    await page.goto(route);
    await expect(page).toHaveURL(`${ORIGIN}/entrar`);
    await expect(page.getByRole("heading", { name: "Entrar", exact: true })).toBeVisible();
  }
});

test("rf01 ca02: cadastro duplicado orienta sem criar outra identidade; senha fraca tem erro associado", async ({ page, request }) => {
  const email = await createAccount(request);
  // The API request fixture has its own cookie jar; the browser stays anonymous.
  await page.goto("/criar-conta");
  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(TEST_PASSWORD);
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  await expect(page.getByRole("region", { name: "Acesso à conta" }).filter({ visible: true }).getByRole("alert")).toBeVisible();
  await expect(page.getByRole("link", { name: "Entrar", exact: true })).toBeVisible();
  await expect(page).toHaveURL(`${ORIGIN}/criar-conta`);

  await page.getByLabel("E-mail", { exact: true }).filter({ visible: true }).fill(uniqueEmail());
  await page.getByLabel("Senha", { exact: true }).fill("12345678");
  await page.getByRole("button", { name: "Criar conta", exact: true }).click();
  const password = page.getByLabel("Senha", { exact: true });
  await expect(password).toHaveAttribute("aria-invalid", "true");
  await expect(password).toHaveAccessibleDescription(/comum|numéric|númer/i);
});

test("rf03 ca07/ca08: solicitação pública genérica e link inválido permitem recuperar o fluxo", async ({ page }) => {
  await page.goto("/entrar");
  await page.getByRole("link", { name: "Esqueci", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Recuperar senha", exact: true })).toBeVisible();
  // Next keeps the previous form mounted but hidden during client navigation.
  await page.getByLabel("E-mail", { exact: true }).filter({ visible: true }).fill(uniqueEmail());
  await page.getByRole("button", { name: "Enviar link", exact: true }).click();
  await expect(page.getByRole("status")).toHaveText("Se houver uma conta com esse e-mail, você receberá um link para criar uma nova senha.");
  await page.getByRole("link", { name: "Voltar para Entrar", exact: true }).click();
  await expect(page).toHaveURL(`${ORIGIN}/entrar`);
  await page.goto("/recuperar-senha/chave-invalida");
  await expect(page.getByRole("region", { name: "Acesso à conta" }).filter({ visible: true }).getByRole("alert")).toContainText("inválido ou expirou");
  await expect(page.getByRole("button", { name: "Salvar nova senha", exact: true })).not.toBeVisible();
  await page.getByRole("link", { name: "Solicitar novo link", exact: true }).click();
  await expect(page).toHaveURL(`${ORIGIN}/recuperar-senha`);
});

test("ca12: Google indisponível tem retorno acessível sem iniciar o provedor", async ({ page }) => {
  // Presentation-only controlled response. The authenticated flows above use the real API.
  await page.route(`**${AUTH}config`, async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.data.socialaccount.providers = [];
    await route.fulfill({ response, json: body });
  });
  await page.goto("/entrar");
  await page.getByRole("button", { name: "Continuar com Google", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Google está indisponível");
  await expect(page).toHaveURL(`${ORIGIN}/entrar`);
});

test("ca13/ca14 rnf08/rnf09: telas responsivas, alvos de toque e screenshots com movimento reduzido", async ({ page }, info) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  for (const [route, name] of [["/entrar", "entrar"], ["/criar-conta", "criar-conta"], ["/recuperar-senha", "recuperar-senha"]]) {
    await page.goto(route);
    await expect(page.locator("h1")).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    const animations = await page.locator("[role=img], [role=img] > div, section[aria-label='Acesso à conta']").evaluateAll((elements) => elements.map((element) => getComputedStyle(element).animationName));
    expect(animations.every((name) => name === "none")).toBe(true);
    await page.screenshot({ path: path.join(SCREENS, `${name}-${info.project.name}.png`), fullPage: true, caret: "initial" });
  }
  await page.setViewportSize({ width: 360, height: 800 });
  for (const route of ["/entrar", "/criar-conta", "/recuperar-senha"]) {
    await page.goto(route);
    await expect(page.locator("h1")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
    const small = await page.locator("a, button, input:not([type=hidden])").evaluateAll((elements) => elements
      .filter((element) => element.checkVisibility())
      .map((element) => ({ label: element.getAttribute("aria-label") || element.textContent, box: element.getBoundingClientRect() }))
      .filter(({ box }) => box.width < 44 || box.height < 44)
      .map(({ label, box }) => `${label}: ${box.width}×${box.height}`));
    expect(small).toEqual([]);
  }
});
