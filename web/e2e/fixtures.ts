import { randomUUID } from "node:crypto";
import { expect, test as base, type APIRequestContext, type Browser, type Page, type PlaywrightWorkerArgs } from "@playwright/test";
import type { components } from "../src/types/api";

export const ORIGIN = "http://localhost:3000";
export const AUTH = "/api/auth/browser/v1/";
// Public, disposable development accounts. No personal credentials are used by this suite.
export const TEST_PASSWORD = "Varal-e2e!93-Linha";
export const uniqueEmail = () => `e2e-${randomUUID()}@varal.test`;
type StorageState = Awaited<ReturnType<APIRequestContext["storageState"]>>;

export async function csrf(request: APIRequestContext) {
  const response = await request.get(`${AUTH}config`);
  expect(response.status()).toBe(200);
  const state = await request.storageState();
  const token = state.cookies.find((cookie) => cookie.name === "csrftoken")?.value;
  expect(token, "GET config must bootstrap the browser CSRF cookie").toBeTruthy();
  return token!;
}

export async function createAccount(request: APIRequestContext, email = uniqueEmail()) {
  // `make e2e`/CI raise allauth's signup limit (ACCOUNT_RATE_LIMIT_SIGNUP): every client is 127.0.0.1.
  const response = await request.post(`${AUTH}auth/signup`, {
    headers: { Origin: ORIGIN, "X-CSRFToken": await csrf(request) },
    data: { email, password: TEST_PASSWORD },
  });
  expect(response.status(), await response.text()).toBe(200);
  return email;
}

export async function me(request: APIRequestContext) {
  const response = await request.get("/api/me/");
  expect(response.status()).toBe(200);
  return (await response.json()) as components["schemas"]["Me"];
}

// The design-system suite needs a real server session. Create one per worker,
// then copy its cookies into isolated browser contexts; those tests never log out.
export const test = base.extend<object, { signedInState: StorageState }>({
  signedInState: [async ({ playwright }, provide) => {
    const request = await playwright.request.newContext({ baseURL: ORIGIN });
    try {
      await createAccount(request);
      await provide(await request.storageState());
    } finally {
      await request.dispose();
    }
  }, { scope: "worker" }],
  storageState: async ({ signedInState }, provide) => provide(signedInState),
});

export { expect };

// ---- Shared by grupos.spec.ts and contas.spec.ts: real API users, groups and browser sessions. ----

export type Papel = "admin" | "membro" | "pagador" | "observador";
export type Conta = { request: APIRequestContext; email: string };

/** The Next dev-tools badge (dev server only) would cover the first TabBar item and show in screenshots. */
export const semBadge = () =>
  addEventListener("DOMContentLoaded", () => {
    const style = document.createElement("style");
    style.textContent = "nextjs-portal { display: none !important; }";
    document.head.append(style);
  });

const abertas: APIRequestContext[] = [];
/** Call in afterEach: disposes the API contexts opened by `novaConta`. */
export const descartarContas = () => Promise.all(abertas.splice(0).map((r) => r.dispose()));

export async function novaConta(playwright: PlaywrightWorkerArgs["playwright"]): Promise<Conta> {
  const request = await playwright.request.newContext({ baseURL: ORIGIN });
  abertas.push(request);
  return { request, email: await createAccount(request) };
}

export async function api(request: APIRequestContext, method: string, url: string, data?: unknown) {
  return request.fetch(url, { method, headers: { Origin: ORIGIN, "X-CSRFToken": await csrf(request) }, data });
}

export async function criarGrupo(admin: Conta, casas = ["Casa da praia"]) {
  const response = await api(admin.request, "POST", "/api/grupos/", { nome: `Família ${randomUUID().slice(0, 6)}`, casas });
  expect(response.status(), await response.text()).toBe(201);
  return (await response.json()) as { id: string; nome: string };
}

export async function convidar(admin: Conta, grupo: string, papel: Papel) {
  const response = await api(admin.request, "POST", `/api/grupos/${grupo}/convites/`, { papel });
  expect(response.status()).toBe(201);
  return ((await response.json()) as { url: string }).url;
}

export async function entrarNoGrupo(admin: Conta, grupo: string, papel: Papel, pessoa: Conta) {
  const token = (await convidar(admin, grupo, papel)).split("/c/")[1];
  expect((await api(pessoa.request, "POST", `/api/convites/${token}/aceitar/`)).status()).toBe(201);
}

/** Copies the API session into the browser page. */
export async function logar(page: Page, conta: Conta) {
  await page.context().addCookies((await conta.request.storageState()).cookies);
}

/** Another browser (same viewport), signed in as `conta` or anonymous. */
export async function outraAba(browser: Browser, page: Page, conta?: Conta) {
  const context = await browser.newContext({
    baseURL: ORIGIN,
    viewport: page.viewportSize(),
    storageState: conta ? await conta.request.storageState() : undefined,
  });
  await context.addInitScript(semBadge);
  const nova = await context.newPage();
  nova.on("dialog", (d) => d.accept());
  return nova;
}

export async function semRolagemEAlvos44(page: Page) {
  // Measure the settled layout: modal-pop scales targets to .96 while it runs.
  await page.evaluate(() =>
    Promise.all(
      document
        .getAnimations()
        .filter((a) => a.effect?.getComputedTiming().endTime !== Infinity)
        .map((a) => a.finished.catch(() => undefined)),
    ),
  );
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  const pequenos = await page.locator("a, button, input:not([type=hidden])").evaluateAll((els) =>
    els
      .filter((el) => el.checkVisibility())
      .map((el) => ({ el: el.outerHTML.slice(0, 80), r: el.getBoundingClientRect() }))
      .filter(({ r }) => r.width < 44 || r.height < 44)
      .map(({ el, r }) => `${Math.round(r.width)}×${Math.round(r.height)} ${el}`),
  );
  expect(pequenos).toEqual([]);
}

const FUSO = "America/Fortaleza";
/** Today in Fortaleza (RNF11) as "AAAA-MM-DD", plus `dias`. */
export function hoje(dias = 0) {
  const [a, m, d] = new Intl.DateTimeFormat("en-CA", { timeZone: FUSO }).format(new Date()).split("-").map(Number);
  return new Date(Date.UTC(a, m - 1, d + dias)).toISOString().slice(0, 10);
}
/** Current month's name in Fortaleza, as the screens label month numbers (Q9): "novembro". */
export const mesAtual = () => new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, month: "long" }).format(new Date());
