import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

const external = process.env.TRADEVELOCITY_E2E_URL;
const localPython = resolve("..", ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const python = process.env.TRADEVELOCITY_TEST_PYTHON ?? (existsSync(localPython) ? localPython : "python");

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  expect: { timeout: 8000 },
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: external ?? "http://127.0.0.1:8804",
    browserName: "chromium",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  // Never attach silently to a user's normal app and mutate their saved session.
  webServer: external ? undefined : {
    command: `"${python}" ../scripts/browser_test_server.py --port 8804`,
    url: "http://127.0.0.1:8804/api/health",
    reuseExistingServer: false,
    timeout: 30000,
  },
});
