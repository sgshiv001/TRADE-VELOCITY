/* Cache public offline assets only. Account and order calls go directly to the server. */
const SHELL = "tradevelocity-offline-v1";
self.addEventListener("install", event => {
  event.waitUntil(caches.open(SHELL).then(cache => cache.addAll(["/offline.html", "/icon-192.png"])));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key =>
    key.startsWith("tradevelocity-offline-") && key !== SHELL).map(key => caches.delete(key)))));
});
self.addEventListener("fetch", event => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || event.request.mode !== "navigate" ||
      url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  event.respondWith(fetch(event.request).catch(() => caches.match("/offline.html")
    .then(cached => cached ?? Response.error())));
});
