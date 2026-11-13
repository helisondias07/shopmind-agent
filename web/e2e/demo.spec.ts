import { expect, test } from "@playwright/test";

test("storefront answers from the catalog and shows the graph", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("product-name").filter({ hasText: "Luminária Lume" })).toBeVisible();
  if (await page.getByTestId("tab-chat").isVisible()) {
    await page.getByTestId("tab-chat").click();
  }
  await page.getByTestId("chat-input").fill("Quanto custa a luminária Lume?");
  await page.getByTestId("chat-send").click();
  await expect(page.getByTestId("assistant-reply")).toContainText("289,00");
  await expect(page.getByTestId("source-chip").first()).toBeVisible();
  if (await page.getByTestId("tab-trace").isVisible()) {
    await page.getByTestId("tab-trace").click();
  }
  await expect(page.getByTestId("trace-node").filter({ hasText: "classify_intent" })).toBeVisible();
  await expect(page.getByTestId("trace-intent")).toHaveText("product");
});

test("language switch reloads the catalog in English", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("locale-en").click();
  await expect(page.getByTestId("product-name").filter({ hasText: "Lume Desk Lamp" })).toBeVisible();
});

test("eval report is all green", async ({ page }) => {
  await page.goto("/evals");
  await expect(page.getByTestId("eval-summary")).toContainText("17/17");
  await expect(page.getByTestId("eval-case").filter({ hasText: "lamp-price" })).toContainText(/passou|passed/);
});
