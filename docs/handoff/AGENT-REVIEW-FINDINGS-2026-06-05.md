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

---

## Welle 3 — Arbeitsscheine-Review (v3.9.151)

### ✅ Gefixt
- **P2 OFFA-Dedupe case-insensitiv** (commitImport): `a.nummer===parsed.nummer` → beidseitig `.toUpperCase()` (wie JUPROWA-Pfad). Sonst Duplikat-Insert bei lowercase-Altscheinen. *(v3.9.151)*

### ✅ GEFIXT v3.9.152 (mockMode-sicher — Sebastian muss vor Go-Live mit echter WA-Config + 1-2 Test-Tickets prüfen)
Verifiziert: keine `whatsapp_config`-Zeile → `_waSendMessage` mockMode → kein Live-Kunden-Send. Daher Logik korrigiert (sendet nichts live):
- 🔴→✅ **Double-Fire**: zentraler `_maybeNotifyAsDone` mit persistierter notified-Menge (`waNotifiedAs` ODB, cap 2000) → kein Duplikat bei erledigt→x→erledigt.
- 🔴→✅ **Edit-Formular/Auto-Close sendet jetzt**: Helper aus updAs UND saveAs aufgerufen.
- ✅ **Telefon**: `telefon||kundTel` in Helper + manuellem Senden-Button → JUPROWA-Tickets funktionieren.
**Sebastian-Go-Live-Test ausstehend** (mockMode nicht real-getestet). Optional offen: DB-Spalte `wa_done_notified` für cross-device-Persistenz (aktuell per-device ODB).

### ⏳ NOCH OFFEN (alte Notiz):

**🔴 P1 Double-Fire bei Rück-Vor-Wechsel:** Seit „alle Wechsel frei" (v3.9.122) löst `erledigt→in_bearbeitung→erledigt` die „Auftrag abgeschlossen"-WhatsApp **erneut** aus (v3.9.124-Guard deckt nur FERTIG→FERTIG, nicht den Round-Trip). Kein persistiertes „bereits benachrichtigt"-Flag vorhanden → Kunde kann Duplikat-Nachricht bekommen.
**Fix-Vorschlag:** AS-Feld `wa_done_notified=true` beim ersten Senden (DB-Spalte via Chat-Claude), Trigger `&& !s.wa_done_notified`; in updAs-Body + JUPROWA-Push aufnehmen. Interim ohne DB-Spalte: client-persistierte notified-AS-id-Menge in ODB.

**🔴 P1 Edit-Formular sendet NIE:** Der WA-Trigger sitzt nur in `updAs` (Inline-Dropdown/Swipe). Der **Edit-Formular-Speichern-Pfad (`saveAs`)** UND der **Auto-Close auf „erledigt"** (Doppel-Unterschrift) rufen `updAs` NICHT auf → die häufigsten Abschluss-Wege (Büro setzt Status im Formular, Monteur schließt vor Ort ab) senden **gar nichts**.
**Fix-Vorschlag:** WA-on-done-Logik aus `updAs` in Helper extrahieren, in `saveAs` mitaufrufen (pre-edit-Status vs. final-Status vergleichen, inkl. Auto-Close-Override).

**P2 Telefon-Feld-Mismatch:** JUPROWA-Tickets mappen Telefon in `kundTel`, nicht `telefon` → `const phone=(s.telefon||...)` ist leer → Notification no-opt für ALLE JUPROWA-Tickets (Großteil). Auch der manuelle Senden-Button (form.telefon-only).
**Fix-Vorschlag:** `const phone=(s.telefon||s.kundTel||updates.telefon||"").trim();` in Auto-Trigger + manuellem Handler. (Achtung: aktiviert neue Sends → mit Double-Fire-Fix koppeln.)

**P2 Billed→Draft-Revert propagiert zu JUPROWA:** Fat-Finger-Revert eines `abgerechnet`-Tickets nach `aufgenommen` wird beim nächsten JUPROWA-Pull/Push in die Buchhaltung propagiert (Sebastians „alle Wechsel frei"-Design). Vorschlag: `confirm()` für Transition aus AS_GRP_FERTIG zurück in AS_GRP_OFFEN (nicht-blockierend, wie storno).

### ✅ Vom Agent als KORREKT bestätigt
- Monteur-Anlage-Verbot solide (UI-Gate `as_create` versteckt „+ Neuer Schein" UND „🎤 Schnellerfassung"; `saveAs` re-blockt; kein Bypass via Edit/Duplicate/Voice/Offline).
- Zahlen-Locale (`_normDauer` „3,5"→„3.5", NaN-Bail), absPerName exact-token (Doppel-Zählung gefixt), Sync-Button-nach-Drain (v3.9.38), Re-Import-Clobber-Schutz (status/termine/dauer aus Merge-Body gelöscht), OFFA-Leer-Zeilen-Filter — alle ✅.

---

## Welle 5 — Zeiterfassung/Bauwochenbericht-Review (v3.9.153)

### ✅ Gefixt
- **🔴 P1 `_kwFromDate` DST-Drift**: nutzte ms-Division `(dt-firstMon)/(7·864e5)` mit Math.floor + local-midnight-Daten → nach Frühjahrs-DST (Ende März) durchgängig **KW−1** (~6 Mon/Jahr falsche KW im Bauwochenbericht: Sheet-Namen, Summen-Zeilen, KW-Filter, Tätigkeitstext). Vienna-Ganzjahr-Test: 30 Tage Mismatch → 0. Fix: UTC-ISO-Woche (driftfrei). *(v3.9.153)*
- **P2 Hidden-Worker in KW-Summen** (generateBWB): `kwTotal` summierte ALLE Einträge inkl. ausgeblendeter Monteure, aber Spalten nur sichtbare → Zeilensumme≠Wochensumme im signierten Kundendokument. Fix: `_visIds`-Set, beide kwEntries-Blöcke nur sichtbare. *(v3.9.153)*

### ⏳ OFFEN (komplexere Roll-up-Refaktorierung / niedrigere Prio)
- **P2 Rollen-Total ignoriert KW-Filter** (generateBWB ~7173-7174): „Gesamtübersicht nach Rolle" nutzt `pEntries` (ganze Projekthistorie) statt der KW-gefilterten Menge → bei gewähltem KW-Subset zeigen Wochentabellen gefiltert, Rollen-Total aber ALLE Wochen → reconcilen nicht. Fix: Rollen-Total aus KW-gefilterter Menge bauen (+ hiddenMA ausschließen).
- **P3 Rundungs-Inkonsistenz**: Von/Bis/Pause-Auto-Fill rundet auf 0.5h (`Math.round(d*2)/2`), manuelles Stunden-Feld behält 2 Dezimalen → je nach zuletzt bearbeitetem Feld unter-/überbezahlt. Einheitliche Rundungsregel definieren.
- **generateAll (7259)**: separate „Alle-Projekte"-Export-Funktion, eigener kwEntries (NICHT gefixt — kein _visIds-Scope, vom Agent nicht reviewt). Prüfen ob gleiche hidden-worker-Logik nötig.

### ✅ Vom Agent als KORREKT bestätigt
- addEntry-Range-Guard (0<h≤24, NaN-Bail) + Doppel-Tap-Ref solide; getMonthEntries kein Doppel-Count (single-pass, wid-Match max 1×); VZeit/VBer-Wochenmathe (getISO+setDate) DST-korrekt (0 Mismatches); Locale via type=number/time (Komma erreicht parseFloat nicht); Feld-User auf eigene monteurId beschränkt (add+delete).
