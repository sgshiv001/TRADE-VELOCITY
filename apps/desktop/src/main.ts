import { app, BrowserWindow, Menu, session, shell } from "electron";
import { X509Certificate } from "node:crypto";
import { mkdirSync, readFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import { browserSignIn } from "./browser-signin.js";
import { createOfflineEngine } from "./offline-engine.js";

const metadata = JSON.parse(readFileSync(join(app.getAppPath(), "package.json"), "utf-8"));
const view = (app.isPackaged ? metadata.tradevelocityDesktopView : process.env.TRADEVELOCITY_DESKTOP_VIEW) === "admin"
  ? "admin" : "trader";
const preview = app.isPackaged && metadata.tradevelocityPreview === true;
const presentation = app.isPackaged && metadata.tradevelocityPresentation === true;
const offline = presentation ? createOfflineEngine() : null;
const title = presentation ? "TradeVelocity" : preview ? "TradeVelocity 2.0 Preview" : view === "admin" ? "TradeVelocity Admin Dashboard" : "TradeVelocity Trader";
app.setName(title);
if (process.platform === "win32" && app.isPackaged && !preview) {
  app.setAppUserModelId(view === "admin" ? "com.tradevelocity.admin"
    : metadata.tradevelocityDesktopView === "trader" ? "com.tradevelocity.trader" : "com.tradevelocity.desktop");
}
const requestedProfile = app.commandLine.getSwitchValue("user-data-dir");
const profile = isAbsolute(requestedProfile) ? requestedProfile : join(app.getPath("appData"), title);
mkdirSync(profile, {recursive: true});
app.setPath("userData", profile);
app.setPath("sessionData", profile);
if (presentation && !app.requestSingleInstanceLock()) app.quit();

const origin = (() => {
  const devUrl = !app.isPackaged ? process.env.TRADEVELOCITY_URL : undefined;
  const url = new URL(preview ? metadata.tradevelocityOrigin : devUrl || "https://gettradevelocity.onrender.com");
  if (url.protocol !== "https:" && (app.isPackaged || url.origin !== "http://127.0.0.1:8000")) {
    throw new Error("Use HTTPS for the hosted workspace");
  }
  if (url.username || url.password) throw new Error("The workspace address cannot contain credentials");
  return url.origin;
})();
const browserLogin = !preview && origin.startsWith("https://");
const workspace = `${origin}/app?desktopView=${view}${browserLogin ? "&desktopBrowser=1" : ""}${presentation ? "&presentation=1" : ""}`;

if (preview && origin === "https://localhost:8443" && /^[0-9A-F:]{95}$/.test(metadata.tradevelocityPreviewFingerprint)) {
  // Desktop staging uses a pinned, short-lived certificate for this loopback origin.
  app.on("certificate-error", (event, _contents, address, _error, certificate, reply) => {
    if (!isWorkspace(address)) return;
    if (new X509Certificate(certificate.data).fingerprint256 === metadata.tradevelocityPreviewFingerprint) {
      event.preventDefault();
      reply(true);
    }
  });
}

function isWorkspace(address: string) {
  try { return new URL(address).origin === origin || Boolean(offline?.matches(address)); } catch { return false; }
}

function openDownload(address: string) {
  try {
    const url = new URL(address);
    if (url.origin === "https://github.com" && url.pathname.startsWith("/sgshiv001/TRADE-VELOCITY/releases")) {
      void shell.openExternal(url.href);
    }
  } catch { /* Deny unsupported URLs. */ }
}

function startupStatus(window: BrowserWindow, heading: string, detail: string) {
  const content = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><title>TradeVelocity</title>
    <body style="max-width:38rem;margin:12vh auto;padding:1.5rem;background:#101820;color:#f0faf6;font:18px system-ui"><h1>${heading}</h1><p>${detail}</p></body></html>`;
  return window.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(content)}`);
}

async function loadOffline(window: BrowserWindow) {
  if (!offline || window.isDestroyed()) return;
  await startupStatus(window, "Opening Offline demo", "Starting the local matching engine and loading the bundled workspace.");
  try {
    const address = await offline.open();
    if (!window.isDestroyed()) await window.loadURL(address);
  } catch {
    if (!window.isDestroyed()) await startupStatus(window, "Offline demo could not start", "Choose View, then Offline demo to retry, or open the live workspace.");
  }
}

async function loadLive(window: BrowserWindow) {
  let timer: NodeJS.Timeout | undefined;
  try {
    if (presentation) await startupStatus(window, "Connecting to TradeVelocity", "Opening the live workspace. Offline demo is available from the View menu.");
    await Promise.race([window.loadURL(workspace), new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new Error("The live workspace took too long to respond.")), 35_000);
    })]);
  }
  catch (cause) {
    if (window.isDestroyed() || (cause instanceof Error && cause.message.includes("ERR_ABORTED"))) return;
    if (offline) await loadOffline(window);
    else await startupStatus(window, "Connection unavailable", "Reconnect and choose Live workspace from the View menu.");
  } finally { clearTimeout(timer); }
}

function openWindow() {
  const window = new BrowserWindow({
    width: 1440, height: 1000, minWidth: 420, minHeight: 620,
    show: false, backgroundColor: "#090C10", title,
    webPreferences: {sandbox: true, contextIsolation: true, nodeIntegration: false, webviewTag: false},
  });
  window.on("page-title-updated", event => event.preventDefault());
  const signIn = browserLogin ? browserSignIn(window, origin, workspace, view) : null;
  window.webContents.on("will-navigate", event => {
    if (offline && isWorkspace(window.webContents.getURL()) && ["tradevelocity-local:offline", "tradevelocity-local:live"].includes(event.url)) {
      event.preventDefault();
      if (event.url.endsWith(":offline")) { signIn?.cancel(); void loadOffline(window); }
      else void loadLive(window);
      return;
    }
    if (signIn?.handle(event.url, window.webContents.getURL())) {
      event.preventDefault();
      return;
    }
    if (!isWorkspace(event.url)) { event.preventDefault(); openDownload(event.url); }
  });
  window.webContents.on("will-redirect", event => {
    if (!isWorkspace(event.url)) event.preventDefault();
  });
  window.webContents.setWindowOpenHandler(({url}) => {
    if (isWorkspace(url)) void window.loadURL(url);
    else openDownload(url);
    return {action: "deny"};
  });
  window.webContents.on("will-attach-webview", event => event.preventDefault());
  window.once("ready-to-show", () => window.show());
  window.webContents.on("did-start-navigation", event => {
    if (event.isMainFrame && isWorkspace(event.url)) signIn?.cancel();
  });
  if (offline && process.argv.includes("--offline-demo")) void loadOffline(window);
  else void loadLive(window);
}

void app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, done) => done(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  offline?.prepareSession(session.defaultSession);
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {label: "TradeVelocity", submenu: [{role: "quit"}]},
    {label: "Edit", submenu: [{role: "copy"}, {role: "paste"}, {role: "selectAll"}]},
    {label: "View", submenu: [
      {label: "Live workspace", accelerator: "CmdOrCtrl+R", click: () => {
        const active = BrowserWindow.getFocusedWindow();
        if (active) void loadLive(active);
      }},
      ...(offline ? [{label: "Offline demo", accelerator: "CmdOrCtrl+Shift+D", click: () => {
        const active = BrowserWindow.getFocusedWindow();
        if (active) void loadOffline(active);
      }}] : []),
      {role: "togglefullscreen"}, {role: "zoomIn"}, {role: "zoomOut"}, {role: "resetZoom"},
    ]},
  ]));
  openWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) openWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
app.on("before-quit", () => offline?.stop());
app.on("second-instance", () => {
  const window = BrowserWindow.getAllWindows()[0];
  if (!window) return;
  if (window.isMinimized()) window.restore();
  window.show();
  window.focus();
});
