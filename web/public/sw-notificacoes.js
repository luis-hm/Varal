/* Push messages deliberately contain no financial data and this worker never caches responses. */
self.addEventListener("push", (event) => {
  event.waitUntil(self.registration.showNotification("Varal", {
    body: "Você tem um novo aviso no Varal.",
    tag: "varal-aviso",
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    const existing = windows.find((client) => new URL(client.url).origin === self.location.origin);
    if (existing) {
      await existing.navigate("/avisos");
      return existing.focus();
    }
    return self.clients.openWindow("/avisos");
  })());
});
