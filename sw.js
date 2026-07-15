// EP Kolar Service Worker v3.9.706 - 🚛-Spezialfahrzeuge am lager_display-Kiosk: kontrollierter Lesepfad via RPC kiosk_fahrzeuge() (SECURITY DEFINER, nur id/kennzeichen/typ/modell/status) statt rohem fahrzeuge-Read, der bei fehlender RLS still [] lieferte; plus Diagnose-Zeile im Tafel-Kopf (v<VER> · FZ:<n> · Spez:<n>). Reiner index.html-Fix, SW nur Versions-Bump.
const CACHE_NAME = "epkolar-v3.9.706";
const ASSETS = [
  './',
  './index.html'
];

self.addEventListener('install', event => {
  // v3.8.7: matchAll({includeUncontrolled:true}) — während install hat SW KEINE controlled clients
  // → vorheriger Code erreichte nie einen Client mit SW_UPDATED
  // v3.9.705: skipWaiting() im install — ein neuer SW aktiviert sofort statt in "waiting" zu
  //           haengen bis alle Tabs geschlossen sind. Der Samsung-TV-Kiosk navigiert/schliesst nie,
  //           darum blieb der neue SW dort ewig "waiting" und das Geraet klebte auf der Altversion.
  //           Jetzt: install -> skipWaiting -> activate -> clients.claim() -> controllerchange.
  self.skipWaiting();
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
  // v3.9.705: Versions-Poll (index.html?_v=<ts>) NIE durch den SW cachen — sonst sammelt der
  // Kiosk bei jedem 10-min-Poll eine weitere Vollkopie der index.html im Cache an. Netzwerk direkt.
  if (url.includes('index.html?_v=')) return;
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
  // v3.9.358 FIX: Navigation/HTML IMMER netzfrisch (cache:'no-store') — sonst servierte fetch() die
  // alte index.html aus dem Browser-/CDN-HTTP-Cache → User hingen nach Deploy auf der Vorversion
  // (sichtbar: bare URL = alt, ?cc=… = neu). SW-Cache bleibt nur Offline-Fallback.
  if (event.request.mode === 'navigate' || event.request.destination === 'document') {
    event.respondWith(
      fetch(event.request, { cache: 'no-store' }).then(response => {
        if (response && response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => { try { cache.put(event.request, clone); } catch(e) {} });
        }
        return response;
      }).catch(() => caches.match(event.request).then(m => m || caches.match('./index.html')))
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
