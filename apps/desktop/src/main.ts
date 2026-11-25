import { app, BrowserWindow, Menu, session, shell } from "electron";
import { X509Certificate } from "node:crypto";
import { mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const metadata = JSON.parse(readFileSync(join(app.getAppPath(), "package.json"), "utf-8"));
const view = (app.isPackaged ? metadata.tradevelocityDesktopView : process.env.TRADEVELOCITY_DESKTOP_VIEW) === "admin"
  ? "admin" : "trader";
const preview = app.isPackaged && metadata.tradevelocityPreview === true;
const title = preview ? "TradeVelocity 2.0 Preview" : view === "admin" ? "TradeVelocity Admin Dashboard" : "TradeVelocity Trader";
app.setName(title);
const profile = join(app.getPath("appData"), title);
mkdirSync(profile, {recursive: true});
app.setPath("userData", profile);
app.setPath("sessionData", profile);

const origin = (() => {
  const devUrl = !app.isPackaged ? process.env.TRADEVELOCITY_URL : undefined;
  const url = new URL(preview ? metadata.tradevelocityOrigin : devUrl || "https://gettradevelocity.onrender.com");
  if (url.protocol !== "https:" && (app.isPackaged || url.origin !== "http://127.0.0.1:8000")) {
    throw new Error("Use HTTPS for the hosted workspace");
  }
  if (url.username || url.password) throw new Error("The workspace address cannot contain credentials");
  return url.origin;
})();
const workspace = `${origin}/app?desktopView=${view}`;

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
  try { return new URL(address).origin === origin; } catch { return false; }
}

function openDownload(address: string) {
  try {
    const url = new URL(address);
    if (url.origin === "https://github.com" && url.pathname.startsWith("/sgshiv001/TRADE-VELOCITY/releases")) {
      void shell.openExternal(url.href);
    }
  } catch { /* Deny unsupported URLs. */ }
}

function openWindow() {
  const window = new BrowserWindow({
    width: 1440, height: 1000, minWidth: 420, minHeight: 620,
    show: false, backgroundColor: "#090C10", title,
    webPreferences: {sandbox: true, contextIsolation: true, nodeIntegration: false, webviewTag: false},
  });
  window.webContents.on("will-navigate", event => {
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
  void window.loadURL(workspace).catch(() => {
    void window.loadURL("data:text/html,<title>TradeVelocity offline</title><main><h1>TradeVelocity is offline</h1><p>Reconnect and choose Workspace from the View menu.</p></main>");
    window.show();
  });
}

void app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, done) => done(false));
  session.defaultSession.setPermissionCheckHandler(() => false);
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {label: "TradeVelocity", submenu: [{role: "quit"}]},
    {label: "Edit", submenu: [{role: "copy"}, {role: "paste"}, {role: "selectAll"}]},
    {label: "View", submenu: [
      {label: "Workspace", accelerator: "CmdOrCtrl+R", click: () => {
        void BrowserWindow.getFocusedWindow()?.loadURL(workspace);
      }},
      {role: "togglefullscreen"}, {role: "zoomIn"}, {role: "zoomOut"}, {role: "resetZoom"},
    ]},
  ]));
  openWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) openWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
