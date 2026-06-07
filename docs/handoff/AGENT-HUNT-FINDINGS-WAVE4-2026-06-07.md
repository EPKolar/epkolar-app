# Overnight-Agenten-Bug-Hunt — Welle 4 Funde (2026-06-07/08, nachts)

3 read-only Audit-Agenten (Login/Auth, Bautagebuch, Checklisten). Tier-1 = sicher+contained → gefixt (v3.9.166);
Tier-2 = real aber auth-/sync-/permission-sensibel → dokumentiert für kontrollierten Fix/Sebastian-Review.

## Checklisten (VCheck)
- **[HOCH] Checklisten#2 `createCustom` persistiert NICHT → ✅ FIX v3.9.166**: `createFromTemplate` macht SQ.push,
  `createCustom` (10152-10159) nur `setForms` → eigene Checklisten beim Reload WEG (Datenverlust), spätere PUTs 404.
  Fix: `SQ.push({url:"/api/checklists",method:"POST",body:{id,project_id,name}})` analog Template.
- **[NIEDRIG] Checklisten#5 Foto-Error-Toast „Material-Foto" → ✅ FIX v3.9.166** (Copy-Paste, 10231): Text → „Checklisten-Foto".
- **[HOCH] Checklisten#1 owner-gate `by` nie persistiert/geladen — DOKUMENTIERT**: POST-Body (10149) + Load-Mapping
  (4884/4208) lassen `by` weg → `_vcIsMineCl` immer false → Monteur kann eigene Checkliste nach Reload nicht löschen,
  Sicherheits-Gate de-facto tot. `checklists` HAT `created_by`-Spalte (DB-verifiziert). Fix: `by:cl.by` in POST +
  `by:c.by||c.created_by||""` im Mapping. Permission-sensibel → kontrollierter Fix.
- **[MITTEL] Checklisten#3 Item-State über Array-Index (key:i) — DOKUMENTIERT**: Items ohne stabile id → bei Reorder
  wandern Häkchen/Fotos. Latent (keine Reorder-UI). Fix: item.id:uid().
- **[MITTEL] Checklisten#4 Foto base64 inline im checklists-PUT — DOKUMENTIERT**: unkomprimierte DataURL in jsonb →
  Payload-Bloat/Sync-Fail-Risiko. Fix: compress/auslagern wie VMang.

## Login / Auth / Session
- **[MITTEL] Login#3 last_login/activity_log blockieren Login-Flow → ✅ FIX v3.9.166**: `await _sbPatch(users,last_login)`
  (2229) + `await _sbPost(activity_log)` (2230) synchron im kritischen Pfad → verzögert Dashboard, kann unnötigen
  Re-Auth triggern. Reine Telemetrie. Fix: fire-and-forget (kein await, .catch).
- **[HOCH] Login#1 `_restoreAuth` feuert `_silentReAuth` (Toast+Reload) bei Cold-Boot ohne Session — DOKUMENTIERT**
  (1478/1484): ausgeloggter User beim App-Öffnen sieht „🔒 Sitzung abgelaufen" + 2× erzwungener Reload, obwohl nie
  eine Session da war. Fix: im `!s`-Zweig still `return false`, `_silentReAuth` nur bei toter-aber-vorhandener Session.
  Auth-Boot-Pfad → kontrollierter Fix + Login-Live-Test.
- **[HOCH] Login#2 Purge-on-User-Wechsel löscht nicht syncQueue/photoQueue — DOKUMENTIERT** (2450/5505): `_USER_SCOPED_
  ODB_STORES` listet syncQueueFailed, NICHT syncQueue/photoQueue → auf Shared-Tablets werden User-A's pending Writes
  unter User-B's Token geflusht (Audit-/Integritäts-Fehler). Fix: syncQueue/photoQueue beim Wechsel flushen ODER
  verwerfen. Daten-/Auth-sensibel (falscher Fix = Datenverlust) → Sebastian-Entscheidung.
- **[MITTEL] Login#4 Offline-PW-Hash global statt user-scoped — DOKUMENTIERT** (4478): Zweit-User kann sich auf Shared-
  Tablet nicht offline einloggen. Fix: Hash-Key inkl. user.id.
- **[NIEDRIG] Login#5 bcrypt-fallback schreibt `epkolar_token='bcrypt-fallback'` — DOKUMENTIERT** (2236): irreführender
  localStorage-State (toter Zweig). Fix: Zweig entfernen.

## Bautagebuch (VBautag)
- **[MEDIUM] Bautagebuch#2 autoFillFromEntries schreibt Worker-IDs ungefiltert → ✅ FIX v3.9.166** (12347-12361): unbekannte
  IDs landen roh im Tagesbericht/Export. Fix: `.filter(wid=>(monteure||MONT).some(m=>m.id===wid))`.
- **[MEDIUM] Bautagebuch#1 Offline-Einträge vom Reload überschrieben — DOKUMENTIERT** (12399-12404): `setBtEntries(mapped)`
  unconditional → noch-nicht-geflushte Offline-Einträge weg. Fix: local-only mergen (wie arbeitsscheine Variante A).
  Sync-Merge-Logik → kontrollierter Fix.
- **[LOW] Bautagebuch#3 autoFillWeather ohne r.ok + Datums-Race — DOKUMENTIERT** (12365). **[LOW] #4 Foto-Effect lädt nur
  Server-Fotos — DOKUMENTIERT** (12391). **[INFO] #5 optimistisches delEntry**.

> Verifiziert sauber bestätigt (kein Bug): Stunden/KW-Mathe (ISO, v3.9.158), Prozent-Berechnung (÷0-safe), Token-Refresh
> Single-Flight + Rotation-Race, Permission-Gates (UI+Defense), Temp-Parsing, Datum-Helper.
