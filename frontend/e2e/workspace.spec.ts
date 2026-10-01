import { test, expect, type Page, type APIRequestContext } from "@playwright/test";
import { readFile } from "node:fs/promises";

async function open(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", {name: "Workspace overview"})).toBeVisible();
  await expect(page.getByText("LIVE WORKSPACE UPDATES", {exact:true})).toBeVisible();
  return (await page.evaluate(() => localStorage.getItem("marketlab-session")))!;
}

async function state(request: APIRequestContext, id: string) {
  const response = await request.get("/api/lab", {headers: {"X-Session-ID": id}});
  expect(response.ok()).toBeTruthy();
  return response.json();
}

async function submit(page: Page, side: "BUY" | "SELL", quantity: number, price: string) {
  await page.getByRole("combobox", {name:"Side", exact:true}).selectOption(side);
  await page.getByRole("spinbutton", {name:"Shares", exact:true}).fill(String(quantity));
  await page.getByRole("spinbutton", {name:"Limit price", exact:true}).fill(price);
  await page.getByRole("button", {name:`Submit ${side.toLowerCase()}`, exact:true}).click();
}

test("order lifecycle, live second tab, export, import and timestamp preservation", async ({page, context, request}) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  const id = await open(page);
  const mirror = await context.newPage(); await open(mirror);
  await page.getByRole("button", {name:"Orders & depth", exact:true}).click();
  await submit(page, "SELL", 5, "100");
  await expect(page.getByRole("status").filter({hasText:"0 shares filled"})).toBeVisible();
  await expect(mirror.locator(".metric-card").filter({hasText:"Active orders"}).locator(".metric-value")).toHaveText("1", {timeout:4000});
  await submit(page, "BUY", 3, "100");
  await expect(page.getByRole("status").filter({hasText:"3 shares filled"})).toBeVisible();
  await page.getByRole("button", {name:"Amend", exact:true}).click();
  await page.getByLabel("New remaining shares").fill("4"); await page.getByLabel("New limit price").fill("101");
  await page.getByRole("button", {name:"Save amendment", exact:true}).click();
  await expect(page.getByRole("status").filter({hasText:"Amended"})).toBeVisible();
  await page.getByRole("button", {name:"Cancel order", exact:true}).click();
  await expect(page.getByText("No active orders for this symbol.", {exact:true})).toBeVisible();
  const original = await state(request,id);
  expect(original.stats.volume).toBe(3); expect(original.total_trades).toBe(1);
  expect(original.trades[0].timestamp).toBeTruthy();
  await page.getByRole("button", {name:"Trade history", exact:true}).click();
  await page.getByLabel("Search trades").fill(original.trades[0].buy_order_id);
  await expect(page.getByText("1–1 of 1 trades", {exact:true})).toBeVisible();
  const csvPromise = page.waitForEvent("download"); await page.getByRole("button", {name:"Export all trades"}).click();
  const csv = await csvPromise;
  expect(await readFile((await csv.path())!, "utf8")).toContain(original.trades[0].timestamp);
  const jsonPromise = page.waitForEvent("download"); await page.getByRole("button", {name:"Export session", exact:true}).click();
  const exported = await jsonPromise;
  const payload = JSON.parse(await readFile((await exported.path())!, "utf8")); expect(payload.version).toBe(2);
  await page.getByRole("button", {name:"Clear session", exact:true}).click();
  await page.getByRole("button", {name:"Keep session", exact:true}).click();
  await page.reload(); await expect(page.getByRole("heading", {name:"Workspace overview"})).toBeVisible();
  expect((await state(request,id)).trades[0].timestamp).toBe(original.trades[0].timestamp);
  await page.getByRole("button", {name:"Trade history", exact:true}).click();
  await page.getByRole("button", {name:"Clear session", exact:true}).click();
  await page.getByRole("button", {name:"Confirm clear session"}).click();
  await expect(page.getByText("Matching session cleared.", {exact:true})).toBeVisible();
  await page.getByLabel("Import session file").setInputFiles({name:"session.json", mimeType:"application/json",buffer:Buffer.from(JSON.stringify(payload))});
  await page.getByRole("button", {name:"Replace and import"}).click();
  await expect(page.getByText("Session imported and replayed by the engine.", {exact:true})).toBeVisible();
  const imported = await state(request,id);
  expect(imported.trades).toEqual(original.trades); expect(imported.stats.volume).toBe(3);
  expect(errors).toEqual([]);
});

test("themes, dark dropdowns, watchlist and adjusted chart controls", async ({page}, testInfo) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  await open(page);
  await page.getByRole("button", {name:"Add RELIANCE to watchlist"}).click();
  await page.getByRole("button", {name:"Switch to dark mode"}).click();
  await page.reload(); await expect(page.getByRole("heading", {name:"Workspace overview"})).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("button", {name:"Remove RELIANCE from watchlist"})).toBeVisible();
  const colors = await page.getByLabel("Select symbol").locator("option").first().evaluate(option => ({background:getComputedStyle(option).backgroundColor, color:getComputedStyle(option).color}));
  expect(colors.background).not.toBe("rgb(255, 255, 255)"); expect(colors.background).not.toBe(colors.color);
  await page.getByRole("button", {name:"Market history", exact:true}).click();
  await expect(page.getByRole("img", {name:/adjusted candlestick chart/})).toBeVisible();
  await page.getByLabel("Chart zoom").selectOption("30");
  await expect(page.getByRole("img", {name:/30 trading days/})).toBeVisible();
  await page.getByRole("button", {name:"Earlier", exact:true}).click();
  await page.getByRole("button", {name:"Later", exact:true}).click();
  await page.getByLabel("Chart style").selectOption("line");
  await expect(page.getByRole("img", {name:/adjusted closing line chart/})).toBeVisible();
  await expect(page.locator(".panel").first()).toHaveCSS("background-color", "rgb(32, 43, 61)");
  await page.screenshot({path:testInfo.outputPath("dark-market.png"),fullPage:true,animations:"disabled"});
  await page.getByRole("button", {name:"Switch to light mode"}).click();
  await expect(page.locator(".panel").first()).toHaveCSS("background-color", "rgb(255, 255, 255)");
  await page.screenshot({path:testInfo.outputPath("light-market.png"),fullPage:true,animations:"disabled"});
  expect(errors).toEqual([]);
});

test("dropped committed order response retries without duplicate execution", async ({page, request}) => {
  const id = await open(page);
  await page.getByRole("button", {name:"Orders & depth", exact:true}).click();
  let dropped = false; const keys: string[] = [];
  await page.route("**/api/lab/orders", async route => {
    keys.push(route.request().headers()["idempotency-key"]);
    if (!dropped) { dropped = true; const committed = await route.fetch(); expect(committed.status()).toBe(200); await route.abort("failed"); }
    else await route.continue();
  });
  await submit(page,"SELL",2,"100");
  await expect(page.getByRole("status").filter({hasText:"0 shares filled"})).toBeVisible();
  expect(keys).toHaveLength(2); expect(keys[0]).toBeTruthy(); expect(keys[0]).toBe(keys[1]);
  const result = await state(request,id);
  expect(result.events).toBe(1); expect(result.orders).toHaveLength(1); expect(result.orders[0].remaining).toBe(2);
});

test("AI review status and investigation notes survive browser reload", async ({page, request}) => {
  const id = await open(page), headers = {"X-Session-ID":id};
  // Test-only commands in disposable storage, never generated by the application.
  // Same seeded, varied baseline used by the backend review regression check.
  // This exercises review controls, not a claim of anomaly-detection accuracy.
  const baseline = [
    [17,99.8],[27,99.9],[24,99.9],[16,100.2],[15,100.2],[37,99.8],[11,99.8],[23,99.9],[42,100.2],
    [11,100.2],[22,100.2],[36,99.9],[38,100.2],[27,99.8],[20,100.1],[31,100],[19,99.9],[31,99.8],
    [15,100.1],[16,100],[32,100.2],[26,99.8],[39,100.2],[17,100.1],[15,100.2],[28,100.2],[33,100.2],
    [22,99.8],[12,99.9],[28,99.8],[24,99.8],[34,100],[39,100],[20,100],[32,99.9],[27,99.8],
    [48,99.9],[44,99.9],[20,100.1],[34,100],[45,99.9],[30,99.8],[24,99.8],[30,100.1],[27,99.8],
  ];
  for (const [index, [quantity, rawPrice]] of baseline.entries()) {
    const price=rawPrice.toFixed(2);
    for (const side of ["SELL", "BUY"]) {
      const response=await request.post("/api/lab/orders", {headers,data:{order_id:`${side}-${index}`,symbol:"RELIANCE",side,quantity,price}});
      expect(response.status()).toBe(200);
    }
  }
  for (const side of ["SELL", "BUY"]) {
    expect((await request.post("/api/lab/orders",{headers,data:{order_id:`LARGE-${side}`,symbol:"RELIANCE",side,quantity:5000,price:"130"}})).status()).toBe(200);
  }
  await page.getByRole("button", {name:"AI watchdog", exact:true}).click();
  await expect(page.getByRole("heading", {name:"Execution review queue"})).toBeVisible();
  const button=page.getByRole("button", {name:"Review #92", exact:true});
  await expect(button).toBeVisible(); await button.click();
  await page.getByLabel("Review status").selectOption("reviewed");
  await page.getByLabel("Investigation notes").fill("Intentional large test execution inspected.");
  await page.getByRole("button", {name:"Save review", exact:true}).click();
  await expect(page.getByText("Intentional large test execution inspected.", {exact:true})).toBeVisible();
  await page.reload(); await expect(page.getByRole("heading", {name:"Workspace overview"})).toBeVisible();
  await page.getByRole("button", {name:"AI watchdog", exact:true}).click();
  await expect(page.getByText("Intentional large test execution inspected.", {exact:true})).toBeVisible();
  const report=await (await request.get("/api/lab/watchdog",{headers})).json();
  expect(report.alerts.at(-1).review.status).toBe("reviewed");
});

test("calibrated watchdog flags the previously missed repetitive-baseline execution", async ({page, request}) => {
  const id = await open(page), headers = {"X-Session-ID":id};
  for (let index=0; index<45; index++) {
    for (const side of ["SELL", "BUY"]) {
      expect((await request.post("/api/lab/orders",{headers,data:{order_id:`${side}-${index}`,symbol:"RELIANCE",side,quantity:10+index%17,price:(100+(index%5-2)/10).toFixed(2)}})).status()).toBe(200);
    }
  }
  for (const side of ["SELL", "BUY"]) {
    expect((await request.post("/api/lab/orders",{headers,data:{order_id:`LARGE-${side}`,symbol:"RELIANCE",side,quantity:5000,price:"130"}})).status()).toBe(200);
  }
  const before = await state(request,id);
  await page.getByRole("button", {name:"AI watchdog", exact:true}).click();
  await expect(page.getByText(/execution-watchdog-v3/)).toBeVisible();
  const row = page.getByRole("row").filter({hasText:"LARGE-BUY"});
  await expect(row).toBeVisible();
  await expect(row.getByText(/robust guard/)).toBeVisible();
  const result = await (await request.get("/api/lab/watchdog",{headers})).json();
  expect(result.alerts.at(-1).detectors).toContain("robust_guard");
  expect(result.calibration.fit_observations).toBe(24);
  expect(result.calibration.cutoff_observations).toBe(16);
  expect(await state(request,id)).toEqual(before); // Monitoring is advisory only.
});

test("private access gate UI rejects bad input, signs in and signs out without storing the key", async ({page}) => {
  // UI-only transport fixture. Real HTTPS-cookie/API/WS authorization is
  // exercised separately by tests/test_security.py, not claimed here.
  let authenticated = false;
  await page.route("**/api/auth/status",route => route.fulfill({json:{required:true,authenticated}}));
  await page.route("**/api/auth/login",async route => {
    const valid = route.request().postDataJSON().access_key === "UI-test-only-key";
    authenticated = valid;
    await route.fulfill({status:valid ? 200 : 401,json:valid ? {authenticated:true} : {detail:"Access key is invalid"}});
  });
  await page.route("**/api/auth/logout",route => {authenticated=false; return route.fulfill({json:{authenticated:false}});});
  await page.goto("/");
  await expect(page.getByRole("heading",{name:"Unlock your workspace"})).toBeVisible();
  await page.getByLabel("Workspace access key").fill("wrong");
  await page.getByRole("button",{name:"Sign in",exact:true}).click();
  await expect(page.getByRole("alert")).toHaveText("Access key is invalid");
  await page.getByLabel("Workspace access key").fill("UI-test-only-key");
  await page.getByRole("button",{name:"Sign in",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Workspace overview"})).toBeVisible();
  expect(await page.evaluate(() => JSON.stringify([localStorage,sessionStorage]))).not.toContain("UI-test-only-key");
  await page.getByRole("button",{name:"Sign out",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Unlock your workspace"})).toBeVisible();
});

test("ten rapid reloads preserve the workspace and reconnect live updates", async ({page,request}) => {
  const id = await open(page);
  for (let iteration=0; iteration<10; iteration++) {
    await page.reload();
    await expect(page.getByText("LIVE WORKSPACE UPDATES",{exact:true})).toBeVisible();
  }
  expect((await state(request,id)).events).toBe(0);
});

for (const width of [390,820,1440]) {
  test(`responsive workspace stays readable at ${width}px`,async ({page}) => {
    await page.setViewportSize({width,height:900});
    await open(page);
    for (const name of ["Orders & depth","Market history","AI watchdog","Trade history","Performance"]) {
      const menu = page.getByRole("button",{name:"Open navigation",exact:true});
      if (await menu.isVisible()) await menu.click();
      await page.getByRole("button",{name,exact:true}).click();
      await expect(page.locator("main.content h1")).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
    }
  });
}
