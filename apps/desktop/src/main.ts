import { app, BrowserWindow, Menu, session, shell } from "electron";

const origin = (() => {
  const url = new URL(!app.isPackaged && process.env.TRADEVELOCITY_URL
    ? process.env.TRADEVELOCITY_URL : "https://gettradevelocity.onrender.com");
  if (url.protocol !== "https:" && (app.isPackaged || url.origin !== "http://127.0.0.1:8000")) {
    throw new Error("Use HTTPS for the hosted workspace");
  }
  if (url.username || url.password) throw new Error("The workspace address cannot contain credentials");
  return url.origin;
})();

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
    show: false, backgroundColor: "#080C14", title: "TradeVelocity",
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
  void window.loadURL(`${origin}/app`).catch(() => {
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
        void BrowserWindow.getFocusedWindow()?.loadURL(`${origin}/app`);
      }},
      {role: "togglefullscreen"}, {role: "zoomIn"}, {role: "zoomOut"}, {role: "resetZoom"},
    ]},
  ]));
  openWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) openWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });
