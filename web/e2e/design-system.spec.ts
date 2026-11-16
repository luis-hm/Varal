// Etapa 01 (design system): CA02, CA12, CA13 (RNF08), CA14 screenshots, CA15, CA18.
// Runs in both projects of playwright.config.ts: mobile 390×844 and desktop 1440×900.
// Next 16 keeps visited routes mounted but hidden, hence the `visible` filters.
import path from "node:path";
import type { Page } from "@playwright/test";
import { expect, test } from "./fixtures";

const VITRINE = "/dev/componentes";
const SCREENS = path.join(__dirname, "__screens__");

const paginas = [
  { href: "/", titulo: "Início" },
  { href: "/contas", titulo: "Contas" },
  { href: "/grupos", titulo: "Grupos" },
  { href: "/avisos", titulo: "Avisos" },
  { href: "/perfil", titulo: "Perfil" },
];

// The showcase also renders TabBar/SideNav samples inside <main>; the shell's own ones live outside it.
const shellSideNav = (page: Page) => page.locator("xpath=//aside[@aria-label='Menu principal'][not(ancestor::main)]");
const shellTabBar = (page: Page) => page.locator("xpath=//nav[@aria-label='Navegação principal'][not(ancestor::main)]");

// The Next dev-tools badge (dev server only) sits over the first TabBar item and would show in screenshots.
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() =>
    addEventListener("DOMContentLoaded", () => {
      const style = document.createElement("style");
      style.textContent = "nextjs-portal { display: none !important; }";
      document.head.append(style);
    }),
  );
});

test("ca02: Bricolage Grotesque e Inter servidas pelo app, sem requisição ao Google", async ({ page }) => {
  const externas: string[] = [];
  const fontesLocais: string[] = [];
  page.on("request", (req) => {
    const url = new URL(req.url());
    if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) externas.push(req.url());
    if (req.resourceType() === "font" && url.origin === "http://localhost:3000") fontesLocais.push(req.url());
  });

  await page.goto(VITRINE);
  await page.evaluate(() => document.fonts.ready);

  const titulo = await page.locator("h1").first().evaluate((el) => getComputedStyle(el).fontFamily);
  const texto = await page.locator("body").evaluate((el) => getComputedStyle(el).fontFamily);
  expect(titulo).toMatch(/^['"]?Bricolage Grotesque/);
  expect(texto).toMatch(/^['"]?Inter/);

  const carregadas = await page.evaluate(() =>
    [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family.replace(/['"]/g, "")),
  );
  expect(carregadas).toEqual(expect.arrayContaining(["Bricolage Grotesque", "Inter"]));
  expect(fontesLocais.length).toBeGreaterThan(0);
  expect(externas).toEqual([]);
});

test("ca12: TabBar abaixo de 1024px, SideNav fixo de 264px a partir de 1024px", async ({ page }, info) => {
  await page.goto(VITRINE);
  const side = shellSideNav(page);
  const tab = shellTabBar(page);

  if (info.project.name === "mobile") {
    await expect(tab).toBeVisible();
    await expect(side).toBeHidden();
    return;
  }

  await expect(side).toBeVisible();
  await expect(tab).toBeHidden();
  const box = await side.boundingBox();
  expect(box).toMatchObject({ x: 0, y: 0, width: 264 });
  // Fixed: still pinned to the top-left after scrolling the (long) showcase.
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
  expect(await side.boundingBox()).toMatchObject({ x: 0, y: 0, width: 264 });
});

test("ca05/d1: Button renderizado com 52px em todos os tons; width full ocupa o pai", async ({ page }) => {
  await page.goto(VITRINE);
  const alturas = await page
    .locator("main button[data-tone]")
    .evaluateAll((els) => els.map((el) => el.getBoundingClientRect().height));
  expect(alturas.length).toBeGreaterThanOrEqual(7);
  expect(new Set(alturas)).toEqual(new Set([52]));

  const [botao, conteudoDoPai] = await page.getByRole("button", { name: "Entrar" }).evaluate((el) => {
    const pai = getComputedStyle(el.parentElement!);
    const largura = el.parentElement!.clientWidth - parseFloat(pai.paddingLeft) - parseFloat(pai.paddingRight);
    return [el.getBoundingClientRect().width, largura];
  });
  expect(botao).toBeCloseTo(conteudoDoPai, 0);
});

test.describe("360px", () => {
  test.use({ viewport: { width: 360, height: 800 } });

  for (const url of [VITRINE, ...paginas.map((p) => p.href)]) {
    test(`rnf08 ca13: ${url} sem rolagem horizontal e alvos ≥ 44px em 360px`, async ({ page }) => {
      await page.goto(url);
      await expect(page.getByRole("heading", { level: 1 }).filter({ visible: true }).first()).toBeVisible();

      const { scrollWidth, clientWidth } = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth);

      const pequenos = await page.locator("a, button").evaluateAll((els) =>
        els
          .filter((el) => el.checkVisibility())
          .map((el) => ({ el: el.outerHTML.slice(0, 80), r: el.getBoundingClientRect() }))
          .filter(({ r }) => r.width < 44 || r.height < 44)
          .map(({ el, r }) => `${Math.round(r.width)}×${Math.round(r.height)} ${el}`),
      );
      expect(pequenos).toEqual([]);
    });
  }
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("ca15: selo Vencida não pulsa e botão não encolhe ao pressionar", async ({ page }) => {
    await page.goto(VITRINE);

    const icone = page.locator('main [data-status="vencida"] svg').first();
    await expect(icone).toBeVisible();
    expect(await icone.evaluate((el) => getComputedStyle(el).animationName)).toBe("none");

    const botao = page.getByRole("button", { name: "Entrar" });
    await botao.scrollIntoViewIfNeeded();
    await botao.hover();
    await page.mouse.down();
    expect(await botao.evaluate((el) => getComputedStyle(el).transform)).toBe("none");
    await page.mouse.up();
  });
});

// Control for ca15: without the preference the same checks do see the motion (the test can fail).
test("ca15 (controle): sem reduced motion o selo pulsa e o botão encolhe", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.goto(VITRINE);

  const icone = page.locator('main [data-status="vencida"] svg').first();
  expect(await icone.evaluate((el) => getComputedStyle(el).animationName)).toContain("badge-pulse");

  const botao = page.getByRole("button", { name: "Entrar" });
  await botao.scrollIntoViewIfNeeded();
  await botao.hover();
  await page.mouse.down();
  await expect.poll(() => botao.evaluate((el) => getComputedStyle(el).transform)).not.toBe("none");
  await page.mouse.up();
});

test("ca18: navegação entre as seções com um único item ativo", async ({ page }, info) => {
  const mobile = info.project.name === "mobile";
  const menu = mobile
    ? page.getByRole("navigation", { name: "Navegação principal" })
    : page.getByRole("complementary", { name: "Menu principal" });
  // TabBar has no Avisos item; SideNav has all five.
  const roteiro = mobile ? paginas.filter((p) => p.href !== "/avisos") : paginas;

  await page.goto("/perfil");
  for (const { href, titulo } of [...roteiro.slice(1), roteiro[0]]) {
    if (href === "/avisos" && !mobile) {
      const anterior = page.url();
      const ativoAnterior = await page.locator('[aria-current="page"]:visible').getAttribute("href");
      await menu.getByRole("link", { name: titulo, exact: true }).click();
      const gaveta = page.getByRole("dialog", { name: "Avisos" });
      await expect(gaveta).toBeVisible();
      await expect(gaveta.getByRole("button", { name: "Marcar todos como lidos" })).toBeVisible();
      expect(page.url()).toBe(anterior);
      await page.keyboard.press("Escape");
      await expect(gaveta).toBeHidden();
      await expect(page.locator('[aria-current="page"]:visible')).toHaveAttribute("href", ativoAnterior!);
      continue;
    }
    await menu.getByRole("link", { name: titulo, exact: true }).click();
    await expect(page).toHaveURL(href);
    // Etapa 04: Início greets by name (D02); Contas and Grupos are real screens.
    if (href !== "/") await expect(page.getByRole("heading", { level: 1 })).toHaveText(titulo);
    if (href === "/perfil") await expect(page.getByText("Em breve", { exact: true }).filter({ visible: true })).toBeVisible();

    const ativos = page.locator('[aria-current="page"]:visible');
    await expect(ativos).toHaveCount(1);
    await expect(ativos).toHaveAttribute("href", href);
    await expect(ativos).toContainText(titulo);
  }

  if (mobile) {
    await page.goto("/avisos");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText("Avisos");
    await expect(page.getByRole("button", { name: "Marcar todos como lidos" }).filter({ visible: true })).toBeVisible();
    await expect(page.locator('[aria-current="page"]:visible')).toHaveCount(0);
  }
});

test("ca14: screenshots da vitrine e da central de avisos", async ({ page }, info) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto(VITRINE);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(SCREENS, `vitrine-${info.project.name}.png`), fullPage: true, caret: "initial" });

  await page.goto("/avisos");
  await expect(page.getByRole("heading", { name: "Avisos", level: 1 }).filter({ visible: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Marcar todos como lidos" }).filter({ visible: true })).toBeVisible();
  await page.screenshot({ path: path.join(SCREENS, `avisos-central-${info.project.name}.png`), caret: "initial", animations: "disabled" });
});
