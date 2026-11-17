/* Only these versioned public assets are cached. All private data remains network-only. */
const CACHE = "varal-public-v1";
const PUBLIC = ["/offline-v1.html", "/icons/varal-192-v1.png", "/icons/varal-512-v1.png"];
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(PUBLIC)));
});
self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter((name) => name.startsWith("varal-public-v") && name !== CACHE).map((name) => caches.delete(name)));
  })());
});
self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (!url.search && PUBLIC.includes(url.pathname)) {
    event.respondWith(caches.open(CACHE).then(async (cache) => (await cache.match(request)) ?? fetch(request)));
  } else if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(async () => (await (await caches.open(CACHE)).match("/offline-v1.html")) ?? new Response("Sem conexão.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } })));
  }
});
self.addEventListener("push", (event) => {
  event.waitUntil(self.registration.showNotification("Varal", { body: "Você tem um novo aviso no Varal.", tag: "varal-aviso" }));
});
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    const existing = windows.find((client) => new URL(client.url).origin === self.location.origin);
    if (existing) { await existing.navigate("/avisos"); return existing.focus(); }
    return self.clients.openWindow("/avisos");
  })());
});
