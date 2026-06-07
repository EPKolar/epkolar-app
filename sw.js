// EP Kolar Service Worker v3.9.168
const CACHE_NAME = "epkolar-v3.9.168";
const ASSETS = [
  './',
  './index.html'
];

self.addEventListener('install', event => {
  // v3.8.7: matchAll({includeUncontrolled:true}) — während install hat SW KEINE controlled clients
  // → vorheriger Code erreichte nie einen Client mit SW_UPDATED
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim()).then(() => {
      // Jetzt sind wir controlled → alle Clients benachrichtigen
      return self.clients.matchAll({ includeUncontrolled: true }).then(clients => {
        clients.forEach(client => client.postMessage({ type: 'SW_UPDATED', ver: CACHE_NAME }));
      });
    })
  );
});

self.addEventListener('fetch', event => {
  const url = event.request.url;
  if (!url.startsWith('http://') && !url.startsWith('https://')) return;
  if (url.includes('supabase.co')) return;
  if (url.includes('cdnjs.cloudflare.com')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        const fetchPromise = fetch(event.request).then(response => {
          if (response && response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }
  event.respondWith(
    fetch(event.request).then(response => {
      if (response && response.ok && event.request.method === 'GET') {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          try { cache.put(event.request, clone); } catch(e) {}
        });
      }
      return response;
    }).catch(() => caches.match(event.request))
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('sync', event => {
  if (event.tag === 'epkolar-sync') {
    event.waitUntil(
      self.clients.matchAll().then(clients => {
        clients.forEach(client => client.postMessage({ type: 'SYNC_TRIGGER' }));
      })
    );
  }
});
