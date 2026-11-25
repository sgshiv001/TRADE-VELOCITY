export function registerOfflineShell() {
  if ("serviceWorker" in navigator && window.isSecureContext) {
    void navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
}
