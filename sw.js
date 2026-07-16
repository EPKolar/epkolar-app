// EP Kolar Service Worker v3.9.753 - #30e Buendel atomar: gleiche Adresse = ein virtueller Chip (Summendauer, eine Anfahrt), Partner konsekutiv in einer Luecke; passt nichts -> ganzes Buendel Folgetag, nie getrennt, nie 00:00. v3.9.743 - Horizont 4 Wochen. v3.9.737 - Textauswahl bei Drag ENDGUELTIG unterbunden. v3.9.736 - keine blaue Text-Markierung (body userSelect none). v3.9.735 - Startzeiten Mittagspause 12-13 + Freitag ohne Pause. v3.9.734 - fixe Termine per Drag umterminieren (Sebastian). _dispoCanResched-Guard (gleicher Monteur, anderer Tag) -> onReschedule -> updAs(terminBestaetigt), E4b-Reschedule-Push, kein Sonderpfad.v3.9.733 - #20 Startzeiten (15-min-Takt ab 07:00, _dispoAblauf) + #16b-neu Kalender-Kachel: Hoehe=Dauer, Uhrzeit rechts, unterer Rand ziehen=Dauer (ersetzt ≡-Griff). Uebernahme schreibt terminZeit (termin_zeit) via AK_TERMIN, kein Push-Key.v3.9.732 - #16b Dauer-Griff (≡): Plan-Dauer am Chip in 15-min-Schritten ziehen (min30/maxNorm), Live-Balken, Uebernahme als dauer (kein Push). #16 komplett.v3.9.731 - #16a-Rest Warteliste ziehbar + Live-Drop-Feedback (gruen/orange/rot) + KW-Tab-Hover-Wechsel (600ms).v3.9.730 - #16a Dragv3.9.729 - #19 km-Kaskade: "+0 km" raus -> ehrliches Label (echte plz_distanz-Matrix "N km" / gleiche PLZ "~2 km" / Geo-Zentroid "~N km" / unbekannt "? km"); Fahrzeit NIE 0. plz_geo/plz_distanz leer-tolerant (auto-echt bei Befuellung). + P1-Review-Fix: OFFA-Sentinel 0001-01-01 nicht mehr als ueberfaellig.Drop Termin fixieren: Chip ziehen (Pointer-Events, Schwelle 8px trennt Klick=oeffnen von Drag) -> Drop auf Tag DERSELBEN Monteur-Zeile fixiert (Pin, localStorage, 📌); _dispoPlan respektiert Pins (gepinnte zuerst, harte Wand bleibt); Neu-berechnen haelt Pins. Fremde Zeile -> Hinweis.
const CACHE_NAME = "epkolar-v3.9.753";
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
