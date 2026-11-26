import { expect, test } from "@playwright/test";

test("intraday quote chart follows provider timestamps and keeps daily history available", async ({page}) => {
  test.skip(!process.env.TRADEVELOCITY_WEB_DIR, "Requires the Next.js trading terminal");
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.setViewportSize({width: 390, height: 844});
  await page.clock.install();
  await page.route("**/api/auth/status", route => route.fulfill({json: {
    required: true, mode: "accounts", authenticated: true,
    trader: {username: "chart-test", workspace_id: "charts-test", tutorial_seen: true},
  }}));
  await page.route("**/api/paper/liquidity/**", route => route.fulfill({json: {updated: false}}));
  let observed = {price: 100, as_of: "2026-11-26T09:15:00+05:30", kind: "intraday"};
  await page.route("**/api/quote/*", route => route.fulfill({json: {
    ...observed, symbol: new URL(route.request().url()).pathname.split("/").at(-1), source: "Test quotes", simulation_supported: true,
  }}));

  await page.goto("/app?view=trade&symbol=RELIANCE");
  const chart = page.locator(".tv2-terminal-chart");
  const daily = chart.getByRole("img", {name: "RELIANCE historical price and volume chart"});
  await expect(daily.locator("canvas").first()).toBeVisible();
  for (const mode of ["bars", "line", "area", "baseline", "candles"]) {
    await chart.getByLabel("Chart style").selectOption(mode);
    await expect(daily.locator("canvas").first()).toBeVisible();
  }
  await chart.getByRole("button", {name: "1Y", exact: true}).click();
  await chart.getByLabel("Volume", {exact: true}).uncheck();
  await chart.getByLabel("SMA 20").check();
  await expect(daily.locator("canvas").first()).toBeVisible();

  await chart.getByRole("button", {name: "Intraday quotes"}).click();
  await expect(chart.getByRole("img", {name: "RELIANCE intraday quote chart"}).locator("canvas").first()).toBeVisible();
  await expect(chart).toContainText("1 observation this session");
  const latest = chart.getByLabel("RELIANCE latest chart observation");
  observed = {...observed, price: 104, as_of: "2026-11-26T09:16:00+05:30"};
  await page.clock.fastForward(61_000);
  await expect(latest).toContainText("09:16 IST");
  await expect(latest.locator(".tv2-up")).toHaveText("+4%");

  observed = {...observed, price: 97, as_of: "2026-11-26T09:17:00+05:30"};
  const refresh = chart.getByRole("button", {name: "Refresh quote"});
  await refresh.click();
  await expect(latest.locator(".tv2-down")).toHaveText("-3%");
  await expect(chart).toContainText("3 observations this session");
  observed = {...observed, price: 105, as_of: "2026-11-26T09:14:00+05:30"};
  await refresh.click();
  await expect(latest).toContainText("09:17 IST");
  await expect(chart).toContainText("3 observations this session");
  for (const mode of ["line", "area", "baseline"]) await chart.getByLabel("Chart style").selectOption(mode);

  await page.getByRole("combobox", {name: "Select symbol", exact: true}).selectOption("TCS");
  await chart.getByRole("button", {name: "Intraday quotes"}).click();
  await expect(chart.getByRole("img", {name: "TCS intraday quote chart"})).toBeVisible();
  await expect(chart).toContainText("1 observation this session");
  await expect(chart.getByRole("link", {name: /Open TCS on TradingView/})).toHaveAttribute("href", /symbol=NSE%3ATCS$/);
  expect(errors).toEqual([]);
});
