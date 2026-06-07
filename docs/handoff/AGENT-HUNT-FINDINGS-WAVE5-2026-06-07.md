# Overnight-Agenten-Bug-Hunt — Welle 5 Funde (2026-06-08, nachts)

3 read-only Audit-Agenten (Foto-Pipeline, Notifications/Glocke, Wochenplanung). Contained → Fix (v3.9.169);
RLS-/struktur-/sync-sensibel → dokumentiert.

## Notifications / Glocke (alle Fixes Frontend, RLS NICHT angefasst = Sebastian)
- **[P1] Notif#1 Klick auf Kunden-/Material-Benachrichtigung navigiert NIE → ✅ FIX-Kandidat v3.9.169**: `pushNotif`
  setzt `link=NOTIF_TYPES[type].cat` (`material`/`kunden`/`system`), Klick-Handler nimmt `n.link` zuerst → `_catTab`-
  Remapping (material→projekte, kunden→arbeitsscheine) wird übersprungen → `findIndex(perm==="material")`=-1 → „Ziel
  nicht verfügbar". Genau die dringenden Notifs (Kunde meldet Mangel) klicken ins Leere. Fix: im Handler `_catTab[n.link]||n.link`
  auflösen ODER `link` leer lassen.
- **[P1] Notif#2 Batch-INSERT: ein RLS-403 verwirft ALLE Notifs des Batches — DOKUMENTIERT**: `/api/notifications/batch`
  = ein Multi-Row-Upsert, eine abgelehnte Zeile (Notif an anderen User) killt den ganzen Batch → nach 5 Retries gedroppt,
  KEINE Benachrichtigung kommt an. Fix: pro user_id einzelnes SQ-Item. (verknüpft mit notifications-RLS / is_staff)
- **[P2] Notif#3/#4 optimistischer Badge/markAllRead ohne Rollback bei RLS-Fail — DOKUMENTIERT** (Badge divergiert,
  „springt" nach Reload). **[P3] Notif#5 read-all ohne user_id PATCHt global — FIX-Kandidat** (bei fehlendem user_id `return`).
  **[P3] Notif#6 silent-notif-Inserts (@-Erwähnung/Urlaub) verschlucken RLS-Fehler — DOKUMENTIERT** (über SQ statt fire-and-forget).

## Wochenplanung / Kalender
- **[HOCH] WP#1 `wpHistory` nur per Woche gekeyt (year fällt weg) — DOKUMENTIERT (strukturell)**: DB-Key ist composite
  `year-week` (2115), Load mappt nur `wpH[wp.week]` (4894) → KW23/2025 und KW23/2026 kollidieren, jahresübergreifende
  Datenvermischung/Überschreiben. Fix: `wpHistory` durchgängig composite `year+"-"+week` keyen (mehrstellig: curKw/switchKw/savedKws/copyWeek). Strukturell → kontrollierter Sprint.
- **[HOCH] WP#2 `yr` über KW-Navigation eingefroren — DOKUMENTIERT**: `yr=isoWY()` (heute) fix; ◀/▶ über Jahresgrenze
  rechnet falsches Jahr → falsche Daten/Export/Save. Fix: `wpYear`-State, switchKw passt ±1 Jahr bei Über/Unterlauf an. (mit WP#1)
- **[MITTEL] WP#3 KW-Nav hart auf 52 gedeckelt → KW53 in 53-Wochen-Jahren unerreichbar → ✅ FIX-Kandidat v3.9.169**:
  `Math.min(52,kw+1)` (14018). 2026 hat 53 Wochen. Fix: Obergrenze dynamisch aus ISO-Wochenzahl des Jahres.
- **[MITTEL] WP#4 BWB-Export Tageslabel kombiniert echten Tag/Monat mit ISO-Wochenjahr → ✅ FIX-Kandidat v3.9.169**:
  `...getMonth()+1..., ".", yr` (7326) → KW1 zeigt „Mo 29.12.2026" statt 2025. Fix: `String(day.getFullYear())` statt `yr`
  (analog v3.9.158 KW-Jahr-Fix). Display-Bug, contained.
- **[NIEDRIG] WP#5 Doppelbelegung nur für Fahrzeuge, nicht Mitarbeiter — DOKUMENTIERT** (otherRow/maConflicts fehlt im MA-Block).

## Foto-Pipeline / Galerie (robust; PhotoQ-Block v3.9.160 ok)
- **[HOCH] Foto#1 Orphan-Storage-Files bei DB-Insert-Fail + Retry — DOKUMENTIERT**: `_storagePath` nutzt `Date.now()` →
  Re-Upload baut neuen Pfad → verwaister Blob pro Fehlversuch. Fix: Pfad deterministisch aus `ph.id` + x-upsert, ODER DB vor Storage.
- **[MITTEL] Foto#2 Storage-5xx nicht als transient erkannt → ✅ FIX-Kandidat v3.9.169**: `_sbUploadFile` wirft „Storage
  upload failed: 503", die flush-Transient-Regex matcht nur `HTTP|Auth:` → 5xx gilt als permanent. Fix: Error-Format auf
  „HTTP"+status angleichen ODER Regex erweitern.
- **[MITTEL] Foto#3 `_dataUrlToBlob` atob crash bei korruptem base64 — FIX-Kandidat** (atob in try/catch → null/„Invalid dataUrl").
- **[MITTEL] Foto#4 Portal-Foto ohne width/height/GPS — DOKUMENTIERT**. **[NIEDRIG] #5 compressedSize-Schätzung ohne Header
  → FIX-Kandidat** (Header abziehen). **[NIEDRIG] #6 getPhotos-Dedup String- statt id-basiert — DOKUMENTIERT** (Doppelanzeige).

> Geprüft sauber: Mutex/Quota/Retry (Foto), Token-Refresh/Single-Flight (Login), Feiertage/ISO-KW (Wochenplan),
> Prozent/÷0-Guards. Die schwersten contained Code-Bugs: Notif#1 (dringende Notifs unklickbar), WP#4 (falsches Export-Datum).
