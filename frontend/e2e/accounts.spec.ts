import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

test.skip(!process.env.TRADEVELOCITY_ACCOUNTS_E2E, "Requires a dedicated HTTPS accounts test server");
test.use({ignoreHTTPSErrors: process.env.TRADEVELOCITY_E2E_ALLOW_SELF_SIGNED === "1"});

test("register, skip and reopen the tutorial, then sign back into the saved workspace", async ({page}) => {
  const username = "trader_" + randomUUID().replaceAll("-", "").slice(0, 15);
  const password = "Browser-test-only password";
  await page.goto("/login");
  await page.getByRole("link", {name: "Create an account"}).click();
  await expect(page).toHaveURL(/\/signup$/);
  await expect(page.getByRole("heading", {name: "Create your account"})).toBeVisible();
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", {name: "Create account"}).click();

  const guide = page.getByRole("dialog");
  await expect(guide.getByRole("heading", {name: "Read your order book"})).toBeVisible();
  await guide.getByRole("button", {name: "Next"}).click();
  await expect(guide.getByRole("heading", {name: "Try a partial fill"})).toBeVisible();
  const saved = page.waitForResponse(response => response.url().endsWith("/api/auth/tutorial") && response.ok());
  await guide.getByRole("button", {name: "Skip tutorial"}).click();
  await saved;
  await expect(guide).toBeHidden();
  await expect(page.getByRole("heading", {name: "Orders & depth"})).toBeVisible();
  await page.getByRole("combobox", {name: "Side", exact: true}).selectOption("SELL");
  await page.getByRole("spinbutton", {name: "Shares", exact: true}).fill("5");
  await page.getByRole("spinbutton", {name: "Limit price", exact: true}).fill("100");
  await page.getByRole("button", {name: "Submit sell"}).click();
  await expect(page.getByRole("heading", {name: "Active orders · 1"})).toBeVisible();

  await page.getByRole("button", {name: "Sign out"}).click();
  await expect(page.getByRole("heading", {name: "Sign in"})).toBeVisible();
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Workspace overview"})).toBeVisible();
  await expect(page.getByText("LIVE WORKSPACE UPDATES", {exact: true})).toBeVisible();
  await expect(guide).toBeHidden();
  await page.getByRole("button", {name: "Orders & depth", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Active orders · 1"})).toBeVisible();
  await page.getByRole("button", {name: "Open tutorial"}).click();
  await expect(guide).toBeVisible();
  await guide.getByRole("button", {name: "Next"}).click();
  await guide.getByRole("button", {name: "Next"}).click();
  await guide.getByRole("button", {name: "Finish tutorial"}).click();
  await expect(guide).toBeHidden();
});
