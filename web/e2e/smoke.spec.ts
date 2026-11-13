import { expect, test } from "@playwright/test";

test("smoke: vitrine abre", async ({ page }) => {
  await page.goto("/dev/componentes");
  await expect(page.locator("body")).toBeVisible();
});
