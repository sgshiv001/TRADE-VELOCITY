import assert from "node:assert/strict";
import { randomBytes, randomUUID } from "node:crypto";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import { chromium, expect, request } from "@playwright/test";

// This check creates a trader and executes orders on the disposable staging database.
const origin = "https://localhost:8443";
const screenshots = process.argv[2];
if (screenshots) await mkdir(screenshots, { recursive: true });

const browser = await chromium.launch();
try {
  const context = await browser.newContext({
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));

  await page.goto(origin);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(/Intelligence behind every trade/i);
  await expect(page.locator("canvas").first()).toBeVisible();
  if (screenshots) await page.screenshot({ path: join(screenshots, "website-desktop.png") });
  await page.locator("#preview-symbol").selectOption("1");
  await page.getByRole("button", { name: "Area", exact: true }).click();
  await expect(page.getByRole("img", { name: /TCS historical price/ })).toBeVisible();
  await page.goto(`${origin}/download`);
  await expect(page.getByRole("heading", { name: "Download TradeVelocity" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Download EXE" })).toHaveAttribute("href", /\/releases\/download\//);

  await page.goto(`${origin}/signup?view=trade&symbol=RELIANCE`);
  const username = `qa_v2_${randomBytes(5).toString("hex")}`;
  const password = randomBytes(18).toString("hex");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await page.getByRole("button", { name: "Skip tutorial" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(/Reliance Industries/);
  await expect(page.getByText("₹10,00,000.00", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "1M", exact: true }).click();
  await expect(page.getByRole("img", { name: /RELIANCE historical price/ })).toBeVisible();
  if (screenshots) await page.screenshot({ path: join(screenshots, "terminal-desktop.png") });

  const identity = await page.request.get(`${origin}/api/auth/status`).then(response => response.json());
  const headers = { "X-Session-ID": identity.trader.workspace_id };
  const quote = await page.request.get(`${origin}/api/quote/RELIANCE`, { headers }).then(response => response.json());
  assert.ok(quote.price > 0 && quote.as_of, "Staging must have a timestamped provider quote");
  const seeded = await page.request.post(`${origin}/api/paper/liquidity/RELIANCE`, {
    headers: { ...headers, Origin: origin, "Idempotency-Key": randomUUID() },
  });
  assert.equal(seeded.status(), 200, "Staging must have a recent reference price for simulated depth");

  for (const side of ["buy", "sell"]) {
    const { book } = await page.request.get(`${origin}/api/paper?symbol=RELIANCE`, { headers }).then(response => response.json());
    const price = (side === "buy" ? book.asks : book.bids)[0].price;
    await page.getByLabel("Order side", { exact: true }).selectOption(side.toUpperCase());
    await page.getByLabel("Shares", { exact: true }).fill("1");
    await page.getByLabel("Limit price", { exact: true }).fill(String(price));
    await page.getByRole("button", { name: `Review ${side}` }).click();
    await page.getByRole("button", { name: "Confirm order" }).click();
    await expect(page.getByText(/1 shares filled · 0 unfilled/)).toBeVisible();
  }
  const wallet = await page.request.get(`${origin}/api/account/portfolio`, { headers }).then(response => response.json());
  assert.equal(wallet.holdings.length, 0);
  assert.notEqual(wallet.cash, "1000000.00");
  const tradeResponse = await page.request.get(`${origin}/api/paper/trades`, { headers }).then(response => response.json());
  assert.equal(tradeResponse.total, 2);

  const native = await playwrightDeviceLogin(context, username, password);
  assert.equal(native.cash, wallet.cash);
  assert.equal(native.available_cash, wallet.available_cash);

  await page.getByRole("button", { name: "Explore markets", exact: true }).click();
  await page.getByLabel("Filter stocks").fill("tcs");
  await page.getByRole("button", { name: "Watch TCS" }).click();
  await expect(page.getByRole("button", { name: "Remove TCS" })).toBeVisible();

  await page.keyboard.press("Control+k");
  const search = page.getByRole("dialog", { name: "Find a stock or page" });
  await search.getByLabel("Search query").fill("tcs");
  await search.getByRole("button", { name: /TCS Tata/ }).click();
  await page.getByRole("button", { name: "AI Analyst", exact: true }).click();
  await expect(page.getByRole("heading", { name: /Tata Consultancy/ })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "AI Assistant", exact: true }).click();
  await page.getByRole("button", { name: "Ask assistant" }).click();
  await expect(page.getByRole("heading", { name: "Explain this signal" })).toBeVisible();

  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await page.getByRole("combobox", { name: /^Theme/ }).selectOption("light");
  await expect(page.locator(".tv2-app")).toHaveAttribute("data-tv-theme", "light");
  const mobile = await context.newPage();
  await mobile.setViewportSize({ width: 390, height: 844 });
  await mobile.goto(`${origin}/app?view=markets`);
  await expect(mobile.locator(".tv2-table tbody tr").first()).toBeVisible();
  assert.ok(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
  if (screenshots) await mobile.screenshot({ path: join(screenshots, "markets-mobile.png") });
  await mobile.getByRole("button", { name: "Open navigation" }).click();
  await mobile.getByRole("button", { name: "Portfolio", exact: true }).click();
  await expect(mobile.getByRole("heading", { name: "Portfolio", exact: true })).toBeVisible();
  assert.equal((await page.request.get(`${origin}/api/admin/activity`, { headers })).status(), 403);
  assert.deepEqual(errors, []);
  console.log("V2 staging passed web signup, cross-client balances, trading, watchlists, Analyst, themes and mobile navigation.");
} finally {
  await browser.close();
}

async function playwrightDeviceLogin(context, username, password) {
  const device = await request.newContext({ ignoreHTTPSErrors: true });
  try {
    const login = await device.post(`${origin}/api/auth/device/login`, { data: { username, password } });
    assert.ok(login.ok());
    const { token } = await login.json();
    const identity = await context.request.get(`${origin}/api/auth/status`).then(response => response.json());
    const response = await device.get(`${origin}/api/account/portfolio`, {
      headers: { Authorization: `Bearer ${token}`, "X-Session-ID": identity.trader.workspace_id },
    });
    assert.ok(response.ok());
    const wallet = await response.json();
    return wallet;
  } finally {
    await device.dispose();
  }
}
