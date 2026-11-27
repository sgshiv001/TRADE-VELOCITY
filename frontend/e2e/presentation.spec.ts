import { expect, test } from "@playwright/test";

test("presentation demo shows FIFO fills and resets its synthetic book", async ({page}) => {
  test.skip(!process.env.TRADEVELOCITY_WEB_DIR, "Requires the Next.js presentation workspace");
  await page.setViewportSize({width: 540, height: 840});
  await page.goto("/app?offlineDemo=1&view=demo");
  await expect(page.getByRole("heading", {name: "Price–time priority"})).toBeVisible();
  const symbol = await page.getByText(/DEMO[A-F0-9]{8} · Synthetic instrument/).textContent();

  await page.getByRole("button", {name: "Place Buy 1 · 10 @ ₹100"}).click();
  await expect(page.getByRole("table", {name: "Demo bids"})).toContainText("10");
  await page.getByRole("button", {name: "Place Buy 2 · 10 @ ₹100"}).click();
  await expect(page.getByRole("table", {name: "Demo bids"})).toContainText("20");
  await page.getByRole("button", {name: "Place Sell · 15 @ ₹100"}).click();
  const fills = page.getByRole("table", {name: "Demo executions"}).getByRole("row");
  await expect(fills).toHaveCount(3);
  await expect(fills.nth(1).getByRole("cell").allTextContents()).resolves.toEqual(["Buy 1", "10", "₹100.00"]);
  await expect(fills.nth(2).getByRole("cell").allTextContents()).resolves.toEqual(["Buy 2", "5", "₹100.00"]);
  const results = page.getByRole("table", {name: "Demo order results"}).getByRole("row");
  await expect(results.nth(1).getByRole("cell").allTextContents()).resolves.toEqual(["Buy 1", "10", "10", "0"]);
  await expect(results.nth(2).getByRole("cell").allTextContents()).resolves.toEqual(["Buy 2", "10", "5", "5"]);
  await expect(page.getByRole("table", {name: "Demo bids"}).getByRole("row").nth(1).getByRole("cell").allTextContents())
    .resolves.toEqual(["₹100.00", "5", "1"]);

  await page.getByRole("button", {name: "Reset demo"}).click();
  await expect(page.getByText("No resting bids.")).toBeVisible();
  await expect(page.getByText("No executions yet.")).toBeVisible();
  await expect(page.getByText(/DEMO[A-F0-9]{8} · Synthetic instrument/)).not.toHaveText(symbol!);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
