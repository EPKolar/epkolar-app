# Agententeam-Review-Funde 2026-06-05 (v3.9.148 → v3.9.149)

Zwei Wellen adversariales Read-Only-Review über den (teils blind gebauten) PlanRadar- + Infrastruktur-Code.

## ✅ Gefixt (v3.9.148 + v3.9.149)
- **P1 Pin-Zentrierung** (PlanViewerCanvas): Liste→Plan-Sprung miszentriert bei Zoom≠1 (flexOffset). → `pan = baseWidth/2 − nx·baseWidth·zoom`. *(v3.9.148)*
- **P3 Layer-Filter** (VPlan): `filteredTickets` Sidebar + Layer-Stat-mx-Baseline nutzten rohes `t.layer` → gewerk-only-Tickets geschluckt / Balken >100%. → `(gewerk||layer)`. *(v3.9.148)*
- **P1 Sync 408/429**: Code klassifizierte 408/429 als permanent (drop nach 5), Kommentar sagte „außer 408/429". → jetzt transient (retrybar). *(v3.9.149)*
- **P2 Sync Retry-Count**: Retry-Zähler wurde nur persistiert wenn KEIN Sibling gedroppt wurde (`&&skipIds.length===0`) → Items loopten ewig bei Drop-Nachbarn. → Guard entfernt. *(v3.9.149)*
- **P2 Notif deadline_fz**: Fahrzeug-Frist (cat=system) navigierte beim Klick nicht. → `_typeTab={deadline_fz:"fahrzeuge"}`. *(v3.9.149)*

## ⏳ OFFEN — bewusst NICHT blind gefixt (Sync-Core = Daten-Integrität, Sebastian/Chat-Claude prüfen)

### P1 — Persistenter 403 (RLS-Denial) wedged Queue für immer
`doSync` behandelt `"Auth:"+status` (401/403) als transient `break`. Ein dauerhaft-403-Item (fehlende RLS-Policy, vgl. historischer Riedmann-Notifications-Bug) hängt ewig: kein Retry-Cap, kein Drop, Banner verschwindet nie, nur wiederkehrender „Sitzung abgelaufen"-Toast.
**Fix-Vorschlag:** 401 (Auth-Expiry → break/refresh) von 403 (Authorization) trennen; 403 nach N Refresh-Fehlversuchen in den Retry/Drop-Pfad → landet in `syncQueueFailed`.

### P2 — Idempotenz: id-lose POST-Create-Pfade → Duplikat bei Retry
`_sbPost` = plain INSERT ohne `merge-duplicates`. Pfade OHNE client-`id`: `wz-service`, `fz-termine`, `photos` + Array-Appends (serviceheft/tank_log/km_log). Retry nach „committed-aber-Response-verloren" (5xx/Failed-to-fetch nach Commit) → Duplikat. Exakt die „Serviceheft-Duplikat"-Klasse.
**Fix-Vorschlag:** jedem POST-Body stabile client-`id` geben + `_sbUpsert` für Create-Pfade; Array-Appends per UUID dedupen vor `JSON.stringify`.

### P3 — `_portalSync` (Kundenportal) ohne Retry-Cap/Klassifikation
`for(item){try{…}catch(e){break;}}` — Poison-Item (4xx) blockt die ganze Portal-Queue für immer (pre-v3.9.131-Bug im Portal-Pfad). → dieselbe transient/permanent+Cap-Logik wie `doSync` portieren.

### P3 — PhotoQ.flush head-of-line-blocking
`break` bei erstem Fehler; ein permanent-failing Foto blockt nachfolgende bis 10-Retry-Cap erreicht (kein Datenverlust, aber langsamer Drain).

### P3 (Notif/UX) — „keine Berechtigung"-Toast bei legitim erhaltener Notif
Monteur erhält `tool_checkout` (default-prefs), aber hat keinen `werkzeuge`-Tab → Klick zeigt verwirrend „Ziel nicht verfügbar". Erwägung: für unerreichbare Tabs still schließen statt Toast. Plus: `pushNotif` schließt den auslösenden User nicht aus seinen eigenen Notifications aus (Self-Spam + Sound).

## ✅ Von den Agenten als KORREKT bestätigt
- Kein weiterer TDZ (der v3.9.142-Fix sitzt korrekt nach der selPlan-Deklaration).
- `_mapPlan`-Passthrough intakt (page_count/intrinsic/filename/pid/isPdf).
- POST/PUT schreiben nur kanonische Spalten (kein nx/x_pct).
- Keine Event-/Interval-Leaks (SQ-Poll cleart Interval, async-Effekte mit active-Flag).
- Notif: keine Permission-Eskalation (Nav indexiert in die bereits permission-gefilterte `tabs`-Liste).
- Notif: markRead/delete/Alle-gelesen persistieren konsistent, unreadCount ist derived (kein Desync).
- Notif: z-index Backdrop(199)/Panel(200) korrekt, Entry-Klicks nicht geschluckt.
- Sync: Regex `/^HTTP(\d{3})/` matcht alle 7 Throw-Sites zuverlässig; transiente Fehler behalten Queue; Drops werden über `syncQueueFailed`+Banner+Toast sichtbar (nicht silent); `_mutex` serialisiert RMW-Ops.
