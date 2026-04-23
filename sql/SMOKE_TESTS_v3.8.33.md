# Smoke-Tests v3.8.33 · 2026-04-23

Post-Deploy Checkliste. Vorbedingung für alle: `window.APP_VERSION === "3.8.33-supabase"` in Console, SW aktiv mit `epkolar-v3.8.33`.

## A · v3.8.33 Iter-19 Fixes (NEU — priorisiert)

### A1 · changePassword ohne lokalen Hash (Iter-19a)
- **Vorbedingung**: Test-User mit `password_hash = NULL` in `public.users` (GoTrue-only Account). Admin kann per SQL `UPDATE public.users SET password_hash=NULL WHERE id='<uuid>'` temporär herstellen — vorher Wert sichern!
- **Schritt**: Als dieser User einloggen (über GoTrue geht das), dann Profil → Passwort ändern → Altes PW + Neues PW eingeben → "Ändern".
- **Soll**: Message `⚠️ Dieser Account hat keinen lokalen Passwort-Hash — bitte Admin um Passwort-Reset bitten`. Console: `[changePassword] Kein lokales password_hash für User <id>`.
- **Fail-Diagnose**: Wenn stattdessen "Falsches Passwort" erscheint → Fix nicht aktiv, Source-Check `!users[0].password_hash` fehlt.

### A2 · Offline-PW-Hash PBKDF2 (Iter-19c) — **fresh install**
- **Vorbedingung**: `indexedDB.deleteDatabase('epkolar_offline')` + Hard-Reload (DevTools → Application → Clear storage → Clear site data).
- **Schritt**: Online-Login mit echten Credentials.
- **Soll**: DevTools → Application → IndexedDB → `epkolar_offline` → `meta` → `offlinePwHash` ist ein **Objekt** `{v:1, algo:"PBKDF2-SHA256", iter:100000, salt:"<32-hex>", hash:"<64-hex>"}`.
- **Fail-Diagnose**: Falls immer noch String `"<base64>"` → `_OFFPW.create` nicht aktiv oder Exception geschluckt (Console check `[login] offlinePwHash create failed:`).

### A3 · Offline-PW-Hash PBKDF2 Verify — Offline-Login
- **Vorbedingung**: A2 erfolgreich durchgeführt.
- **Schritt**: DevTools → Network → "Offline"-Mode → Logout (per Offline-Bestätigung) → erneut einloggen mit denselben Credentials.
- **Soll**: Login erfolgreich, Dashboard lädt.
- **Fail-Diagnose**: "Offline — Kein gespeicherter Login" → Hash-Vergleich hat nicht gematched. Console check `[login-offline] verify threw:`.

### A4 · Offline-PW-Hash Legacy-Migration
- **Vorbedingung**: IDB-State ist `offlinePwHash: "<base64-string>"` (Legacy, d.h. vor v3.8.33 eingeloggt und noch nicht neu eingeloggt). Kann manuell hergestellt werden via DevTools → IndexedDB → Edit-Value.
- **Schritt**: Offline gehen → Login → sollte funktionieren (Legacy-Verify). Online gehen → Logout + neuer Online-Login.
- **Soll**: Nach Online-Login ist der Eintrag auf neues PBKDF2-Objekt umgestellt (A2-Format).
- **Fail-Diagnose**: Legacy-String bleibt — Online-Login-Pfad schreibt nicht neu (L3554 Check).

## B · v3.8.32 Observability (Regression-Check)

### B1 · Silent-Catch-Breadcrumbs loggen
- **Schritt**: DevTools Console öffnen, Sync starten (Pull-to-refresh oder Auto-Tick), dann Notification-Prefs-Laden triggern, dann SW-Reload.
- **Soll**: Breadcrumbs `[NOTIF-PREFS]`, `[SW-REG-SETUP]` + (13 verbleibende `.catch(()=>{})` sind intentional leise).

## C · v3.8.31 Kpi-Stagger (Regression-Check)

### C1 · Kpi-Kacheln faden gestaffelt ein
- **Schritt**: Dashboard laden, dann Tab wechseln, wieder zurück.
- **Soll**: Jede Kpi-Kachel erscheint mit 40 ms Delay nacheinander (sichtbare Welle).

## D · v3.8.28-30 Polish (Regression-Check)

### D1 · Tageszeit-Motto
- **Schritt**: Dashboard laden. Morgens/Mittags/Abends unterschiedliche Tageszeit simulieren.
- **Soll**: Motto passt zur Tageszeit (z. B. morgens: Motivation, abends: Ausklang).

### D2 · AS-Save Emoji-Rotation
- **Schritt**: AS öffnen, speichern, erneut öffnen+speichern (3×).
- **Soll**: Success-Toast zeigt jedes Mal ein anderes Emoji. Bei Auto-Close (Status=erledigt) Celebration-Set.

### D3 · App-Header Last-Sync-Indikator
- **Schritt**: Nach Auto-Sync warten 30 s.
- **Soll**: Header rechts zeigt `⏱ vor X Min`. Aktualisiert sich alle 30 s.

### D4 · Gewerk-Filter (Material-Bestellung)
- **Vorbedingung**: User-Profil → Gewerk auf "Elektriker" setzen.
- **Schritt**: Material-Bestellung öffnen.
- **Soll**: Nur Elektro-Kataloge sichtbar. Mit "Installateur" umgekehrt. Mit "Beide" alles.

### D5 · Upload-Toast-Fehler
- **Vorbedingung**: DevTools → Network → Offline-Mode oder Fehler-Intercept.
- **Schritt**: Foto/Plan/Abwesenheits-File hochladen.
- **Soll**: Fehler-Toast (rot) statt stummer Fail.

## E · Core-Flow Smoke (Cross-User-Isolation, Iter 11/17/12 Regression-Check)

### E1 · Logout + Login-Wechsel Admin↔Monteur (Iter 11/17)
- **Schritt**: Admin einloggen → Daten sichten → Logout → Monteur einloggen → Daten sichten → Logout → Admin wieder einloggen.
- **Soll**: Monteur sieht KEINE Admin-Daten im Cache. Nach Admin-Relogin alle Daten wieder da. Keine Präferenzen-Leak (Theme/Fav pro User).

### E2 · Photo-Capture als Monteur (Iter 12)
- **Schritt**: Als Monteur AS öffnen → Foto aufnehmen → speichern.
- **Soll**: In `photos`-Tabelle hat Row `uploaded_by = <monteur-uuid>` (per SQL prüfen: `SELECT uploaded_by,created_at FROM photos ORDER BY created_at DESC LIMIT 1;`).

### E3 · _selfTest Role-Check (Iter 13)
- **Schritt**: Als Monteur `window._selfTest({mode:"quick"})` in Console.
- **Soll**: Role `monteur`, id = korrekte UUID (nicht `unknown`).

### E4 · `window._curUser()` gibt akt. User
- **Schritt**: In Console `window._curUser()`.
- **Soll**: Objekt `{id, username, role, ...}` für aktuellen User.

## F · B-020 Login-Smoke (ausstehend für Sebastian)

5 User: paschinger, barger, cracana, pinger, schmid. Pro User: Login OK, Dashboard lädt, Logout OK. B-020 Error-Codes (B20-A..H) dürfen nicht aufpoppen.

---

**Bei Fail**: Screenshot + Console-Ausgabe + `window._selfTest({mode:"full"})` Output sammeln, dann Issue.
