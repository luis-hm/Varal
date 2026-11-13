import { expect, me, test } from "./fixtures";

test("etapa01 ca16: produção devolve HTTP 404 real para a vitrine mesmo com sessão válida", async ({ page }) => {
  // A signed-in user reaches the app API; a login redirect must not mask this check.
  await me(page.request);
  const response = await page.goto("/dev/componentes");
  expect(response?.status()).toBe(404);
  await expect(page.getByRole("heading", { name: "404", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Componentes", exact: true })).toHaveCount(0);
});
