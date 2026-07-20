// EP Kolar Service Worker v3.9.771 - #19b Geo-Selbstnachzieh: Nominatim+OSRM fuellen plz_geo/plz_distanz im Hintergrund (rate-limited, nie haengen) -> echte Fahrminuten fuer #28. v3.9.764 - #28 Planungskern V2: Dispo optimiert auf Fahrminuten (28a) + Nachbarschafts-Bonus buendelt nahe Adressen (28b). v3.9.763 - P3-Nachbesserung: Dispo-Sperr-Toggle kollidiert nicht mehr mit Karten/Chips (reservierter 18px-Kopfstreifen, Kollisionen 2->0 Desktop+Mobile). v3.9.762 - P3: Dispo-Sperrsymbol-Position (top:2,right:8 statt 1,1 — klar innerhalb der Zelle). v3.9.761 - #30f Datenfrische: visibilitychange-Refresh der Dispo (60s-Guard, geste-defer, read-only dispo_blocks-Refetch + Recompute). v3.9.760 - #1 Teil 2: 🚫-Sperr-Toggle (dispo_blocks INSERT/DELETE via Eltern-Prop, Whitelist 5, sofort-Recompute, 42P01-Hinweis). v3.9.759 - #28d Vollbilanz (_dispoBilanz, luekenlose Partition + Invariante) + Dead-Code #8-13 (_dispoDropFeedback/_dispoCanResched raus). v3.9.758 - #31g-Aufholer WIRING-FIX: Mount-Sweep am App-Start (curUser+Auth-Ready, ref-once), nicht mehr tab-gated. v3.9.757 - #31a Monteur-Guard (vs public.workers-Mirror) + #31b Pull-Echo-Schutz (code-loser Monteur nicht cloud-clobbern). v3.9.756 - #31g-Konsolidierung: W2 stillgelegt + EINE per-Schein-Debounce-Klammer _juprowaSchedulePush (genau 1 Push) + Mount-Aufholer. v3.9.755 - #31g JUPROWA Push-Queue Selbstheilung (updAs W1-Straggler: doSync drain-on-write-Tick, echo-gated Reset-Check + juprowa_push_fail-Log, Badge Alter+Grund). v3.9.754 - #31f Monteur-Codes P026=Kiener/P028=Aliti in die Map (Push+Pull); #31c Badge "Monteur nicht nach OFFA uebertragbar" wenn kein Juprowa-Code. v3.9.743 - Horizont 4 Wochen. v3.9.737 - Textauswahl bei Drag ENDGUELTIG unterbunden. v3.9.736 - keine blaue Text-Markierung (body userSelect none). v3.9.735 - Startzeiten Mittagspause 12-13 + Freitag ohne Pause. v3.9.734 - fixe Termine per Drag umterminieren (Sebastian). _dispoCanResched-Guard (gleicher Monteur, anderer Tag) -> onReschedule -> updAs(terminBestaetigt), E4b-Reschedule-Push, kein Sonderpfad.v3.9.733 - #20 Startzeiten (15-min-Takt ab 07:00, _dispoAblauf) + #16b-neu Kalender-Kachel: Hoehe=Dauer, Uhrzeit rechts, unterer Rand ziehen=Dauer (ersetzt ≡-Griff). Uebernahme schreibt terminZeit (termin_zeit) via AK_TERMIN, kein Push-Key.v3.9.732 - #16b Dauer-Griff (≡): Plan-Dauer am Chip in 15-min-Schritten ziehen (min30/maxNorm), Live-Balken, Uebernahme als dauer (kein Push). #16 komplett.v3.9.731 - #16a-Rest Warteliste ziehbar + Live-Drop-Feedback (gruen/orange/rot) + KW-Tab-Hover-Wechsel (600ms).v3.9.730 - #16a Dragv3.9.729 - #19 km-Kaskade: "+0 km" raus -> ehrliches Label (echte plz_distanz-Matrix "N km" / gleiche PLZ "~2 km" / Geo-Zentroid "~N km" / unbekannt "? km"); Fahrzeit NIE 0. plz_geo/plz_distanz leer-tolerant (auto-echt bei Befuellung). + P1-Review-Fix: OFFA-Sentinel 0001-01-01 nicht mehr als ueberfaellig.Drop Termin fixieren: Chip ziehen (Pointer-Events, Schwelle 8px trennt Klick=oeffnen von Drag) -> Drop auf Tag DERSELBEN Monteur-Zeile fixiert (Pin, localStorage, 📌); _dispoPlan respektiert Pins (gepinnte zuerst, harte Wand bleibt); Neu-berechnen haelt Pins. Fremde Zeile -> Hinweis.
const CACHE_NAME = "epkolar-v3.9.771";
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
