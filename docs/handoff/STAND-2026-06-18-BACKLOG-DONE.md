# EPKolar — Backlog-Abschluss 18.06.2026 (read-only verifiziert)

Aufgabe: „Alle offenen technischen Punkte (BLOCK 1–5) der Reihe nach erledigen."
Ergebnis: **BLOCK 1, 2, 3 bereits erledigt; BLOCK 5 sauber; BLOCK 4 blockiert (keine Quelle).**
Alle Befunde read-only gegen Supabase `jiggujpruejkaomgxarp` verifiziert. **Kein Code-Change nötig → keine Schein-Commits** (außer diesem Handoff).

## BLOCK 1 — gefahrstoff_files → privater Bucket ✅ BEREITS ERLEDIGT (v3.9.403)
- Spalte `storage_path` existiert; **59/59 Zeilen befüllt** (alle migriert).
- Bucket `epkolar-gefahrstoff` = **privat** (`public=false`).
- **0** Zeilen mit Legacy-`file_url` → kein öffentlicher Rest-Leak.
- RLS: `SELECT = authenticated`, `ALL (Write) = is_staff()`.
- Code: `SB_GEF_BUCKET="epkolar-gefahrstoff"`, `_sbUploadGef` (→ storage_path), Anzeige `_sbSignedGefUrl` (signiert), `delFile` löscht DB + Storage-Objekt.
- **→ Privacy-Ziel voll erreicht.** Die in der Aufgabe genannte „Migration nach epkolar-docs" ist nicht nötig — gefahrstoff hat einen eigenen, dedizierten privaten Bucket (sauberer als Sammel-Bucket). Keine SQL/Code-Änderung.

## BLOCK 2 — Zombie-Absences ✅ NICHTS ZU TUN
- `SELECT count(*) FROM absences WHERE worker_id IS NULL OR worker_id NOT IN (SELECT id FROM workers)` → **0**.
- Keine verwaisten Einträge. DELETE würde 0 Zeilen treffen. Nicht ausgeführt.

## BLOCK 3 — tickets.page ✅ BEREITS VORHANDEN
- Spalte `tickets.page` **existiert** bereits (information_schema verifiziert). Kein ALTER nötig.

## BLOCK 5 — RLS-Backlog „~15 Tabellen ALL(true)" ✅ LÄNGST GETIGHTENED
- `SELECT … FROM pg_policies WHERE qual='true'` → nur **EINE** Policy:
  `system_config.system_config_select` (SELECT, roles=`{authenticated}`, qual=`true`).
- `system_config` zusätzlich: `system_config_admin_write` (ALL, `current_user_role()='admin'`).
- **Bewertung:** Kein Sicherheitsloch — Lesen nur für **authentifizierte** Nutzer (nicht anon), Schreiben nur admin; system_config enthält App-Konfiguration (nicht-sensibel) und wird von vielen Views gelesen. **Bewusst so gelassen** (deckt sich mit Stand 15.06.: „system_config/juprowa/notif-insert bewusst offen"). Empfehlung: belassen. Falls dennoch gewünscht, einzeiliger Tighten auf eine konkrete Rolle möglich — aber funktional riskant (App liest Config früh).
- Die übrigen ~14 vermuteten ALL(true)-Tabellen (werkzeuge/fahrzeuge/projects/workers/…) sind bereits rollen-/staff-gegated (frühere Härtungswellen).

## BLOCK 4 — Edge Function `sync_supplier` v3 ⛔ BLOCKIERT (keine Quelle)
- `C:\temp\epkfn\supabase\functions` enthält: **`supplier-sync`** + `admin-create-user` — **kein `sync_supplier`**.
- Repo `supabase/functions`: `admin-create-user`, `ocr_tankbeleg`, **`supplier-sync`** — ebenfalls kein `sync_supplier`.
- Die **Live**-Funktion heißt `sync_supplier` (deployed, `verify_jwt=false`), aber **ihr v3-Quellcode liegt nirgends vor** (weder Repo noch C:\temp). → Deploy einer „v3" ist ohne Quelle nicht möglich.
- Zusätzlich: Supabase-CLI ist nicht eingeloggt (`LegacyPlatformAuthRequiredError`, kein `SUPABASE_ACCESS_TOKEN`) → CLI-Deploy generell blockiert; Alternative wäre `deploy_edge_function` via Plugin.
- **ENTSCHEIDUNG Sebastian (18.06.2026): Option 3 — nichts deployen, Live bleibt.**
  sync_supplier-v3-Quelle nicht auffindbar, aktuell kein Handlungsbedarf. Live-`sync_supplier`
  (verify_jwt=false) läuft; Frontend ruft sie ohnehin nicht auf (DATANORM-Import clientseitig
  `_parseDatanormFiles`). **Block geschlossen.** Falls künftig doch ein v3-Sync gebraucht wird:
  Quelle nach `C:\temp\epkfn\supabase\functions\sync_supplier\` legen + via Plugin
  `deploy_edge_function` (CLI ist uneingeloggt).

## Fazit
Stand HEAD `35b2da5` (v3.9.460) bleibt unverändert — alle technischen Backlog-Punkte sind entweder bereits umgesetzt (1/2/3), bewusst belassen (5) oder per Chef-Entscheidung geschlossen (4, kein Deploy). Es wurden keine überflüssigen Migrationen/Commits erzeugt. **Backlog vollständig abgeschlossen.**
